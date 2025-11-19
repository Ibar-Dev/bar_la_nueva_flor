import unittest
import sqlite3
import os
import json
from src.database import connect_db, get_datos_iniciales, guardar_compra
from app import guardar_compra_validada

class TestAppBackend(unittest.TestCase):
    def setUp(self):
        # Usar una base de datos temporal para pruebas
        self.test_db = 'test_stock_app.db'
        # Cambiar el nombre de la base de datos en el módulo
        import src.database
        self.original_db = src.database.DB_NAME
        src.database.DB_NAME = self.test_db
        # Crear base de datos y datos iniciales
        import setup.database_setup as database_setup
        database_setup.DB_NAME = self.test_db
        database_setup.crear_base_de_datos()

    def tearDown(self):
        # Eliminar la base de datos de prueba
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        # Restaurar el nombre original
        import src.database
        src.database.DB_NAME = self.original_db
        import setup.database_setup as database_setup
        database_setup.DB_NAME = self.original_db

    def test_connect_db(self):
        conn = connect_db()
        self.assertIsNotNone(conn)
        conn.close()

    def test_get_datos_iniciales(self):
        datos = get_datos_iniciales()
        self.assertIn('productos', datos)
        self.assertIn('proveedores', datos)
        self.assertIn('unidades_map', datos)
        self.assertIn('Pollo', datos['productos'])
        self.assertIn('Distribuidora Central', datos['proveedores'])
        self.assertIsInstance(datos['unidades_map'], dict)

    def test_guardar_compra(self):
        datos = {
            'producto': 'Harina',
            'proveedor': 'Distribuidora Central',
            'cantidad': 2,
            'unidad': 'kg',
            'precio': 20.5,
            'fecha_compra': '2025-11-17',
            'descuento': '0'
        }
        resultado = guardar_compra(datos)
        self.assertTrue(resultado['success'])
        # Verificar que la compra se guardó
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Compras WHERE cantidad=2 AND unidad_medida='kg' AND precio_total=20.5")
        compra = cursor.fetchone()
        self.assertIsNotNone(compra)
        conn.close()

    def test_guardar_compra_producto_inexistente(self):
        datos = {
            'producto': 'NoExiste',
            'proveedor': 'Distribuidora Central',
            'cantidad': 1,
            'unidad': 'kg',
            'precio': 10,
            'fecha_compra': '2025-11-17',
            'descuento': '0'
        }
        resultado = guardar_compra(datos)
        self.assertFalse(resultado['success'])
        self.assertIn('error', resultado)

    def test_guardar_compra_validada(self):
        """Test de la función con validación del app.py"""
        datos = {
            'producto': 'Harina',
            'proveedor': 'Distribuidora Central',
            'cantidad': 2,
            'unidad': 'kg',
            'precio': 20.5,
            'fecha_compra': '2025-11-17',
            'descuento': '0'
        }
        resultado = guardar_compra_validada(datos)
        self.assertTrue(resultado['success'])
        self.assertIn('compra_id', resultado)

if __name__ == '__main__':
    unittest.main()
