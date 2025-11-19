# app.py
# Script principal de la aplicación. Ejecutar: python app.py

import eel
import json
from src.database import get_datos_iniciales, guardar_compra, verificar_conexion
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
    return get_datos_iniciales()

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