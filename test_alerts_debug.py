#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prueba de debug para sistema de alertas"""

import sys
import sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import connect_db

def test_each_alert_function():
    """Prueba cada función de alertas por separado"""
    print("\n" + "="*60)
    print("DEBUG: Probando cada función de alertas por separado")
    print("="*60 + "\n")

    try:
        from src.alerts import (
            _generar_alertas_stock,
            _generar_alertas_inactividad,
            _generar_alertas_precios,
            _generar_alertas_proveedores
        )

        conn = connect_db()
        if not conn:
            print("❌ No se puede conectar a la BD")
            return False

        cursor = conn.cursor()

        # Prueba 1: Alertas de stock
        try:
            print("1. Probando _generar_alertas_stock...")
            alertas = _generar_alertas_stock(cursor)
            print(f"   ✅ OK: {len(alertas)} alertas de stock")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

        # Prueba 2: Alertas de inactividad
        try:
            print("2. Probando _generar_alertas_inactividad...")
            alertas = _generar_alertas_inactividad(cursor)
            print(f"   ✅ OK: {len(alertas)} alertas de inactividad")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

        # Prueba 3: Alertas de precios
        try:
            print("3. Probando _generar_alertas_precios...")
            alertas = _generar_alertas_precios(cursor)
            print(f"   ✅ OK: {len(alertas)} alertas de precios")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            print(f"      Tipo: {type(e)}")

        # Prueba 4: Alertas de proveedores
        try:
            print("4. Probando _generar_alertas_proveedores...")
            alertas = _generar_alertas_proveedores(cursor)
            print(f"   ✅ OK: {len(alertas)} alertas de proveedores")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            print(f"      Tipo: {type(e)}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_each_alert_function()
