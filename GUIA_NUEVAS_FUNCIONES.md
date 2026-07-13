# 📋 Guía de Uso: Nuevas Funciones de Publicación y Extracción

## ⚠️ PASO CRÍTICO: Renovar OAuth

Ya que cambiamos los SCOPES en `main.py`, **DEBES hacer esto**:

```powershell
# 1. Borra el token.json viejo (para forzar re-autenticación)
Remove-Item token.json

# 2. Ejecuta main.py nuevamente
python main.py

# 3. Se abrirá el navegador pidiendo permisos
# 4. Verifica que incluya: "Modify your Google Classroom coursework"
# 5. Autoriza y listo
```

---

## 1️⃣ Función: `extraer_texto_de_archivo_local()`

**Para qué:** Extraer texto de archivos locales (PDFs, DOCX, imágenes) sin usar Google Drive.

### Uso Simple:

```python
from main import extraer_texto_de_archivo_local

# Extraer desde PDF (escaneado o digital)
texto = extraer_texto_de_archivo_local("C:/ruta/documento.pdf")
print(f"Extraído: {len(texto)} caracteres")

# Extraer desde DOCX
texto = extraer_texto_de_archivo_local("C:/ruta/documento.docx")

# Extraer desde Imagen
texto = extraer_texto_de_archivo_local("C:/ruta/foto.jpg")
```

### Flujo Interno:

```
PDF digital
    ↓
[Intenta PyPDF2]
    ├─ Sí, >80 chars → Return (rápido)
    └─ No → [Activa OCR Tesseract]
         ├─ Sí → Return
         └─ No → [Gemini multimodal]

PDF escaneado / Imagen
    ↓
[Tesseract OCR] → Return

DOCX
    ↓
[python-docx] → Return
```

### Casos de Uso:

```python
# Testing local sin Google Drive
pdf_path = "Correcciones_Classroom/Sist. Operativos/Trabajo Practico N 1.3/german rodriguez/entrega.pdf"
texto = extraer_texto_de_archivo_local(pdf_path)

# Procesamiento en lote
import glob
for archivo in glob.glob("C:/entregas/*.pdf"):
    texto = extraer_texto_de_archivo_local(archivo)
    print(f"{archivo}: {len(texto)} chars")
```

---

## 2️⃣ Función: `publicar_evaluacion_en_classroom()`

**Para qué:** Publicar nota + comentario + devolver tarea en UNA sola llamada centralizada.

### Uso Simple:

```python
from main import publicar_evaluacion_en_classroom

# Parámetros
course_id = "123456789"
course_work_id = "987654321"
submission_id = "abcdef123456"
nota = 7  # Escala 1-10 (se convierte a 0-100 internamente)
feedback = "Excelente trabajo, cubriste todos los temas. Solo faltó...\n\nNota final: 7/10"
alumno_nombre = "Juan Pérez"

# Publicar TODO
resultado = publicar_evaluacion_en_classroom(
    service=service,  # Cliente Classroom API
    course_id=course_id,
    course_work_id=course_work_id,
    submission_id=submission_id,
    nota_num=nota,
    feedback_texto=feedback,
    alumno_nombre=alumno_nombre
)

# Verificar resultado
if resultado['exito']:
    print(f"✅ Todo publicado para {alumno_nombre}")
else:
    print(f"❌ Error: {resultado['error']}")
    # Analizar qué falló:
    print(f"   Nota: {resultado['nota_asignada']}")
    print(f"   Comentario: {resultado['comentario_publicado']}")
    print(f"   Devuelta: {resultado['devuelta']}")
```

### Estructura de Retorno:

```python
{
    'exito': bool,                    # ¿Todo funcionó?
    'nota_asignada': bool,            # ¿Se publicó la nota?
    'comentario_publicado': bool,     # ¿Se publicó el comentario?
    'devuelta': bool,                 # ¿Se devolvió la tarea?
    'error': str                      # Mensaje de error (si aplica)
}
```

### Manejo de Errores:

```python
resultado = publicar_evaluacion_en_classroom(...)

if "403 Forbidden" in str(resultado['error']):
    print("❌ Permisos insuficientes")
    print("   SOLUCIÓN: Borra token.json y vuelve a autenticar")
    print("   Verifica que los SCOPES incluyan 'classroom.coursework.me.modify'")

elif resultado['nota_asignada'] and not resultado['comentario_publicado']:
    print("⚠️ Nota publicada pero sin comentario")
    print(f"   Razón: {resultado['error']}")
    # Reintentar solo comentario manualmente si necesario
```

