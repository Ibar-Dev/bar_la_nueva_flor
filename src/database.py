# database.py
# Módulo central para todas las operaciones de base de datos

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_NAME = 'stock.db'

# Configurar logger
logger = logging.getLogger('BarStock')

def connect_db() -> Optional[sqlite3.Connection]:
    """Conecta a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        logger.debug("Conexión a base de datos establecida")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

def get_datos_iniciales() -> Dict:
    """Busca los productos y proveedores para llenar los menús <select>."""
    conn = connect_db()
    if not conn:
        return {"error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Obtenemos productos (con sus unidades válidas)
        cursor.execute("SELECT nombre, unidades_validas_json FROM Productos ORDER BY nombre")
        productos = []
        unidades_map = {}

        for row in cursor.fetchall():
            nombre, unidades_json = row['nombre'], row['unidades_validas_json']
            productos.append(nombre)
            unidades_map[nombre] = __import__('json').loads(unidades_json)

        # Obtenemos proveedores
        cursor.execute("SELECT nombre FROM Proveedores ORDER BY nombre")
        proveedores = [row['nombre'] for row in cursor.fetchall()]

        logger.info(f"Cargados {len(productos)} productos y {len(proveedores)} proveedores")

        return {
            "productos": productos,
            "proveedores": proveedores,
            "unidades_map": unidades_map
        }

    except sqlite3.Error as e:
        logger.error(f"Error al obtener datos iniciales: {e}")
        return {"error": str(e)}
    finally:
        conn.close()

def guardar_compra(datos: Dict) -> Dict:
    """Guarda una compra en la base de datos."""
    logger.info(f"Guardando compra: {datos}")

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Buscar ID de Producto
        cursor.execute("SELECT id FROM Productos WHERE nombre = ?", (datos['producto'],))
        producto_result = cursor.fetchone()

        if not producto_result:
            return {"success": False, "error": "Producto no encontrado"}

        producto_id = producto_result['id']

        # Buscar ID de Proveedor (puede ser opcional)
        proveedor_id = None
        if datos.get('proveedor'):
            cursor.execute("SELECT id FROM Proveedores WHERE nombre = ?", (datos['proveedor'],))
            proveedor_result = cursor.fetchone()
            if proveedor_result:
                proveedor_id = proveedor_result['id']

        # Insertar los datos en la tabla Compras
        sql = """
        INSERT INTO Compras (producto_id, proveedor_id, cantidad, unidad_medida, precio_total, fecha_compra, descuento)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            producto_id,
            proveedor_id,
            float(datos.get('cantidad', 0)),
            datos.get('unidad'),
            float(datos.get('precio', 0)),
            datos.get('fecha_compra'),
            datos.get('descuento')
        )

        cursor.execute(sql, params)
        conn.commit()

        compra_id = cursor.lastrowid
        logger.info(f"Compra guardada exitosamente con ID: {compra_id}")

        return {"success": True, "compra_id": compra_id}

    except sqlite3.Error as e:
        logger.error(f"Error al guardar la compra: {e}")
        return {"success": False, "error": str(e)}
    except (ValueError, TypeError) as e:
        logger.error(f"Error en los datos de la compra: {e}")
        return {"success": False, "error": f"Datos inválidos: {str(e)}"}
    finally:
        conn.close()

def obtener_historial_compras(limit: int = 50) -> List[Dict]:
    """Obtiene el historial de compras más recientes."""
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        query = """
        SELECT
            c.id,
            p.nombre as producto,
            prov.nombre as proveedor,
            c.cantidad,
            c.unidad_medida,
            c.precio_total,
            c.fecha_compra,
            c.descuento
        FROM Compras c
        JOIN Productos p ON c.producto_id = p.id
        LEFT JOIN Proveedores prov ON c.proveedor_id = prov.id
        ORDER BY c.fecha_compra DESC, c.id DESC
        LIMIT ?
        """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        compras = []
        for row in rows:
            compras.append({
                'id': row['id'],
                'producto': row['producto'],
                'proveedor': row['proveedor'] or 'N/A',
                'cantidad': row['cantidad'],
                'unidad_medida': row['unidad_medida'],
                'precio_total': row['precio_total'],
                'fecha_compra': row['fecha_compra'],
                'descuento': row['descuento'] or 'N/A'
            })

        return compras

    except sqlite3.Error as e:
        logger.error(f"Error al obtener historial: {e}")
        return []
    finally:
        conn.close()

def verificar_conexion() -> bool:
    """Verifica si la base de datos es accesible."""
    conn = connect_db()
    if conn:
        conn.close()
        return True
    return False