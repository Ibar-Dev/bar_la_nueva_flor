import unittest
import sqlite3
import os
import json
from setup.database_setup import crear_base_de_datos, DB_NAME

class TestDatabaseSetup(unittest.TestCase):
    def setUp(self):
        # Usar una base de datos temporal para pruebas
        self.test_db = 'test_stock.db'
        self.original_db = DB_NAME
        # Cambiar el nombre de la base de datos en el módulo
        import setup.database_setup as database_setup
        database_setup.DB_NAME = self.test_db
        crear_base_de_datos()

    def tearDown(self):
        # Eliminar la base de datos de prueba
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        # Restaurar el nombre original
        import setup.database_setup as database_setup
        database_setup.DB_NAME = self.original_db

    def test_tablas_creadas(self):
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = set(row[0] for row in cursor.fetchall())
        self.assertIn('Productos', tablas)
        self.assertIn('Proveedores', tablas)
        self.assertIn('Compras', tablas)
        conn.close()

    def test_datos_iniciales(self):
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM Productos")
        productos = set(row[0] for row in cursor.fetchall())
        self.assertIn('Pollo', productos)
        self.assertIn('Harina', productos)
        cursor.execute("SELECT nombre FROM Proveedores")
        proveedores = set(row[0] for row in cursor.fetchall())
        self.assertIn('Distribuidora Central', proveedores)
        conn.close()

if __name__ == '__main__':
    unittest.main()
