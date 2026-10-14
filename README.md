# TP2 · Equipo 04 — Morosidad y devoluciones fuera de término

**Seminario de Actualización · Unidad 5: Data Analytics e Ingeniería de Datos · 2026**

> **Variante 4 — Morosidad y devoluciones fuera de término**  
> **Pregunta de negocio:** ¿Cuánto se demoran los clientes en devolver las películas y cuánto expone eso al negocio? ¿Qué perfil tiene el cliente moroso?

## Equipo académico

| Rol | Nombre y apellido |
|---|---|
| **Docente** | **Jorge Insfrán** |
| Alumno | **Lucas Valenzuela** |
| Alumno | **Franco Amendolara** |
| Alumno | **Diego Insua** |

**Institución:** Instituto Superior Nuestra Señora de Luján del Buen Viaje.  
**Repositorio:** [Franconext/TP2BD2](https://github.com/Franconext/TP2BD2)

### Organización del trabajo

| Actividad | Responsable principal | Alcance |
|---|---|---|
| 1 y 2 | Lucas Valenzuela | Integración SQL–Python y diagnóstico de calidad |
| 3 | Diego Insua | Indicadores, visualizaciones y hallazgos |
| 4 | Franco Amendolara | Pipeline ETL, carga y validaciones |
| 0 y documentación | Equipo completo | Reconciliación, revisión y documentación |

> **Trabajo colaborativo:** las responsabilidades indican quién lideró cada actividad, pero **todos los integrantes participaron en consultas, pruebas, revisión de código y resolución de problemas**, con el objetivo de comprender el proyecto completo. Los commits se centralizaron mediante la cuenta de GitHub de Franco Amendolara (`Franconext`); esa autoría de Git no representa una autoría individual de todas las actividades.

---

## 1. Resumen del proyecto

El proyecto utiliza la base **Sakila**, migrada a **SQL Server**, y un flujo de análisis en **Python** para estudiar los alquileres de un videoclub. El trabajo aborda el atraso en las devoluciones, el comportamiento de los clientes y la exposición económica por películas no devueltas.

| Etapa | Objetivo | Entregable |
|---|---|---|
| **Actividad 0** | Reconciliar el esquema migrado y centralizar nombres de tablas y columnas | `esquema.py`, `sql/reconciliacion.csv` |
| **Actividad 1** | Integrar SQL Server con Python y contrastar métricas | Notebook de análisis y consulta SQL |
| **Actividad 2** | Perfilar nulos, duplicados, reglas de negocio y outliers | Diagnóstico de calidad |
| **Actividad 3** | Calcular indicadores y comunicar tres hallazgos | Notebook y gráficos PNG |
| **Actividad 4** | Ejecutar un ETL repetible e idempotente | `pipeline/pipeline_tp2.py` y tabla `TP2_MorosidadPorCliente` |

### Tecnologías

**SQL Server · T-SQL · Python 3.11+ · pandas · NumPy · SQLAlchemy · pyodbc · matplotlib · seaborn · Jupyter / VS Code**

---

## 2. Estructura del repositorio

```text
TP2BD2/
├── README.md
├── requirements.txt
├── .gitignore
└── sakila-data-analytics-tp2/
    ├── config_conexion.py
    ├── esquema.py
    ├── probar_conexion.py
    ├── generar_reconciliacion.py
    ├── sql/
    │   ├── conjunto_trabajo.sql
    │   └── reconciliacion.csv
    ├── notebooks/
    │   ├── analisis.ipynb
    │   ├── actividad_1.py
    │   ├── actividad_2.py
    │   └── actividad_3.py
    ├── pipeline/
    │   ├── pipeline_tp2.py
    │   ├── datos/
    │   │   └── multas_por_categoria.csv
    │   └── logs/
    │       └── pipeline_tp2.log
    └── graficos/
        ├── grafico_1_boxplot.png
        ├── grafico_2_narrativo.png
        └── grafico_3_distribucion_morosidad.png
```

> La estructura anterior describe la organización documentada del proyecto. Las carpetas de datos y logs deben existir en el entorno de ejecución; los archivos de logs se generan al correr el pipeline.

---

## 3. Requisitos e instalación

- Windows con acceso a una instancia de **SQL Server** que contenga la base Sakila migrada.
- **Python 3.11** o superior.
- **ODBC Driver 17 for SQL Server** (configuración documentada; otro driver requiere ajustar la conexión).
- Dependencias Python incluidas en `requirements.txt`.

Desde la raíz del repositorio, crear y activar el entorno virtual:

**PowerShell**

```powershell
python -m venv venv_tp2
.\venv_tp2\Scripts\Activate.ps1
pip install -r requirements.txt
cd sakila-data-analytics-tp2
```

**CMD**

```bat
python -m venv venv_tp2
venv_tp2\Scripts\activate.bat
pip install -r requirements.txt
cd sakila-data-analytics-tp2
```

> Los comandos de las siguientes secciones se ejecutan desde `sakila-data-analytics-tp2/` y con el entorno virtual activo.

---

## 4. Configuración de la base de datos

`config_conexion.py` utiliza **Autenticación Integrada de Windows** (`Trusted_Connection=yes`), sin guardar usuario ni contraseña en el código.

| Variable | Valor predeterminado | Descripción |
|---|---|---|
| `DB_SERVER` | `localhost\SQLEXPRESS` | Servidor e instancia SQL Server |
| `DB_NAME` | `sakila` | Base migrada |
| `DB_DRIVER` | `ODBC Driver 17 for SQL Server` | Driver ODBC |

Ejemplo en **PowerShell**:

```powershell
$env:DB_SERVER = 'localhost\SQLEXPRESS'
$env:DB_NAME = 'sakila'
python probar_conexion.py
```

Ejemplo en **CMD**:

```bat
set DB_SERVER=localhost\SQLEXPRESS
set DB_NAME=sakila
python probar_conexion.py
```

Si solo está instalado **ODBC Driver 18**, puede ser necesario ajustar los parámetros de cifrado y validación del certificado en la cadena de conexión, según la configuración del servidor.

---

## 5. Ejecución por actividad

### Actividad 0 — Reconciliación

```powershell
python generar_reconciliacion.py
```

Compara los conteos de las tablas de SQL Server con el origen y guarda el resultado en `sql/reconciliacion.csv`. En el archivo de reconciliación analizado, **15 de 16 tablas coinciden**; `pago` presenta **5 registros menos en SQL Server** (16.044 frente a 16.049 en origen). Esta diferencia se mantiene documentada y pendiente de explicación.

### Actividades 1, 2 y 3 — Notebook

Abrir `notebooks/analisis.ipynb` en VS Code o Jupyter y seleccionar el kernel del entorno virtual. Ejecutar **Restart & Run All** para reproducir los cálculos y exportar los gráficos a `graficos/`.

Los archivos `notebooks/actividad_1.py`, `actividad_2.py` y `actividad_3.py` contienen versiones en script del desarrollo.

### Actividad 4 — Pipeline ETL

```powershell
# Ejecución normal: escribe en SQL Server
python pipeline/pipeline_tp2.py

# Filtra alquileres desde una fecha determinada
python pipeline/pipeline_tp2.py --desde 2005-01-01

# Ejecuta las transformaciones sin cargar la tabla destino
python pipeline/pipeline_tp2.py --simulacion
```

La ejecución registra sus etapas en consola y en `pipeline/logs/pipeline_tp2.log`. Según el comportamiento documentado, devuelve **código 0** cuando finaliza correctamente y **código distinto de 0** ante errores.

---

## 6. Diseño y decisiones metodológicas

### Diccionario de esquema

`esquema.py` centraliza la traducción de nombres canónicos de Sakila a los nombres reales de SQL Server. Ejemplos:

| Sakila | SQL Server |
|---|---|
| `rental` | `alquiler` |
| `film` | `pelicula` |
| `customer` | `cliente` |
| `inventory` | `inventario` |
| `rental_date` | `fecha_alquiler` |
| `return_date` | `fecha_devolucion` |

Esto facilita adaptar consultas sin modificar los nombres físicos en múltiples archivos. Los valores variables, como la fecha mínima, se pasan como **parámetros**, evitando concatenarlos en SQL.

### Conjunto de trabajo

La extracción relaciona `rental`, `inventory`, `film`, `customer`, `film_category` y `category`. Las relaciones con categorías usan `LEFT JOIN` para conservar alquileres aunque falte una categoría asociada. La consulta de referencia está en `sql/conjunto_trabajo.sql`.

### Tratamiento de alquileres sin devolución

Una fecha `return_date` nula **no equivale a cero días de atraso ni implica por sí sola un error**: el alquiler se considera *censurado a derecha*.

- **Devueltos:** `max(0, días entre alquiler y devolución − duración pactada)`.
- **No devueltos:** se calcula una **cota mínima** del atraso hasta una fecha de corte obtenida de los datos.
- **Fecha de corte documentada:** `2006-02-14 15:16:03`.

El pipeline conserva dos perspectivas: `atraso_prom_excluyendo` (solo devueltos) y `atraso_prom_cota_minima` (incluye la cota mínima para no devueltos). Ambas requieren interpretación: no representan la duración definitiva de los alquileres pendientes.

### Calidad de datos

Se analizan nulos, duplicados por `rental_id`, fechas de devolución anteriores al alquiler, plazos fuera de **1 a 30 días**, costos de reposición no positivos y valores atípicos mediante **IQR**. Los alquileres sin devolución se conservan; los casos imposibles se apartan y registran. Los outliers no se eliminan automáticamente si pueden ser casos reales de morosidad.

---

## 7. Arquitectura del pipeline ETL

```text
SQL Server (alquileres) ──┐
                          ├── EXTRAER ── TRANSFORMAR ── CARGAR
CSV (multas/categoría) ──┘      │           │             │
                                │           │             └── TP2_MorosidadPorCliente
                                │           ├── limpieza y validaciones
                                │           ├── merge por categoría
                                │           ├── cálculo de atraso y censura
                                │           └── agregación por cliente
                                └── logging y control de errores
```

**Dos orígenes:** SQL Server y `pipeline/datos/multas_por_categoria.csv`. El CSV contiene tarifas diarias de multa **supuestas por el equipo**, no importes reales de Sakila. El `merge` se realiza por categoría con validación `m:1`; para categorías sin tarifa se documenta una multa predeterminada de **USD 0,75 por día**.

**Idempotencia:** el pipeline realiza `DELETE + INSERT` dentro de una única transacción, utiliza `id_cliente` como clave primaria y obtiene una fecha de corte determinista a partir de los datos. Con entradas iguales, las ejecuciones deben producir la misma tabla. Ante una falla de carga, la transacción permite revertir cambios.

### Tabla destino: `TP2_MorosidadPorCliente`

| Columna | Descripción |
|---|---|
| `id_cliente` | Clave primaria |
| `nombre`, `apellido` | Identificación del cliente |
| `total_alquileres` | Alquileres analizados |
| `devueltos`, `no_devueltos` | Alquileres con y sin fecha de devolución |
| `alquileres_morosos` | Alquileres con atraso positivo, según la metodología del pipeline |
| `tasa_morosidad_pct` | Porcentaje de alquileres morosos |
| `atraso_prom_excluyendo` | Atraso promedio de alquileres devueltos |
| `atraso_prom_cota_minima` | Atraso promedio incluyendo la cota mínima de los pendientes |
| `exposicion_reposicion` | Suma de costos de reposición de no devueltos (USD) |
| `multa_estimada` | Estimación ilustrativa basada en las multas del CSV (USD) |
| `fecha_corte` | Fecha de referencia de los cálculos |

### Evidencia de ejecución documentada

De acuerdo con el registro de ejecución compartido en la documentación del proyecto:

| Indicador | Resultado |
|---|---:|
| Alquileres extraídos | **16.044** |
| Categorías en el archivo plano | **16** |
| Clientes procesados | **599** |
| Alquileres sin devolución | **183** |
| Duplicados por `rental_id` | **0** |
| Registros apartados por reglas de negocio | **0** |
| Filas en tabla destino tras dos ejecuciones | **599** |

**Validación de idempotencia:** ejecutar el pipeline dos veces consecutivas y comparar, después de cada corrida, el resultado de esta consulta en SQL Server Management Studio (SSMS):

```sql
SELECT
    COUNT(*) AS filas,
    SUM(exposicion_reposicion) AS suma_exposicion,
    CHECKSUM_AGG(CHECKSUM(*)) AS checksum_tabla
FROM TP2_MorosidadPorCliente;
```

Los tres valores deben coincidir entre ambas corridas. El checksum funciona como control práctico, aunque no sustituye una comparación exhaustiva de todas las filas y columnas.

---

## 8. Visualizaciones y hallazgos

El notebook exporta tres gráficos PNG a **150 dpi**.

### 8.1. Días de atraso por categoría

![Distribución de días de atraso por categoría](sakila-data-analytics-tp2/graficos/grafico_1_boxplot.png)

**Hallazgo:** entre los alquileres que presentan mora, las medianas de atraso por categoría son relativamente similares, aproximadamente entre **2 y 3 días**. No se identifica una categoría claramente dominante. Esto **no equivale** a comparar la probabilidad de mora de todas las categorías, porque el gráfico incluye solamente alquileres morosos.

**Decisión posible:** evaluar recordatorios generales y estudiar tasas de mora por categoría antes de aplicar políticas diferenciadas.

### 8.2. Exposición por películas no devueltas

![Exposición económica por cliente](sakila-data-analytics-tp2/graficos/grafico_2_narrativo.png)

**Hallazgo:** **Tammy Sanders** registra la mayor exposición individual entre los clientes representados, con **USD 68,97** en costos estimados de reposición. Esto representa exposición potencial, **no una pérdida definitiva**.

**Decisión posible:** priorizar el seguimiento de alquileres pendientes según el valor económico expuesto.

### 8.3. Distribución de la tasa de morosidad

![Distribución de la tasa de morosidad](sakila-data-analytics-tp2/graficos/grafico_3_distribucion_morosidad.png)

**Hallazgo:** el histograma muestra una concentración importante de clientes con tasas aproximadas entre **40 % y 65 %**, con un pico cercano al **50 %**. Las tasas deben interpretarse junto con el número de alquileres de cada cliente.

**Decisión posible:** segmentar clientes según recurrencia de atraso, volumen de alquileres y exposición económica.

---

## 9. Alcance y limitaciones

- La base representa un **conjunto histórico**: la fecha de corte se obtiene del último evento registrado, no de la fecha actual.
- Los alquileres sin devolución son **observaciones censuradas**; su atraso final es desconocido.
- La exposición por costo de reposición **no equivale a una pérdida confirmada**.
- Las multas por categoría son **supuestos didácticos del equipo**, no cobros reales.
- Los gráficos permiten detectar **asociaciones y patrones**, pero no demuestran causalidad.
- La reconciliación detectó una diferencia de **cinco registros en `pago`**, pendiente de explicación.

---

## 10. Reproducibilidad y documentación

Para reproducir el trabajo:

1. Preparar SQL Server con Sakila migrada y configurar `DB_SERVER`, `DB_NAME` y `DB_DRIVER`.
2. Crear el entorno virtual e instalar `requirements.txt`.
3. Verificar la conexión con `python probar_conexion.py`.
4. Ejecutar `python generar_reconciliacion.py`.
5. Abrir `notebooks/analisis.ipynb` y ejecutar todas las celdas.
6. Comprobar que exista `pipeline/datos/multas_por_categoria.csv` y ejecutar el ETL.
7. Repetir el ETL y verificar la idempotencia en `TP2_MorosidadPorCliente`.

La bitácora del equipo y las páginas de **Diccionario de esquema**, **Diagnóstico de calidad**, **Hallazgos** y **Dudas** complementan la documentación técnica.

---

**TP2 · Equipo 04 · Seminario de Actualización · 2026**  
**Docente:** Jorge Insfrán  
**Alumnos:** Lucas Valenzuela · Franco Amendolara · Diego Insua
