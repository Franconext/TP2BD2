import pandas as pd
from config_conexion import obtener_motor

try:
    motor = obtener_motor()
    # Hacemos una consulta rápida al sistema para verificar conexión
    df = pd.read_sql("SELECT @@SERVERNAME AS Servidor, DB_NAME() AS BaseDatos", motor)
    print("¡Conexión exitosa!")
    print(df)
except Exception as e:
    print("Error al conectar:")
    print(e)