# app.py
# Este es el script principal. Ejecútalo para iniciar la aplicación: python app.py

import eel
import sqlite3
import json
import datetime

DB_NAME = 'stock.db'

# Inicializa Eel para que busque los archivos web en la carpeta 'web'
eel.init('web')

# --- Funciones Auxiliares de Base de Datos ---

def connect_db():
    """Conecta a la base de datos SQLite."""
    try:
        return sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# --- Funciones Expuestas (Llamadas desde JavaScript) ---

@eel.expose  # Permite que JavaScript llame a esta función
def get_datos_iniciales():
    """Busca los productos y proveedores para llenar los menús <select> al cargar la app."""
    conn = connect_db()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()
    
    # Obtenemos productos (con sus unidades válidas)
    cursor.execute("SELECT nombre, unidades_validas_json FROM Productos ORDER BY nombre")
    productos = []
    # Creamos el mapa de unidades válidas que usará JavaScript
    unidades_map = {}
    for row in cursor.fetchall():
        nombre, unidades_json = row
        productos.append(nombre)
        unidades_map[nombre] = json.loads(unidades_json)
    
    # Obtenemos proveedores
    cursor.execute("SELECT nombre FROM Proveedores ORDER BY nombre")
    proveedores = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Enviamos todo a la interfaz
    return {
        "productos": productos,
        "proveedores": proveedores,
        "unidades_map": unidades_map
    }

@eel.expose
def guardar_compra(datos):
    """Recibe un objeto 'datos' desde JS y lo guarda en la tabla Compras."""
    print(f"Recibidos datos para guardar: {datos}")
    
    # 1. Necesitamos los IDs de producto y proveedor, no solo los nombres
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}
        
    cursor = conn.cursor()
    
    try:
        # Buscar ID de Producto
        cursor.execute("SELECT id FROM Productos WHERE nombre = ?", (datos['producto'],))
        producto_id = cursor.fetchone()[0]
        
        # Buscar ID de Proveedor (puede ser opcional)
        proveedor_id = None
        if datos.get('proveedor'):
            cursor.execute("SELECT id FROM Proveedores WHERE nombre = ?", (datos['proveedor'],))
            res = cursor.fetchone()
            if res:
                proveedor_id = res[0]

        # 2. Insertar los datos en la tabla Compras
        sql = """
        INSERT INTO Compras (producto_id, proveedor_id, cantidad, unidad_medida, precio_total, fecha_compra, descuento)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            producto_id,
            proveedor_id,
            datos.get('cantidad'),
            datos.get('unidad'),
            datos.get('precio'),
            datos.get('fecha_compra'),
            datos.get('descuento')
        )
        
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        
        print("Compra guardada con éxito.")
        return {"success": True}
        
    except sqlite3.Error as e:
        print(f"Error al guardar la compra: {e}")
        conn.close()
        return {"success": False, "error": str(e)}
    except TypeError:
         # Esto pasa si el producto_id no se encuentra (cursor.fetchone() es None)
        print("Error: El producto no existe en la base de datos.")
        conn.close()
        return {"success": False, "error": "Producto no encontrado"}

# --- Iniciar la Aplicación ---
print("Iniciando aplicación. Abrí la ventana...")
# Inicia la app con el index.html y define el tamaño de la ventana
eel.start('index.html', size=(1200, 900))