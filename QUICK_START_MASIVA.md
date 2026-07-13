# 🚀 QUICK START - CORRECCIÓN MASIVA INTEGRADA

## ¡Hola! Sistema listo para usar 🎉

Tu sistema de **corrección pedagógica masiva** ya está completamente instalado y funcionando.

---

## 📋 ¿Qué hace el sistema?

✅ **Detecta automáticamente**:
- ✓ Todas tus 12 materias
- ✓ Todas las actividades de cada materia
- ✓ Todos los estudiantes

✅ **Evalúa automáticamente**:
- ✓ Compara entregas vs consigna
- ✓ Asigna notas del 1 al 10
- ✓ Genera feedback pedagógico personalizado

✅ **Genera un Excel profesional**:
- ✓ 12-13 hojas (una por materia)
- ✓ Dentro de cada hoja: TODAS las actividades de esa materia
- ✓ Código de colores por nota
- ✓ Hoja de resumen con estadísticas

---

## 🎯 Paso 1: Organiza tus carpetas

Tu estructura debe ser así:

```
Correcciones_Classroom/
├── Sistemas Digitales 5to/
│   ├── TP 1 - Circuitos/
│   │   ├── consigna_referencia.txt        ← IMPORTANTE
│   │   └── German Rodriguez/
│   │       └── entrega_*.docx             ← IMPORTANTE
│   └── TP 2 - Electrónica/
│       ├── consigna_referencia.txt
│       └── Juan Garcia/
│           └── entrega_*.docx
│
├── Inst. Mant. De Redes Inf./
│   ├── Actividad 1/
│   │   ├── consigna_referencia.txt
│   │   └── [Estudiante]/
│   │       └── entrega_*.docx
│   ...
│
└── [Otras 10 materias]
```

**IMPORTANTE**:
- El archivo `consigna_referencia.txt` **DEBE existir** en cada carpeta de actividad
- Sin esto, el sistema no puede evaluar

---

## 🔧 Paso 2: Agrega tus archivos reales

1. Copia tus **consignas** en `consigna_referencia.txt`
2. Copia las **entregas de estudiantes** como `entrega_*.docx`

Ejemplo:
```
Correcciones_Classroom/Sistemas Digitales 5to/TP 1 - Circuitos/
├── consigna_referencia.txt
├── German Rodriguez/
│   ├── entrega_German Rodriguez.docx
│   ├── entrega_German Rodriguez_1.docx
│   └── informe_tecnico_pedagogico.json
└── Juan Garcia/
    └── entrega_Juan Garcia.docx
```

---

## ⚡ Paso 3: Ejecuta la corrección masiva

### Opción A: Desde el menú interactivo (RECOMENDADO)

```bash
python main.py
```

Luego selecciona: **[4] 📊 Corrección Masiva - TODAS las Materias y Actividades**

### Opción B: Directamente desde terminal

```bash
python corrector_masivo_integrado.py
```

---

## 📊 Paso 4: Revisa tu Excel

Se genera automáticamente: **`evaluaciones_completas.xlsx`**

### Contenido del Excel:

**Hoja "Resumen"**:
| Materia | Total Estudiantes | Actividades | Promedio | Aprobados |
|---------|-------------------|-------------|----------|-----------|
| Sist. Dig. 5to | 10 | 2 | 7.5 | 8 |
| Lab Hardware | 8 | 3 | 6.8 | 5 |
| ... | ... | ... | ... | ... |

**Hoja "Sist. Digitales 5to"**:
| Actividad | Apellido y Nombre | Nota | Descripción | Comentario |
|-----------|-------------------|------|-------------|-----------|
| TP 1 | German Rodriguez | 8 | Cumple 5/6... | Estimado German... |
| TP 1 | Juan Garcia | 6 | Cumple 3/6... | Estimado Juan... |
| TP 2 | Maria Lopez | 9 | Cumple 6/6... | Excelente trabajo Maria... |

---

## 🎨 Código de Colores

- 🟢 **Verde**: Nota ≥ 8 (Excelente)
- 🟡 **Amarillo**: Nota 6-7 (Aprobado)
- 🔴 **Rojo**: Nota < 6 (Requiere mejora)

---

## 📝 ¿Cómo se calcula la nota?

El sistema evalúa automáticamente estos criterios:

1. ✓ **Infografía/Elementos visuales**
2. ✓ **Justificación de decisiones**
3. ✓ **Temas específicos de la consigna**
4. ✓ **Presentación/Estructura**
5. ✓ **Contenido mínimo (>200 caracteres)**
6. ✓ **Organización (intro-desarrollo-conclusión)**

**Escala de notas**:
- 10 puntos → 90-100% criterios cumplidos
- 9 puntos → 80-89%
- 8 puntos → 70-79%
- 7 puntos → 60-69%
- 6 puntos → 50-59%
- 1-5 puntos → Menos del 50%

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Evaluar una clase completa

