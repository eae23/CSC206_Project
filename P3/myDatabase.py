import mariadb
import sys

def myConnect():
    try:
        conn = mariadb.connect(
            user="root",
            password="Bi11s723!",
            host="localhost",
            port=3307,
            database="csc206cars")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return conn