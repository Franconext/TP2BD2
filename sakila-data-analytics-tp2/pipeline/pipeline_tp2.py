#!/usr/bin/env python
"""
Pipeline ETL - TP2 Equipo 4 - Variante 4: Morosidad y devoluciones fuera de término.

Orígenes:
    1. SQL Server: conjunto de trabajo (alquiler + inventario + película + cliente + categoría).
    2. Archivo plano pipeline/datos/multas_por_categoria.csv (multa diaria por categoría).
Destino:
    Tabla TP2_MorosidadPorCliente, en la misma base (una fila por cliente).

Uso (desde la raíz del repo, con el venv activado):
    python pipeline/pipeline_tp2.py
    python pipeline/pipeline_tp2.py --desde 2005-01-01
    python pipeline/pipeline_tp2.py --simulacion        # hace todo menos escribir en la base

Códigos de salida:  0 = terminó bien  |  1 = falló (la traza queda en el log).

IDEMPOTENCIA: la carga hace DELETE + INSERT dentro de UNA sola transacción, sobre una tabla
con clave primaria id_cliente. Además la salida depende solo de los datos de entrada
(la fecha de corte sale de los datos, no de la fecha de hoy). Correrlo N veces deja siempre
la misma tabla; si algo falla a mitad de la carga, se hace rollback y queda como estaba.

CONSULTAS: los NOMBRES de tablas/columnas salen de esquema.py (único lugar con nombres
propios) y la consulta se arma con SQLAlchemy Core, sin f-strings. El único VALOR variable
(la fecha 'desde') viaja como parámetro.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import (Column, Date, Integer, MetaData, Numeric, Table, Unicode,
                        bindparam, column, func, select, table)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from config_conexion import obtener_motor        # noqa: E402
from esquema import TABLAS as T, COLUMNAS as C    # noqa: E402

TABLA_DESTINO = "TP2_MorosidadPorCliente"
ARCHIVO_MULTAS = RAIZ / "pipeline" / "datos" / "multas_por_categoria.csv"
DIR_LOGS = RAIZ / "pipeline" / "logs"
DESDE_POR_DEFECTO = "2000-01-01"
MULTA_POR_DEFECTO = 0.75          # USD/día para categorías que no figuren en el archivo plano
PLAZO_MIN, PLAZO_MAX = 1, 30      # rango razonable del período de alquiler pactado (días)

COLUMNAS_DESTINO = [
    "id_cliente", "nombre", "apellido", "total_alquileres", "devueltos", "no_devueltos",
    "alquileres_morosos", "tasa_morosidad_pct", "atraso_prom_excluyendo",
    "atraso_prom_cota_minima", "exposicion_reposicion", "multa_estimada", "fecha_corte",
]

log = logging.getLogger("pipeline_tp2")


# =============================================================================
# EXTRAER
# =============================================================================
def construir_consulta():
    """Conjunto de trabajo de la variante 4, armado con SQLAlchemy Core."""
    def tabla(canon, columnas, alias):
        return table(T[canon], *[column(C[c]) for c in columnas]).alias(alias)

    a = tabla("rental", ["rental_id", "rental_date", "return_date", "customer_id", "inventory_id"], "a")
    i = tabla("inventory", ["inventory_id", "film_id"], "i")
    p = tabla("film", ["film_id", "title", "rental_duration", "rental_rate", "replacement_cost"], "p")
    c = tabla("customer", ["customer_id", "first_name", "last_name"], "c")
    pc = tabla("film_category", ["film_id", "category_id"], "pc")
    cat = tabla("category", ["category_id", "name"], "cat")

    def col(t, canon):
        return t.c[C[canon]]

    union = (a.join(i, col(a, "inventory_id") == col(i, "inventory_id"))
              .join(p, col(i, "film_id") == col(p, "film_id"))
              .join(c, col(a, "customer_id") == col(c, "customer_id"))
              .outerjoin(pc, col(p, "film_id") == col(pc, "film_id"))
              .outerjoin(cat, col(pc, "category_id") == col(cat, "category_id")))

    return (select(col(a, "rental_id").label("rental_id"),
                   col(a, "rental_date").label("rental_date"),
                   col(a, "return_date").label("return_date"),
                   col(c, "customer_id").label("customer_id"),
                   col(c, "first_name").label("first_name"),
                   col(c, "last_name").label("last_name"),
                   col(p, "film_id").label("film_id"),
                   col(p, "title").label("title"),
                   col(p, "rental_duration").label("rental_duration"),
                   col(p, "replacement_cost").label("replacement_cost"),
                   col(p, "rental_rate").label("rental_rate"),
                   col(cat, "name").label("category"))
            .select_from(union)
            .where(col(a, "rental_date") >= bindparam("desde"))
            .order_by(col(a, "rental_date")))


def extraer_alquileres(motor, desde: datetime) -> pd.DataFrame:
    """Origen 1: SQL Server. El filtro de fecha viaja por params."""
    df = pd.read_sql(construir_consulta(), motor, params={"desde": desde})
    df["rental_date"] = pd.to_datetime(df["rental_date"])
    df["return_date"] = pd.to_datetime(df["return_date"])
    for nombre in ("rental_duration", "replacement_cost", "rental_rate"):
        df[nombre] = pd.to_numeric(df[nombre])
    return df


def extraer_multas(ruta: Path = ARCHIVO_MULTAS, alquileres: pd.DataFrame | None = None) -> pd.DataFrame:
    """Lee el CSV; si falta, lo crea con categorías reales y una tarifa de ejemplo."""
    ruta = Path(ruta)
    if not ruta.is_file():
        if alquileres is None or alquileres.empty:
            raise FileNotFoundError(f"No existe el CSV complementario: {ruta}")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        categorias = alquileres["category"].dropna().astype(str).drop_duplicates().sort_values()
        if categorias.empty:
            raise ValueError("No hay categorías para generar el CSV")
        pd.DataFrame({"categoria": categorias.to_numpy(),
                      "multa_por_dia_usd": MULTA_POR_DEFECTO}).to_csv(
                          ruta, index=False, encoding="utf-8")
        log.warning("Se creó %s con tarifa de EJEMPLO %.2f USD/día; revisarla antes de entregar",
                    ruta, MULTA_POR_DEFECTO)
    df = pd.read_csv(ruta, encoding="utf-8")
    necesarias = {"categoria", "multa_por_dia_usd"}
    if not necesarias.issubset(df.columns):
        raise ValueError(f"{ruta.name}: faltan columnas {sorted(necesarias - set(df.columns))}")
    if df["categoria"].isna().any() or df["categoria"].duplicated().any():
        raise ValueError(f"{ruta.name}: categorías vacías o repetidas")
    df["multa_por_dia_usd"] = pd.to_numeric(df["multa_por_dia_usd"], errors="coerce")
    if df["multa_por_dia_usd"].isna().any() or (df["multa_por_dia_usd"] < 0).any():
        raise ValueError(f"{ruta.name}: multas inválidas")
    return df


# =============================================================================
# TRANSFORMAR
# =============================================================================
def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza justificada en la Actividad 2: se apartan (y se cuentan) los registros imposibles.

    NO se descartan los alquileres sin devolución: son datos censurados, no errores.
    """
    n0 = len(df)
    df = df.drop_duplicates(subset=["rental_id"], keep="first")
    log.info("Duplicados por rental_id eliminados: %d", n0 - len(df))

    fechas_invertidas = df["return_date"].notna() & (df["return_date"] < df["rental_date"])
    plazo_invalido = ~df["rental_duration"].between(PLAZO_MIN, PLAZO_MAX)
    costo_invalido = ~(df["replacement_cost"] > 0)
    log.info("Reglas de negocio violadas | devolución anterior al alquiler: %d | "
             "plazo fuera de [%d, %d]: %d | costo de reposición <= 0: %d",
             int(fechas_invertidas.sum()), PLAZO_MIN, PLAZO_MAX,
             int(plazo_invalido.sum()), int(costo_invalido.sum()))

    df = df[~(fechas_invertidas | plazo_invalido | costo_invalido)].copy()
    log.info("Filas apartadas por reglas de negocio: %d", n0 - len(df))
    return df


