# utils.py
# Utilidades comunes de la aplicación

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger():
    """Configura logger de aplicación."""
    # Crear directorio de logs si no existe
    Path("logs").mkdir(exist_ok=True)

    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configurar handlers
    handlers = [
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]

    # Configurar logger raíz
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        force=True  # Evita duplicación en modo desarrollo
    )

    # Crear logger específico para la app
    logger = logging.getLogger('BarStock')
    logger.info("Logger inicializado")

    return logger

def crear_directorios():
    """Crea los directorios necesarios para la aplicación."""
    directorios = ['logs', 'backups', 'exports']

    for directorio in directorios:
        Path(directorio).mkdir(exist_ok=True)
        print(f"Directorio '{directorio}' listo")

def format_numero(numero: float, decimales: int = 2) -> str:
    """Formatea un número con decimales consistentes."""
    try:
        return f"{numero:.{decimales}f}".replace('.', ',')
    except (ValueError, TypeError):
        return "0,00"

def format_fecha(fecha_str: str, formato_salida: str = "%d/%m/%Y") -> str:
    """Formatea una fecha de YYYY-MM-DD a otro formato."""
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha.strftime(formato_salida)
    except ValueError:
        return fecha_str  # Retorna original si hay error

def calcular_precio_unitario(precio_total: float, cantidad: float) -> float:
    """Calcula el precio unitario de forma segura."""
    try:
        if cantidad <= 0:
            return 0
        return round(precio_total / cantidad, 4)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def generar_timestamp() -> str:
    """Genera un timestamp para nombres de archivo."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def safe_divide(dividendo: float, divisor: float, default: float = 0) -> float:
    """División segura con valor por defecto."""
    try:
        if divisor == 0:
            return default
        return dividendo / divisor
    except (ValueError, TypeError):
        return default