# 📋 RESUMEN DEL FLUJO COMPLETO DE CORRECCIÓN DE TRABAJOS EN CLASSROOM

## 🎯 Visión General del Proceso

El sistema automatiza la corrección de trabajos mediante:
1. **Descarga de entregas** desde Classroom y Google Drive
2. **Extracción de texto** desde PDFs, Word y Google Docs
3. **Análisis automático** de concordancia con la consigna
4. **Generación de calificaciones** (nota 1-10) y feedback personalizado
5. **Publicación en Classroom** de notas y comentarios privados
6. **Generación de reportes JSON** para auditoría y seguimiento

---

## 📥 PASO 1: DESCARGA Y EXTRACCIÓN DE ENTREGAS

### Entrada de datos
- **Usuario selecciona**: Materia → Tema → Actividad/TP
- **Sistema obtiene**: Lista de alumnos vinculados a la actividad
- **Para cada alumno**: Se descargan adjuntos de Google Drive

### Proceso de descarga (`preparar_carpeta_y_descargar_entrega()`)

```
Carpeta local: Correcciones_Classroom/[Materia]/[TP]/[Alumno]/
├── entrega_[archivo1].docx
├── entrega_[archivo2].pdf
├── consigna_referencia.txt
├── comentario_privado.txt
├── informe_tecnico_pedagogico.json
├── informe_tecnico_pedagogico.docx
└── estado_descarga.txt
```

**Manejo de archivos de Google Drive:**
- Google Docs/Sheets → Se exportan a .docx/.xlsx automáticamente
- PDFs nativos → Se descargan tal cual
- Otros formatos → Se procesan según su MIME type

---

## 🔤 PASO 2: EXTRACCIÓN DE TEXTO

### Estrategia híbrida de OCR (función `extraer_texto_de_pdf()`)

#### **Fase 1: Extracción digital (PDFs con capa de texto)**
```python
- PyPDF2 intenta leer texto de PDF
- Si extrae >80 caracteres → Se devuelve como válido
- Sino → Pasa a Fase 2
```

#### **Fase 2: OCR local con Tesseract**
```python
- pdf2image convierte páginas a imágenes (DPI 250)
- Tesseract aplica OCR (idioma: español + inglés)
- Si genera texto → Se devuelve
- Sino → Pasa a Fase 3
```

#### **Fase 3: OCR multimodal con Gemini**
```python
- Envía PDF completo a Gemini 2.5 Flash
- Gemini extrae texto visualmente
- Si no tiene GEMINI_API_KEY → Fallback a Tesseract o error
```

**Límite de output**: 12,000 caracteres máximo por archivo

### Para archivos DOCX
- `Document()` (python-docx) extrae párrafos
- Concatena todos los párrafos en texto simple

### Resultado
```
texto_entrega = "[Página 1] párrafos..."  # o error descriptivo
```

---

## ✅ PASO 3: ANÁLISIS DE CONCORDANCIA CON CONSIGNA

### Función: `evaluar_entrega_automatica()`

#### **Validaciones previas (filtros anti-trampa):**

1. **¿Hay adjuntos?**
   - NO → Estado: "Adeuda entrega"
   - SÍ → Continuar

2. **¿El texto es legible?**
   - NO (PDF escaneado no procesado, imagen, etc.) → Estado: "Revisión manual requerida"
   - SÍ → Continuar

3. **¿Es solo imágenes sin texto?**
   - SÍ → Estado: "Rehacer" (Nota: 1/10) - "Formato no evaluable"
   - NO → Continuar

4. **Validación IA de pertinencia** (si `GEMINI_API_KEY` existe)
   - Gemini verifica: ¿La entrega corresponde a la consigna?
   - SI FALLA → Estado: "Rehacer" (Nota: 1/10) - "No pertinente"
   - SI PASA → Continuar

5. **Validación léxica de pertinencia**
   - Extrae palabras clave (>4 caracteres) de la consigna
   - Cuenta coincidencias en la entrega
   - Si cobertura < 15% → Estado: "Rehacer" (Nota: 1/10)
   - Sino → Continuar

#### **Análisis de concordancia real** (función: `analizar_concordancia_consigna_entrega()`)

```
concordancia_score = (palabras_clave_encontradas / total_palabras_clave) × 100

+ Criterios de calidad:
  - Longitud de entrega (palabras)
  - Cobertura de temas
  - Profundidad (ajuste por extensión)

= Puntuación 0-1.0
```

#### **Generación de nota** (función: `generar_nota_desde_concordancia()`)

