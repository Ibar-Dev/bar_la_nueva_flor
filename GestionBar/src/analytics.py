# analytics.py
# Módulo de análisis de volúmenes y precios de compras

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from src.database import connect_db
from src.utils import safe_divide, calcular_precio_unitario

logger = logging.getLogger('BarStock')

def analizar_volumenes_periodo(inicio: str, fin: str, producto: str = None) -> List[Dict]:
    """
    Analiza volúmenes de compra en un período.

    Args:
        inicio: Fecha inicio (YYYY-MM-DD)
        fin: Fecha fin (YYYY-MM-DD)
        producto: Filtrar por producto específico (opcional)

    Returns:
        List[Dict]: Estadísticas agregadas
    """
    logger.info(f"Analizando volúmenes del {inicio} al {fin}, producto: {producto or 'todos'}")

    conn = connect_db()
    if not conn:
        logger.error("No se puede conectar a la base de datos")
        return []

    cursor = conn.cursor()

    try:
        query = """
        SELECT
            p.nombre as producto,
            p.unidades_validas_json as unidades_json,
            COUNT(*) as num_compras,
            SUM(c.cantidad) as volumen_total,
            AVG(c.precio_total / c.cantidad) as precio_promedio_unitario,
            MIN(c.precio_total / c.cantidad) as mejor_precio_unitario,
            MAX(c.precio_total / c.cantidad) as peor_precio_unitario,
            SUM(c.precio_total) as gasto_total
        FROM Compras c
        JOIN Productos p ON c.producto_id = p.id
        WHERE c.fecha_compra BETWEEN ? AND ?
        """

        params = [inicio, fin]

        if producto:
            query += " AND p.nombre = ?"
            params.append(producto)

        query += " GROUP BY p.nombre ORDER BY gasto_total DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        resultados = []
        for row in rows:
            # Obtener unidad más común para este producto
            unidades = __import__('json').loads(row['unidades_json'])
            unidad_principal = unidades[0] if unidades else 'unidad'

            resultados.append({
                'producto': row['producto'],
                'num_compras': row['num_compras'],
                'volumen_total': round(row['volumen_total'], 2),
                'unidad': unidad_principal,
                'gasto_total': round(row['gasto_total'], 2),
                'precio_promedio': round(row['precio_promedio_unitario'], 4),
                'mejor_precio': round(row['mejor_precio_unitario'], 4),
                'peor_precio': round(row['peor_precio_unitario'], 4),
                'ahorro_potencial': round(
                    (row['peor_precio_unitario'] - row['mejor_precio_unitario']) * row['volumen_total'], 2
                )
            })

        logger.info(f"Análisis completado: {len(resultados)} productos analizados")
        return resultados

    except sqlite3.Error as e:
        logger.error(f"Error en análisis de volúmenes: {e}")
        return []
    finally:
        conn.close()

def comparar_proveedores(producto: str, ultimas_n: int = 5) -> List[Dict]:
    """
    Compara precios de proveedores para un producto.

    Args:
        producto: Nombre del producto a analizar
        ultimas_n: Número de compras recientes a considerar

    Returns:
        List[Dict]: Comparación de proveedores
    """
    logger.info(f"Comparando proveedores para '{producto}' (últimas {ultimas_n} compras)")

    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        query = """
        SELECT
            COALESCE(prov.nombre, 'Sin proveedor') as proveedor,
            AVG(c.precio_total / c.cantidad) as precio_avg,
            COUNT(*) as num_compras,
            SUM(c.cantidad) as volumen_total,
            MAX(c.fecha_compra) as ultima_compra,
            MIN(c.precio_total / c.cantidad) as precio_min,
            MAX(c.precio_total / c.cantidad) as precio_max
        FROM Compras c
        JOIN Productos p ON c.producto_id = p.id
        LEFT JOIN Proveedores prov ON c.proveedor_id = prov.id
        WHERE p.nombre = ?
        GROUP BY prov.nombre
        HAVING COUNT(*) > 0
        ORDER BY precio_avg ASC
        """

        cursor.execute(query, (producto,))
        rows = cursor.fetchall()

        if not rows:
            logger.warning(f"No se encontraron compras para el producto: {producto}")
            return []

        # Marcar el mejor precio
        mejor_precio = rows[0]['precio_avg']

        resultados = []
        for row in rows:
            es_mejor = abs(row['precio_avg'] - mejor_precio) < 0.001  # Para evitar problemas de float

            resultados.append({
                'proveedor': row['proveedor'],
                'precio_promedio': round(row['precio_avg'], 4),
                'num_compras': row['num_compras'],
                'volumen_total': round(row['volumen_total'], 2),
                'ultima_compra': row['ultima_compra'],
                'precio_min': round(row['precio_min'], 4),
                'precio_max': round(row['precio_max'], 4),
                'es_mejor': es_mejor,
                'variacion_precio': round(row['precio_max'] - row['precio_min'], 4)
            })

        logger.info(f"Comparación completada: {len(resultados)} proveedores para '{producto}'")
        return resultados

    except sqlite3.Error as e:
        logger.error(f"Error comparando proveedores: {e}")
        return []
    finally:
        conn.close()

