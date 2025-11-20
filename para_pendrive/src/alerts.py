# alerts.py
# Sistema de alertas dinámicas basado en configuración

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.database import connect_db
from src.utils import safe_divide

logger = logging.getLogger('BarStock')

def get_config(clave: str, default=None):
    """Obtiene un valor de configuración de la base de datos."""
    conn = connect_db()
    if not conn:
        return default

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM Configuracion WHERE clave = ?", (clave,))
        result = cursor.fetchone()
        return result[0] if result else default
    except sqlite3.Error:
        return default
    finally:
        conn.close()

def set_config(clave: str, valor: str, descripcion: str = None):
    """Establece un valor de configuración."""
    conn = connect_db()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO Configuracion (clave, valor, descripcion, fecha_modificacion)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (clave, valor, descripcion))
        conn.commit()
        logger.info(f"Configuración actualizada: {clave} = {valor}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error guardando configuración: {e}")
        return False
    finally:
        conn.close()

def generar_alertas() -> List[Dict]:
    """
    Genera alertas basadas en reglas configurables.

    Returns:
        List[Dict]: Lista de alertas activas
    """
    logger.info("Generando alertas dinámicas...")
    alertas = []
    conn = connect_db()

    if not conn:
        logger.error("No se puede conectar a la base de datos para generar alertas")
        return alertas

    cursor = conn.cursor()

    try:
        # 1. Alerta de productos con stock alto
        alertas.extend(_generar_alertas_stock(cursor))

        # 2. Alerta de productos sin compras recientes
        alertas.extend(_generar_alertas_inactividad(cursor))

        # 3. Alerta de variaciones de precio
        alertas.extend(_generar_alertas_precios(cursor))

        # 4. Alerta de proveedores con precios altos
        alertas.extend(_generar_alertas_proveedores(cursor))

        logger.info(f"Se generaron {len(alertas)} alertas")
        return alertas

    except sqlite3.Error as e:
        logger.error(f"Error generando alertas: {e}")
        return []
    finally:
        conn.close()

def _generar_alertas_stock(cursor) -> List[Dict]:
    """Genera alertas de exceso de stock."""
    alertas = []
    umbral = float(get_config('umbral_exceso_stock', 10.0))

    query = """
    SELECT
        p.nombre,
        SUM(c.cantidad) as stock_actual,
        COUNT(c.id) as total_compras
    FROM Compras c
    JOIN Productos p ON c.producto_id = p.id
    GROUP BY p.nombre
    HAVING stock_actual > ?
    ORDER BY stock_actual DESC
    """

    for row in cursor.execute(query, (umbral,)):
        alertas.append({
            'tipo': 'warning',
            'categoria': 'stock',
            'titulo': 'Exceso de Stock Detectado',
            'mensaje': f"{row['nombre']}: {row['stock_actual']:.1f} unidades (umbral: {umbral})",
            'datos': {
                'producto': row['nombre'],
                'stock_actual': row['stock_actual'],
                'umbral': umbral,
                'total_compras': row['total_compras']
            },
            'prioridad': 'media'
        })

    return alertas

def _generar_alertas_inactividad(cursor) -> List[Dict]:
    """Genera alertas de productos sin compras recientes."""
    alertas = []
    dias = int(get_config('dias_sin_compra_alerta', 30))
    fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    query = """
    SELECT
        p.nombre,
        MAX(c.fecha_compra) as ultima_compra,
        COUNT(c.id) as total_compras
    FROM Productos p
    LEFT JOIN Compras c ON p.id = c.producto_id
    GROUP BY p.nombre
    HAVING ultima_compra < ? OR ultima_compra IS NULL
    ORDER BY ultima_compra ASC
    """

    for row in cursor.execute(query, (fecha_limite,)):
        ultima = row['ultima_compra'] or "nunca"
        estado = "Sin compras registradas" if row['total_compras'] == 0 else f"Última compra: {ultima}"

        alertas.append({
            'tipo': 'info',
            'categoria': 'inactividad',
            'titulo': 'Sin Movimiento Reciente',
            'mensaje': f"{row['nombre']}: {estado}",
            'datos': {
                'producto': row['nombre'],
                'ultima_compra': ultima,
                'dias_sin_compra': dias,
                'total_compras': row['total_compras']
            },
            'prioridad': 'baja'
        })

    return alertas