def calcular_atraso(df: pd.DataFrame, fecha_corte: pd.Timestamp) -> pd.DataFrame:
    """Días de atraso por alquiler con DATOS CENSURADOS. Todo vectorizado.

    - Devuelto:    atraso = días(alquiler -> devolución) - plazo pactado.
    - No devuelto: el atraso real se DESCONOCE; solo se sabe que es AL MENOS
                   días(alquiler -> fecha de corte) - plazo pactado (cota inferior).
    - Un valor negativo (devolución anticipada) se informa como 0 días de atraso.
    """
    df = df.copy()
    df["devuelto"] = df["return_date"].notna()

    dias_a_devolucion = (df["return_date"] - df["rental_date"]).dt.total_seconds() / 86400.0
    dias_a_corte = (fecha_corte - df["rental_date"]).dt.total_seconds() / 86400.0

    atraso_devueltos = dias_a_devolucion - df["rental_duration"]              # NaN si no devuelto
    atraso_minimo_no_devueltos = dias_a_corte - df["rental_duration"]         # cota inferior

    atraso = atraso_devueltos.where(df["devuelto"], atraso_minimo_no_devueltos)
    df["atraso_dias"] = atraso.clip(lower=0)
    df["moroso"] = df["atraso_dias"] > 0
    return df


