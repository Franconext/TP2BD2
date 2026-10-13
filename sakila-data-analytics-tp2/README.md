# TP2 · Equipo 04 — Morosidad y devoluciones fuera de término

Seminario de Actualización 2026 · Sakila migrada a SQL Server + Python (pandas, SQLAlchemy, matplotlib, seaborn)

**Variante 4.** Pregunta de negocio: *¿cuánto se demoran los clientes en devolver las películas y cuánto expone eso al negocio? ¿Qué perfil tiene el cliente moroso?*

**Integrantes:** _completar_

---

## 1. Qué hace este proyecto

Toma la base **Sakila** (videoclub) ya migrada a SQL Server y responde la pregunta de negocio en cinco pasos:

| Paso | Qué se hace | Dónde está |
|---|---|---|
| Actividad 0 | Reconciliar la base migrada contra el volcado original (conteo de filas por tabla) | `generar_reconciliacion.py` → `sql/reconciliacion.csv` |
| Actividad 1 | Integrar SQL y Python: extraer el conjunto de trabajo con una consulta parametrizada y comparar una misma métrica calculada en T-SQL y en pandas | `notebooks/analisis.ipynb` |
| Actividad 2 | Perfilar los datos y diagnosticar su calidad (nulos, duplicados, fechas imposibles, atípicos) | `notebooks/analisis.ipynb` |
| Actividad 3 | Calcular el atraso, comparar categorías y clientes, y comunicar hallazgos con gráficos | `notebooks/analisis.ipynb` → `graficos/` |
| Actividad 4 | Pipeline ETL repetible que carga el resultado por cliente en SQL Server | `pipeline/pipeline_tp2.py` → tabla `TP2_MorosidadPorCliente` |

---

## 2. Estructura del repositorio

```
TP2BD2/
├── README.md
├── requirements.txt                  # dependencias (pip freeze del entorno virtual)
├── .gitignore
└── sakila-data-analytics-tp2/        # todo el código se ejecuta desde acá
    ├── config_conexion.py            # crea el engine de SQLAlchemy (sin credenciales)
    ├── esquema.py                    # diccionario de nombres: canónico (Sakila) -> nombre real en SQL Server
    ├── probar_conexion.py            # verifica la conexión
    ├── generar_reconciliacion.py     # Actividad 0
    ├── sql/
    │   ├── conjunto_trabajo.sql      # el conjunto de trabajo, escrito en T-SQL (referencia)
    │   └── reconciliacion.csv        # resultado de la Actividad 0
    ├── notebooks/
    │   ├── analisis.ipynb            # Actividades 0 a 3
    │   └── actividad_1.py … actividad_3.py   # versiones iniciales en script
    ├── pipeline/
    │   ├── pipeline_tp2.py           # Actividad 4
    │   ├── datos/multas_por_categoria.csv    # archivo plano complementario
    │   └── logs/pipeline_tp2.log     # registro de las ejecuciones
    └── graficos/                     # PNG exportados por el notebook (150 dpi)
```

---

## 3. Requisitos

- Windows con **SQL Server** (el proyecto se probó con una instancia `localhost\SQLEXPRESS`) y la base **Sakila migrada**.
- **ODBC Driver 17 for SQL Server** instalado en la máquina cliente.
- **Python 3.11** o superior.
- Librerías principales: `pandas`, `SQLAlchemy`, `pyodbc`, `matplotlib`, `seaborn`, `numpy` (versiones exactas en `requirements.txt`).

**Controlador elegido: `pyodbc` (a través de SQLAlchemy).** Es el controlador sobre el que SQLAlchemy arma la conexión a SQL Server y el enfoque que recomienda el apunte de la Unidad 5 para trabajar con pandas (`read_sql` / `to_sql`).

---

## 4. Instalación

Desde la raíz del repositorio:

```bash
python -m venv venv_tp2
venv_tp2\Scripts\activate.bat          # Windows CMD   (PowerShell: venv_tp2\Scripts\Activate.ps1)
pip install -r requirements.txt
cd sakila-data-analytics-tp2
```

> Todos los comandos siguientes se ejecutan desde la carpeta `sakila-data-analytics-tp2/`, con el entorno virtual activado.

---

## 5. Conexión a la base (sin credenciales en el código)

`config_conexion.py` usa **Autenticación Integrada de Windows** (`Trusted_Connection=yes`): no hay usuario ni contraseña escritos en ningún archivo. Los datos de conexión se pueden cambiar con variables de entorno:

| Variable | Valor por defecto | Para qué sirve |
|---|---|---|
| `DB_SERVER` | `localhost\SQLEXPRESS` | Servidor / instancia |
| `DB_NAME` | `sakila` | Nombre de la base migrada |
| `DB_DRIVER` | `ODBC Driver 17 for SQL Server` | Controlador ODBC |

```bash
set DB_SERVER=localhost\SQLEXPRESS
set DB_NAME=sakila
python probar_conexion.py
```

> Si la máquina solo tiene el **ODBC Driver 18**, la conexión cifrada es obligatoria por defecto: hay que agregar `Encrypt` y `TrustServerCertificate` a la cadena de conexión en `config_conexion.py`.