```
Mapeo de concordancia a escala 1-10:
- 0.0-0.2   → Nota 1-3 (No aprobado)
- 0.2-0.4   → Nota 3-5 (Reprobado)
- 0.4-0.6   → Nota 5-7 (Aprobado con deficiencias)
- 0.6-0.8   → Nota 7-9 (Bien/Muy bien)
- 0.8-1.0   → Nota 9-10 (Excelente)

Ajustes por longitud:
- < 50 palabras: -2
- < 100 palabras: -1
- > 500 palabras: +0.5 bonus

Rango final: max(1, min(10, nota_base))
```

---

## 💬 PASO 4: GENERACIÓN DE FEEDBACK PERSONALIZADO

### Función: `_generar_feedback_personalizado()`

**No usa plantillas genéricas.** Genera feedback dinámico según:
- **Nota obtenida**
- **Temas cubiertos**
- **Temas faltantes**
- **Observaciones del análisis**

#### Estructura del feedback:

```
1. Introducción contextualizada por nota
   - Nota ≥9: "Excelente trabajo, integral y profundo"
   - Nota ≥7: "Buen trabajo, mayoría de aspectos cubiertos"
   - Nota ≥5: "Desarrollo parcial, analicemos qué falta"
   - Nota <5: "Requiere atención importante"

2. Detalle de cobertura
   - ✓ Temas que SÍ abordó bien (máx 5)
   - ✗ Temas por mejorar o que faltaron (máx 5)

3. Observaciones técnicas
   - "Entrega muy breve, falta profundidad"
   - "Cobertura parcial de temas solicitados"
   - etc.

4. Recomendaciones
   - Si nota ≥7: "Mantén este nivel"
   - Si nota <7: Pasos concretos para mejorar

5. Firma
   - "Calificación: X/10"
```

**Ejemplo de feedback generado:**

```
Buen trabajo en Sistemas Operativos - TP1. Has cubierto la mayoría de 
los aspectos solicitados.

✓ Temas que sí abordaste bien: configuración básica, instalación de SO.

✗ Temas por mejorar: gestión de particiones, instalación de bootloader.

Entrega moderadamente desarrollada. Cobertura parcial de temas solicitados.

Para mejorar en próximas entregas:
1. Lee cuidadosamente TODA la consigna antes de comenzar.
2. Identifica los puntos clave que deben estar en tu trabajo.
3. Desarrolla cada punto con profundidad y claridad.

Calificación: 7/10.
```

---

## 📊 PASO 5: ALMACENAMIENTO LOCAL DE REPORTES

### Función: `guardar_reportes_locales()`

**En la carpeta del alumno se generan:**

1. **consigna_referencia.txt**
   - Contenido: Título + Descripción + Materiales del TP
   - Propósito: Referencia local para revisar qué se pedía

2. **comentario_privado.txt**
   - Contenido: Feedback completo generado
   - Propósito: Backup del comentario a publicar en Classroom

3. **informe_tecnico_pedagogico.json**
   ```json
   {
     "fecha": "2026-06-10 14:30:45",
     "alumno": "Juan Pérez",
     "materia": "Sistemas Operativos",
     "trabajo_practico": "TP1 - Instalación",
     "estado_resultado": "Aprobado",
     "nota": 7,
     "motivo_tecnico": "Análisis de concordancia: 65% cobertura...",
     "feedback": "[Feedback completo aquí]"
   }
   ```

4. **informe_tecnico_pedagogico.docx**
   - Misma información que el JSON pero en formato Word
   - Propósito: Printeable y legible para docentes

5. **estado_descarga.txt**
   ```
   Fecha: 2026-06-10 14:30:45
   Alumno: Juan Pérez
   
   Archivos descargados: 2
   Listado de archivos:
   - entrega_tp1_config.docx
   - entrega_referencias.pdf
   
   Errores de descarga: 0
   ```

---

## 🎯 PASO 6: PUBLICACIÓN EN CLASSROOM

### Función: `publicar_resultados_en_classroom()`

**Para cada alumno en el lote:**

#### Paso 6.1: Conversión de nota
```python
nota_1_10 = 7
nota_100 = nota_1_10 × 10  # Nota 70/100 en Classroom
```

#### Paso 6.2: Publicación de nota
```
PATCH /courses/{courseId}/courseWork/{workId}/studentSubmissions/{id}
{
  "assignedGrade": 70,      # Nota visible al alumno
  "draftGrade": 70           # Nota en borrador
}
```
✅ **Resultado**: Nota aparece en Classroom

