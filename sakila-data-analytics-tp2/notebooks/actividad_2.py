import sys
import os
import pandas as pd
from sqlalchemy import text

# Agregar la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_conexion import obtener_motor
from esquema import TABLAS, COLUMNAS

motor = obtener_motor()


# ==========================================================
# ACTIVIDAD 2 - PERFILADO Y CALIDAD DE DATOS
# ==========================================================


# ==========================================================
# 1. CARGAR EL CONJUNTO DE TRABAJO
# ==========================================================

query_raw = f"""
SELECT 
    a.{COLUMNAS['rental_id']}        AS rental_id,
    a.{COLUMNAS['rental_date']}      AS rental_date,
    a.{COLUMNAS['return_date']}      AS return_date,

    c.{COLUMNAS['customer_id']}      AS customer_id,
    c.{COLUMNAS['first_name']}       AS first_name,
    c.{COLUMNAS['last_name']}        AS last_name,

    p.{COLUMNAS['film_id']}          AS film_id,
    p.{COLUMNAS['title']}            AS title,
    p.{COLUMNAS['rental_duration']}  AS rental_duration,
    p.{COLUMNAS['replacement_cost']} AS replacement_cost,
    p.{COLUMNAS['rental_rate']}      AS rental_rate,

    cat.{COLUMNAS['name']}           AS category

FROM {TABLAS['rental']} a

INNER JOIN {TABLAS['inventory']} i 
    ON a.{COLUMNAS['inventory_id']} = i.{COLUMNAS['inventory_id']}

INNER JOIN {TABLAS['film']} p 
    ON i.{COLUMNAS['film_id']} = p.{COLUMNAS['film_id']}

INNER JOIN {TABLAS['customer']} c 
    ON a.{COLUMNAS['customer_id']} = c.{COLUMNAS['customer_id']}

LEFT JOIN {TABLAS['film_category']} pc 
    ON p.{COLUMNAS['film_id']} = pc.{COLUMNAS['film_id']}

LEFT JOIN {TABLAS['category']} cat 
    ON pc.{COLUMNAS['category_id']} = cat.{COLUMNAS['category_id']}
"""

df = pd.read_sql(
    text(query_raw),
    motor
)

# Conversión explícita de fechas
df['rental_date'] = pd.to_datetime(
    df['rental_date']
)

df['return_date'] = pd.to_datetime(
    df['return_date']
)


# ==========================================================
# 2. RECONOCIMIENTO GENERAL DEL DATASET
# ==========================================================

print("\n==================================================")
print("1. RECONOCIMIENTO GENERAL")
print("==================================================")

print(
    f"\nDimensiones: "
    f"{df.shape[0]} filas x {df.shape[1]} columnas"
)

print("\nTIPOS DE DATOS:")
print(df.dtypes)

print("\nPRIMERAS FILAS:")
print(df.head())

print("\nMUESTRA ALEATORIA:")
print(
    df.sample(
        min(5, len(df)),
        random_state=42
    )
)

print("\nINFORMACIÓN GENERAL:")
df.info()

print("\nESTADÍSTICAS DESCRIPTIVAS:")

columnas_numericas = [
    'rental_duration',
    'replacement_cost',
    'rental_rate'
]

print(
    df[columnas_numericas].describe(
        percentiles=[
            0.01,
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
            0.99
        ]
    )
)


# ==========================================================
# 3. VALORES NULOS
# ==========================================================

print("\n==================================================")
print("2. VALORES NULOS")
print("==================================================")

nulos = df.isnull().sum()

pct_nulos = (
    nulos / len(df)
) * 100

df_nulos = pd.DataFrame({
    'Nulos': nulos,
    'Porcentaje (%)': pct_nulos
})

print(df_nulos)


# ==========================================================
# 4. DUPLICADOS SEGÚN CLAVE DE NEGOCIO
# ==========================================================

print("\n==================================================")
print("3. DUPLICADOS")
print("==================================================")

duplicados_pk = df.duplicated(
    subset=['rental_id']
).sum()

print(
    f"Duplicados por rental_id: "
    f"{duplicados_pk}"
)


# ==========================================================
# 5. CONTROL ESPECÍFICO:
#    ALQUILERES SIN DEVOLUCIÓN
# ==========================================================

