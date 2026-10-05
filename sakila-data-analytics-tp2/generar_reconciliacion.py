import pandas as pd
from config_conexion import obtener_motor
from esquema import TABLAS


FILAS_ORIGEN_SAKILA = {
    "actor": 200,
    "address": 603,
    "category": 16,
    "city": 600,
    "country": 109,
    "customer": 599,
    "film": 1000,
    "film_actor": 5462,
    "film_category": 1000,
    "film_text": 1000,
    "inventory": 4581,
    "language": 6,
    "payment": 16049,
    "rental": 16044,
    "staff": 2,
    "store": 2,
}

def ejecutar():
    motor = obtener_motor()
    registros = []

    for tabla_canon, tabla_sql in TABLAS.items():
        if tabla_canon in FILAS_ORIGEN_SAKILA:
            origen = FILAS_ORIGEN_SAKILA[tabla_canon]
            query = f"SELECT COUNT(*) AS total FROM {tabla_sql}"
            try:
                df = pd.read_sql(query, motor)
                filas_sql = int(df["total"].iloc[0])
                dif = filas_sql - origen
            except Exception as e:
                filas_sql = f"Error: {e}"
                dif = "Error"

            registros.append({
                "tabla": tabla_sql,
                "filas_origen": origen,
                "filas_sql_server": filas_sql,
                "diferencia": dif
            })

    df_resultado = pd.DataFrame(registros)
    

    print("\n================ TABLA DE RECONCILIACIÓN ================")
    print(df_resultado.to_string(index=False))
    print("=========================================================\n")

    import os
    os.makedirs("sql", exist_ok=True)
    df_resultado.to_csv("sql/reconciliacion.csv", index=False)
    print("Resultado guardado en: sql/reconciliacion.csv")

if __name__ == "__main__":
    ejecutar()