#### Paso 6.3: Publicación de comentario privado
```
POST /courses/{courseId}/courseWork/{workId}/{id}/comments
{
  "text": "[Feedback completo]"
}
```
✅ **Resultado**: Comentario privado visible solo para el alumno

#### Paso 6.4: Devolución de entrega
```
POST /courses/{courseId}/courseWork/{workId}/{id}/return
```
✅ **Resultado**: La entrega regresa de estado "RETURNED" → alumno ve calificación

### Manejo de errores
- Si falla comentario por API → Se guarda en **comentarios_privados_pendientes_[timestamp].json**
- Archivo guardado en carpeta de reportes diarios
- Sistema abre links de entregas fallidas para comentario web manual
- Opción de copiar comentario al portapapeles e insertar manualmente

---

## 📝 PASO 7: GENERACIÓN DE REPORTES JSON CENTRALIZADOS

### Función: `CorrectorPedagogico.generar_json()`

**Estructura JSON final que se guarda en carpeta de reportes:**

```json
{
  "materia": "Sistemas Operativos",
  "tp": "TP1 - Instalación y Configuración",
  "fecha_correccion": "2026-06-10",
  "reporte_entregas": [
    {
      "alumno": "Juan Pérez",
      "estado_interno": "Aprobado",
      "nota": 7,
      "motivo_correccion": "Análisis de concordancia: 65% cobertura de temas principales...",
      "devolucion_alumno": "[Feedback personalizado completo]"
    },
    {
      "alumno": "María González",
      "estado_interno": "Adeuda Entrega",
      "nota": null,
      "motivo_correccion": "Alumno no entregó la actividad",
      "devolucion_alumno": "Estimada María: Según el registro actual de Classroom..."
    },
    {
      "alumno": "Pedro López",
      "estado_interno": "Reentrega Técnica",
      "nota": null,
      "motivo_correccion": "Archivo con hojas en blanco o no legible",
      "devolucion_alumno": "Estimado Pedro: Al proceder a la corrección..."
    },
    {
      "alumno": "Laura Martínez",
      "estado_interno": "Rehacer",
      "nota": 1,
      "motivo_correccion": "Entrega no pertinente a la consigna. La entrega no evidencia alineación...",
      "devolucion_alumno": "La entrega no corresponde de forma directa a la consigna del TP..."
    }
  ]
}
```

**Ubicación**: `Correcciones_Classroom/reportes/[YYYY-MM-DD]/reporte_[Materia]_[TP]_[timestamp].json`

### Campos del reporte por alumno:

| Campo | Tipo | Significado |
|-------|------|------------|
| `alumno` | string | Nombre completo del alumno |
| `estado_interno` | string | Estado de corrección: "Aprobado", "Desaprobado", "Adeuda Entrega", "Reentrega Técnica", "Rehacer" |
| `nota` | int/null | Calificación 1-10 (null si no aplica) |
| `motivo_correccion` | string | Resumen técnico del análisis automático (para auditoría docente) |
| `devolucion_alumno` | string | Feedback personalizado para mostrar al alumno en Classroom |

---

## 🔄 FLUJO COMPLETO (VISUAL)

```
┌─────────────────────────────┐
│ 1. SELECCIÓN              │
│ (Materia → Tema → TP)    │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│ 2. DESCARGA ENTREGAS      │
│ (Classroom → Google Drive) │
│ (Archivos → Carpeta local) │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│ 3. EXTRACCIÓN DE TEXTO    │
│ (PDF → Tesseract/Gemini)  │
│ (DOCX → python-docx)      │
└──────────┬──────────────────┘
           │
           ↓
┌─────────────────────────────┐
│ 4. VALIDACIONES           │
│ (Adjuntos? Legible?       │
│  ¿IA de pertinencia?      │
│  Cobertura léxica?)       │
└──────────┬──────────────────┘
           │
          ↙ ↓ ↖
    ┌─────────────────┐
    │ Estado válido?  │
    └─────────────────┘
         ↙   ↓   ↖
      [SÍ] [NO] [REVISAR]
        │    │     │
        ↓    ↓     ↓
     ┌────────────────────────────────┐
     │ 5. ANÁLISIS DE CONCORDANCIA   │
     │ (¿Cubre temas de consigna?)   │
     │ (Generar nota 1-10)           │
     └────────────────────────────────┘
           │
           ↓
     ┌────────────────────────────────┐
     │ 6. FEEDBACK PERSONALIZADO     │
     │ (No plantillas genéricas)     │
     │ (Dinámico según contexto)     │
     └────────────────────────────────┘
           │
           ↓
     ┌────────────────────────────────┐
     │ 7. ALMACENAMIENTO LOCAL       │
     │ (.txt, .json, .docx)          │
     └────────────────────────────────┘
           │
           ↓
     ┌────────────────────────────────┐
     │ 8. PUBLICACIÓN CLASSROOM      │
     │ (Nota 0-100)                  │
     │ (Comentario privado)          │
     │ (Devolución entrega)          │
     └────────────────────────────────┘
           │
           ↓
     ┌────────────────────────────────┐
     │ 9. REPORTE CENTRAL JSON       │
     │ (reporte_[materia]_[tp].json) │
     └────────────────────────────────┘
```

