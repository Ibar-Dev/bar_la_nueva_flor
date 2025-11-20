# backup.py
# Sistema de backups automáticos de la base de datos

import shutil
import gzip
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from src.utils import generar_timestamp

logger = logging.getLogger('BarStock')

DB_NAME = 'stock.db'
BACKUPS_DIR = 'backups'
DEFAULT_RETENTION_DAYS = 30

def backup_database(comprimir: bool = True) -> Optional[Path]:
    """
    Crea un backup de la base de datos.

    Args:
        comprimir: Si True, crea backup comprimido con gzip

    Returns:
        Path: Ruta del archivo de backup creado, o None si hubo error
    """
    try:
        # Asegurar que el directorio de backups exista
        backups_path = Path(BACKUPS_DIR)
        backups_path.mkdir(exist_ok=True)

        # Generar nombre de archivo con timestamp
        timestamp = generar_timestamp()
        extension = '.db.gz' if comprimir else '.db'
        backup_name = f'stock_backup_{timestamp}{extension}'
        backup_path = backups_path / backup_name

        # Verificar que la base de datos existe
        db_path = Path(DB_NAME)
        if not db_path.exists():
            logger.error(f"Base de datos no encontrada: {DB_NAME}")
            return None

        # Realizar backup con integridad
        logger.info(f"Iniciando backup de base de datos...")

        # Opción 1: Usar SQLite backup API (más seguro)
        if _backup_sqlite_api(db_path, backup_path, comprimir):
            logger.info(f"Backup creado exitosamente: {backup_path}")
            return backup_path
        else:
            # Opción 2: Copia directa del archivo
            return _backup_copia_directa(db_path, backup_path, comprimir)

    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        return None