def agregar_por_cliente(df: pd.DataFrame, fecha_corte: pd.Timestamp) -> pd.DataFrame:
    """Una fila por cliente, con las dos decisiones sobre los no devueltos."""
    d = df.assign(
        atraso_solo_devueltos=df["atraso_dias"].where(df["devuelto"]),             # decisión A: excluir
        costo_no_devuelto=df["replacement_cost"].astype(float).where(~df["devuelto"], 0.0),
        multa_estimada=df["atraso_dias"] * df["multa_por_dia_usd"],
    )
    out = d.groupby("customer_id").agg(
        nombre=("first_name", "first"),
        apellido=("last_name", "first"),
        total_alquileres=("rental_id", "count"),
        devueltos=("devuelto", "sum"),
        alquileres_morosos=("moroso", "sum"),
        atraso_prom_excluyendo=("atraso_solo_devueltos", "mean"),                  # A: excluye no devueltos
        atraso_prom_cota_minima=("atraso_dias", "mean"),                           # B: imputa la cota mínima
        exposicion_reposicion=("costo_no_devuelto", "sum"),
        multa_estimada=("multa_estimada", "sum"),
    ).reset_index().rename(columns={"customer_id": "id_cliente"})

    out["no_devueltos"] = out["total_alquileres"] - out["devueltos"]
    out["tasa_morosidad_pct"] = out["alquileres_morosos"] / out["total_alquileres"] * 100
    out["fecha_corte"] = fecha_corte.date()

    for nombre in ("total_alquileres", "devueltos", "no_devueltos", "alquileres_morosos"):
        out[nombre] = out[nombre].astype(int)
    for nombre in ("tasa_morosidad_pct", "atraso_prom_excluyendo", "atraso_prom_cota_minima"):
        out[nombre] = out[nombre].round(4)
    for nombre in ("exposicion_reposicion", "multa_estimada"):
        out[nombre] = out[nombre].round(2)
    return out[COLUMNAS_DESTINO].sort_values("id_cliente").reset_index(drop=True)


def transformar(alquileres: pd.DataFrame, multas: pd.DataFrame) -> pd.DataFrame:
    """Limpia, combina los dos orígenes (merge), calcula la métrica y agrega por cliente."""
    if alquileres.empty:
        raise ValueError("La extracción devolvió 0 alquileres: se aborta antes de tocar el destino")

    df = limpiar(alquileres)

    # Fecha de corte = último evento registrado en los datos (NO la fecha de hoy): así el
    # resultado depende solo de los datos y el pipeline es repetible.
    fecha_corte = max(df["rental_date"].max(), df["return_date"].max())
    log.info("Fecha de corte (último evento registrado): %s", fecha_corte)

    df = df.merge(multas, how="left", left_on="category", right_on="categoria", validate="m:1")
    sin_multa = int(df["multa_por_dia_usd"].isna().sum())
    if sin_multa:
        log.warning("%d alquileres sin multa en el archivo plano; se usa %.2f USD/día",
                    sin_multa, MULTA_POR_DEFECTO)
        df["multa_por_dia_usd"] = df["multa_por_dia_usd"].fillna(MULTA_POR_DEFECTO)

    df = calcular_atraso(df, fecha_corte)
    log.info("Alquileres sin devolución (censurados): %d", int((~df["devuelto"]).sum()))
    return agregar_por_cliente(df, fecha_corte)


