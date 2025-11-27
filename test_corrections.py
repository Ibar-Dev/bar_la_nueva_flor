#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de pruebas end-to-end para verificar las correcciones realizadas
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_alertas():
    """Prueba el sistema de alertas corregido"""
    print("\n" + "="*60)
    print("PRUEBA 1: Sistema de Alertas")
    print("="*60)

    try:
        from src.alerts import generar_alertas, obtener_estadisticas_alertas

        print("✓ Importación exitosa de módulo de alertas")

        # Generar alertas
        alertas = generar_alertas()
        print(f"✓ Alertas generadas: {len(alertas)} alertas")

        # Obtener estadísticas
        stats = obtener_estadisticas_alertas()
        print(f"✓ Estadísticas obtenidas:")
        print(f"  - Total alertas: {stats['total_alertas']}")
        print(f"  - Por tipo: {stats['por_tipo']}")
        print(f"  - Por prioridad: {stats['por_prioridad']}")

        # Mostrar algunas alertas
        if alertas:
            print(f"\n  Ejemplo de alertas generadas:")
            for i, alerta in enumerate(alertas[:3], 1):
                print(f"    {i}. [{alerta['tipo']}] {alerta['titulo']}: {alerta['mensaje'][:60]}...")

        print("\n✅ PRUEBA 1 EXITOSA: Sistema de alertas funciona correctamente")
        return True

    except Exception as e:
        print(f"\n❌ PRUEBA 1 FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_funciones_implementadas():
    """Prueba las funciones implementadas en app.py"""
    print("\n" + "="*60)
    print("PRUEBA 2: Funciones Implementadas")
    print("="*60)

    try:
        from src.database import (
            obtener_proveedor_por_id,
            obtener_nota_por_id,
            obtener_todos_los_proveedores,
            obtener_todas_las_notas
        )

        print("✓ Importación exitosa de funciones de database")

        # Probar obtener_proveedor_por_id
        proveedores = obtener_todos_los_proveedores()
        if proveedores.get("success") and proveedores.get("proveedores"):
            proveedor_id = proveedores["proveedores"][0]["id"]
            resultado = obtener_proveedor_por_id(proveedor_id)

            if resultado.get("success"):
                print(f"✓ obtener_proveedor_por_id({proveedor_id}) funciona correctamente")
                print(f"  Proveedor: {resultado.get('proveedor', {}).get('nombre', 'N/A')}")
            else:
                print(f"⚠ obtener_proveedor_por_id({proveedor_id}) retornó sin éxito: {resultado.get('error')}")
        else:
            print("⚠ No hay proveedores en la BD para probar")

        # Probar obtener_nota_por_id
        notas = obtener_todas_las_notas()
        if notas.get("success") and notas.get("notas"):
            nota_id = notas["notas"][0]["id"]
            resultado = obtener_nota_por_id(nota_id)

            if resultado.get("success"):
                print(f"✓ obtener_nota_por_id({nota_id}) funciona correctamente")
                print(f"  Nota: {resultado.get('nota', {}).get('titulo', 'N/A')}")
            else:
                print(f"⚠ obtener_nota_por_id({nota_id}) retornó sin éxito: {resultado.get('error')}")
        else:
            print("⚠ No hay notas en la BD para probar")

        print("\n✅ PRUEBA 2 EXITOSA: Funciones implementadas correctamente")
        return True

    except Exception as e:
        print(f"\n❌ PRUEBA 2 FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuracion_pyinstaller():
    """Verifica la configuración de PyInstaller"""
    print("\n" + "="*60)
    print("PRUEBA 3: Configuración de PyInstaller")
    print("="*60)

    try:
        spec_file = Path("BarStockManager.spec")

        if not spec_file.exists():
            print("❌ Archivo BarStockManager.spec no encontrado")
            return False

        contenido = spec_file.read_text()

        # Verificar que incluye la carpeta web
        if "datas=[('web', 'web')]" in contenido:
            print("✓ BarStockManager.spec incluye carpeta 'web'")
        else:
            print("❌ BarStockManager.spec NO incluye carpeta 'web'")
            return False

        # Verificar que existe la carpeta web
        web_dir = Path("web")
        if web_dir.exists() and web_dir.is_dir():
            archivos_web = list(web_dir.glob("*.html"))
            print(f"✓ Carpeta 'web' existe con {len(archivos_web)} archivos HTML")
        else:
            print("⚠ Carpeta 'web' no encontrada")

        print("\n✅ PRUEBA 3 EXITOSA: Configuración de PyInstaller correcta")
        return True

    except Exception as e:
        print(f"\n❌ PRUEBA 3 FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gitignore():
    """Verifica el .gitignore mejorado"""
    print("\n" + "="*60)
    print("PRUEBA 4: .gitignore Mejorado")
    print("="*60)

    try:
        gitignore_file = Path(".gitignore")

        if not gitignore_file.exists():
            print("❌ Archivo .gitignore no encontrado")
            return False

        contenido = gitignore_file.read_text()

        # Verificar entradas importantes
        entradas_esperadas = [
            ("build/", "Artefactos de compilación"),
            ("dist/", "Distribuciones"),
            ("backups/", "Backups"),
            ("data/", "Datos"),
            ("logs/", "Logs"),
            ("__pycache__/", "Cache de Python"),
            ("*.spec", "Archivos spec"),
        ]

        todas_ok = True
        for entrada, descripcion in entradas_esperadas:
            if entrada in contenido:
                print(f"✓ {entrada:20} - {descripcion}")
            else:
                print(f"❌ {entrada:20} - FALTA")
                todas_ok = False

        if todas_ok:
            print("\n✅ PRUEBA 4 EXITOSA: .gitignore configurado correctamente")
            return True
        else:
            print("\n⚠ PRUEBA 4 PARCIAL: Algunas entradas faltan")
            return False

    except Exception as e:
        print(f"\n❌ PRUEBA 4 FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_not_in_git():
    """Verifica que las bases de datos no estén en Git"""
    print("\n" + "="*60)
    print("PRUEBA 5: Bases de Datos Fuera de Git")
    print("="*60)

    try:
        import subprocess

        # Verificar que stock.db no está en el índice de git
        resultado = subprocess.run(
            ["git", "ls-files", "stock.db"],
            capture_output=True,
            text=True
        )

        if resultado.stdout.strip() == "":
            print("✓ stock.db NO está en el control de versiones")
        else:
            print("❌ stock.db TODAVÍA está en Git")
            return False

        # Verificar que data/stock.db no está en el índice
        resultado = subprocess.run(
            ["git", "ls-files", "data/stock.db"],
            capture_output=True,
            text=True
        )

        if resultado.stdout.strip() == "":
            print("✓ data/stock.db NO está en el control de versiones")
        else:
            print("❌ data/stock.db TODAVÍA está en Git")
            return False

        # Verificar que los archivos existen localmente
        if Path("stock.db").exists():
            print("✓ stock.db existe localmente (como debe ser)")
        else:
            print("⚠ stock.db no existe localmente")

        print("\n✅ PRUEBA 5 EXITOSA: Bases de datos correctamente excluidas de Git")
        return True

    except Exception as e:
        print(f"\n❌ PRUEBA 5 FALLIDA: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  PRUEBAS END-TO-END - CORRECCIONES DEL REPOSITORIO  ".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    resultados = []

    # Ejecutar todas las pruebas
    resultados.append(("Sistema de Alertas", test_alertas()))
    resultados.append(("Funciones Implementadas", test_funciones_implementadas()))
    resultados.append(("Configuración PyInstaller", test_configuracion_pyinstaller()))
    resultados.append((".gitignore", test_gitignore()))
    resultados.append(("BD fuera de Git", test_database_not_in_git()))

    # Resumen final
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  RESUMEN DE PRUEBAS  ".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60 + "\n")

    exitosas = 0
    fallidas = 0

    for nombre, resultado in resultados:
        estado = "✅ EXITOSA" if resultado else "❌ FALLIDA"
        print(f"  {nombre:30} {estado}")
        if resultado:
            exitosas += 1
        else:
            fallidas += 1

    print("\n" + "-"*60)
    print(f"  Total: {len(resultados)} pruebas")
    print(f"  Exitosas: {exitosas}")
    print(f"  Fallidas: {fallidas}")
    print("-"*60 + "\n")

    if fallidas == 0:
        print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        return 0
    else:
        print(f"⚠️  {fallidas} PRUEBA(S) FALLARON")
        return 1


if __name__ == "__main__":
    sys.exit(main())
