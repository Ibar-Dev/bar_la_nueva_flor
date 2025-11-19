# test_analytics.py
# Tests de integración para el módulo de analytics

import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analytics import (
    analizar_volumenes_periodo,
    comparar_proveedores,
    obtener_resumen_general,
    buscar_compras_similares
)
from src.database import connect_db, guardar_compra
from src.backup import backup_database, limpiar_backups_antiguos
from src.alerts import generar_alertas, set_config, get_config

class TestAnalytics(unittest.TestCase):
    """Tests para las funciones de análisis."""

    @classmethod
    def setUpClass(cls):
        """Configurar entorno de pruebas."""
        # Crear base de datos temporal para pruebas
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = Path(cls.temp_dir) / 'test_stock.db'

        # Configurar base de datos temporal
        import src.database
        src.database.DB_NAME = str(cls.db_path)

        # Crear estructura básica de la base de datos
        cls._setup_test_database()

    @classmethod
    def tearDownClass(cls):
        """Limpiar entorno de pruebas."""
        import src.database
        src.database.DB_NAME = 'stock.db'  # Restaurar original

        # Eliminar directorio temporal
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        """Configurar para cada test."""
        # Limpiar datos de pruebas anteriores
        self._clear_test_data()

        # Insertar datos de prueba
        self._insert_test_data()

    def _setup_test_database(self):
        """Crear estructura de base de datos para pruebas."""
        conn = connect_db()
        if not conn:
            raise Exception("No se puede conectar a la base de datos de pruebas")

        try:
            cursor = conn.cursor()

            # Crear tablas
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS Productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    unidades_validas_json TEXT
                );

                CREATE TABLE IF NOT EXISTS Proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS Compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER,
                    proveedor_id INTEGER,
                    cantidad REAL,
                    unidad_medida TEXT,
                    precio_total REAL,
                    fecha_compra TEXT,
                    descuento TEXT,
                    FOREIGN KEY (producto_id) REFERENCES Productos (id),
                    FOREIGN KEY (proveedor_id) REFERENCES Proveedores (id)
                );

                CREATE TABLE IF NOT EXISTS Configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()

        finally:
            conn.close()

    def _clear_test_data(self):
        """Limpiar datos de prueba."""
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Compras")
            cursor.execute("DELETE FROM Productos")
            cursor.execute("DELETE FROM Proveedores")
            cursor.execute("DELETE FROM Configuracion")
            conn.commit()
            conn.close()

    def _insert_test_data(self):
        """Insertar datos de prueba."""
        conn = connect_db()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Insertar productos
            productos = [
                ('Pollo', '["kg", "unidad"]'),
                ('Patatas', '["kg", "bolsa"]'),
                ('Leche', '["litro", "brick"]')
            ]
            cursor.executemany(
                "INSERT INTO Productos (nombre, unidades_validas_json) VALUES (?, ?)",
                productos
            )

            # Insertar proveedores
            proveedores = [
                ('Distribuidora Central',),
                ('Verdulería Pepe',),
                ('Lacteos S.A.',)
            ]
            cursor.executemany(
                "INSERT INTO Proveedores (nombre) VALUES (?)",
                proveedores
            )

            # Insertar compras de prueba
            hoy = datetime.now()
            compras = [
                # Pollo - diferentes proveedores y precios
                ('Pollo', 'Distribuidora Central', 5.0, 'kg', 10.50,
                 (hoy - timedelta(days=5)).strftime('%Y-%m-%d'), None),
                ('Pollo', 'Verdulería Pepe', 3.0, 'kg', 5.70,
                 (hoy - timedelta(days=3)).strftime('%Y-%m-%d'), '5% descuento'),
                ('Pollo', 'Distribuidora Central', 2.0, 'kg', 4.60,
                 (hoy - timedelta(days=1)).strftime('%Y-%m-%d'), None),

                # Patatas - diferentes precios
                ('Patatas', 'Verdulería Pepe', 10.0, 'kg', 18.80,
                 (hoy - timedelta(days=10)).strftime('%Y-%m-%d'), None),
                ('Patatas', 'Distribuidora Central', 5.0, 'kg', 9.50,
                 (hoy - timedelta(days=2)).strftime('%Y-%m-%d'), None),

                # Leche - solo un proveedor
                ('Leche', 'Lacteos S.A.', 20.0, 'litro', 30.00,
                 (hoy - timedelta(days=7)).strftime('%Y-%m-%d'), None),
            ]

            for compra in compras:
                cursor.execute("""
                    INSERT INTO Compras (producto_id, proveedor_id, cantidad, unidad_medida,
                                       precio_total, fecha_compra, descuento)
                    SELECT p.id, pr.id, ?, ?, ?, ?, ?
                    FROM Productos p, Proveedores pr
                    WHERE p.nombre = ? AND pr.nombre = ?
                """, (compra[2], compra[3], compra[4], compra[5], compra[6], compra[0], compra[1]))

            # Insertar configuración de prueba
            configs = [
                ('umbral_exceso_stock', '10.0', 'Kg máximo antes de alerta'),
                ('dias_sin_compra_alerta', '30', 'Días sin compra para alertar')
            ]
            cursor.executemany(
                "INSERT INTO Configuracion (clave, valor, descripcion) VALUES (?, ?, ?)",
                configs
            )

            conn.commit()

        finally:
            conn.close()

    def test_analisis_periodo_vacio(self):
        """Período sin compras retorna lista vacía."""
        inicio = '2030-01-01'
        fin = '2030-12-31'
        resultado = analizar_volumenes_periodo(inicio, fin)
        self.assertEqual(resultado, [])

    def test_analisis_periodo_con_datos(self):
        """Período con datos retorna estadísticas correctas."""
        inicio = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        fin = datetime.now().strftime('%Y-%m-%d')

        resultado = analizar_volumenes_periodo(inicio, fin)

        # Debe encontrar al menos los 3 productos de prueba
        self.assertGreater(len(resultado), 0)

        # Verificar estructura de resultados
        for item in resultado:
            self.assertIn('producto', item)
            self.assertIn('num_compras', item)
            self.assertIn('volumen_total', item)
            self.assertIn('gasto_total', item)
            self.assertIn('precio_promedio', item)
            self.assertIn('mejor_precio', item)
            self.assertIn('peor_precio', item)

        # Verificar datos específicos para Pollo
        pollo_data = next((item for item in resultado if item['producto'] == 'Pollo'), None)
        if pollo_data:
            self.assertEqual(pollo_data['num_compras'], 3)
            self.assertEqual(pollo_data['volumen_total'], 10.0)
            self.assertGreater(pollo_data['gasto_total'], 0)

    def test_analisis_filtrado_por_producto(self):
        """Análisis filtrado por producto específico."""
        inicio = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        fin = datetime.now().strftime('%Y-%m-%d')

        resultado = analizar_volumenes_periodo(inicio, fin, 'Pollo')

        # Solo debe retornar Pollo
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['producto'], 'Pollo')
        self.assertEqual(resultado[0]['num_compras'], 3)

    def test_comparador_proveedores_identifica_mejor_precio(self):
        """El proveedor más barato se marca como mejor."""
        resultado = comparar_proveedores('Pollo')

        # Debe encontrar 2 proveedores para Pollo
        self.assertEqual(len(resultado), 2)

        # Verificar que solo uno está marcado como mejor
        mejores = [r for r in resultado if r['es_mejor']]
        self.assertEqual(len(mejores), 1)

        # El mejor debe tener el precio más bajo
        mejor_precio = min(r['precio_promedio'] for r in resultado)
        self.assertEqual(mejores[0]['precio_promedio'], mejor_precio)

    def test_comparador_producto_sin_compras(self):
        """Producto sin compras retorna lista vacía."""
        resultado = comparar_proveedores('ProductoInexistente')
        self.assertEqual(resultado, [])

    def test_resumen_general_estructura(self):
        """Resumen general tiene la estructura correcta."""
        resultado = obtener_resumen_general()

        # Verificar campos principales
        self.assertIn('total_compras', resultado)
        self.assertIn('gasto_total', resultado)
        self.assertIn('top_productos', resultado)
        self.assertIn('top_proveedores', resultado)

        # Debe tener compras de prueba
        self.assertGreater(resultado['total_compras'], 0)
        self.assertGreater(resultado['gasto_total'], 0)

        # Top productos debe tener hasta 5 elementos
        self.assertLessEqual(len(resultado['top_productos']), 5)

        # Top proveedores debe tener hasta 5 elementos
        self.assertLessEqual(len(resultado['top_proveedores']), 5)

    def test_buscar_compras_similares(self):
        """Búsqueda de compras similares funciona correctamente."""
        similares = buscar_compras_similares('Pollo', 5.0, margen_precio=0.2)

        # Debe encontrar compras similares de pollo
        self.assertGreater(len(similares), 0)

        # Verificar estructura de resultados
        for item in similares:
            self.assertIn('fecha', item)
            self.assertIn('cantidad', item)
            self.assertIn('precio_unitario', item)
            self.assertIn('proveedor', item)

    def test_alertas_dinamicas(self):
        """Sistema de alertas genera alertas basadas en configuración."""
        # Configurar umbral bajo para generar alerta
        set_config('umbral_exceso_stock', '5.0', 'Test: umbral bajo')

        alertas = generar_alertas()

        # Debe generar alertas con estructura correcta
        for alerta in alertas:
            self.assertIn('tipo', alerta)
            self.assertIn('categoria', alerta)
            self.assertIn('titulo', alerta)
            self.assertIn('mensaje', alerta)
            self.assertIn('prioridad', alerta)

        # Debe haber al menos una alerta de stock (10kg de pollo > 5kg umbral)
        alertas_stock = [a for a in alertas if a['categoria'] == 'stock']
        self.assertGreater(len(alertas_stock), 0)

    def test_configuracion_get_set(self):
        """Configuración get/set funciona correctamente."""
        # Set
        resultado_set = set_config('test_key', 'test_value', 'Test description')
        self.assertTrue(resultado_set)

        # Get
        resultado_get = get_config('test_key')
        self.assertEqual(resultado_get, 'test_value')

        # Get con default
        resultado_default = get_config('nonexistent_key', 'default_value')
        self.assertEqual(resultado_default, 'default_value')

    def test_backup_creacion(self):
        """Sistema de backup crea archivos correctamente."""
        backup_path = backup_database(comprimir=True)

        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.stat().st_size > 0)

        # Limpiar
        if backup_path and backup_path.exists():
            backup_path.unlink()

    def test_backup_limpieza(self):
        """Sistema de limpieza de backups funciona correctamente."""
        # Crear backups de prueba con diferentes fechas
        temp_backups_dir = Path(self.temp_dir) / 'test_backups'
        temp_backups_dir.mkdir(exist_ok=True)

        import src.backup
        original_backups_dir = src.backup.BACKUPS_DIR
        src.backup.BACKUPS_DIR = str(temp_backups_dir)

        try:
            # Crear backup actual
            backup_path = backup_database(comprimir=True)

            # Simular backups antiguos (creando archivos vacíos)
            fecha_antigua = (datetime.now() - timedelta(days=40)).strftime('%Y%m%d_%H%M%S')
            old_backup = temp_backups_dir / f'stock_backup_{fecha_antigua}.db.gz'
            old_backup.write_text('test')

            # Contar archivos antes de limpiar
            backups_antes = len(list(temp_backups_dir.glob('*.db*')))

            # Limpiar backups antiguos (retención de 30 días)
            eliminados = limpiar_backups_antiguos(retention_days=30)

            # Verificar que se eliminó el backup antiguo
            self.assertEqual(eliminados, 1)
            self.assertFalse(old_backup.exists())

            # El backup actual debe permanecer
            backups_despues = len(list(temp_backups_dir.glob('*.db*')))
            self.assertEqual(backups_despues, backups_antes - 1)

        finally:
            # Restaurar configuración original
            src.backup.BACKUPS_DIR = original_backups_dir
            shutil.rmtree(temp_backups_dir, ignore_errors=True)

    def test_integridad_validaciones(self):
        """Validaciones manejan correctamente datos inválidos."""
        from src.validators import validar_compra, validar_fecha_analisis

        # Validación de compra con datos inválidos
        datos_invalidos = {
            'producto': '',
            'cantidad': -5,
            'precio': 'invalido',
            'fecha_compra': 'fecha-invalida'
        }

        es_valido, mensaje = validar_compra(datos_invalidos)
        self.assertFalse(es_valido)
        self.assertIsInstance(mensaje, str)
        self.assertGreater(len(mensaje), 0)

        # Validación de fechas de análisis
        valido, mensaje = validar_fecha_analisis('2025-01-01', '2024-12-31')  # inicio > fin
        self.assertFalse(valido)
        self.assertIn('posterior', mensaje)

        valido, mensaje = validar_fecha_analisis('2025-01-01', '2025-01-31')  # rango válido
        self.assertTrue(valido)
        self.assertEqual(mensaje, 'OK')

if __name__ == '__main__':
    unittest.main()