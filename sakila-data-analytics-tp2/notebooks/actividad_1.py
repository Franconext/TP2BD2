import sys
import os
import time
import pandas as pd
from sqlalchemy import text


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_conexion import obtener_motor

from esquema import TABLAS, COLUMNAS

motor = obtener_motor()


fecha_corte = '2005-01-01'


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
ORDER BY a.{COLUMNAS['rental_date']} ASC;
"""

query_extraccion = text(sql_raw)

print("Cargando datos con pandas.read_sql parametrizado...")

df_alquileres = pd.read_sql(query_extraccion, motor, params={"fecha": fecha_corte})
print(f"Filas recuperadas: {len(df_alquileres)}")



t0_sql = time.perf_counter()
query_metrica_sql = text(f"""
SELECT AVG(CAST(p.{COLUMNAS['replacement_cost']} AS FLOAT)) AS promedio_costo
FROM {TABLAS['rental']} a
INNER JOIN {TABLAS['inventory']} i 
    ON a.{COLUMNAS['inventory_id']} = i.{COLUMNAS['inventory_id']}
INNER JOIN {TABLAS['film']} p 
    ON i.{COLUMNAS['film_id']} = p.{COLUMNAS['film_id']}
WHERE a.{COLUMNAS['rental_date']} >= :fecha
""")
df_res_sql = pd.read_sql(query_metrica_sql, motor, params={"fecha": fecha_corte})
t1_sql = time.perf_counter()
tiempo_sql = t1_sql - t0_sql
promedio_sql = df_res_sql.iloc[0, 0]


t0_pd = time.perf_counter()
promedio_pandas = df_alquileres['replacement_cost'].astype(float).mean()
t1_pd = time.perf_counter()
tiempo_pandas = t1_pd - t0_pd

print("\n--- COMPARACIÓN DE RESULTADOS Y TIEMPOS (ACTIVIDAD 1) ---")
print(f"Métrica en SQL Server : {promedio_sql:.4f} (Tiempo: {tiempo_sql:.6f} seg)")
print(f"Métrica en Pandas     : {promedio_pandas:.4f} (Tiempo: {tiempo_pandas:.6f} seg)")
print(f"Diferencia entre ambos: {abs(promedio_sql - promedio_pandas):.8f}")