import os
import urllib
from sqlalchemy import create_engine

def obtener_motor():
    """
    Crea el engine de SQLAlchemy usando Autenticación Integrada de Windows
    o variables de entorno, sin exponer credenciales en el código.
    """

    servidor = os.getenv("DB_SERVER", "localhost") 
    base_datos = os.getenv("DB_NAME", "sakila")  
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")


    cadena_conexion = (
        f"DRIVER={{{driver}}};"
        f"SERVER={servidor};"
        f"DATABASE={base_datos};"
        f"Trusted_Connection=yes;"
    )

    params = urllib.parse.quote_plus(cadena_conexion)
    motor = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return motor