# 🎓 GUÍA DE USO - SISTEMA DE CORRECCIÓN PEDAGÓGICA MASIVA

## 📋 Descripción General

Sistema **completamente automatizado** que realiza evaluaciones pedagógicas masivas de entregas de estudiantes en Google Classroom. Genera:

1. **JSON estructurado** con evaluaciones estrictas
2. **Planilla Excel** con estadísticas por materia
3. **Feedback pedagógico** personalizado para cada alumno

---

## 🚀 Uso Rápido

### Opción 1: Script Integrado (RECOMENDADO)

Ejecuta todo el proceso en una sola línea:

```bash
python procesamiento_completo.py
```

**Genera automáticamente:**
- `evaluaciones_masivas.json` - Evaluaciones en formato JSON
- `evaluaciones_estudiantes.xlsx` - Planilla Excel con todas las hojas

---

### Opción 2: Scripts Individuales

Si prefieres ejecutarlos por separado:

```bash
# Paso 1: Generar evaluaciones en JSON
python evaluacion_masiva.py

# Paso 2: Convertir JSON a Excel
python generar_planilla.py
```

---

## 📂 Estructura de Carpetas Esperada

```
Correcciones_Classroom/
└── probando/
    └── actividad 1/
        ├── consigna_referencia.txt          ← Consigna del docente
        └── [Nombre Estudiante]/
            ├── entrega_*.docx               ← Entrega del alumno (si existe)
            ├── informe_tecnico_pedagogico.json
            └── comentario_privado.txt
```

---

## 📊 Formato JSON Generado

Cada evaluación contiene los campos obligatorios:

```json
{
  "apellido_nombre": "German Rodriguez",
  "actividad": "actividad 1",
  "nota": 7,
  "descripcion": "Cumple 4/6 criterios. Fortalezas: justificacion, contenido_minimo. Mejoras: estructura, temas_especificos.",
  "comentario_privado": "Estimado/a German Rodriguez,\n\n✓ Lo que hiciste bien: justificacion, contenido_minimo.\n\nPuntos a mejorar:\n- Organiza con introducción, desarrollo y conclusión\n- Profundiza en los temas específicos de la consigna\n\nPróximos pasos:\n1. Revisa la consigna nuevamente\n2. Aborda todos los aspectos solicitados\n3. Si tienes dudas, consulta en clase o escribe un comentario\n\n¡Sigue adelante!"
}
```

---

## 📈 Planilla Excel

### Características:

- **Hoja "Resumen"**: Estadísticas generales por materia
- **Hojas por Materia**: Cada actividad tiene su propia hoja
- **Código de Colores**:
  - 🟢 **Verde**: Nota ≥ 8 (Excelente)
  - 🟡 **Amarillo**: Nota 6-7 (Aprobado)
  - 🔴 **Rojo**: Nota < 6 (Requiere mejora)

### Columnas:
1. **Apellido y Nombre** - Nombre del alumno
2. **Actividad** - TP/Actividad evaluada
3. **Nota (1-10)** - Calificación numérica
4. **Descripción Técnica** - Resumen de cumplimiento de criterios
5. **Comentario Pedagógico** - Feedback detallado para el alumno

---

## 🔧 Criterios de Evaluación

El sistema evalúa automáticamente:

- ✓ **Infografía**: Presencia de elementos visuales
- ✓ **Justificación**: Explicación de decisiones
- ✓ **Temas Específicos**: Cobertura de tópicos requeridos
- ✓ **Presentación**: Exposición clara
- ✓ **Contenido Mínimo**: Extensión adecuada
- ✓ **Estructura**: Introducción, desarrollo, conclusión

**Escala de Notas:**
- 10: 90-100% criterios cumplidos
- 9: 80-89%
- 8: 70-79%
- 7: 60-69%
- 6: 50-59%
- 5-1: Menos del 50%

---

## 🎯 Casos Especiales

### Entrega con Problemas Técnicos
- Archivo no legible, PDF escaneado, imagen no procesable
- **Nota automática**: 2
- **Comentario**: Solicita re-entrega en formato editable

### Entrega Vacía o Incompleta
- Contenido mínimo no alcanzado
- **Nota automática**: 1
- **Comentario**: Solicita completar el trabajo

### Entrega Válida
- El sistema analiza criterios vs consigna
- Genera nota y feedback pedagógico personalizado

---

## 📝 Personalización

Si necesitas agregar nuevos criterios, edita la función `_extraer_criterios_consigna()` en `procesamiento_completo.py`:

```python
def _extraer_criterios_consigna(self, consigna):
    return {
        "tu_criterio": "palabra_clave" in consigna.lower(),
        # Agrega más aquí...
    }
```

---

## 🐛 Solución de Problemas

### "ModuleNotFoundError: No module named 'openpyxl'"
```bash
pip install openpyxl
```

### "ModuleNotFoundError: No module named 'docx'"
```bash
pip install python-docx
```

### El JSON está vacío
- Verifica que exista `consigna_referencia.txt` en la carpeta de actividad
- Comprueba que haya al menos una subcarpeta de estudiante

### Excel generado pero sin datos
- Asegúrate de que existe `evaluaciones_masivas.json`
- Verifica que el JSON tenga el formato correcto

---

## 🔄 Flujo Completo

```
1. Lee consigna_referencia.txt
   ↓
2. Para cada estudiante:
   → Lee entrega (.docx)
   → Compara con consigna
   → Extrae criterios
   → Asigna nota (1-10)
   → Genera comentario pedagógico
   ↓
3. Guardaen JSON (evaluaciones_masivas.json)
   ↓
4. Convierte a Excel por materia
   ↓
5. Agrega hoja de Resumen con estadísticas
```

---

## 📞 Soporte

Si tienes problemas o necesitas modificaciones, verifica:
- Rutas de carpetas (deben existir)
- Formato de archivos (.docx, .txt, .json)
- Permisos de lectura/escritura

---

**Última actualización**: 12/06/2026