```bash
# Estructura esperada
Correcciones_Classroom/Sistemas Digitales 5to/TP 1/
├── consigna_referencia.txt
├── Alumno 1/
│   └── entrega_Alumno1.docx
├── Alumno 2/
│   └── entrega_Alumno2.docx
└── ...

# Ejecutar
python main.py → Opción [4]

# Resultado
✅ Excel con todas las notas y feedback
```

### Ejemplo 2: Múltiples actividades por materia

```bash
# Estructura
Correcciones_Classroom/Lab Hardware/
├── Actividad 1 - Circuitos/
│   ├── consigna_referencia.txt
│   └── [Estudiantes]/
├── Actividad 2 - Electrónica/
│   ├── consigna_referencia.txt
│   └── [Estudiantes]/
└── Actividad 3 - Proteus/
    ├── consigna_referencia.txt
    └── [Estudiantes]/

# Resultado
✅ Hoja "Lab Hardware" con 3 actividades y todos los estudiantes
```

---

## 🐛 Si algo no funciona

### "No se encontraron materias"
✓ Verifica que existan carpetas en `Correcciones_Classroom/`

### "0 estudiantes evaluados"
✓ Asegúrate de que exista `consigna_referencia.txt` en cada actividad
✓ Verifica que haya archivos `entrega_*.docx` en las carpetas de estudiantes

### "Excel vacío"
✓ Busca mensajes de error en la consola
✓ Verifica la codificación UTF-8 de los nombres de archivos

### Archivo .docx dañado
✓ Reemplázalo con una versión nuevo
✓ O crea un `informe_tecnico_pedagogico.json` con nota manual

---

## 🔄 Flujo Completo

```
1. Organizas carpetas de materias
   ↓
2. Agregas consignas (consigna_referencia.txt)
   ↓
3. Copias entregas de estudiantes (.docx)
   ↓
4. Ejecutas: python main.py → [4]
   ↓
5. Sistema detecta todo automáticamente
   ↓
6. Evalúa cada entrega vs consigna
   ↓
7. Asigna nota y genera feedback
   ↓
8. Crea Excel profesional
   ↓
9. ¡Listo! Descarga el Excel y úsalo en Classroom
```

---

## 📂 Archivos del Sistema

```
Proyecto/
├── main.py                          ← Menú principal
├── corrector_masivo_integrado.py    ← Motor de evaluación (core)
├── aux_correccion_masiva.py         ← Funciones auxiliares
├── crear_estructura_demo.py         ← Crea carpetas de prueba
├── ESTRUCTURA_CARPETAS_MASIVA.md    ← Documentación detallada
├── GUIA_SISTEMA_EVALUACION.md       ← Guía de uso
├── QUICK_START.md                   ← Este archivo
│
└── Correcciones_Classroom/          ← 👈 TUS DATOS AQUÍ
    ├── Sistemas Digitales 5to/
    ├── Lab Hardware/
    ├── Inst. Mant. De Redes Inf./
    └── [Otras 9 materias]/
```

---

## 🎓 Próximos Pasos

1. **Hoy**: Organiza tus carpetas de materias
2. **Hoy**: Copia tus consignas en `consigna_referencia.txt`
3. **Hoy**: Copia las entregas de estudiantes
4. **Hoy**: Ejecuta `python main.py` y selecciona [4]
5. **Hoy**: Descarga el Excel generado
6. **Mañana**: Usa el Excel para publicar notas en Classroom

---

## 💬 Soporte

¿Tienes dudas? Revisa:
- `ESTRUCTURA_CARPETAS_MASIVA.md` - Cómo organizar carpetas
- `GUIA_SISTEMA_EVALUACION.md` - Uso detallado del sistema
- `corrector_masivo_integrado.py` - Código fuente (comentado)

---

## ✅ Checklist Final

Antes de ejecutar, verifica:

- [ ] Python 3.8+ instalado
- [ ] Carpeta `Correcciones_Classroom/` creada
- [ ] Carpetas de materias creadas
- [ ] Carpetas de actividades dentro de materias
- [ ] `consigna_referencia.txt` en cada actividad
- [ ] Archivos `entrega_*.docx` en carpetas de estudiantes
- [ ] Dependencias instaladas (`openpyxl`, `python-docx`)

---

**¿Listo para empezar?**

```bash
python main.py
```

**Selecciona → [4] 📊 Corrección Masiva - TODAS las Materias y Actividades**

¡Que disfrutes del sistema! 🎉

---

**Versión**: 1.0  
**Última actualización**: 12/06/2026  
**Autor**: Sistema de Corrección Pedagógica Automatizada
