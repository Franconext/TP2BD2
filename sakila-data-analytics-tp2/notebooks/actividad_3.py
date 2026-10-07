import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_conexion import obtener_motor
from esquema import TABLAS, COLUMNAS

os.makedirs("graficos", exist_ok=True)
motor = obtener_motor()

# =============================================================================
# 1. EXTRACCIÓN (Desacoplada con esquema.py)
# =============================================================================
query_raw = f"""
SELECT 
    a.{COLUMNAS['rental_id']}        AS rental_id,
    a.{COLUMNAS['rental_date']}      AS rental_date,
    a.{COLUMNAS['return_date']}      AS return_date,
    c.{COLUMNAS['customer_id']}      AS customer_id,
    CONCAT(c.{COLUMNAS['first_name']}, ' ', c.{COLUMNAS['last_name']}) AS full_name,
    p.{COLUMNAS['film_id']}          AS film_id,
    p.{COLUMNAS['rental_duration']}  AS rental_duration,
    CAST(p.{COLUMNAS['replacement_cost']} AS FLOAT) AS replacement_cost,
    cat.{COLUMNAS['name']}           AS category
FROM {TABLAS['rental']} a
INNER JOIN {TABLAS['inventory']} i ON a.{COLUMNAS['inventory_id']} = i.{COLUMNAS['inventory_id']}
INNER JOIN {TABLAS['film']} p ON i.{COLUMNAS['film_id']} = p.{COLUMNAS['film_id']}
INNER JOIN {TABLAS['customer']} c ON a.{COLUMNAS['customer_id']} = c.{COLUMNAS['customer_id']}
LEFT JOIN {TABLAS['film_category']} pc ON p.{COLUMNAS['film_id']} = pc.{COLUMNAS['film_id']}
LEFT JOIN {TABLAS['category']} cat ON pc.{COLUMNAS['category_id']} = cat.{COLUMNAS['category_id']};
"""

df = pd.read_sql(text(query_raw), motor)
df['rental_date'] = pd.to_datetime(df['rental_date'])
df['return_date'] = pd.to_datetime(df['return_date'])

# =============================================================================
# 2. MÉTRICA DERIVADA
# =============================================================================
fecha_corte = max(df['rental_date'].max(), df['return_date'].max())
fecha_efectiva = df['return_date'].fillna(fecha_corte)

dias_transcurridos = (fecha_efectiva - df['rental_date']).dt.total_seconds() / 86400.0
df['dias_atraso'] = np.maximum(0.0, dias_transcurridos - df['rental_duration'])
df['esta_devuelto'] = df['return_date'].notnull()
df['es_moroso'] = df['dias_atraso'] > 0

resumen_clientes = df.groupby(['customer_id', 'full_name']).agg(
    total_alquileres=('rental_id', 'count'),
    alquileres_con_mora=('es_moroso', 'sum'),
    exposicion_no_devueltos=('replacement_cost', lambda x: x[~df.loc[x.index, 'esta_devuelto']].sum())
).reset_index()
resumen_clientes['tasa_morosidad'] = (resumen_clientes['alquileres_con_mora'] / resumen_clientes['total_alquileres']) * 100

print("Cálculos vectorizados completados. Generando gráficos...")

# =============================================================================
# 3. VISUALIZACIÓN DE DATOS 
# =============================================================================


plt.figure(figsize=(12, 6))
df_con_atraso = df[df['dias_atraso'] > 0]
orden_cat = df_con_atraso.groupby('category')['dias_atraso'].median().sort_values(ascending=False).index

sns.boxplot(data=df_con_atraso, x='category', y='dias_atraso', order=orden_cat, palette='Set2')
plt.title("Distribución de Días de Atraso por Categoría de Película (Solo Alquileres con Mora)", fontsize=13, weight='bold')
plt.xlabel("Categoría de Película", fontsize=11)
plt.ylabel("Días de Atraso Acumulados", fontsize=11)
plt.xticks(rotation=45, ha='right')


plt.ylim(-1, 15)

plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("graficos/grafico_1_boxplot.png", dpi=150)
plt.close()


top_morosos = resumen_clientes.sort_values(by='exposicion_no_devueltos', ascending=False).head(10).copy()
plt.figure(figsize=(10, 6))

colores = ['#d9534f' if i == 0 else '#6c757d' for i in range(len(top_morosos))]
bars = plt.barh(top_morosos['full_name'][::-1], top_morosos['exposicion_no_devueltos'][::-1], color=colores[::-1])

plt.title("Riesgo Crítico: Una sola persona concentra la mayor deuda en películas retenidas", fontsize=13, weight='bold')
plt.xlabel("Exposición por Costo de Reposición (USD)", fontsize=11)
plt.ylabel("Cliente", fontsize=11)

max_exposicion = top_morosos.iloc[0]['exposicion_no_devueltos']
max_nombre = top_morosos.iloc[0]['full_name']
plt.annotate(
    f"Exposición máxima:\n${max_exposicion:.2f} USD",
    xy=(max_exposicion, 9),
    xytext=(max_exposicion * 0.70, 7.5),
    arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
    fontsize=10, weight='semibold', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=0.8)
)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("graficos/grafico_2_narrativo.png", dpi=150)
plt.close()


plt.figure(figsize=(10, 5))
sns.histplot(resumen_clientes['tasa_morosidad'], bins=20, color='#0275d8')
plt.title("Distribución de la Tasa de Morosidad en el Padrón de Clientes", fontsize=13, weight='bold')
plt.xlabel("Porcentaje de Alquileres Devueltos Fuera de Término (%)", fontsize=11)
plt.ylabel("Cantidad de Clientes", fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("graficos/grafico_3_distribucion_morosidad.png", dpi=150)
plt.close()

print("Gráficos exportados exitosamente en la carpeta 'graficos/'.")