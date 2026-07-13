"""
🔍 PRUEBA: Verificar extracción de Google Docs exportados
"""

import io
import sys
sys.path.insert(0, '.')

# Intentar importar la función de extracción
try:
    from main import extraer_texto_de_docx, descargar_adjunto_drive, obtener_credenciales
    print("✅ Importadas funciones de main.py")
except Exception as e:
    print(f"❌ Error importando: {e}")
    sys.exit(1)

# Simular descarga de un Google Doc pequeño (Bruno's document)
print("\n" + "="*70)
print("🧪 TESTE: Extracción de Google Docs")
print("="*70)

print("""
Este script simularía:
1. Descargar Google Doc de Bruno desde Drive
2. Exportarlo a DOCX
3. Extraer texto del DOCX

Para hacer una prueba real, necesitaríamos:
- El file_id del documento de Bruno
- Credenciales autenticadas

Alternativa: Ver si en Correcciones_Classroom ya existe el PDF descargado
""")

# Buscar si existe el archivo descargado de Bruno
import os
import glob

print("\n🔍 Buscando archivos de Bruno en Correcciones_Classroom...")
for root, dirs, files in os.walk("Correcciones_Classroom"):
    for file in files:
        if "Bruno" in file or "bruno" in file.lower():
            ruta = os.path.join(root, file)
            tam = os.path.getsize(ruta)
            print(f"  ✅ {ruta} ({tam} bytes)")
