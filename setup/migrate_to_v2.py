# migrate_to_v2.py
# Script de migración para ampliar la base de datos con gestión de proveedores y sistema de notas
# Ejecutar: python migrate_to_v2.py

import sqlite3
import json
import sys
from datetime import datetime

# Configurar codificación para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DB_NAME = '../stock.db'

# Categorías de notas predefinidas
CATEGORIAS_NOTAS = [
    "💡 Ideas de Funcionalidad",
    "🐛 Reporte de Problemas",
    "🎨 Mejoras de Interfaz",
    "📊 Sugerencias de Análisis",
    "📋 Notas de Negocio",
    "🔧 Problemas Técnicos"
]

def migrar_base_datos():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print("Iniciando migracion a version 2.0...")

        # 1. Migrar tabla Proveedores a la version ampliada
        print("Migrando tabla Proveedores...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Proveedores_V2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            contacto TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            cif_nif TEXT,
            notas_cliente TEXT,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Migrar datos existentes de Proveedores a Proveedores_V2
        cursor.execute('''
        INSERT OR IGNORE INTO Proveedores_V2 (id, nombre, fecha_creacion, fecha_modificacion)
        SELECT id, nombre, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM Proveedores
        ''')

        # 2. Crear tabla de Notas para el cliente
        print("Creando tabla de Notas...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            categoria TEXT NOT NULL,
            prioridad TEXT DEFAULT 'media',
            estado TEXT DEFAULT 'activa',
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP,
            usuario_creador TEXT DEFAULT 'cliente',
            etiquetas TEXT,
            producto_relacionado INTEGER,
            proveedor_relacionado INTEGER,
            compra_relacionada INTEGER,
            FOREIGN KEY (producto_relacionado) REFERENCES Productos (id),
            FOREIGN KEY (proveedor_relacionado) REFERENCES Proveedores_V2 (id),
            FOREIGN KEY (compra_relacionada) REFERENCES Compras (id)
        )
        ''')

        # 3. Crear tabla de Etiquetas para las notas
        print("Creando tabla de Etiquetas...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#6B7280'
        )
        ''')

        # 4. Insertar etiquetas predefinidas
        etiquetas_predefinidas = [
            ('mejora', '#10B981'),
            ('bug', '#EF4444'),
            ('urgente', '#F59E0B'),
            ('idea', '#3B82F6'),
            ('interfaz', '#8B5CF6'),
            ('negocio', '#EC4899')
        ]

        cursor.executemany("INSERT OR IGNORE INTO Etiquetas (nombre, color) VALUES (?, ?)", etiquetas_predefinidas)

        # 5. Crear tabla de relacion entre notas y etiquetas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Notas_Etiquetas (
            nota_id INTEGER,
            etiqueta_id INTEGER,
            PRIMARY KEY (nota_id, etiqueta_id),
            FOREIGN KEY (nota_id) REFERENCES Notas (id) ON DELETE CASCADE,
            FOREIGN KEY (etiqueta_id) REFERENCES Etiquetas (id) ON DELETE CASCADE
        )
        ''')

        # 6. Insertar nota de bienvenida
        nota_bienvenida_titulo = "Bienvenido al Sistema de Notas!"
        nota_bienvenida_contenido = '''Usa este sistema para dejar anotaciones sobre como mejorar la aplicacion.

Puedes crear notas sobre:
- Nuevas funcionalidades que necesites
- Problemas o errores que encuentres
- Ideas para mejorar la interfaz
- Sugerencias para analisis de datos
- Notas sobre tu negocio

Todas tus anotaciones me ayudaran a mejorar continuamente la aplicacion para tu bar.

Gracias por tu feedback!'''

        cursor.execute('''
        INSERT OR IGNORE INTO Notas (titulo, contenido, categoria, prioridad, estado, usuario_creador)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            nota_bienvenida_titulo,
            nota_bienvenida_contenido,
            "Ideas de Funcionalidad",
            "media",
            "activa",
            "cliente"
        ))

        # 7. Actualizar configuracion
        print("Actualizando configuracion...")
        configuracion_v2 = [
            ('app_version', '2.0', 'Version actual de la aplicacion'),
            ('proveedores_habilitados', 'true', 'Gestion de proveedores habilitada'),
            ('notas_habilitadas', 'true', 'Sistema de notas habilitado'),
            ('migracion_v2_completada', str(datetime.now()), 'Fecha de migracion a v2.0')
        ]

        cursor.executemany("INSERT OR REPLACE INTO Configuracion (clave, valor, descripcion) VALUES (?, ?, ?)", configuracion_v2)

        # 8. Guardar cambios
        conn.commit()
        print("Migracion completada exitosamente!")

        # 9. Verificar la migracion
        print("\nVerificando datos migrados:")
        cursor.execute("SELECT COUNT(*) FROM Proveedores_V2")
        proveedores_migrados = cursor.fetchone()[0]
        print(f"   Proveedores migrados: {proveedores_migrados}")

        cursor.execute("SELECT COUNT(*) FROM Notas")
        notas_creadas = cursor.fetchone()[0]
        print(f"   Notas creadas: {notas_creadas}")

        cursor.execute("SELECT COUNT(*) FROM Etiquetas")
        etiquetas_creadas = cursor.fetchone()[0]
        print(f"   Etiquetas creadas: {etiquetas_creadas}")

        print(f"\nMigracion a version 2.0 completada con exito!")

    except sqlite3.Error as e:
        print(f"Error durante la migracion: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Conexion a base de datos cerrada.")

def verificar_migracion():
    """Verifica si la migración ya fue realizada"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT valor FROM Configuracion WHERE clave = 'migracion_v2_completada'")
        resultado = cursor.fetchone()

        conn.close()

        return resultado is not None
    except:
        return False

if __name__ == "__main__":
    if verificar_migracion():
        print("La migracion a v2.0 ya fue realizada anteriormente.")
        respuesta = input("Desea volver a ejecutar la migracion? (s/N): ").lower()
        if respuesta != 's':
            print("Migracion cancelada.")
            exit(0)

    print("Iniciando migracion de la base de datos a version 2.0...")
    print("Asegurate de hacer un backup de tu base de datos actual antes de continuar.")
    respuesta = input("Continuar con la migracion? (s/N): ").lower()

    if respuesta == 's':
        migrar_base_datos()
    else:
        print("Migracion cancelada.")