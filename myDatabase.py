import mariadb
import sys
from config import Config

def myConnect():
    try:
        conn = mariadb.connect(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_DATABASE
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return conn