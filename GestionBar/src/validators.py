# validators.py
# Sistema de validación de datos de la aplicación

import re
from datetime import datetime
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger('BarStock')

def validar_compra(datos: Dict) -> Tuple[bool, str]:
    """
    Valida datos de compra antes de persistir.

    Returns:
        Tuple[bool, str]: (es_válido, mensaje_error)
    """

    # Validar campo requerido: producto
    if not datos.get('producto') or not isinstance(datos['producto'], str):
        return False, "El producto es requerido y debe ser un texto válido"

    # Validar cantidad
    try:
        cantidad = float(datos.get('cantidad', 0))
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero"
        if cantidad > 10000:  # Límite razonable para un bar
            return False, "La cantidad parece excesivamente grande"
    except (ValueError, TypeError):
        return False, "La cantidad debe ser un número válido"

    # Validar unidad
    if not datos.get('unidad') or not isinstance(datos['unidad'], str):
        return False, "La unidad de medida es requerida"

    # Validar precio
    try:
        precio = float(datos.get('precio', 0))
        if precio < 0:
            return False, "El precio no puede ser negativo"
        if precio > 10000:  # Límite razonable
            return False, "El precio parece excesivamente alto"
    except (ValueError, TypeError):
        return False, "El precio debe ser un número válido"

    # Validar fecha de compra
    fecha_str = datos.get('fecha_compra')
    if not fecha_str:
        return False, "La fecha de compra es requerida"

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        # Validar que no sea una fecha futura (con margen de 1 día para diferencias de horario)
        hoy = datetime.now()
        if fecha > hoy.replace(hour=23, minute=59, second=59):
            return False, "La fecha de compra no puede ser futura"

        # Validar que no sea muy antigua (más de 1 año)
        un_anio_atras = hoy.replace(year=hoy.year - 1)
        if fecha < un_anio_atras:
            return False, "La fecha de compra es muy antigua (más de 1 año)"

    except ValueError:
        return False, "La fecha debe tener formato YYYY-MM-DD"

    # Validar descuento (opcional)
    descuento = datos.get('descuento', '').strip()
    if descuento:
        if len(descuento) > 100:
            return False, "El descuento no puede exceder 100 caracteres"

        # Validar formato común de descuentos
        patrones_validos = [
            r'^\d+%$',  # "10%"
            r'^\d+%\s+por\s+.+',  # "10% por volumen"
            r'^\.\d+€',  # ".5€"
            r'^\d+€',  # "5€"
            r'^[A-Za-z0-9\s\-_.]+$',  # Texto simple
        ]

        patron_valido = any(re.match(patron, descuento) for patron in patrones_validos)
        if not patron_valido:
            logger.warning(f"Formato de descuento inusual: '{descuento}'")
            # No bloqueamos, solo advertimos

    logger.debug(f"Validación exitosa para compra: {datos['producto']}")
    return True, "OK"

def validar_producto(producto: str) -> Tuple[bool, str]:
    """Valida el nombre de un producto."""
    if not producto or not isinstance(producto, str):
        return False, "El producto es requerido"

    producto = producto.strip()
    if len(producto) < 2:
        return False, "El nombre del producto debe tener al menos 2 caracteres"

    if len(producto) > 50:
        return False, "El nombre del producto no puede exceder 50 caracteres"

    if not re.match(r'^[A-Za-z0-9\s\-_áéíóúÁÉÍÓÚñÑ]+$', producto):
        return False, "El nombre contiene caracteres inválidos"

    return True, "OK"

def validar_proveedor(proveedor: str) -> Tuple[bool, str]:
    """Valida el nombre de un proveedor."""
    if not proveedor or not isinstance(proveedor, str):
        return False, "El proveedor es requerido"

    proveedor = proveedor.strip()
    if len(proveedor) < 2:
        return False, "El nombre del proveedor debe tener al menos 2 caracteres"

    if len(proveedor) > 100:
        return False, "El nombre del proveedor no puede exceder 100 caracteres"

    if not re.match(r'^[A-Za-z0-9\s\-_áéíóúÁÉÍÓÚñÑ.,&]+$', proveedor):
        return False, "El nombre contiene caracteres inválidos"

    return True, "OK"

def validar_fecha_analisis(inicio: str, fin: str) -> Tuple[bool, str]:
    """Valida un rango de fechas para análisis."""
    try:
        fecha_inicio = datetime.strptime(inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fin, '%Y-%m-%d')

        if fecha_inicio > fecha_fin:
            return False, "La fecha de inicio no puede ser posterior a la fecha fin"

        # Limitar el rango a 2 años máximo
        diferencia = fecha_fin - fecha_inicio
        if diferencia.days > 730:  # 2 años
            return False, "El rango de fechas no puede exceder 2 años"

        return True, "OK"

    except ValueError:
        return False, "Las fechas deben tener formato YYYY-MM-DD"

def sanitizar_string(texto: str, max_length: int = None) -> str:
    """Limpia y sanitiza un string de texto."""
    if not isinstance(texto, str):
        texto = str(texto) if texto is not None else ""

    texto = texto.strip()

    # Eliminar caracteres potencialmente problemáticos
    texto = re.sub(r'[<>"\';]', '', texto)

    if max_length and len(texto) > max_length:
        texto = texto[:max_length]

    return texto

def validar_configuracion(clave: str, valor: str) -> Tuple[bool, str]:
    """Valida una entrada de configuración."""
    if not clave or not isinstance(clave, str):
        return False, "La clave de configuración es requerida"

    clave = clave.strip()
    if not re.match(r'^[a-z_][a-z0-9_]*$', clave):
        return False, "La clave debe seguir el formato: solo minúsculas, números y guiones bajos"

    if len(clave) > 50:
        return False, "La clave no puede exceder 50 caracteres"

    if not isinstance(valor, str):
        valor = str(valor)

    if len(valor) > 200:
        return False, "El valor no puede exceder 200 caracteres"

    return True, "OK"