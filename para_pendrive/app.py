# app.py
# Script principal de la aplicación. Ejecutar: python app.py

import eel
import json
from src.database import (
    get_datos_iniciales as db_get_datos_iniciales,
    guardar_compra,
    verificar_conexion,
    obtener_todos_los_productos,
    crear_producto,
    actualizar_producto,
    eliminar_producto,
    obtener_todos_los_proveedores,
    crear_proveedor,
    actualizar_proveedor,
    eliminar_proveedor,
    obtener_todas_las_notas,
    crear_nota,
    actualizar_nota,
    eliminar_nota
)
from src.validators import validar_compra
from src.utils import setup_logger, crear_directorios, generar_timestamp
from src.analytics import (
    analizar_volumenes_periodo as analytics_analizar_volumenes,
    comparar_proveedores as analytics_comparar_proveedores,
    obtener_resumen_general as analytics_obtener_resumen
)
from src.alerts import generar_alertas as alerts_generar_alertas, ejecutar_analisis_programado
from src.backup import ejecutar_backup_automatico, obtener_estadisticas_backups
from pathlib import Path
import csv
from datetime import datetime, timedelta

# Inicializar logger y directorios
logger = setup_logger()
crear_directorios()

# Inicializa Eel para que busque los archivos web en la carpeta 'web'
eel.init('web')

# --- Funciones Expuestas (Llamadas desde JavaScript) ---

@eel.expose
def get_datos_iniciales():
    """Busca los productos y proveedores para llenar los menús <select> al cargar la app."""
    logger.info("Solicitando datos iniciales para la interfaz")
    return db_get_datos_iniciales()

@eel.expose
def guardar_compra_validada(datos):
    """Valida y guarda una compra en la base de datos."""
    logger.info(f"Recibidos datos para guardar: {datos}")

    # 1. Validar datos
    es_valido, mensaje = validar_compra(datos)
    if not es_valido:
        logger.warning(f"Datos inválidos: {mensaje}")
        return {"success": False, "error": mensaje}

    # 2. Guardar en base de datos
    resultado = guardar_compra(datos)

    if resultado.get("success"):
        logger.info(f"Compra guardada exitosamente: ID {resultado.get('compra_id')}")
    else:
        logger.error(f"Error al guardar compra: {resultado.get('error')}")

    return resultado

@eel.expose
def analizar_volumenes_periodo(inicio, fin, producto=None):
    """Analiza volúmenes de compra en un período."""
    logger.info(f"Análisis solicitado: {inicio} al {fin}, producto: {producto}")
    return analytics_analizar_volumenes(inicio, fin, producto)

@eel.expose
def comparar_proveedores(producto, ultimas_n=5):
    """Compara precios de proveedores para un producto."""
    logger.info(f"Comparación de proveedores solicitada para: {producto}")
    return analytics_comparar_proveedores(producto, ultimas_n)

@eel.expose
def obtener_resumen_general():
    """Obtiene un resumen general del inventario."""
    logger.info("Resumen general solicitado")
    return analytics_obtener_resumen()

@eel.expose
def generar_alertas():
    """Genera alertas basadas en datos actuales."""
    logger.info("Generación de alertas solicitada")
    return alerts_generar_alertas()

# --- Funciones para Gestión de Productos ---

@eel.expose
def get_todos_los_productos():
    """Obtiene todos los productos con sus detalles para administración."""
    logger.info("Solicitando todos los productos para administración")
    return obtener_todos_los_productos()

@eel.expose
def crear_nuevo_producto(nombre: str, unidades_validas: list):
    """Crea un nuevo producto."""
    logger.info(f"Creando nuevo producto: {nombre} con unidades: {unidades_validas}")
    resultado = crear_producto(nombre, unidades_validas)

    if resultado.get("success"):
        logger.info(f"Producto creado exitosamente: {resultado}")
    else:
        logger.error(f"Error al crear producto: {resultado}")

    return resultado

@eel.expose
def actualizar_producto_existente(producto_id: int, nombre: str, unidades_validas: list):
    """Actualiza un producto existente."""
    logger.info(f"Actualizando producto ID {producto_id}: {nombre} con unidades: {unidades_validas}")
    resultado = actualizar_producto(producto_id, nombre, unidades_validas)

    if resultado.get("success"):
        logger.info(f"Producto actualizado exitosamente: {resultado}")
    else:
        logger.error(f"Error al actualizar producto: {resultado}")

    return resultado

