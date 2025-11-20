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

# ==================== CRUD DE PRODUCTOS ====================

def obtener_todos_los_productos() -> Dict:
    """Obtiene todos los productos con sus detalles."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        query = """
        SELECT
            id,
            nombre,
            unidades_validas_json,
            (SELECT COUNT(*) FROM Compras WHERE producto_id = p.id) as total_compras
        FROM Productos p
        ORDER BY nombre
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        productos = []
        for row in rows:
            productos.append({
                'id': row['id'],
                'nombre': row['nombre'],
                'unidades_validas': __import__('json').loads(row['unidades_validas_json']),
                'total_compras': row['total_compras']
            })

        logger.info(f"Obtenidos {len(productos)} productos")
        return {"success": True, "productos": productos}

    except sqlite3.Error as e:
        logger.error(f"Error al obtener productos: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def crear_producto(nombre: str, unidades_validas: List[str]) -> Dict:
    """Crea un nuevo producto."""
    if not nombre or not unidades_validas:
        return {"success": False, "error": "El nombre y las unidades válidas son requeridos"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si el producto ya existe
        cursor.execute("SELECT id FROM Productos WHERE nombre = ?", (nombre.strip(),))
        if cursor.fetchone():
            return {"success": False, "error": f"El producto '{nombre}' ya existe"}

        # Insertar nuevo producto
        unidades_json = __import__('json').dumps(unidades_validas)
        cursor.execute(
            "INSERT INTO Productos (nombre, unidades_validas_json) VALUES (?, ?)",
            (nombre.strip(), unidades_json)
        )

        conn.commit()
        producto_id = cursor.lastrowid

        logger.info(f"Producto creado exitosamente: {nombre} (ID: {producto_id})")
        return {
            "success": True,
            "producto_id": producto_id,
            "mensaje": f"Producto '{nombre}' creado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al crear producto: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def actualizar_producto(producto_id: int, nombre: str, unidades_validas: List[str]) -> Dict:
    """Actualiza un producto existente."""
    if not nombre or not unidades_validas:
        return {"success": False, "error": "El nombre y las unidades válidas son requeridos"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si el producto existe
        cursor.execute("SELECT nombre FROM Productos WHERE id = ?", (producto_id,))
        producto_actual = cursor.fetchone()
        if not producto_actual:
            return {"success": False, "error": "Producto no encontrado"}

        # Verificar si el nuevo nombre ya existe (para otro producto)
        cursor.execute("SELECT id FROM Productos WHERE nombre = ? AND id != ?",
                      (nombre.strip(), producto_id))
        if cursor.fetchone():
            return {"success": False, "error": f"Ya existe otro producto con el nombre '{nombre}'"}

        # Actualizar producto
        unidades_json = __import__('json').dumps(unidades_validas)
        cursor.execute(
            "UPDATE Productos SET nombre = ?, unidades_validas_json = ? WHERE id = ?",
            (nombre.strip(), unidades_json, producto_id)
        )

        conn.commit()

        logger.info(f"Producto actualizado: {producto_actual['nombre']} -> {nombre}")
        return {
            "success": True,
            "mensaje": f"Producto '{nombre}' actualizado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al actualizar producto: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def eliminar_producto(producto_id: int) -> Dict:
    """Elimina un producto (verificando que no tenga compras asociadas)."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si el producto existe y obtener su nombre
        cursor.execute("SELECT nombre FROM Productos WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()
        if not producto:
            return {"success": False, "error": "Producto no encontrado"}

        nombre_producto = producto['nombre']

        # Verificar si tiene compras asociadas
        cursor.execute("SELECT COUNT(*) as count FROM Compras WHERE producto_id = ?", (producto_id,))
        count = cursor.fetchone()['count']

        if count > 0:
            return {
                "success": False,
                "error": f"No se puede eliminar '{nombre_producto}' porque tiene {count} compras asociadas"
            }

        # Eliminar el producto
        cursor.execute("DELETE FROM Productos WHERE id = ?", (producto_id,))
        conn.commit()

        logger.info(f"Producto eliminado: {nombre_producto}")
        return {
            "success": True,
            "mensaje": f"Producto '{nombre_producto}' eliminado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al eliminar producto: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# ==================== CRUD DE PROVEEDORES ====================

def obtener_todos_los_proveedores() -> Dict:
    """Obtiene todos los proveedores con sus detalles."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Usar Proveedores_V2 si existe, sino la tabla original
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proveedores_V2'")
        tabla_v2_existe = cursor.fetchone()

        if tabla_v2_existe:
            query = """
            SELECT
                id,
                nombre,
                contacto,
                telefono,
                email,
                direccion,
                cif_nif,
                notas_cliente,
                activo,
                fecha_creacion,
                fecha_modificacion,
                (SELECT COUNT(*) FROM Compras WHERE proveedor_id = p.id) as total_compras
            FROM Proveedores_V2 p
            ORDER BY nombre
            """
        else:
            query = """
            SELECT
                id,
                nombre,
                '' as contacto,
                '' as telefono,
                '' as email,
                '' as direccion,
                '' as cif_nif,
                '' as notas_cliente,
                1 as activo,
                CURRENT_TIMESTAMP as fecha_creacion,
                CURRENT_TIMESTAMP as fecha_modificacion,
                (SELECT COUNT(*) FROM Compras WHERE proveedor_id = p.id) as total_compras
            FROM Proveedores p
            ORDER BY nombre
            """

        cursor.execute(query)
        rows = cursor.fetchall()

        proveedores = []
        for row in rows:
            proveedores.append({
                'id': row['id'],
                'nombre': row['nombre'],
                'contacto': row['contacto'] or '',
                'telefono': row['telefono'] or '',
                'email': row['email'] or '',
                'direccion': row['direccion'] or '',
                'cif_nif': row['cif_nif'] or '',
                'notas_cliente': row['notas_cliente'] or '',
                'activo': bool(row['activo']),
                'fecha_creacion': row['fecha_creacion'],
                'fecha_modificacion': row['fecha_modificacion'],
                'total_compras': row['total_compras']
            })

        logger.info(f"Obtenidos {len(proveedores)} proveedores")
        return {"success": True, "proveedores": proveedores}

    except sqlite3.Error as e:
        logger.error(f"Error al obtener proveedores: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def crear_proveedor(datos: Dict) -> Dict:
    """Crea un nuevo proveedor."""
    campos_requeridos = ['nombre']
    for campo in campos_requeridos:
        if not datos.get(campo) or not datos[campo].strip():
            return {"success": False, "error": f"El campo '{campo}' es requerido"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la tabla V2 existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proveedores_V2'")
        tabla_v2_existe = cursor.fetchone()

        if tabla_v2_existe:
            # Verificar si el proveedor ya existe
            cursor.execute("SELECT id FROM Proveedores_V2 WHERE nombre = ?", (datos['nombre'].strip(),))
            if cursor.fetchone():
                return {"success": False, "error": f"El proveedor '{datos['nombre']}' ya existe"}

            # Insertar nuevo proveedor
            query = """
            INSERT INTO Proveedores_V2 (nombre, contacto, telefono, email, direccion, cif_nif, notas_cliente)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                datos['nombre'].strip(),
                datos.get('contacto', '').strip(),
                datos.get('telefono', '').strip(),
                datos.get('email', '').strip(),
                datos.get('direccion', '').strip(),
                datos.get('cif_nif', '').strip(),
                datos.get('notas_cliente', '').strip()
            )
        else:
            # Si no existe la tabla V2, usar la original
            cursor.execute("SELECT id FROM Proveedores WHERE nombre = ?", (datos['nombre'].strip(),))
            if cursor.fetchone():
                return {"success": False, "error": f"El proveedor '{datos['nombre']}' ya existe"}

            query = "INSERT INTO Proveedores (nombre) VALUES (?)"
            params = (datos['nombre'].strip(),)

        cursor.execute(query, params)
        conn.commit()
        proveedor_id = cursor.lastrowid

        logger.info(f"Proveedor creado exitosamente: {datos['nombre']} (ID: {proveedor_id})")
        return {
            "success": True,
            "proveedor_id": proveedor_id,
            "mensaje": f"Proveedor '{datos['nombre']}' creado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al crear proveedor: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def actualizar_proveedor(proveedor_id: int, datos: Dict) -> Dict:
    """Actualiza un proveedor existente."""
    if not datos.get('nombre') or not datos['nombre'].strip():
        return {"success": False, "error": "El nombre del proveedor es requerido"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la tabla V2 existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proveedores_V2'")
        tabla_v2_existe = cursor.fetchone()

        if tabla_v2_existe:
            # Verificar si el proveedor existe
            cursor.execute("SELECT nombre FROM Proveedores_V2 WHERE id = ?", (proveedor_id,))
            proveedor_actual = cursor.fetchone()
            if not proveedor_actual:
                return {"success": False, "error": "Proveedor no encontrado"}

            # Verificar si el nuevo nombre ya existe (para otro proveedor)
            cursor.execute("SELECT id FROM Proveedores_V2 WHERE nombre = ? AND id != ?",
                          (datos['nombre'].strip(), proveedor_id))
            if cursor.fetchone():
                return {"success": False, "error": f"Ya existe otro proveedor con el nombre '{datos['nombre']}'"}

            # Actualizar proveedor
            query = """
            UPDATE Proveedores_V2
            SET nombre = ?, contacto = ?, telefono = ?, email = ?, direccion = ?,
                cif_nif = ?, notas_cliente = ?, fecha_modificacion = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            params = (
                datos['nombre'].strip(),
                datos.get('contacto', '').strip(),
                datos.get('telefono', '').strip(),
                datos.get('email', '').strip(),
                datos.get('direccion', '').strip(),
                datos.get('cif_nif', '').strip(),
                datos.get('notas_cliente', '').strip(),
                proveedor_id
            )
        else:
            # Si no existe V2, no se puede actualizar
            return {"success": False, "error": "La versión de base de datos no soporta actualización de proveedores"}

        cursor.execute(query, params)
        conn.commit()

        logger.info(f"Proveedor actualizado: {proveedor_actual['nombre']} -> {datos['nombre']}")
        return {
            "success": True,
            "mensaje": f"Proveedor '{datos['nombre']}' actualizado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al actualizar proveedor: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def eliminar_proveedor(proveedor_id: int) -> Dict:
    """Elimina un proveedor (verificando que no tenga compras asociadas)."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la tabla V2 existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proveedores_V2'")
        tabla_v2_existe = cursor.fetchone()

        if tabla_v2_existe:
            # Verificar si el proveedor existe y obtener su nombre
            cursor.execute("SELECT nombre FROM Proveedores_V2 WHERE id = ?", (proveedor_id,))
            proveedor = cursor.fetchone()
            if not proveedor:
                return {"success": False, "error": "Proveedor no encontrado"}

            nombre_proveedor = proveedor['nombre']

            # Verificar si tiene compras asociadas
            cursor.execute("SELECT COUNT(*) as count FROM Compras WHERE proveedor_id = ?", (proveedor_id,))
            count = cursor.fetchone()['count']

            if count > 0:
                return {
                    "success": False,
                    "error": f"No se puede eliminar '{nombre_proveedor}' porque tiene {count} compras asociadas"
                }

            # Eliminar el proveedor
            cursor.execute("DELETE FROM Proveedores_V2 WHERE id = ?", (proveedor_id,))
        else:
            # Si no existe V2, usar la tabla original
            cursor.execute("SELECT nombre FROM Proveedores WHERE id = ?", (proveedor_id,))
            proveedor = cursor.fetchone()
            if not proveedor:
                return {"success": False, "error": "Proveedor no encontrado"}

            nombre_proveedor = proveedor[0]

            # Verificar si tiene compras asociadas
            cursor.execute("SELECT COUNT(*) as count FROM Compras WHERE proveedor_id = ?", (proveedor_id,))
            count = cursor.fetchone()[0]

            if count > 0:
                return {
                    "success": False,
                    "error": f"No se puede eliminar '{nombre_proveedor}' porque tiene {count} compras asociadas"
                }

            # Eliminar el proveedor
            cursor.execute("DELETE FROM Proveedores WHERE id = ?", (proveedor_id,))

        conn.commit()

        logger.info(f"Proveedor eliminado: {nombre_proveedor}")
        return {
            "success": True,
            "mensaje": f"Proveedor '{nombre_proveedor}' eliminado exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al eliminar proveedor: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def obtener_proveedor_por_id(proveedor_id: int) -> Dict:
    """Obtiene un proveedor por su ID."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la tabla V2 existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Proveedores_V2'")
        tabla_v2_existe = cursor.fetchone()

        if tabla_v2_existe:
            query = """
            SELECT id, nombre, contacto, telefono, email, direccion, cif_nif, notas_cliente, activo
            FROM Proveedores_V2
            WHERE id = ?
            """
        else:
            query = "SELECT id, nombre FROM Proveedores WHERE id = ?"

        cursor.execute(query, (proveedor_id,))
        row = cursor.fetchone()

        if not row:
            return {"success": False, "error": "Proveedor no encontrado"}

        if tabla_v2_existe:
            proveedor = {
                'id': row['id'],
                'nombre': row['nombre'],
                'contacto': row['contacto'] or '',
                'telefono': row['telefono'] or '',
                'email': row['email'] or '',
                'direccion': row['direccion'] or '',
                'cif_nif': row['cif_nif'] or '',
                'notas_cliente': row['notas_cliente'] or '',
                'activo': bool(row['activo'])
            }
        else:
            proveedor = {
                'id': row[0],
                'nombre': row[1],
                'contacto': '',
                'telefono': '',
                'email': '',
                'direccion': '',
                'cif_nif': '',
                'notas_cliente': '',
                'activo': True
            }

        return {"success": True, "proveedor": proveedor}

    except sqlite3.Error as e:
        logger.error(f"Error al obtener proveedor: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# ==================== CRUD DE NOTAS ====================

def obtener_todas_las_notas(filtros: Dict = None) -> Dict:
    """Obtiene todas las notas con filtros opcionales."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        query = """
        SELECT
            id,
            titulo,
            contenido,
            categoria,
            prioridad,
            estado,
            fecha_creacion,
            fecha_modificacion,
            usuario_creador,
            etiquetas,
            producto_relacionado,
            proveedor_relacionado,
            compra_relacionada
        FROM Notas
        WHERE 1=1
        """
        params = []

        # Aplicar filtros si existen
        if filtros:
            if filtros.get('categoria'):
                query += " AND categoria = ?"
                params.append(filtros['categoria'])

            if filtros.get('prioridad'):
                query += " AND prioridad = ?"
                params.append(filtros['prioridad'])

            if filtros.get('estado'):
                query += " AND estado = ?"
                params.append(filtros['estado'])

            if filtros.get('busqueda'):
                query += " AND (titulo LIKE ? OR contenido LIKE ?)"
                busqueda = f"%{filtros['busqueda']}%"
                params.extend([busqueda, busqueda])

        query += " ORDER BY fecha_modificacion DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        notas = []
        for row in rows:
            notas.append({
                'id': row['id'],
                'titulo': row['titulo'],
                'contenido': row['contenido'],
                'categoria': row['categoria'],
                'prioridad': row['prioridad'],
                'estado': row['estado'],
                'fecha_creacion': row['fecha_creacion'],
                'fecha_modificacion': row['fecha_modificacion'],
                'usuario_creador': row['usuario_creador'],
                'etiquetas': json.loads(row['etiquetas']) if row['etiquetas'] else [],
                'producto_relacionado': row['producto_relacionado'],
                'proveedor_relacionado': row['proveedor_relacionado'],
                'compra_relacionada': row['compra_relacionada']
            })

        logger.info(f"Obtenidas {len(notas)} notas")
        return {"success": True, "notas": notas}

    except sqlite3.Error as e:
        logger.error(f"Error al obtener notas: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def crear_nota(datos: Dict) -> Dict:
    """Crea una nueva nota."""
    campos_requeridos = ['titulo', 'contenido', 'categoria']
    for campo in campos_requeridos:
        if not datos.get(campo) or not datos[campo].strip():
            return {"success": False, "error": f"El campo '{campo}' es requerido"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Preparar etiquetas como JSON
        etiquetas = json.dumps(datos.get('etiquetas', []))

        query = """
        INSERT INTO Notas (titulo, contenido, categoria, prioridad, estado,
                           etiquetas, producto_relacionado, proveedor_relacionado, compra_relacionada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            datos['titulo'].strip(),
            datos['contenido'].strip(),
            datos['categoria'].strip(),
            datos.get('prioridad', 'media'),
            datos.get('estado', 'activa'),
            etiquetas,
            datos.get('producto_relacionado'),
            datos.get('proveedor_relacionado'),
            datos.get('compra_relacionada')
        )

        cursor.execute(query, params)
        conn.commit()
        nota_id = cursor.lastrowid

        logger.info(f"Nota creada exitosamente: {datos['titulo']} (ID: {nota_id})")
        return {
            "success": True,
            "nota_id": nota_id,
            "mensaje": f"Nota '{datos['titulo']}' creada exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al crear nota: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def actualizar_nota(nota_id: int, datos: Dict) -> Dict:
    """Actualiza una nota existente."""
    campos_requeridos = ['titulo', 'contenido', 'categoria']
    for campo in campos_requeridos:
        if not datos.get(campo) or not datos[campo].strip():
            return {"success": False, "error": f"El campo '{campo}' es requerido"}

    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la nota existe
        cursor.execute("SELECT titulo FROM Notas WHERE id = ?", (nota_id,))
        nota_actual = cursor.fetchone()
        if not nota_actual:
            return {"success": False, "error": "Nota no encontrada"}

        # Preparar etiquetas como JSON
        etiquetas = json.dumps(datos.get('etiquetas', []))

        query = """
        UPDATE Notas
        SET titulo = ?, contenido = ?, categoria = ?, prioridad = ?, estado = ?,
            etiquetas = ?, fecha_modificacion = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        params = (
            datos['titulo'].strip(),
            datos['contenido'].strip(),
            datos['categoria'].strip(),
            datos.get('prioridad', 'media'),
            datos.get('estado', 'activa'),
            etiquetas,
            nota_id
        )

        cursor.execute(query, params)
        conn.commit()

        logger.info(f"Nota actualizada: {nota_actual['titulo']} -> {datos['titulo']}")
        return {
            "success": True,
            "mensaje": f"Nota '{datos['titulo']}' actualizada exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al actualizar nota: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def eliminar_nota(nota_id: int) -> Dict:
    """Elimina una nota."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        # Verificar si la nota existe y obtener su título
        cursor.execute("SELECT titulo FROM Notas WHERE id = ?", (nota_id,))
        nota = cursor.fetchone()
        if not nota:
            return {"success": False, "error": "Nota no encontrada"}

        nombre_nota = nota['titulo']

        # Eliminar la nota
        cursor.execute("DELETE FROM Notas WHERE id = ?", (nota_id,))
        conn.commit()

        logger.info(f"Nota eliminada: {nombre_nota}")
        return {
            "success": True,
            "mensaje": f"Nota '{nombre_nota}' eliminada exitosamente"
        }

    except sqlite3.Error as e:
        logger.error(f"Error al eliminar nota: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def obtener_nota_por_id(nota_id: int) -> Dict:
    """Obtiene una nota por su ID."""
    conn = connect_db()
    if not conn:
        return {"success": False, "error": "No se pudo conectar a la BD"}

    cursor = conn.cursor()

    try:
        query = """
        SELECT id, titulo, contenido, categoria, prioridad, estado,
               fecha_creacion, fecha_modificacion, usuario_creador, etiquetas,
               producto_relacionado, proveedor_relacionado, compra_relacionada
        FROM Notas
        WHERE id = ?
        """

        cursor.execute(query, (nota_id,))
        row = cursor.fetchone()

        if not row:
            return {"success": False, "error": "Nota no encontrada"}

        nota = {
            'id': row['id'],
            'titulo': row['titulo'],
            'contenido': row['contenido'],
            'categoria': row['categoria'],
            'prioridad': row['prioridad'],
            'estado': row['estado'],
            'fecha_creacion': row['fecha_creacion'],
            'fecha_modificacion': row['fecha_modificacion'],
            'usuario_creador': row['usuario_creador'],
            'etiquetas': json.loads(row['etiquetas']) if row['etiquetas'] else [],
            'producto_relacionado': row['producto_relacionado'],
            'proveedor_relacionado': row['proveedor_relacionado'],
            'compra_relacionada': row['compra_relacionada']
        }

        return {"success": True, "nota": nota}

    except sqlite3.Error as e:
        logger.error(f"Error al obtener nota: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def verificar_conexion() -> bool:
    """Verifica si la base de datos es accesible."""
    conn = connect_db()
    if conn:
        conn.close()
        return True
    return False