def _backup_sqlite_api(db_path: Path, backup_path: Path, comprimir: bool) -> bool:
    """
    Realiza backup usando SQLite backup API.
    Es más seguro porque mantiene la integridad de la base de datos.
    """
    try:
        if comprimir:
            # Para backups comprimidos, primero creamos un temporal
            temp_backup = backup_path.with_suffix('.temp.db')

            # Conectar a la base de datos original y crear backup
            source = sqlite3.connect(str(db_path))
            dest = sqlite3.connect(str(temp_backup))

            try:
                source.backup(dest)
            finally:
                source.close()
                dest.close()

            # Comprimir el archivo temporal
            with open(temp_backup, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Eliminar archivo temporal
            temp_backup.unlink()
        else:
            # Backup sin compresión directamente
            source = sqlite3.connect(str(db_path))
            dest = sqlite3.connect(str(backup_path))

            try:
                source.backup(dest)
            finally:
                source.close()
                dest.close()

        return True

    except Exception as e:
        logger.error(f"Error en backup SQLite API: {e}")
        return False

def _backup_copia_directa(db_path: Path, backup_path: Path, comprimir: bool) -> Optional[Path]:
    """
    Realiza backup por copia directa del archivo.
    Menos seguro si la base de datos está en uso, pero más simple.
    """
    try:
        if comprimir:
            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(db_path, backup_path)

        logger.info(f"Backup por copia directa creado: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Error en copia directa: {e}")
        return None

def listar_backups() -> List[dict]:
    """
    Lista todos los backups disponibles.

    Returns:
        List[dict]: Información de cada backup
    """
    backups = []
    backups_path = Path(BACKUPS_DIR)

    if not backups_path.exists():
        return backups

    try:
        for backup_file in backups_path.glob('*.db*'):
            stat = backup_file.stat()

            # Determinar si está comprimido
            es_comprimido = backup_file.suffix == '.gz'

            # Extraer timestamp del nombre del archivo
            try:
                # Formato: stock_backup_YYYYMMDD_HHMMSS.db[.gz]
                timestamp_str = backup_file.stem.replace('stock_backup_', '')
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                edad = datetime.now() - timestamp
            except ValueError:
                # Si no puede parsear el timestamp, usa la fecha del archivo
                timestamp = datetime.fromtimestamp(stat.st_mtime)
                edad = datetime.now() - timestamp

            backups.append({
                'archivo': str(backup_file),
                'nombre': backup_file.name,
                'timestamp': timestamp,
                'edad_dias': edad.days,
                'tamano_mb': round(stat.st_size / (1024 * 1024), 2),
                'es_comprimido': es_comprimido
            })

        # Ordenar por timestamp (más reciente primero)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

        return backups

    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        return []

def limpiar_backups_antiguos(retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """
    Elimina backups más antiguos que el período de retención.

    Args:
        retention_days: Días a conservar los backups

    Returns:
        int: Número de archivos eliminados
    """
    backups = listar_backups()
    eliminados = 0
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    try:
        for backup in backups:
            if backup['timestamp'] < cutoff_date:
                backup_path = Path(backup['archivo'])
                backup_path.unlink()
                eliminados += 1
                logger.info(f"Backup antiguo eliminado: {backup['nombre']}")

        logger.info(f"Limpieza completada: {eliminados} backups eliminados")
        return eliminados

    except Exception as e:
        logger.error(f"Error en limpieza de backups: {e}")
        return 0

def restaurar_backup(backup_path: str, destino_path: str = None) -> bool:
    """
    Restaura un backup a la base de datos actual.

    Args:
        backup_path: Ruta del backup a restaurar
        destino_path: Ruta destino (opcional, usa DB_NAME por defecto)

    Returns:
        bool: True si la restauración fue exitosa
    """
    try:
        backup_file = Path(backup_path)

        if not backup_file.exists():
            logger.error(f"Backup no encontrado: {backup_path}")
            return False

        target_path = Path(destino_path or DB_NAME)

        # Crear backup de seguridad de la base actual
        if target_path.exists():
            backup_actual = backup_database(comprimir=False)
            if backup_actual:
                logger.info(f"Backup de seguridad creado: {backup_actual}")

        # Restaurar desde el backup
        if backup_file.suffix == '.gz':
            # Backup comprimido
            with gzip.open(backup_file, 'rb') as f_in:
                with open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Backup sin comprimir
            shutil.copy2(backup_file, target_path)

        logger.info(f"Base de datos restaurada desde: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Error restaurando backup: {e}")
        return False

def verificar_backup_integridad(backup_path: str) -> bool:
    """
    Verifica la integridad de un backup.

    Args:
        backup_path: Ruta del backup a verificar

    Returns:
        bool: True si el backup es válido
    """
    try:
        backup_file = Path(backup_path)

        if not backup_file.exists():
            return False

        # Crear archivo temporal para verificación
        temp_db = backup_file.with_suffix('.temp_verify.db')

        if backup_file.suffix == '.gz':
            # Descomprimir backup
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_db, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Copiar backup sin comprimir
            shutil.copy2(backup_file, temp_db)

        # Verificar integridad conectándose a la base temporal
        try:
            conn = sqlite3.connect(str(temp_db))
            cursor = conn.cursor()

            # Verificar que las tablas principales existan
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('Productos', 'Proveedores', 'Compras')
            """)
            tables = cursor.fetchall()

            if len(tables) < 3:
                logger.warning(f"Backup incompleto: faltan tablas en {backup_path}")
                return False

            # Verificar integridad de la base de datos
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()
            return result[0] == 'ok'

        except sqlite3.Error as e:
            logger.error(f"Error de integridad en backup {backup_path}: {e}")
            return False

        finally:
            # Eliminar archivo temporal
            if temp_db.exists():
                temp_db.unlink()

    except Exception as e:
        logger.error(f"Error verificando backup: {e}")
        return False

def ejecutar_backup_automatico() -> dict:
    """
    Ejecuta el proceso completo de backup automático.

    Returns:
        dict: Resultados del proceso
    """
    logger.info("Iniciando proceso de backup automático...")

    resultado = {
        'timestamp': datetime.now().isoformat(),
        'backup_creado': False,
        'backup_path': None,
        'limpieza_realizada': False,
        'backups_eliminados': 0,
        'errores': []
    }

    try:
        # 1. Crear backup
        backup_path = backup_database(comprimir=True)
        if backup_path:
            resultado['backup_creado'] = True
            resultado['backup_path'] = str(backup_path)
        else:
            resultado['errores'].append("No se pudo crear el backup")

        # 2. Limpiar backups antiguos
        eliminados = limpiar_backups_antiguos()
        if eliminados > 0:
            resultado['limpieza_realizada'] = True
            resultado['backups_eliminados'] = eliminados

        logger.info(f"Backup automático completado: {resultado}")
        return resultado

    except Exception as e:
        error_msg = f"Error en backup automático: {e}"
        logger.error(error_msg)
        resultado['errores'].append(error_msg)
        return resultado

def obtener_estadisticas_backups() -> dict:
    """
    Obtiene estadísticas sobre los backups.

    Returns:
        dict: Estadísticas de backups
    """
    backups = listar_backups()

    if not backups:
        return {
            'total_backups': 0,
            'tamano_total_mb': 0,
            'backup_mas_reciente': None,
            'backup_mas_antiguo': None,
            'promedio_edad_dias': 0
        }

    total_tamano = sum(b['tamano_mb'] for b in backups)
    edad_total = sum(b['edad_dias'] for b in backups)

    return {
        'total_backups': len(backups),
        'tamano_total_mb': round(total_tamano, 2),
        'backup_mas_reciente': backups[0] if backups else None,
        'backup_mas_antiguo': backups[-1] if backups else None,
        'promedio_edad_dias': round(edad_total / len(backups), 1) if backups else 0,
        'backups_comprimidos': sum(1 for b in backups if b['es_comprimido']),
        'backups_no_comprimidos': sum(1 for b in backups if not b['es_comprimido'])
    }