def _generar_alertas_precios(cursor) -> List[Dict]:
    """Genera alertas por variaciones significativas de precios."""
    alertas = []
    variacion_limite = float(get_config('variacion_precio_alerta', 0.15))  # 15%

    # Buscar productos con alta variación de precios
    query = """
    SELECT
        p.nombre as producto,
        COUNT(*) as num_compras,
        MIN(c.precio_total / c.cantidad) as precio_min,
        MAX(c.precio_total / c.cantidad) as precio_max,
        AVG(c.precio_total / c.cantidad) as precio_promedio,
        MAX(c.fecha_compra) as ultima_compra
    FROM Compras c
    JOIN Productos p ON c.producto_id = p.id
    WHERE c.fecha_compra >= date('now', '-90 days')  # Últimos 90 días
    GROUP BY p.nombre
    HAVING num_compras >= 3  # Al menos 3 compras
       AND (precio_max - precio_min) / precio_promedio > ?
    ORDER BY (precio_max - precio_min) DESC
    """

    for row in cursor.execute(query, (variacion_limite,)):
        variacion_pct = (row['precio_max'] - row['precio_min']) / row['precio_promedio'] * 100

        alertas.append({
            'tipo': 'warning',
            'categoria': 'precio',
            'titulo': 'Alta Variación de Precios',
            'mensaje': f"{row['producto']}: variación del {variacion_pct:.1f}% entre proveedores",
            'datos': {
                'producto': row['producto'],
                'precio_min': round(row['precio_min'], 3),
                'precio_max': round(row['precio_max'], 3),
                'variacion_pct': round(variacion_pct, 1),
                'ahorro_potencial': round((row['precio_max'] - row['precio_min']) * 5, 2)  # Estimado para 5 unidades
            },
            'prioridad': 'alta'
        })

    return alertas

def _generar_alertas_proveedores(cursor) -> List[Dict]:
    """Genera alertas sobre proveedores con precios consistentemente altos."""
    alertas = []

    # Comparar precios entre proveedores para el mismo producto
    query = """
    WITH precios_proveedor AS (
        SELECT
            p.nombre as producto,
            COALESCE(pr.nombre, 'Sin proveedor') as proveedor,
            AVG(c.precio_total / c.cantidad) as precio_promedio,
            COUNT(*) as num_compras
        FROM Compras c
        JOIN Productos p ON c.producto_id = p.id
        LEFT JOIN Proveedores pr ON c.proveedor_id = pr.id
        WHERE c.fecha_compra >= date('now', '-60 days')  # Últimos 60 días
        GROUP BY p.nombre, pr.nombre
        HAVING num_compras >= 2
    ),
    mejor_precio AS (
        SELECT
            producto,
            MIN(precio_promedio) as mejor_precio
        FROM precios_proveedor
        GROUP BY producto
    )
    SELECT
        pp.producto,
        pp.proveedor,
        pp.precio_promedio,
        mp.mejor_precio,
        (pp.precio_promedio - mp.mejor_precio) / mp.mejor_precio as exceso_pct
    FROM precios_proveedor pp
    JOIN mejor_precio mp ON pp.producto = mp.producto
    WHERE pp.precio_promedio > mp.mejor_precio * 1.20  # 20% más caro que el mejor
    ORDER BY exceso_pct DESC
    LIMIT 5
    """

    for row in cursor.execute(query):
        exceso_pct = row['exceso_pct'] * 100

        alertas.append({
            'tipo': 'info',
            'categoria': 'proveedor',
            'titulo': 'Proveedor con Precios Elevados',
            'mensaje': f"{row['proveedor']}: {exceso_pct:.1f}% más caro que el mejor precio para {row['producto']}",
            'datos': {
                'producto': row['producto'],
                'proveedor': row['proveedor'],
                'precio_actual': round(row['precio_promedio'], 3),
                'mejor_precio': round(row['mejor_precio'], 3),
                'exceso_pct': round(exceso_pct, 1)
            },
            'prioridad': 'media'
        })

    return alertas

def obtener_estadisticas_alertas() -> Dict:
    """
    Obtiene estadísticas sobre las alertas generadas.

    Returns:
        Dict: Estadísticas de alertas
    """
    alertas = generar_alertas()

    stats = {
        'total_alertas': len(alertas),
        'por_tipo': {},
        'por_categoria': {},
        'por_prioridad': {'alta': 0, 'media': 0, 'baja': 0},
        'mas_recientes': alertas[:5] if alertas else []
    }

    for alerta in alertas:
        # Contar por tipo
        tipo = alerta['tipo']
        stats['por_tipo'][tipo] = stats['por_tipo'].get(tipo, 0) + 1

        # Contar por categoría
        categoria = alerta['categoria']
        stats['por_categoria'][categoria] = stats['por_categoria'].get(categoria, 0) + 1

        # Contar por prioridad
        prioridad = alerta['prioridad']
        stats['por_prioridad'][prioridad] += 1

    return stats

def ejecutar_analisis_programado():
    """
    Ejecuta un análisis completo y registra resultados.
    Útil para ejecuciones periódicas automáticas.
    """
    logger.info("Ejecutando análisis programado...")

    # Generar alertas
    alertas = generar_alertas()

    # Estadísticas
    stats = obtener_estadisticas_alertas()

    # Registrar en log
    logger.info(f"Análisis completado: {len(alertas)} alertas generadas")
    logger.info(f"Distribución: {stats['por_tipo']}")

    return {
        'timestamp': datetime.now().isoformat(),
        'alertas_generadas': len(alertas),
        'estadisticas': stats,
        'alertas_criticas': [a for a in alertas if a['prioridad'] == 'alta']
    }