---

## 6. Cómo ejecutar cada parte

### Actividad 0 · Reconciliación
```bash
python generar_reconciliacion.py       # imprime la tabla y la guarda en sql/reconciliacion.csv
```
Compara la cantidad de filas de cada tabla en SQL Server contra la del volcado original de Sakila.

### Actividades 1 a 3 · Notebook
Abrir `notebooks/analisis.ipynb` en VS Code o JupyterLab con el kernel del entorno `venv_tp2` y ejecutar **Kernel → Restart & Run All**. Al terminar quedan los gráficos en `graficos/`.

### Actividad 4 · Pipeline ETL
```bash
python pipeline/pipeline_tp2.py                    # corrida normal: carga TP2_MorosidadPorCliente
python pipeline/pipeline_tp2.py --desde 2005-01-01 # solo alquileres desde esa fecha
python pipeline/pipeline_tp2.py --simulacion       # ejecuta todo menos escribir en la base
```
Código de salida **0** si terminó bien y **1** si falló (la traza completa queda en `pipeline/logs/pipeline_tp2.log`).

**Verificar la idempotencia:** ejecutar el pipeline dos veces seguidas y correr esta consulta en SSMS después de cada corrida; los tres valores deben ser idénticos.
```sql
SELECT COUNT(*)                  AS filas,
       SUM(exposicion_reposicion) AS suma_exposicion,
       CHECKSUM_AGG(CHECKSUM(*))  AS checksum_tabla
FROM TP2_MorosidadPorCliente;
```

---

## 7. Cómo está resuelto

### 7.1 Portabilidad: `esquema.py`
Es el **único lugar** del proyecto con nombres propios de la base (`alquiler`, `fecha_devolucion`, `id_cliente`…). El resto del código usa nombres canónicos de Sakila (`rental`, `return_date`, `customer_id`…) y los traduce a través del diccionario. Para correr el trabajo contra la base de otro equipo se cambia solo ese archivo y la variable `DB_NAME`.

### 7.2 Consultas seguras
Los **nombres** de tablas y columnas salen de `esquema.py`; los **valores variables** (por ejemplo la fecha mínima de alquiler) viajan siempre como parámetro (`params`), nunca concatenados en el texto de la consulta. El pipeline arma la consulta con SQLAlchemy Core, sin f-strings.

### 7.3 Qué se resuelve en SQL Server y qué en pandas
- **SQL Server:** uniones entre las seis tablas del conjunto de trabajo, filtro por fecha y controles de integridad por conteo. El motor tiene índices y evita transferir filas que no se usan.
- **pandas:** cálculo del atraso con datos censurados, cruce con el archivo plano, agregación por cliente y gráficos. Dependen de un valor global (la fecha de corte) y son análisis iterativos sobre un conjunto ya reducido.

### 7.4 El conjunto de trabajo
Una fila por **alquiler**: `rental` unido con `inventory`, `film`, `customer`, `film_category` y `category`. Las uniones hacia la categoría son `LEFT JOIN` para no perder alquileres de películas sin categoría. Está escrito en T-SQL en `sql/conjunto_trabajo.sql` (para probarlo a mano en SSMS) y armado desde `esquema.py` en el código.

### 7.5 La decisión metodológica central: alquileres sin devolución
Un alquiler sin `return_date` **no** es un error ni un atraso de 0 días: su atraso real **se desconoce**. Por eso se trata como **dato censurado**:

- **Fecha de corte** = último evento registrado en la base (no la fecha de hoy). Con la base del equipo es **2006-02-14 15:16:03**.
- **Alquiler devuelto:** atraso = días entre alquiler y devolución − plazo pactado (`rental_duration`). Si es negativo (devolución anticipada) se informa como 0.
- **Alquiler no devuelto:** el atraso es **al menos** (fecha de corte − fecha de alquiler − plazo pactado). Es una **cota inferior**, no un valor exacto.

El pipeline calcula el atraso promedio por cliente con **las dos decisiones** posibles sobre los no devueltos, para poder compararlas:

| Columna | Decisión | Sesgo |
|---|---|---|
| `atraso_prom_excluyendo` | **Excluir** los no devueltos | Subestima: solo describe a quienes ya devolvieron, y los peores casos son justamente los que todavía no volvieron. |
| `atraso_prom_cota_minima` | **Imputar la cota mínima** a los no devueltos | También subestima, pero menos: el valor imputado es el mínimo posible. El resultado es un piso, no una estimación puntual. |

### 7.6 Calidad de datos (Actividad 2)
El notebook ejecuta el perfilado completo (forma, tipos, muestra, `info`, `describe`, nulos, duplicados por `rental_id`), un **control específico de la variante** (alquileres sin devolución, fechas de devolución anteriores al alquiler, plazos fuera de rango), atípicos con la regla del rango intercuartílico y un **control espejo** en T-SQL cuyos conteos se comparan con los de pandas. Cada transformación aplicada está justificada, y el pipeline reutiliza esa misma limpieza.

