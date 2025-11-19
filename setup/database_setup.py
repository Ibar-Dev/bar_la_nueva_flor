# database_setup.py
# Este script crea y configura la base de datos 'stock.db' por primera vez.
# Ejecútalo una sola vez: python database_setup.py

import sqlite3
import json

DB_NAME = 'stock.db'

# Definimos las unidades válidas para cada producto.
# Usamos JSON para guardar esta "regla de negocio" en la base de datos.
PRODUCTOS_INICIALES = [
    ("Pollo", json.dumps(["kg", "unidad"])),
    ("Carne de Vaca", json.dumps(["kg"])),
    ("Patatas", json.dumps(["kg", "bolsa"])),
    ("Leche", json.dumps(["litro", "brick", "unidad"])),
    ("Tomates", json.dumps(["kg", "unidad"])),
    ("Harina", json.dumps(["kg", "bolsa"]))
]

PROVEEDORES_INICIALES = [
    ("Distribuidora Central",),
    ("Verdulería Pepe",),
    ("Lacteos S.A.",)
]

CONFIGURACION_DEFAULT = [
    ('umbral_exceso_stock', '10.0', 'Kg máximo antes de alerta'),
    ('dias_vencimiento_alerta', '7', 'Días antes de alertar vencimiento'),
    ('dias_sin_compra_alerta', '30', 'Días sin compra para alertar'),
    ('variacion_precio_alerta', '0.15', 'Variación de precio para alerta (15%)'),
    ('max_dias_analisis', '730', 'Máximo días para análisis (2 años)')
]

def crear_base_de_datos():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print("Creando tablas...")

        # Tabla de Productos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            unidades_validas_json TEXT
        )
        ''')

        # Tabla de Proveedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
        ''')

        # Tabla de Compras (el corazón de la app)
        cursor.execute('''
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
        )
        ''')

        # Tabla de Configuracion para umbrales dinámicos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL,
            descripcion TEXT,
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        print("Tablas creadas con éxito.")

        # Insertar datos iniciales (ignorando si ya existen)
        print("Insertando datos iniciales...")
        cursor.executemany("INSERT OR IGNORE INTO Productos (nombre, unidades_validas_json) VALUES (?, ?)", PRODUCTOS_INICIALES)
        cursor.executemany("INSERT OR IGNORE INTO Proveedores (nombre) VALUES (?)", PROVEEDORES_INICIALES)
        cursor.executemany("INSERT OR IGNORE INTO Configuracion (clave, valor, descripcion) VALUES (?, ?, ?)", CONFIGURACION_DEFAULT)

        conn.commit()
        print("Datos iniciales insertados.")

    except sqlite3.Error as e:
        print(f"Error al configurar la base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print(f"Base de datos '{DB_NAME}' lista.")

if __name__ == "__main__":
    crear_base_de_datos()