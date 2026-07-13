"""
SCRIPT DE PRUEBA - Verificar que todo funciona sin input interactivo
"""

import os
import sys

print("="*80)
print(" VERIFICACIÓN DEL SISTEMA DE CORRECCIÓN MASIVA")
print("="*80)

# Verificar que los archivos existen
archivos_requeridos = [
    "corrector_masivo_integrado.py",
    "aux_correccion_masiva.py",
    "main.py"
]

print("\n[1/3] Verificando archivos...")
for archivo in archivos_requeridos:
    if os.path.exists(archivo):
        print(f"  ✓ {archivo}")
    else:
        print(f"  ❌ {archivo} - NO ENCONTRADO")
        sys.exit(1)

# Verificar que las importaciones funcionan
print("\n[2/3] Verificando importaciones...")
try:
    from aux_correccion_masiva import iniciar_correccion_masiva_completa
    print("  ✓ aux_correccion_masiva")
except ImportError as e:
    print(f"  ❌ Error importando aux_correccion_masiva: {e}")
    sys.exit(1)

try:
    from corrector_masivo_integrado import CorrectorMasivoIntegrado
    print("  ✓ corrector_masivo_integrado")
except ImportError as e:
    print(f"  ❌ Error importando corrector_masivo_integrado: {e}")
    sys.exit(1)

# Verificar estructura de carpetas
print("\n[3/3] Verificando estructura de carpetas...")
if os.path.exists("Correcciones_Classroom"):
    carpetas = os.listdir("Correcciones_Classroom")
    print(f"  ✓ Carpeta Correcciones_Classroom existe")
    print(f"    → {len(carpetas)} carpetas detectadas: {', '.join(carpetas[:3])}{'...' if len(carpetas) > 3 else ''}")
else:
    print(f"  ⚠️ Carpeta Correcciones_Classroom no existe (crear con create_estructura_demo.py)")

print("\n" + "="*80)
print(" ✅ VERIFICACIÓN COMPLETADA - SISTEMA LISTO")
print("="*80)
print("\nPróximos pasos:")
print("1. Ejecuta: python main.py")
print("2. Selecciona: [4] Corrección Masiva")
print("\nO directamente:")
print("python corrector_masivo_integrado.py")
print("="*80 + "\n")
