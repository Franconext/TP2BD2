import os
import urllib
from sqlalchemy import create_engine

def obtener_motor():
    """
    Crea el engine de SQLAlchemy usando Autenticación Integrada de Windows
    o variables de entorno, sin exponer credenciales en el código.
    """
    # Tomar de variables de entorno si existen, o usar defaults locales seguros
    servidor = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")  # o "localhost\SQLEXPRESS" si usás instancia nombrada
    base_datos = os.getenv("DB_NAME", "sakila")  # Cambiá al nombre exacto de tu BD migrada
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

    # Cadena de conexión con Trusted_Connection (Windows Auth)
    cadena_conexion = (
        f"DRIVER={{{driver}}};"
        f"SERVER={servidor};"
        f"DATABASE={base_datos};"
        f"Trusted_Connection=yes;"
    )

    params = urllib.parse.quote_plus(cadena_conexion)
    motor = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return motor