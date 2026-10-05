import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy import text


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_conexion import obtener_motor

from esquema import TABLAS, COLUMNAS

motor = obtener_motor()


query_raw = f"""
SELECT 
    a.{COLUMNAS['rental_id']}        AS rental_id,
    a.{COLUMNAS['rental_date']}      AS rental_date,
    a.{COLUMNAS['return_date']}      AS return_date,
    c.{COLUMNAS['customer_id']}      AS customer_id,
    p.{COLUMNAS['film_id']}          AS film_id,
    p.{COLUMNAS['rental_duration']}  AS rental_duration,
    p.{COLUMNAS['replacement_cost']} AS replacement_cost,
    p.{COLUMNAS['rental_rate']}      AS rental_rate
FROM {TABLAS['rental']} a
INNER JOIN {TABLAS['inventory']} i 
    ON a.{COLUMNAS['inventory_id']} = i.{COLUMNAS['inventory_id']}
INNER JOIN {TABLAS['film']} p 
    ON i.{COLUMNAS['film_id']} = p.{COLUMNAS['film_id']}
INNER JOIN {TABLAS['customer']} c 
    ON a.{COLUMNAS['customer_id']} = c.{COLUMNAS['customer_id']};
"""

df = pd.read_sql(text(query_raw), motor)
df['rental_date'] = pd.to_datetime(df['rental_date'])
df['return_date'] = pd.to_datetime(df['return_date'])

print("==================================================")
print("1. FORMA Y TIPOS DE DATOS")
print(f"Dimensiones: {df.shape[0]} filas, {df.shape[1]} columnas\n")
print(df.dtypes)

print("\n==================================================")
print("2. VALORES NULOS Y DUPLICADOS")
nulos = df.isnull().sum()
pct_nulos = (df.isnull().sum() / len(df)) * 100
df_nulos = pd.DataFrame({'Nulos': nulos, 'Porcentaje (%)': pct_nulos})
print(df_nulos[df_nulos['Nulos'] > 0])

duplicados_pk = df.duplicated(subset=['rental_id']).sum()
print(f"\nDuplicados por clave primaria (rental_id): {duplicados_pk}")

print("\n==================================================")
print("3. CONTROL ESPECÍFICO DE VARIANTE: ALQUILERES SIN DEVOLUCIÓN")
sin_devolucion = df[df['return_date'].isnull()]
total_sin_dev = len(sin_devolucion)
pct_sin_dev = (total_sin_dev / len(df)) * 100

print(f"Cantidad de alquileres sin devolución (censurados): {total_sin_dev} ({pct_sin_dev:.2f}%)")
print("Diagnóstico: NO son datos erróneos ni valores faltantes ordinarios;")
print("representan películas en préstamo al momento de corte del sistema (censura a derecha).")

print("\n==================================================")
print("4. REGLAS DE NEGOCIO PROPIAS")


viajes_tiempo = df[df['return_date'] < df['rental_date']]
print(f"Regla 1 (return_date < rental_date): {len(viajes_tiempo)} filas violan la regla.")


df_devueltos = df[df['return_date'].notnull()].copy()
df_devueltos['dias_prestamo'] = (df_devueltos['return_date'] - df_devueltos['rental_date']).dt.total_seconds() / 86400.0

duracion_extrema = df_devueltos[df_devueltos['dias_prestamo'] > 30]
print(f"Regla 2 (Devoluciones con más de 30 días de préstamo): {len(duracion_extrema)} filas violan la regla.")

print("\n==================================================")
print("5. OUTLIERS CON MÉTODO IQR (Días de préstamo en devueltos)")
q1 = df_devueltos['dias_prestamo'].quantile(0.25)
q3 = df_devueltos['dias_prestamo'].quantile(0.75)
iqr = q3 - q1
lim_inf = q1 - 1.5 * iqr
lim_sup = q3 + 1.5 * iqr

outliers = df_devueltos[(df_devueltos['dias_prestamo'] < lim_inf) | (df_devueltos['dias_prestamo'] > lim_sup)]
print(f"Q1: {q1:.2f} días | Q3: {q3:.2f} días | IQR: {iqr:.2f} días")
print(f"Límite inferior: {lim_inf:.2f} días | Límite superior: {lim_sup:.2f} días")
print(f"Cantidad de outliers: {len(outliers)}")
print("Diagnóstico: Son casos reales de retención prolongada permitidos por el negocio, no errores de tipeo.")

print("\n==================================================")
print("6. COMPARACIÓN EN MOTOR SQL (Control Espejo)")


query_espejo_raw = f"""
SELECT 
    COUNT(CASE WHEN {COLUMNAS['return_date']} IS NULL THEN 1 END) AS nulos_devolucion,
    COUNT(CASE WHEN {COLUMNAS['return_date']} < {COLUMNAS['rental_date']} THEN 1 END) AS violaciones_fechas
FROM {TABLAS['rental']};
"""

df_espejo = pd.read_sql(text(query_espejo_raw), motor)
print("Resultados calculados en SQL Server:")
print(f"- Nulos en devolución: {df_espejo.iloc[0]['nulos_devolucion']} (Pandas: {total_sin_dev})")
print(f"- Violaciones temporales: {df_espejo.iloc[0]['violaciones_fechas']} (Pandas: {len(viajes_tiempo)})")
print("==================================================")