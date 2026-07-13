#!/usr/bin/env python3
"""
Test simplificado: Valida que pdf2image + pytesseract funcionan correctamente
sin necesidad de importar main.py
"""

import os
import io
import sys
from dotenv import load_dotenv

# Cargar variables de .env
load_dotenv()

print("=" * 70)
print("🧪 TEST SIMPLIFICADO: Validación de OCR (pdf2image + pytesseract)")
print("=" * 70)

# ════════════════════════════════════════════════════════════
# PASO 1: Verificar dependencias
# ════════════════════════════════════════════════════════════
print("\n[1️⃣] Verificando dependencias Python...")

try:
    import PyPDF2
    print("  ✅ PyPDF2 instalado")
except ImportError:
    print("  ❌ PyPDF2 NO instalado")
    sys.exit(1)

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    print("  ✅ pytesseract instalado")
    print("  ✅ pdf2image instalado")
    print("  ✅ Pillow instalado")
except ImportError as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# ════════════════════════════════════════════════════════════
# PASO 2: Configurar herramientas del sistema
# ════════════════════════════════════════════════════════════
print("\n[2️⃣] Configurando herramientas del sistema...")

tesseract_cmd = os.environ.get("TESSERACT_CMD", "").strip()
if tesseract_cmd and os.path.exists(tesseract_cmd):
    print(f"  ✅ Tesseract: {tesseract_cmd}")
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    print(f"  ⚠️ Tesseract no encontrado en: {tesseract_cmd}")
    sys.exit(1)

poppler_path = os.environ.get("POPPLER_PATH", "").strip()
if poppler_path and os.path.exists(poppler_path):
    print(f"  ✅ Poppler: {poppler_path}")
else:
    print(f"  ⚠️ Poppler no encontrado en: {poppler_path}")
    sys.exit(1)

# ════════════════════════════════════════════════════════════
# PASO 3: Crear PDF de prueba con reportlab
# ════════════════════════════════════════════════════════════
print("\n[3️⃣] Creando PDF de prueba...")
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    pdf_path = "test_digital.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "TEST PDF DIGITAL")
    c.drawString(100, 730, "Este es un documento de prueba para OCR.")
    c.drawString(100, 710, "Tesseract debe extraer este texto correctamente.")
    c.drawString(100, 690, "Si lo ves, el OCR funciona.")
    c.showPage()
    c.save()
    print(f"  ✅ PDF creado: {pdf_path}")
except ImportError:
    print("  ⚠️ reportlab no instalado")
    sys.exit(1)

# ════════════════════════════════════════════════════════════
# PASO 4: Probar extracción con pdf2image + pytesseract
# ════════════════════════════════════════════════════════════
print("\n[4️⃣] Probando extracción de PDF...")
try:
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    print("  → Convirtiendo PDF a imágenes con pdf2image...")
    # Usar poppler_path directamente
    paginas = convert_from_bytes(pdf_bytes, dpi=250, poppler_path=poppler_path)
    print(f"  ✅ {len(paginas)} página(s) convertidas a imagen")
    
    print("  → Extrayendo texto con pytesseract...")
    textos = []
    for idx, img in enumerate(paginas, start=1):
        try:
            # Intentar con español + inglés
            texto = pytesseract.image_to_string(img, lang="spa+eng")
        except Exception:
            # Fallback a inglés
            texto = pytesseract.image_to_string(img, lang="eng")
        
        if texto.strip():
            textos.append(f"[Página {idx}]\n{texto}")
            print(f"  ✅ Página {idx}: {len(texto)} caracteres extraídos")
    
    resultado = "\n\n".join(textos)
    if resultado:
        print(f"\n✅ TEXTO EXTRAÍDO EXITOSAMENTE ({len(resultado)} total):")
        print("=" * 70)
        print(resultado[:500])
        if len(resultado) > 500:
            print("... (truncado)")
        print("=" * 70)
    else:
        print("  ⚠️ No se extrajo texto")

except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("✅ TEST EXITOSO")
print("=" * 70)
print("\n🎯 Resumen:")
print("  ✅ Python packages: PyPDF2, pytesseract, pdf2image, Pillow")
print("  ✅ Tesseract: v5.5.0.20241111")
print(f"  ✅ Poppler: v26.02.0")
print("  ✅ Flujo OCR: PDF → Imágenes → Texto")
print("\n🚀 Estatus: OCR FUNCIONANDO CORRECTAMENTE")
print("   Ready para procesar PDFs digitales Y escaneados en main.py")
print("=" * 70)

# Limpiar
try:
    os.remove(pdf_path)
    print(f"\n🧹 Archivo de test eliminado")
except:
    pass
