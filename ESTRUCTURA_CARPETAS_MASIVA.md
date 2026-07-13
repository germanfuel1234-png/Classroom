# 📂 ESTRUCTURA DE CARPETAS - SISTEMA DE CORRECCIÓN MASIVA

## ¿Cómo debe estar organizada la carpeta?

Para que el **Corrector Masivo Integrado** funcione correctamente, tus materias deben estar organizadas así:

```
Correcciones_Classroom/
│
├── probando/
│   ├── actividad 1/
│   │   ├── consigna_referencia.txt
│   │   └── [Nombre Estudiante]/
│   │       ├── entrega_*.docx
│   │       └── informe_tecnico_pedagogico.json
│   └── actividad 2/
│       ├── consigna_referencia.txt
│       └── [Nombre Estudiante 2]/
│           ├── entrega_*.docx
│           └── informe_tecnico_pedagogico.json
│
├── Sistemas Digitales 5to/
│   ├── TP 1 - Circuitos Digitales/
│   │   ├── consigna_referencia.txt
│   │   └── [Estudiante A]/
│   │       └── entrega_*.docx
│   └── TP 2 - Electrónica/
│       ├── consigna_referencia.txt
│       └── [Estudiante B]/
│           └── entrega_*.docx
│
├── Inst. Mant. De Redes Inf./
│   ├── Actividad 1/
│   │   ├── consigna_referencia.txt
│   │   └── [Estudiante]/
│   │       └── entrega_*.docx
│   ...
│
├── Sist. Operativos/
├── Sistemas Digitales/
├── Procesos Industriales/
├── Desarrollo de aplicaciones web (dinamicas)/
├── Lab Hardware/
├── DES. SOFT. PLAT. MOVILES/
├── Lab. Aplicaciones 2026 4to/
├── Lab. Programacion 4to 2026/
├── Lab. Programacion 2026/
│
└── [Otras materias]/
```

---

## 📋 Componentes Obligatorios

### 1. Carpeta de Materia
- **Nombre**: Exactamente como aparece en tu lista (ej: "Sistemas Digitales 5to")
- **Ubicación**: Dentro de `Correcciones_Classroom/`
- **Contenido**: Carpetas de actividades

### 2. Carpeta de Actividad
- **Nombre**: Nombre descriptivo (ej: "TP 1 - Circuitos", "Actividad 1")
- **Ubicación**: Dentro de la carpeta de materia
- **Archivos necesarios**:
  - `consigna_referencia.txt` ← Obligatorio (la consigna del docente)
  - Carpetas de estudiantes

### 3. Carpeta de Estudiante
- **Nombre**: Nombre del estudiante (ej: "German Rodriguez", "Juan Garcia")
- **Ubicación**: Dentro de la carpeta de actividad
- **Archivos**:
  - `entrega_*.docx` (ej: "entrega_German Rodriguez.docx") - Obligatorio si existe entrega
  - O `informe_tecnico_pedagogico.json` - Si no hay entrega pero hay informe

---

## 🔍 Regla de Detección

El sistema **automáticamente**:

1. ✅ Detecta todas las carpetas en `Correcciones_Classroom/` como **materias**
2. ✅ Detecta todas las subcarpetas de materia como **actividades**
3. ✅ Detecta todas las subcarpetas de actividad como **estudiantes**
4. ✅ Busca `consigna_referencia.txt` en cada actividad
5. ✅ Busca archivos `entrega_*.docx` en cada carpeta de estudiante
6. ✅ Lee `informe_tecnico_pedagogico.json` si existe

**Carpetas IGNORADAS automáticamente**:
- `reportes`
- `temp`
- `.git`
- Cualquier carpeta que empiece con punto (`.`)

---

## 📝 Archivo: consigna_referencia.txt

Este archivo **DEBE estar en cada carpeta de actividad** y contiene el enunciado de la tarea.

### Ejemplo:
```
TRABAJO PRÁCTICO N° 1 - CIRCUITOS DIGITALES

Objetivo:
Diseñar un circuito digital que implemente una puerta NOT utilizando:
- 1 transistor BJT
- 2 resistencias
- 1 LED

Requisitos:
1. Justificar la selección de componentes
2. Presentar un diagrama esquemático
3. Calcular voltajes de operación
4. Explicar el funcionamiento paso a paso

Recursos recomendados:
- Apuntes de la Unidad 2
- Simulador: Proteus

Plazo de entrega: 15 de julio de 2026
```

---

## 📄 Archivos de Entrega

### Formato esperado:
- **Nombre**: `entrega_<Nombre Estudiante>.docx` o `entrega_<Nombre>_1.docx`
- **Ubicación**: Carpeta del estudiante
- **Contenido**: Texto editable (Word, Google Docs, etc.)
- **Formato NO soportado**: Imágenes sin OCR, PDFs escaneados sin extraer texto