print("\n==================================================")
print("4. ALQUILERES SIN DEVOLUCIÓN")
print("==================================================")

sin_devolucion = df[
    df['return_date'].isna()
].copy()

total_sin_dev = len(
    sin_devolucion
)

pct_sin_dev = (
    total_sin_dev / len(df)
) * 100

print(
    f"Cantidad: {total_sin_dev}"
)

print(
    f"Porcentaje: {pct_sin_dev:.2f}%"
)

print("""
Diagnóstico:
Una fecha de devolución NULL no se interpreta automáticamente
como un error de calidad.

En esta variante representa un dato censurado a derecha:
el alquiler todavía no registra una devolución y, por lo tanto,
no se conoce su atraso definitivo.

Estos registros se conservan y se analizan separadamente.
""")


# ==========================================================
# 6. REGLA DE NEGOCIO 1
#    DEVOLUCIÓN ANTERIOR AL ALQUILER
# ==========================================================

print("\n==================================================")
print("5. REGLAS DE NEGOCIO")
print("==================================================")

viajes_tiempo = df[
    df['return_date'].notna()
    &
    (
        df['return_date']
        < df['rental_date']
    )
]

print(
    "Regla 1 - devolución anterior al alquiler: "
    f"{len(viajes_tiempo)} violaciones"
)


# ==========================================================
# 7. CONTROL ESPECÍFICO:
#    PERÍODO PACTADO DE ALQUILER
# ==========================================================

print("\nDistribución de rental_duration:")

print(
    df['rental_duration'].describe()
)

# Una duración pactada debe ser positiva.
# Como control adicional se marca como sospechoso cualquier
# valor superior a 30 días.

periodos_invalidos = df[
    (df['rental_duration'] <= 0)
    |
    (df['rental_duration'] > 30)
]

print(
    "Períodos pactados fuera del rango razonable: "
    f"{len(periodos_invalidos)}"
)


# ==========================================================
# 8. REGLA DE NEGOCIO 2
#    COSTO DE REPOSICIÓN
# ==========================================================

costos_invalidos = df[
    df['replacement_cost'] <= 0
]

print(
    "Regla 2 - costo de reposición <= 0: "
    f"{len(costos_invalidos)} violaciones"
)


# ==========================================================
# 9. CÁLCULO DE DÍAS DE PRÉSTAMO Y DÍAS DE ATRASO
# ==========================================================

df_devueltos = df[
    df['return_date'].notna()
].copy()

df_devueltos['dias_prestamo'] = (
    df_devueltos['return_date']
    -
    df_devueltos['rental_date']
).dt.total_seconds() / 86400.0


# Métrica principal:
#
# atraso = duración real - duración pactada
#
# Si el resultado es negativo significa que fue devuelto
# antes del vencimiento, por lo que el atraso se considera 0.

df_devueltos['dias_atraso'] = (
    df_devueltos['dias_prestamo']
    -
    df_devueltos['rental_duration']
).clip(lower=0)


print("\nResumen de días de atraso:")

print(
    df_devueltos['dias_atraso'].describe(
        percentiles=[
            0.01,
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
            0.99
        ]
    )
)


# ==========================================================
# 10. OUTLIERS MEDIANTE IQR
# ==========================================================

print("\n==================================================")
print("6. OUTLIERS DE DÍAS DE ATRASO - MÉTODO IQR")
print("==================================================")

q1 = df_devueltos[
    'dias_atraso'
].quantile(0.25)

q3 = df_devueltos[
    'dias_atraso'
].quantile(0.75)

iqr = q3 - q1

lim_inf = q1 - 1.5 * iqr
lim_sup = q3 + 1.5 * iqr

outliers = df_devueltos[
    (
        df_devueltos['dias_atraso']
        < lim_inf
    )
    |
    (
        df_devueltos['dias_atraso']
        > lim_sup
    )
]

print(
    f"Q1: {q1:.2f} días"
)

print(
    f"Q3: {q3:.2f} días"
)

print(
    f"IQR: {iqr:.2f} días"
)

print(
    f"Límite inferior: "
    f"{lim_inf:.2f} días"
)

print(
    f"Límite superior: "
    f"{lim_sup:.2f} días"
)