@eel.expose
def eliminar_producto_por_id(producto_id: int):
    """Elimina un producto por su ID."""
    logger.info(f"Eliminando producto con ID: {producto_id}")
    resultado = eliminar_producto(producto_id)

    if resultado.get("success"):
        logger.info(f"Producto eliminado exitosamente: {resultado}")
    else:
        logger.error(f"Error al eliminar producto: {resultado}")

    return resultado

@eel.expose
def exportar_analisis_csv(inicio, fin, producto=None):
    """Exporta análisis a CSV."""
    logger.info(f"Exportación CSV solicitada: {inicio} al {fin}, producto: {producto}")

    try:
        # Obtener datos del análisis
        datos = analytics_analizar_volumenes(inicio, fin, producto)

        if not datos:
            return "No hay datos para exportar"

        # Generar nombre de archivo
        timestamp = generar_timestamp()
        producto_str = f"_{producto}" if producto else ""
        filename = f'analisis_{inicio}_{fin}{producto_str}_{timestamp}.csv'

        # Asegurar que el directorio exports exista
        Path('exports').mkdir(exist_ok=True)
        filepath = Path('exports') / filename

        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            if datos:
                fieldnames = datos[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(datos)

        logger.info(f"CSV exportado exitosamente: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Error exportando CSV: {e}")
        raise

# --- Funciones para Gestión de Proveedores ---

@eel.expose
def get_todos_los_proveedores():
    """Obtiene todos los proveedores con sus detalles para administración."""
    logger.info("Solicitando todos los proveedores para administración")
    return obtener_todos_los_proveedores()

@eel.expose
def crear_nuevo_proveedor(datos):
    """Crea un nuevo proveedor."""
    logger.info(f"Creando nuevo proveedor: {datos}")
    resultado = crear_proveedor(datos)

    if resultado.get("success"):
        logger.info(f"Proveedor creado exitosamente: {resultado}")
    else:
        logger.error(f"Error al crear proveedor: {resultado}")

    return resultado

@eel.expose
def actualizar_proveedor_existente(proveedor_id, datos):
    """Actualiza un proveedor existente."""
    logger.info(f"Actualizando proveedor ID {proveedor_id}: {datos}")
    resultado = actualizar_proveedor(proveedor_id, datos)

    if resultado.get("success"):
        logger.info(f"Proveedor actualizado exitosamente: {resultado}")
    else:
        logger.error(f"Error al actualizar proveedor: {resultado}")

    return resultado

@eel.expose
def eliminar_proveedor_por_id(proveedor_id):
    """Elimina un proveedor por su ID."""
    logger.info(f"Eliminando proveedor con ID: {proveedor_id}")
    resultado = eliminar_proveedor(proveedor_id)

    if resultado.get("success"):
        logger.info(f"Proveedor eliminado exitosamente: {resultado}")
    else:
        logger.error(f"Error al eliminar proveedor: {resultado}")

    return resultado

@eel.expose
def get_proveedor_por_id(proveedor_id):
    """Obtiene un proveedor por su ID."""
    logger.info(f"Obteniendo proveedor con ID: {proveedor_id}")
    # Esta función necesita ser implementada en database.py
    return {"success": False, "error": "Función no implementada"}

# --- Funciones para Sistema de Notas ---

@eel.expose
def get_todas_las_notas(filtros=None):
    """Obtiene todas las notas con filtros opcionales."""
    logger.info("Solicitando todas las notas")
    return obtener_todas_las_notas(filtros)

@eel.expose
def crear_nueva_nota(datos):
    """Crea una nueva nota."""
    logger.info(f"Creando nueva nota: {datos.get('titulo')}")
    resultado = crear_nota(datos)

    if resultado.get("success"):
        logger.info(f"Nota creada exitosamente: {resultado}")
    else:
        logger.error(f"Error al crear nota: {resultado}")

    return resultado

@eel.expose
def actualizar_nota_existente(nota_id, datos):
    """Actualiza una nota existente."""
    logger.info(f"Actualizando nota ID {nota_id}: {datos.get('titulo')}")
    resultado = actualizar_nota(nota_id, datos)

    if resultado.get("success"):
        logger.info(f"Nota actualizada exitosamente: {resultado}")
    else:
        logger.error(f"Error al actualizar nota: {resultado}")

    return resultado

@eel.expose
def eliminar_nota_por_id(nota_id):
    """Elimina una nota por su ID."""
    logger.info(f"Eliminando nota con ID: {nota_id}")
    resultado = eliminar_nota(nota_id)

    if resultado.get("success"):
        logger.info(f"Nota eliminada exitosamente: {resultado}")
    else:
        logger.error(f"Error al eliminar nota: {resultado}")

    return resultado

@eel.expose
def get_nota_por_id(nota_id):
    """Obtiene una nota por su ID."""
    logger.info(f"Obteniendo nota con ID: {nota_id}")
    # Esta función necesita ser implementada en database.py
    return {"success": False, "error": "Función no implementada"}

# --- Iniciar la Aplicación ---

def verificar_y_ejecutar_backup_automatico():
    """Verifica si es necesario ejecutar backup automático."""
    try:
        # Buscar backup más reciente
        backups_dir = Path('backups')
        if backups_dir.exists():
            backup_files = list(backups_dir.glob('stock_backup_*.db.gz'))
            if backup_files:
                # Obtener el backup más reciente
                backup_mas_reciente = max(backup_files, key=lambda f: f.stat().st_mtime)
                edad_horas = (datetime.now().timestamp() - backup_mas_reciente.stat().st_mtime) / 3600

                # Si el backup es reciente (menos de 24h), no crear nuevo
                if edad_horas < 24:
                    logger.info(f"Backup reciente encontrado (hace {edad_horas:.1f}h), omitiendo creación")
                    return

        # Ejecutar backup automático
        logger.info("Ejecutando backup automático...")
        resultado = ejecutar_backup_automatico()

        if resultado['backup_creado']:
            logger.info(f"Backup automático creado: {resultado['backup_path']}")
        else:
            logger.warning("No se pudo crear backup automático")

        if resultado['limpieza_realizada']:
            logger.info(f"Limpieza realizada: {resultado['backups_eliminados']} backups eliminados")

        if resultado['errores']:
            for error in resultado['errores']:
                logger.error(f"Error en backup: {error}")

    except Exception as e:
        logger.error(f"Error en verificación de backup automático: {e}")

def iniciar_app():
    """Inicia la aplicación con verificaciones de seguridad."""
    logger.info("Iniciando aplicación...")

    # Verificar conexión a base de datos
    if not verificar_conexion():
        logger.error("No se puede conectar a la base de datos. Ejecuta 'python setup/database_setup.py' primero.")
        return

    # Ejutar backup automático si es necesario
    verificar_y_ejecutar_backup_automatico()

    # Ejutar análisis programado para alertas
    try:
        analisis_resultado = ejecutar_analisis_programado()
        logger.info(f"Análisis programado: {analisis_resultado['alertas_generadas']} alertas generadas")
    except Exception as e:
        logger.warning(f"No se pudo ejecutar análisis programado: {e}")

    # Cargar configuración
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        window_size = (
            config['ui']['window_size']['width'],
            config['ui']['window_size']['height']
        )
        logger.info(f"Configuración cargada. Ventana: {window_size}")
    except Exception as e:
        logger.warning(f"Error cargando configuración, usando valores por defecto: {e}")
        window_size = (1200, 900)

    # Mostrar estadísticas de backups
    try:
        stats = obtener_estadisticas_backups()
        logger.info(f"Estadísticas de backups: {stats['total_backups']} archivos, "
                   f"{stats['tamano_total_mb']}MB total")
    except Exception as e:
        logger.warning(f"No se pudieron obtener estadísticas de backups: {e}")

    # Iniciar la aplicación
    logger.info("Iniciando interfaz web...")
    try:
        eel.start('index.html', size=window_size)
    except Exception as e:
        logger.error(f"Error al iniciar Eel: {e}")
        raise

if __name__ == "__main__":
    iniciar_app()