### Ejemplos válidos:
```
entrega_German Rodriguez.docx
entrega_Juan Garcia_1.docx
entrega_Maria Lopez - actividad 1.docx
```

---

## 🎯 Flujo Completo de Uso

### Paso 1: Organizar Carpetas
Asegúrate de que tu estructura sea exactamente como se muestra arriba.

### Paso 2: Agregar Consignas
En cada carpeta de actividad, coloca un archivo `consigna_referencia.txt` con la consigna.

### Paso 3: Agregar Entregas
En cada carpeta de estudiante, coloca archivo(s) `entrega_*.docx` con la entrega.

### Paso 4: Ejecutar Corrector
```bash
python main.py
# Selecciona opción [4]: Corrección Masiva - TODAS las Materias y Actividades
```

### Paso 5: Revisar Excel
Se generará automáticamente `evaluaciones_completas.xlsx` con:
- **Hoja "Resumen"**: Estadísticas por materia
- **Una hoja por materia**: Con todas las actividades y estudiantes
- **Código de colores**: Verde (≥8), Amarillo (6-7), Rojo (<6)

---

## ✅ Checklist Antes de Ejecutar

- [ ] Carpetas de materias creadas en `Correcciones_Classroom/`
- [ ] Carpetas de actividades dentro de cada materia
- [ ] `consigna_referencia.txt` en cada actividad
- [ ] Archivos `entrega_*.docx` en carpetas de estudiantes
- [ ] Nombres de carpetas sin caracteres especiales (ej: NO usar `@`, `#`, `*`)
- [ ] Nombres de archivos en UTF-8 sin caracteres especiales

---

## 🚨 Casos Especiales

### Si un estudiante no entregó
- **Opción 1**: No crear carpeta para ese estudiante
- **Opción 2**: Crear carpeta vacía (sistema la ignorará)
- **Opción 3**: Agregar `informe_tecnico_pedagogico.json` con estado

### Si una entrega está dañada
- Crear un archivo `informe_tecnico_pedagogico.json` con:
```json
{
  "nota": 2,
  "motivo_tecnico": "Archivo corrupto",
  "feedback": "Re-entrega requerida en formato editable"
}
```

### Si hay múltiples entregas de un estudiante
- El sistema procesa la **primera entrega encontrada** (orden alfabético)
- Ejemplo: Si hay `entrega_Juan_1.docx` y `entrega_Juan_2.docx`, procesa `entrega_Juan_1.docx`

---

## 📊 Output Esperado

Después de ejecutar, obtendrás:

**Archivo**: `evaluaciones_completas.xlsx`

**Contenido**:
- **Hoja "Resumen"**: 
  - Total de estudiantes por materia
  - Número de actividades por materia
  - Promedio de notas
  - Cantidad de aprobados

- **Hojas por Materia** (ej: "Sistemas Digitales 5to"):
  - Columna A: Nombre de Actividad
  - Columna B: Apellido y Nombre
  - Columna C: Nota (1-10)
  - Columna D: Descripción Técnica
  - Columna E: Comentario Pedagógico

---

## 🔧 Troubleshooting

### "No se encontraron materias"
✓ Verifica que existan carpetas en `Correcciones_Classroom/`

### "Actividades no detectadas"
✓ Verifica que haya subcarpetas dentro de la carpeta de materia

### "Estudiantes sin procesar"
✓ Asegúrate de que exista `entrega_*.docx` o `informe_tecnico_pedagogico.json`

### "consigna_referencia.txt no encontrada"
✓ Crea el archivo en cada carpeta de actividad

### Excel vacío o sin datos
✓ Verifica que los archivos de entrega sean `.docx` válidos
✓ Verifica la codificación UTF-8 de los nombres

---

## 💡 Ejemplos Listos para Copiar

Si quieres crear la estructura desde cero, copia estos comandos PowerShell:

```powershell
# Crear estructura de ejemplo
mkdir "Correcciones_Classroom/Sistemas Digitales 5to/TP 1 - Circuitos" -Force
mkdir "Correcciones_Classroom/Sistemas Digitales 5to/TP 1 - Circuitos/German Rodriguez" -Force
mkdir "Correcciones_Classroom/Inst. Mant. De Redes Inf./Actividad 1" -Force
mkdir "Correcciones_Classroom/Inst. Mant. De Redes Inf./Actividad 1/Juan Garcia" -Force

# Crear archivo consigna de ejemplo
@"
TRABAJO PRÁCTICO N° 1

Objetivo: Completar la tarea
Requisitos: Ver apuntes de clase
Plazo: 30 de junio de 2026
"@ | Out-File -Encoding UTF8 "Correcciones_Classroom/Sistemas Digitales 5to/TP 1 - Circuitos/consigna_referencia.txt"
```

---

**Última actualización**: 12/06/2026
