import sys
import os
import time
import pandas as pd
from sqlalchemy import text

# Agregar la raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_conexion import obtener_motor
from esquema import TABLAS, COLUMNAS

motor = obtener_motor()

# ==========================================================
# ACTIVIDAD 1 - INTEGRACIÓN SQL - PYTHON
# ==========================================================

# Fecha utilizada como parámetro de la consulta
fecha_corte = '2005-01-01'


# ==========================================================
# 1. CONSTRUCCIÓN DEL CONJUNTO DE TRABAJO
# ==========================================================

# Los nombres de tablas y columnas se obtienen exclusivamente
# desde esquema.py.
#
# Los valores variables, como fecha_corte, se envían mediante
# params para evitar concatenarlos directamente en la consulta.

sql_raw = f"""
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

WHERE a.{COLUMNAS['rental_date']} >= :fecha

ORDER BY a.{COLUMNAS['rental_date']} ASC
"""

query_extraccion = text(sql_raw)

print("Cargando conjunto de trabajo...")

df_alquileres = pd.read_sql(
    query_extraccion,
    motor,
    params={"fecha": fecha_corte}
)

# Conversión explícita de fechas
df_alquileres['rental_date'] = pd.to_datetime(
    df_alquileres['rental_date']
)

df_alquileres['return_date'] = pd.to_datetime(
    df_alquileres['return_date']
)

print(f"Filas recuperadas: {len(df_alquileres)}")
print(f"Columnas recuperadas: {len(df_alquileres.columns)}")

print("\nPrimeras filas:")
print(df_alquileres.head())


# ==========================================================
# 2. COMPARACIÓN DE UNA MISMA MÉTRICA EN SQL Y PANDAS
# ==========================================================
#
# Métrica elegida:
# promedio de días de atraso de los alquileres DEVUELTOS.
#
# Un alquiler devuelto antes de la fecha pactada tiene
# 0 días de atraso y no un valor negativo.
#
# Los alquileres sin devolución se excluyen de esta métrica
# porque su atraso definitivo todavía no se conoce.


# ----------------------------------------------------------
# ENFOQUE A - MÉTRICA CALCULADA EN SQL SERVER
# ----------------------------------------------------------

query_metrica_sql = text(f"""
SELECT
    AVG(
        CAST(
            CASE
                WHEN DATEDIFF(
                    SECOND,
                    a.{COLUMNAS['rental_date']},
                    a.{COLUMNAS['return_date']}
                ) / 86400.0 - p.{COLUMNAS['rental_duration']} > 0

                THEN DATEDIFF(
                    SECOND,
                    a.{COLUMNAS['rental_date']},
                    a.{COLUMNAS['return_date']}
                ) / 86400.0 - p.{COLUMNAS['rental_duration']}

                ELSE 0
            END
        AS FLOAT)
    ) AS promedio_dias_atraso

FROM {TABLAS['rental']} a

INNER JOIN {TABLAS['inventory']} i
    ON a.{COLUMNAS['inventory_id']} = i.{COLUMNAS['inventory_id']}

INNER JOIN {TABLAS['film']} p
    ON i.{COLUMNAS['film_id']} = p.{COLUMNAS['film_id']}

WHERE
    a.{COLUMNAS['rental_date']} >= :fecha
    AND a.{COLUMNAS['return_date']} IS NOT NULL
""")


t0_sql = time.perf_counter()

df_res_sql = pd.read_sql(
    query_metrica_sql,
    motor,
    params={"fecha": fecha_corte}
)

tiempo_sql = time.perf_counter() - t0_sql

promedio_sql = float(
    df_res_sql.iloc[0]['promedio_dias_atraso']
)


# ----------------------------------------------------------
# ENFOQUE B - MISMA MÉTRICA CALCULADA EN PANDAS
# ----------------------------------------------------------

t0_pd = time.perf_counter()

df_devueltos = df_alquileres[
    df_alquileres['return_date'].notna()
].copy()

df_devueltos['dias_prestamo'] = (
    df_devueltos['return_date']
    - df_devueltos['rental_date']
).dt.total_seconds() / 86400.0

df_devueltos['dias_atraso'] = (
    df_devueltos['dias_prestamo']
    - df_devueltos['rental_duration']
).clip(lower=0)

promedio_pandas = df_devueltos['dias_atraso'].mean()

tiempo_pandas = time.perf_counter() - t0_pd


# ==========================================================
# 3. RESULTADOS
# ==========================================================

diferencia = abs(
    promedio_sql - promedio_pandas
)

print("\n==================================================")
print("COMPARACIÓN SQL SERVER VS PANDAS")
print("==================================================")

print(
    f"Promedio atraso SQL Server : "
    f"{promedio_sql:.6f} días"
)

print(
    f"Promedio atraso Pandas     : "
    f"{promedio_pandas:.6f} días"
)

print(
    f"Diferencia                 : "
    f"{diferencia:.10f}"
)

print(
    f"Tiempo SQL Server          : "
    f"{tiempo_sql:.6f} segundos"
)

print(
    f"Tiempo Pandas              : "
    f"{tiempo_pandas:.6f} segundos"
)

if diferencia < 0.000001:
    print("\nVALIDACIÓN: ambos métodos producen el mismo resultado.")
else:
    print("\nATENCIÓN: existe una diferencia entre ambos cálculos.")


# ==========================================================
# 4. CONCLUSIÓN DEL REPARTO DE TRABAJO
# ==========================================================

print("\n==================================================")
print("CONCLUSIÓN ACTIVIDAD 1")
print("==================================================")

print("""
SQL Server se utiliza para realizar las uniones entre las tablas,
aplicar filtros y reducir el conjunto de datos antes de transferirlo
a Python.

Pandas se utiliza posteriormente para el análisis exploratorio,
control de calidad, cálculo de métricas derivadas y visualización.

Los valores variables de las consultas se envían mediante parámetros.
Los nombres de tablas y columnas no provienen del usuario, sino del
diccionario controlado esquema.py.

La comparación de la métrica de atraso permite comprobar que el cálculo
realizado en SQL Server coincide con el realizado posteriormente en
pandas.
""")