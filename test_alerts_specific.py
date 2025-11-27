#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prueba específica del sistema de alertas"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_alertas_sin_logs():
    """Prueba el sistema de alertas sin logs antiguos"""
    print("\n" + "="*60)
    print("PRUEBA ESPECÍFICA: Sistema de Alertas (Sin Logs Antiguos)")
    print("="*60)

    try:
        from src.alerts import generar_alertas

        print("Generando alertas...")
        alertas = generar_alertas()

        print(f"✅ Alertas generadas exitosamente: {len(alertas)} alertas")

        if alertas:
            print("\nPrimeras 3 alertas:")
            for i, alerta in enumerate(alertas[:3], 1):
                print(f"  {i}. [{alerta['prioridad']}] {alerta['titulo']}")
        else:
            print("No se generaron alertas (la BD puede estar vacía o sin datos que generen alertas)")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_alertas_sin_logs()
    sys.exit(0 if success else 1)