print(
    f"Cantidad de outliers: "
    f"{len(outliers)}"
)


# ==========================================================
# 11. INSPECCIÓN DE OUTLIERS
# ==========================================================

if len(outliers) > 0:

    print("\nEjemplos de valores atípicos:")

    columnas_outliers = [
        'rental_id',
        'customer_id',
        'title',
        'rental_date',
        'return_date',
        'rental_duration',
        'dias_prestamo',
        'dias_atraso'
    ]

    print(
        outliers[
            columnas_outliers
        ]
        .sort_values(
            'dias_atraso',
            ascending=False
        )
        .head(20)
    )

print("""
Los valores identificados mediante IQR no se eliminan
automáticamente.

El método IQR identifica observaciones estadísticamente
atípicas, pero eso no demuestra que sean errores.

Se conservan mientras no violen una regla de negocio o exista
evidencia adicional de un error de carga.
""")


# ==========================================================
# 12. CONTROL ESPEJO EN SQL SERVER
# ==========================================================

print("\n==================================================")
print("7. COMPARACIÓN CON SQL SERVER")
print("==================================================")

query_espejo_raw = f"""
SELECT

    COUNT(
        CASE
            WHEN {COLUMNAS['return_date']} IS NULL
            THEN 1
        END
    ) AS nulos_devolucion,

    COUNT(
        CASE
            WHEN {COLUMNAS['return_date']}
                 < {COLUMNAS['rental_date']}
            THEN 1
        END
    ) AS violaciones_fechas

FROM {TABLAS['rental']}
"""

df_espejo = pd.read_sql(
    text(query_espejo_raw),
    motor
)

sql_nulos = int(
    df_espejo.iloc[0][
        'nulos_devolucion'
    ]
)

sql_fechas = int(
    df_espejo.iloc[0][
        'violaciones_fechas'
    ]
)

print(
    "Alquileres sin devolución:"
)

print(
    f"SQL Server: {sql_nulos}"
)

print(
    f"Pandas:     {total_sin_dev}"
)

print(
    "\nDevoluciones anteriores al alquiler:"
)

print(
    f"SQL Server: {sql_fechas}"
)

print(
    f"Pandas:     {len(viajes_tiempo)}"
)


# ==========================================================
# 13. VALIDACIÓN AUTOMÁTICA
# ==========================================================

print("\n==================================================")
print("8. VALIDACIÓN")
print("==================================================")

if sql_nulos == total_sin_dev:
    print(
        "OK - El conteo de alquileres sin devolución coincide."
    )
else:
    print(
        "ERROR - El conteo de alquileres sin devolución no coincide."
    )

if sql_fechas == len(viajes_tiempo):
    print(
        "OK - El control de fechas coincide."
    )
else:
    print(
        "ERROR - El control de fechas no coincide."
    )


# ==========================================================
# 14. RESUMEN DEL DIAGNÓSTICO
# ==========================================================

print("\n==================================================")
print("RESUMEN DEL DIAGNÓSTICO")
print("==================================================")

print(
    f"Registros analizados: {len(df)}"
)

print(
    f"Alquileres devueltos: {len(df_devueltos)}"
)

print(
    f"Alquileres sin devolución: {total_sin_dev}"
)

print(
    f"Duplicados: {duplicados_pk}"
)

print(
    f"Violaciones temporales: {len(viajes_tiempo)}"
)

print(
    f"Períodos pactados sospechosos: "
    f"{len(periodos_invalidos)}"
)

print(
    f"Costos de reposición inválidos: "
    f"{len(costos_invalidos)}"
)

print(
    f"Outliers de atraso mediante IQR: "
    f"{len(outliers)}"
)

print("""
Decisión general de limpieza:

- No eliminar los alquileres sin devolución, porque representan
  observaciones censuradas relevantes para el análisis de morosidad.

- No imputar una fecha de devolución ficticia.

- No eliminar automáticamente los valores atípicos identificados
  mediante IQR.

- Investigar y excluir únicamente registros que violen reglas de
  negocio comprobables, documentando la decisión tomada.

- Mantener separados los alquileres devueltos y los no devueltos
  cuando se calculen métricas cuyo valor definitivo dependa de la
  fecha de devolución.
""")