def obtener_tendencias_precios(producto: str, dias: int = 30) -> List[Dict]:
    """
    Obtiene la tendencia de precios para un producto.

    Args:
        producto: Nombre del producto
        dias: Número de días hacia atrás

    Returns:
        List[Dict]: Evolución de precios en el tiempo
    """
    logger.info(f"Obteniendo tendencia de precios para '{producto}' últimos {dias} días")

    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

        query = """
        SELECT
            c.fecha_compra,
            c.precio_total / c.cantidad as precio_unitario,
            c.cantidad,
            prov.nombre as proveedor
        FROM Compras c
        JOIN Productos p ON c.producto_id = p.id
        LEFT JOIN Proveedores prov ON c.proveedor_id = prov.id
        WHERE p.nombre = ? AND c.fecha_compra >= ?
        ORDER BY c.fecha_compra ASC
        """

        cursor.execute(query, (producto, fecha_limite))
        rows = cursor.fetchall()

        tendencias = []
        for row in rows:
            tendencias.append({
                'fecha': row['fecha_compra'],
                'precio_unitario': round(row['precio_unitario'], 4),
                'cantidad': row['cantidad'],
                'proveedor': row['proveedor'] or 'N/A'
            })

        logger.info(f"Tendencias obtenidas: {len(tendencias)} registros para '{producto}'")
        return tendencias

    except sqlite3.Error as e:
        logger.error(f"Error obteniendo tendencias: {e}")
        return []
    finally:
        conn.close()

def obtener_resumen_general() -> Dict:
    """
    Obtiene un resumen general del estado actual del inventario.

    Returns:
        Dict: Resumen con estadísticas generales
    """
    logger.info("Generando resumen general del inventario")

    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor()

    try:
        resumen = {}

        # 1. Compras totales y gasto acumulado
        cursor.execute("""
            SELECT COUNT(*) as total_compras, SUM(precio_total) as gasto_total
            FROM Compras
        """)
        stats = cursor.fetchone()
        resumen['total_compras'] = stats['total_compras'] or 0
        resumen['gasto_total'] = round(stats['gasto_total'] or 0, 2)

        # 2. Productos más comprados
        cursor.execute("""
            SELECT p.nombre, COUNT(*) as compras, SUM(c.cantidad) as volumen
            FROM Compras c
            JOIN Productos p ON c.producto_id = p.id
            GROUP BY p.nombre
            ORDER BY compras DESC
            LIMIT 5
        """)
        resumen['top_productos'] = [
            {'nombre': row['nombre'], 'compras': row['compras'], 'volumen': round(row['volumen'], 2)}
            for row in cursor.fetchall()
        ]

        # 3. Compras recientes (últimos 7 días)
        semana_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as compras_recientes, SUM(precio_total) as gasto_reciente
            FROM Compras
            WHERE fecha_compra >= ?
        """, (semana_atras,))
        recientes = cursor.fetchone()
        resumen['compras_semana'] = recientes['compras_recientes'] or 0
        resumen['gasto_semana'] = round(recientes['gasto_reciente'] or 0, 2)

        # 4. Proveedores más utilizados
        cursor.execute("""
            SELECT COALESCE(pr.nombre, 'Sin proveedor') as proveedor, COUNT(*) as usos
            FROM Compras c
            LEFT JOIN Proveedores pr ON c.proveedor_id = pr.id
            GROUP BY pr.nombre
            ORDER BY usos DESC
            LIMIT 5
        """)
        resumen['top_proveedores'] = [
            {'nombre': row['proveedor'], 'usos': row['usos']}
            for row in cursor.fetchall()
        ]

        logger.info("Resumen general generado exitosamente")
        return resumen

    except sqlite3.Error as e:
        logger.error(f"Error generando resumen: {e}")
        return {}
    finally:
        conn.close()

def buscar_compras_similares(producto: str, cantidad: float, margen_precio: float = 0.1) -> List[Dict]:
    """
    Busca compras similares para referencia de precios.

    Args:
        producto: Nombre del producto
        cantidad: Cantidad de referencia
        margen_precio: Margen de variación de precio (0.1 = 10%)

    Returns:
        List[Dict]: Compras similares
    """
    logger.info(f"Buscando compras similares para '{producto}', cantidad: {cantidad}")

    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        # Primero obtener el precio promedio del producto
        cursor.execute("""
            SELECT AVG(precio_total / cantidad) as precio_promedio
            FROM Compras c
            JOIN Productos p ON c.producto_id = p.id
            WHERE p.nombre = ?
        """, (producto,))

        resultado = cursor.fetchone()
        if not resultado or not resultado['precio_promedio']:
            return []

        precio_ref = resultado['precio_promedio']
        precio_min = precio_ref * (1 - margen_precio)
        precio_max = precio_ref * (1 + margen_precio)

        # Buscar compras dentro del margen
        cursor.execute("""
            SELECT
                c.fecha_compra,
                c.cantidad,
                c.precio_total,
                c.precio_total / c.cantidad as precio_unitario,
                prov.nombre as proveedor,
                c.descuento
            FROM Compras c
            JOIN Productos p ON c.producto_id = p.id
            LEFT JOIN Proveedores prov ON c.proveedor_id = prov.id
            WHERE p.nombre = ?
              AND c.precio_total / c.cantidad BETWEEN ? AND ?
            ORDER BY c.fecha_compra DESC
            LIMIT 10
        """, (producto, precio_min, precio_max))

        rows = cursor.fetchall()

        similares = []
        for row in rows:
            similares.append({
                'fecha': row['fecha_compra'],
                'cantidad': row['cantidad'],
                'precio_total': row['precio_total'],
                'precio_unitario': round(row['precio_unitario'], 4),
                'proveedor': row['proveedor'] or 'N/A',
                'descuento': row['descuento'] or 'N/A'
            })

        logger.info(f"Encontradas {len(similares)} compras similares")
        return similares

    except sqlite3.Error as e:
        logger.error(f"Error buscando compras similares: {e}")
        return []
    finally:
        conn.close()