---

## 3️⃣ Integración en Flujo Existente

Ahora el código de publicación en `main.py` (alrededor de línea 1540) se simplifica:

### ANTES (código disperso):
```python
# Código mezclado, repetido, difícil de mantener
try:
    # Publicar nota
    service.courses().courseWork().studentSubmissions().patch(...)
    # Publicar comentario
    service.courses().courseWork().studentSubmissions().comments().create(...)
    # Devolver
    service.courses().courseWork().studentSubmissions().return_(...)
except Exception as e:
    # Manejo de errores inconsistente
```

### AHORA (limpio y centralizado):
```python
resultado = publicar_evaluacion_en_classroom(
    service=service,
    course_id=course_id,
    course_work_id=work_id,
    submission_id=submission_id,
    nota_num=nota_final,
    feedback_texto=feedback_txt,
    alumno_nombre=alumno_nombre
)

if resultado['exito']:
    publicados += 1
else:
    # Guardar pendientes si falla
    pendientes.append({
        'alumno': alumno_nombre,
        'error': resultado['error']
    })
```

---

## 🔍 Ejemplo Completo: Corrección de TP

```python
from main import (
    extraer_texto_de_archivo_local,
    publicar_evaluacion_en_classroom,
    CorrectorPedagogico
)

# Setup
course_id = "123456789"
course_work_id = "987654321"
materia = "Sistemas Operativos"
tp = "TP 1 - Instalación"

# Crear corrector pedagógico
corrector = CorrectorPedagogico(materia, tp)

# Procesar cada alumno
alumnos = [
    {
        'nombre': 'Juan Pérez',
        'submission_id': 'sub_001',
        'pdf_local': 'Correcciones_Classroom/Sist. Operativos/.../Trabajo_Practico_1.pdf'
    },
    {
        'nombre': 'María García',
        'submission_id': 'sub_002',
        'pdf_local': 'Correcciones_Classroom/Sist. Operativos/.../Trabajo_Practico_1.pdf'
    }
]

for alumno in alumnos:
    print(f"\n📋 Procesando {alumno['nombre']}...")
    
    # 1. Extraer texto
    texto = extraer_texto_de_archivo_local(alumno['pdf_local'])
    print(f"   ✅ Extraído: {len(texto)} caracteres")
    
    # 2. Evaluar
    consigna_referencia = "Explicar el proceso de instalación de Linux..."
    evaluacion = corrector.evaluar_entrega_automatica(
        alumno_nombre=alumno['nombre'],
        texto_entrega=texto,
        consigna_referencia=consigna_referencia,
        aplicar_filtro_rapido=True
    )
    
    nota_final = evaluacion['nota']
    feedback_final = evaluacion['comentario_privado']
    
    # 3. Publicar TODO
    resultado = publicar_evaluacion_en_classroom(
        service=service,
        course_id=course_id,
        course_work_id=course_work_id,
        submission_id=alumno['submission_id'],
        nota_num=nota_final,
        feedback_texto=feedback_final,
        alumno_nombre=alumno['nombre']
    )
    
    if resultado['exito']:
        print(f"   ✅ Publicado: {nota_final}/10")
    else:
        print(f"   ❌ Error: {resultado['error']}")
```

---

## 🚀 Ventajas de las Nuevas Funciones

| Ventaja | Beneficio |
|---------|-----------|
| **Función centralizada** | Menos código, más mantenible, testeable |
| **Manejo de errores robusto** | Distingue entre 403 vs otros errores |
| **Extracción local** | Test sin Google Drive, más rápido |
| **Logging detallado** | Sabe exactamente dónde falló |
| **Scopes completados** | Permisos de escritura habilitados |

---

## ⚙️ Próximos Pasos

1. ✅ Borra `token.json` (para renovar OAuth)
2. ✅ Ejecuta `python main.py` y autoriza con permisos nuevos
3. ✅ Prueba `extraer_texto_de_archivo_local()` con un PDF local
4. ✅ Prueba `publicar_evaluacion_en_classroom()` con un alumno de test
5. 🚀 Ejecuta correcciones en producción
