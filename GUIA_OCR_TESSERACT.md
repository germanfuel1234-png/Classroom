# 📋 Guía de Configuración: OCR para PDFs Escaneados

## Problema Resuelto
Ahora el sistema extrae texto de:
- ✅ PDFs digitales (con capa de texto) — extracción rápida
- ✅ PDFs escaneados / fotos convertidas a PDF — OCR local con Tesseract
- ✅ Imágenes directas — OCR local

**Ahorro de recursos:** Si el PDF es digital, no activa OCR (ahorra tokens + latencia).

---

## Requisitos del Sistema Windows

### 1️⃣ Tesseract-OCR
Descarga e instala el ejecutable oficial de Windows:

**Descarga:** https://github.com/UB-Mannheim/tesseract/wiki  
**Versión recomendada:** `tesseract-ocr-w64-setup-v5.x.x.exe` (64-bit)

**Pasos de instalación:**
1. Ejecuta el instalador `.exe`
2. En la pantalla de "Select Components", marca:
   - ☑ **English** (requerido)
   - ☑ **Spanish** (opcional pero recomendado para escuelas hispanohablantes)
3. Anota la ruta de instalación (ej: `C:\Program Files\Tesseract-OCR`)
4. Completa la instalación

**Verificar instalación en PowerShell:**
```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

### 2️⃣ Poppler
Necesario para convertir PDFs a imágenes (usado por `pdf2image`).

**Opción A: Descargar release precompilado (más fácil)**
1. Ve a: https://github.com/oschwartz10612/poppler-windows/releases/
2. Descarga `Release-24.xx.0.zip` (o versión más reciente)
3. Extrae a una carpeta, ej: `C:\poppler-24.01.0`
4. Agrega la carpeta `bin` a tu PATH, o configura en `.env`:
   ```
   POPPLER_PATH=C:\poppler-24.01.0\bin
   ```

**Opción B: Instalar via Chocolatey (si tienes)**
```powershell
choco install poppler
```

**Verificar instalación en PowerShell:**
```powershell
& "C:\poppler-24.01.0\bin\pdftoppm.exe" -v
```

---

## Configuración en `.env`

Agrega estas líneas a tu archivo `.env` (si usas paths no estándar):

```bash
# Rutas de ejecutables del sistema (opcional, solo si no están en PATH global)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\poppler-24.01.0\bin

# Variables Gemini (para fallback)
GEMINI_API_KEY=tu_api_key_aqui
```

---

## Dependencias Python (Ya Instaladas ✅)

```bash
pip install pytesseract pdf2image pillow pypdf
```

Verificar instalación:
```powershell
python -c "import pytesseract, pdf2image; print('✅ OCR ready')"
```

---

## Flujo de Ejecución

### En `extraer_texto_de_pdf()`

```
┌─ PDF recibido en bytes
│
├─ [FASE 1] Intenta extracción rápida (PDF digital)
│  └─ Si texto >= 80 caracteres → ✅ Return (ahorro de recursos)
│
├─ [FASE 2] Activa OCR local con Tesseract
│  ├─ Convierte páginas a imágenes (usando Poppler)
│  ├─ Procesa cada imagen con pytesseract
│  └─ Si encuentra texto → ✅ Return
│
└─ [FALLBACK] Envía a Gemini para análisis multimodal
   └─ Última opción si OCR no está disponible
```

---

## Testing

### Test 1: PDF Digital (debe ser instantáneo)
```python
from main import extraer_texto_de_pdf

# Archivo PDF normal (con capa de texto)
with open("documento_normal.pdf", "rb") as f:
    texto = extraer_texto_de_pdf(f.read())
    print(f"✅ Extraído: {len(texto)} caracteres")
```

### Test 2: PDF Escaneado (activa OCR)
```python
# Foto de un documento convertida a PDF o PDF escaneado
with open("documento_escaneado.pdf", "rb") as f:
    texto = extraer_texto_de_pdf(f.read())
    print(f"✅ OCR procesó: {len(texto)} caracteres")
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'pytesseract'` | `pip install pytesseract` |
| `ModuleNotFoundError: No module named 'pdf2image'` | `pip install pdf2image` |
| `TesseractNotFoundError: tesseract is not installed or it's not in your PATH` | Instala Tesseract desde el .exe y agrega a PATH, o configura `TESSERACT_CMD` en `.env` |
| `FileNotFoundError: poppler/bin/pdftoppm not found` | Instala Poppler y agrega `POPPLER_PATH` en `.env` |
| OCR extrae caracteres basura | Aumenta DPI en `convert_from_bytes(..., dpi=300)` (línea ~1921) |
| OCR es muy lento | Reduce DPI a 150-200 (por defecto es 250) |
| OCR no reconoce español | Instala language pack: Tesseract installer → Spanish |

---

## Optimizaciones Futuras

1. **Caché de OCR:** Guardar PDFs procesados para evitar re-OCR
2. **Procesamiento paralelo:** Múltiples páginas simultáneamente
3. **Fine-tuning de DPI:** Detectar automáticamente calidad del PDF y ajustar DPI
4. **Validación de confianza:** Rechazar OCR si confianza < 60%