# =============================================================================
# CARGAR
# =============================================================================
def definir_tabla_destino(metadata: MetaData, nombre: str) -> Table:
    return Table(
        nombre, metadata,
        Column("id_cliente", Integer, primary_key=True, autoincrement=False),
        Column("nombre", Unicode(100)),
        Column("apellido", Unicode(100)),
        Column("total_alquileres", Integer),
        Column("devueltos", Integer),
        Column("no_devueltos", Integer),
        Column("alquileres_morosos", Integer),
        Column("tasa_morosidad_pct", Numeric(8, 4)),
        Column("atraso_prom_excluyendo", Numeric(10, 4)),
        Column("atraso_prom_cota_minima", Numeric(10, 4)),
        Column("exposicion_reposicion", Numeric(12, 2)),
        Column("multa_estimada", Numeric(12, 2)),
        Column("fecha_corte", Date),
    )


def cargar(df: pd.DataFrame, motor, nombre_tabla: str = TABLA_DESTINO, simulacion: bool = False) -> int:
    """Carga idempotente: DELETE + INSERT en una única transacción (todo o nada)."""
    if simulacion:
        log.info("[simulación] Se habrían cargado %d filas en %s", len(df), nombre_tabla)
        return 0

    metadata = MetaData()
    destino = definir_tabla_destino(metadata, nombre_tabla)
    metadata.create_all(motor, checkfirst=True)

    with motor.begin() as conexion:                 # commit al salir; rollback si hay excepción
        conexion.execute(destino.delete())
        df.to_sql(nombre_tabla, conexion, if_exists="append", index=False, chunksize=1000)

    with motor.connect() as conexion:
        return int(conexion.execute(select(func.count()).select_from(destino)).scalar_one())


# =============================================================================
# ORQUESTACIÓN
# =============================================================================
def ejecutar_pipeline(desde: str = DESDE_POR_DEFECTO, nombre_tabla: str = TABLA_DESTINO,
                      archivo_multas: Path = ARCHIVO_MULTAS, simulacion: bool = False) -> int:
    """Ejecuta las tres etapas. Registra con log.exception y RELANZA cualquier error."""
    try:
        log.info("=== Inicio del pipeline ===")
        fecha_desde = datetime.strptime(desde, "%Y-%m-%d")
        motor = obtener_motor()

        log.info("[EXTRAER] inicio")
        alquileres = extraer_alquileres(motor, fecha_desde)
        multas = extraer_multas(archivo_multas, alquileres)
        log.info("[EXTRAER] fin | alquileres=%d | categorías en archivo plano=%d",
                 len(alquileres), len(multas))

        log.info("[TRANSFORMAR] inicio")
        resultado = transformar(alquileres, multas)
        log.info("[TRANSFORMAR] fin | clientes=%d", len(resultado))

        log.info("[CARGAR] inicio | destino=%s", nombre_tabla)
        en_destino = cargar(resultado, motor, nombre_tabla, simulacion)
        if simulacion:
            log.info("[CARGAR] fin | simulación: no se escribió nada en la base")
        else:
            log.info("[CARGAR] fin | filas cargadas=%d | filas en la tabla destino=%d",
                     len(resultado), en_destino)

        log.info("=== Pipeline finalizado correctamente ===")
        return len(resultado)
    except Exception:
        log.exception("El pipeline falló")
        raise                                       # no se silencia: el código de salida será != 0


def configurar_logging() -> None:
    DIR_LOGS.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)
    raiz.handlers.clear()
    for handler in (logging.StreamHandler(sys.stdout),
                    logging.FileHandler(DIR_LOGS / "pipeline_tp2.log", encoding="utf-8")):
        handler.setFormatter(formato)
        raiz.addHandler(handler)


def parsear_argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline ETL TP2 - Morosidad por cliente")
    p.add_argument("--desde", default=DESDE_POR_DEFECTO,
                   help="Fecha mínima de alquiler a procesar (AAAA-MM-DD). Por defecto: todo el historial")
    p.add_argument("--tabla-destino", default=TABLA_DESTINO, help="Tabla destino en SQL Server")
    p.add_argument("--archivo-multas", type=Path, default=ARCHIVO_MULTAS,
                   help="CSV complementario con la multa diaria por categoría")
    p.add_argument("--simulacion", action="store_true", help="Ejecuta todo sin escribir en la base")
    return p.parse_args()


def main() -> int:
    args = parsear_argumentos()
    configurar_logging()
    try:
        ejecutar_pipeline(args.desde, args.tabla_destino, args.archivo_multas, args.simulacion)
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


