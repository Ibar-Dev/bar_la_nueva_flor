#!/usr/bin/env python3
"""
Script de validación final para el Gestor de Stock para Bar
Valida todas las funcionalidades principales de la Versión 1.1.0
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

def test_modulos_core():
    """Test de módulos principales"""
    print("🔍 Test 1: Módulos Core")
    try:
        from src.database import get_datos_iniciales, guardar_compra, verificar_conexion
        from src.analytics import analizar_volumenes_periodo, comparar_proveedores
        from src.validators import validar_compra
        from src.backup import backup_database
        print("   ✅ Todos los módulos importados correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error importando módulos: {e}")
        return False

def test_conexion_base_datos():
    """Test de conexión a base de datos"""
    print("🔍 Test 2: Conexión Base de Datos")
    try:
        from src.database import verificar_conexion, get_datos_iniciales

        if not verificar_conexion():
            print("   ❌ No se puede conectar a la base de datos")
            return False

        datos = get_datos_iniciales()
        if 'productos' not in datos or 'proveedores' not in datos:
            print("   ❌ Estructura de datos incorrecta")
            return False

        print(f"   ✅ Conexión OK - {len(datos['productos'])} productos, {len(datos['proveedores'])} proveedores")
        return True
    except Exception as e:
        print(f"   ❌ Error en conexión: {e}")
        return False

def test_validacion_datos():
    """Test de sistema de validación"""
    print("🔍 Test 3: Sistema de Validación")
    try:
        from src.validators import validar_compra

        # Test válido
        datos_validos = {
            'producto': 'Pollo',
            'cantidad': 2.5,
            'unidad': 'kg',
            'precio': 12.50,
            'fecha_compra': '2025-11-19'
        }
        es_valido, mensaje = validar_compra(datos_validos)
        if not es_valido:
            print(f"   ❌ Validación falló para datos válidos: {mensaje}")
            return False

        # Test inválido
        datos_invalidos = {
            'producto': '',
            'cantidad': -1,
            'precio': 'invalido',
            'fecha_compra': 'fecha-invalida'
        }
        es_valido, mensaje = validar_compra(datos_invalidos)
        if es_valido:
            print("   ❌ Validación pasó para datos inválidos")
            return False

        print("   ✅ Sistema de validación funcionando correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error en validación: {e}")
        return False

def test_guardar_compra():
    """Test de guardado de compras"""
    print("🔍 Test 4: Guardado de Compras")
    try:
        from src.database import guardar_compra

        compra_test = {
            'producto': 'Pollo',
            'proveedor': 'Distribuidora Central',
            'cantidad': 2.5,
            'unidad': 'kg',
            'precio': 12.50,
            'fecha_compra': '2025-11-19',
            'descuento': 'Test Final'
        }

        resultado = guardar_compra(compra_test)
        if not resultado.get('success'):
            print(f"   ❌ Error guardando compra: {resultado.get('error')}")
            return False

        print("   ✅ Compra guardada correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error guardando compra: {e}")
        return False

def test_analisis_volumenes():
    """Test de análisis de volúmenes"""
    print("🔍 Test 5: Análisis de Volúmenes")
    try:
        from src.analytics import analizar_volumenes_periodo

        # Análisis último mes
        fin = datetime.now().strftime('%Y-%m-%d')
        inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        resultado = analizar_volumenes_periodo(inicio, fin)

        if not isinstance(resultado, list):
            print("   ❌ Análisis no retorna lista")
            return False

        print(f"   ✅ Análisis completado - {len(resultado)} productos analizados")
        return True
    except Exception as e:
        print(f"   ❌ Error en análisis: {e}")
        return False

def test_comparador_proveedores():
    """Test de comparador de proveedores"""
    print("🔍 Test 6: Comparador de Proveedores")
    try:
        from src.analytics import comparar_proveedores

        resultado = comparar_proveedores('Pollo')

        if not isinstance(resultado, list):
            print("   ❌ Comparador no retorna lista")
            return False

        print(f"   ✅ Comparador funcionando - {len(resultado)} proveedores para Pollo")
        return True
    except Exception as e:
        print(f"   ❌ Error en comparador: {e}")
        return False

def test_sistema_backups():
    """Test de sistema de backups"""
    print("🔍 Test 7: Sistema de Backups")
    try:
        from src.backup import backup_database

        backup_path = backup_database(comprimir=True)

        if not backup_path or not backup_path.exists():
            print("   ❌ No se pudo crear backup")
            return False

        # Limpiar backup de prueba
        backup_path.unlink()

        print("   ✅ Sistema de backups funcionando")
        return True
    except Exception as e:
        print(f"   ❌ Error en backups: {e}")
        return False

def test_configuracion():
    """Test de sistema de configuración"""
    print("🔍 Test 8: Sistema de Configuración")
    try:
        from src.alerts import get_config, set_config

        # Test set/get
        set_config('test_final', 'valor_test', 'Test de validación final')
        valor = get_config('test_final')

        if valor != 'valor_test':
            print("   ❌ Sistema de configuración no funciona")
            return False

        print("   ✅ Sistema de configuración funcionando")
        return True
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🚀 VALIDACIÓN FINAL - GESTOR DE STOCK PARA BAR v1.1.0")
    print("=" * 60)

    tests = [
        test_modulos_core,
        test_conexion_base_datos,
        test_validacion_datos,
        test_guardar_compra,
        test_analisis_volumenes,
        test_comparador_proveedores,
        test_sistema_backups,
        test_configuracion
    ]

    aprobados = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                aprobados += 1
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")

    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {aprobados}/{total} tests aprobados")

    if aprobados == total:
        print("🎉 ¡TODOS LOS TESTS APROBADOS! Sistema listo para producción.")
        return True
    else:
        print(f"⚠️  {total - aprobados} tests fallaron. Revisar errores.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)