---

## 8. Pipeline ETL

```
EXTRAER                         TRANSFORMAR                          CARGAR
SQL Server (alquileres)  ─┐     limpiar  →  fecha de corte      ┌─  DELETE + INSERT en una
                          ├──►  merge con multas por categoría ─┤   única transacción sobre
CSV multas por categoría ─┘     atraso con censura               └─  TP2_MorosidadPorCliente
                                agregación por cliente
```

- **Orígenes:** (1) SQL Server, conjunto de trabajo; (2) `pipeline/datos/multas_por_categoria.csv`, archivo plano con la multa diaria (USD) por categoría. Las tarifas son **supuestos del equipo**, no datos de Sakila.
- **Combinación:** `merge` por categoría con `validate="m:1"` (falla si el CSV repitiera una categoría). Las categorías sin tarifa usan 0,75 USD/día y quedan registradas con una advertencia.
- **Limpieza:** se eliminan duplicados por `rental_id` y se apartan (y cuentan) los registros imposibles: devolución anterior al alquiler, plazo fuera de [1, 30] días y costo de reposición ≤ 0. Los alquileres sin devolución **no** se descartan.
- **Funciones de responsabilidad única:** `extraer_alquileres` / `extraer_multas`, `limpiar` / `calcular_atraso` / `agregar_por_cliente` / `transformar`, `cargar`, y `ejecutar_pipeline` como orquestación.
- **Registro (`logging`):** inicio y fin de cada etapa con la cantidad de filas procesadas, en consola y en `pipeline/logs/pipeline_tp2.log`. Si algo falla se registra con `log.exception` y el error se **vuelve a lanzar**, de modo que el proceso termina con código ≠ 0.

### Idempotencia
Ejecutarlo una o diez veces deja la misma tabla. Lo aseguran tres decisiones de diseño:
1. **`DELETE` + `INSERT` dentro de una sola transacción:** si la carga falla a mitad de camino se hace *rollback* y la tabla queda como estaba; nunca queda vacía ni a medias.
2. **Clave primaria `id_cliente`:** si el borrado no se ejecutara, el `INSERT` fallaría en lugar de duplicar filas.
3. **Salida determinista:** la fecha de corte se obtiene de los datos y no de la fecha de hoy, así que los mismos datos de entrada producen siempre el mismo resultado.

### Tabla destino `TP2_MorosidadPorCliente` (una fila por cliente)

| Columna | Descripción |
|---|---|
| `id_cliente` | Clave primaria |
| `nombre`, `apellido` | Datos del cliente |
| `total_alquileres` | Alquileres analizados del cliente |
| `devueltos`, `no_devueltos` | Cuántos tienen / no tienen fecha de devolución |
| `alquileres_morosos` | Alquileres con atraso > 0 (en los no devueltos, con mora mínima > 0) |
| `tasa_morosidad_pct` | `alquileres_morosos / total_alquileres × 100` |
| `atraso_prom_excluyendo` | Atraso promedio en días, excluyendo los no devueltos |
| `atraso_prom_cota_minima` | Atraso promedio en días, imputando la cota mínima a los no devueltos |
| `exposicion_reposicion` | Suma del costo de reposición (USD) de los alquileres no devueltos |
| `multa_estimada` | Atraso en días × multa diaria de la categoría (USD) |
| `fecha_corte` | Fecha de corte usada en el cálculo |

### Última ejecución registrada (`pipeline/logs/pipeline_tp2.log`)
- 16.044 alquileres extraídos · 16 categorías en el archivo plano · 599 clientes.
- 0 duplicados por `rental_id` y 0 registros apartados por reglas de negocio.
- 183 alquileres sin devolución (censurados) · fecha de corte 2006-02-14 15:16:03.
- Dos corridas completas consecutivas dejaron **599 filas** en `TP2_MorosidadPorCliente`.

---

## 9. Gráficos

El notebook exporta tres gráficos de tipos distintos en `graficos/` (PNG, 150 dpi):

| Archivo | Tipo | Qué muestra |
|---|---|---|
| `grafico_1_boxplot.png` | Diagramas de caja | Días de devolución respecto del plazo pactado, por categoría de película |
| `grafico_2_narrativo.png` | Barras (una barra destacada y una anotación) | Los 10 clientes con más exposición por películas sin devolver |
| `grafico_3_distribucion_morosidad.png` | Histograma | Distribución de la tasa de morosidad por cliente |

---

## 10. Alcance y limitaciones del análisis

- El atraso de los alquileres no devueltos es una **cota inferior**: el valor real es mayor o igual.
- Con las columnas disponibles no se puede distinguir un alquiler "que todavía no volvió" de una "devolución no registrada"; el notebook acota la duda midiendo cuánto tiempo pasó hasta la fecha de corte.
- La fecha de corte es el último evento registrado en la base, no la fecha actual.
- Las multas por categoría son supuestos del equipo: `multa_estimada` es ilustrativa, no un ingreso real.
- Las diferencias entre categorías son una **asociación**, no prueban causalidad.