---

## 🎲 POSIBLES ESTADOS DE ENTREGA

| Estado | Nota | Significado | Acción Requerida |
|--------|------|------------|------------------|
| **Aprobado** | 7-10 | Entrega válida y aprobatoria | Publicar en Classroom |
| **Desaprobado** | 1-6 | Entrega válida pero insuficiente | Publicar en Classroom |
| **Adeuda Entrega** | null | No hay archivos adjuntos | Solicitar reentrega |
| **Reentrega Técnica** | null | PDF/archivo vacío o no legible | Pedir archivo correcto |
| **Rehacer** | 1 | Entrega no corresponde a la consigna | Solicitar TP nuevo |
| **Revisión Manual** | null | Archivo escaneado, requiere inspección humana | Revisar manualmente |

---

## 🗂️ ESTRUCTURA DE CARPETAS DE REPORTES

```
Correcciones_Classroom/
├── [Materia]/
│   └── [TP]/
│       └── [Alumno]/
│           ├── entrega_*.pdf
│           ├── entrega_*.docx
│           ├── consigna_referencia.txt
│           ├── comentario_privado.txt
│           ├── informe_tecnico_pedagogico.json
│           ├── informe_tecnico_pedagogico.docx
│           └── estado_descarga.txt
│
└── reportes/
    └── [YYYY-MM-DD]/
        ├── reporte_[Materia]_[TP]_[timestamp].json
        ├── comentarios_privados_pendientes_[timestamp].json
        └── [otras entregas...]
```

---

## 🔑 VARIABLES DE ENTORNO REQUERIDAS

```env
GEMINI_API_KEY=xxxxx         # Para OCR multimodal y validación IA
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # OCR local
POPPLER_PATH=C:\Program Files\poppler\Library\bin           # PDF a imagen
OPENAI_API_KEY=xxxxx         # OCR alternativo (fallback)
```

---

## 📊 RESUMEN DE CAMPOS JSON FINALES

### Reporte Central (reporte_[materia]_[tp].json)
- **materia**: Nombre de la materia
- **tp**: Título del trabajo práctico
- **fecha_correccion**: YYYY-MM-DD
- **reporte_entregas**: Array de objetos por alumno

### Por Alumno en Reporte
- **alumno**: Nombre completo
- **estado_interno**: Clasificación de corrección
- **nota**: 1-10 o null
- **motivo_correccion**: Análisis técnico (auditoría)
- **devolucion_alumno**: Feedback para mostrar

### Informe Técnico Local (por alumno)
- **fecha**: Timestamp completo
- **alumno**: Nombre
- **materia**: Materia
- **trabajo_practico**: TP
- **estado_resultado**: Estado
- **nota**: Calificación
- **motivo_tecnico**: Análisis de concordancia
- **feedback**: Devolución completa

---

## ⚡ FLUJO RÁPIDO (Versión resumida)

```
1. Selecciona Materia/Tema/TP
   ↓
2. Descarga entregas de alumnos a carpeta local
   ↓
3. Extrae texto (OCR si es PDF escaneado)
   ↓
4. Valida: ¿Hay adjuntos? ¿Es legible? ¿Pertinencia IA?
   ↓
5. Analiza concordancia con consigna → Genera nota 1-10
   ↓
6. Crea feedback personalizado dinámico
   ↓
7. Guarda reportes locales (.txt, .json, .docx)
   ↓
8. Publica en Classroom (nota + comentario privado)
   ↓
9. Genera reporte JSON central para auditoría
```

---

## 🎯 CONCLUSIÓN

El sistema **automatiza y personaliza** el flujo de corrección mediante:
- ✅ OCR inteligente con fallback múltiple
- ✅ Análisis real de concordancia consigna-entrega
- ✅ Notas justas basadas en cobertura de temas
- ✅ Feedback dinámico sin plantillas genéricas
- ✅ Publicación segura en Classroom con fallbacks
- ✅ Reportes JSON para auditoría y seguimiento
- ✅ Almacenamiento local duplicado por seguridad
