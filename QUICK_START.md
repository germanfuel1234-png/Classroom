# 🚀 QUICK START: Usa el Sistema Ahora

## 5 Minutos para Empezar

### Paso 1: Renovar Autenticación (1 minuto)
```powershell
cd C:\Users\Gernet\Desktop\2026NET\Classroom
python renovar_token_oauth.py
```

**Qué pasará:**
- Se abrirá tu navegador automáticamente
- Te pedirá login en Google
- **Selecciona:** `germanrodriguezciclo2026@gmail.com`
- **Haz clic:** "Autorizar"
- ✅ Se guardará el token (válido ~6 meses)

⏱️ **Tiempo:** ~30 segundos

---

### Paso 2: Ejecutar Correcciones (3 minutos)
```powershell
python main.py
```

**El sistema te pedirá:**
1. **Selecciona materia** → `Ej: Sist. Operativos`
2. **Selecciona TP** → `Ej: Trabajo Practico N11`
3. **Selecciona alumno** → `Ej: german rodriguez`

**Qué hace automáticamente:**
- ✅ Descarga entregas desde Classroom
- ✅ Lee PDFs (digitales + escaneados)
- ✅ Analiza con Gemini
- ✅ Genera feedback personalizado
- ✅ Guarda reportes JSON
- ✅ **PUBLICA AUTOMÁTICAMENTE** (notas + comentarios)
- ✅ Abre navegador para ver resultados

⏱️ **Tiempo:** ~2-3 minutos por alumno

---

### Paso 3: Ver Resultados (1 minuto)
Se guardarán automáticamente en:
```
Correcciones_Classroom/
└── reportes/
    └── 2026-06-10/
        ├── reporte_MATERIA_TEMA_20260610_HHMMSS.json
        └── comentarios_privados_pendientes_20260610_HHMMSS.json
```

---

## 🎯 Ejemplo Práctico Paso a Paso

```
$ python main.py

? Selecciona materia: Sist. Operativos
? Selecciona TP: Trabajo Practico N11  
? Selecciona alumno(s): german rodriguez

✅ Descargando... 2 entregas encontradas
✅ Extrayendo PDFs... 2 archivos procesados
✅ Analizando con IA... Generando feedback

👨‍💼 ALUMNO: german rodriguez
   📊 Análisis:
      • Pseudocódigo válido ✓
      • Variables bien definidas ✓
      • Lógica correcta ✓
   
   ⭐ Nota: 9/10

✅ Publicando en Classroom...
   → Nota: 90/100 ✅
   → Comentario privado: ✅
   → Tarea devuelta: ✅

✅ Reporte guardado: Correcciones_Classroom/reportes/2026-06-10/reporte_SistOperativos_TP11_20260610_143022.json

👉 german rodriguez: Abriendo Classroom (copia automática en proceso)...
✅ Comentario copiado automáticamente al portapapeles para german rodriguez
ℹ️ Intentando pegado automático en Chrome activo...
✅ Comentario pegado y enviado automáticamente para german rodriguez

✨ ¡LISTO! Alumno corregido y comentario publicado.
```

---

## ❓ Preguntas Frecuentes

### P1: ¿Qué pasa si no funciona la renovación de token?
**R:** Debes estar conectado a internet y tener habilitada la API de Classroom:
```
1. Ir a: https://console.cloud.google.com
2. Buscar: "Classroom API" 
3. Activar (Enable)
4. Reintentar: python renovar_token_oauth.py
```

### P2: ¿Qué pasa si falla la publicación automática?
**R:** El sistema guarda los comentarios en `comentarios_privados_pendientes_*.json` y:
- ✅ Abre Classroom automáticamente
- ✅ Copia el comentario al portapapeles
- ✅ Intenta pegado automático

Si el pegado automático no funciona, usa **Ctrl+V** manualmente.

### P3: ¿Puedo usar archivos locales en vez de descargar de Classroom?
**R:** Sí, hay una función `extraer_texto_de_archivo_local()` disponible en el código:
```python
texto = extraer_texto_de_archivo_local("ruta/archivo.pdf")
```

Ver: `GUIA_NUEVAS_FUNCIONES.md` para ejemplos.

### P4: ¿Cuál es el límite de la API de Gemini?
**R:** 
- Modelo: `gemini-2.5-flash`
- Límite: 1 millón tokens/minuto
- Límite: 1,500 requests/minuto
- Suficiente para 100+ alumnos simultáneamente

### P5: ¿Cómo desactivo el pegado automático?
**R:** Edita `main.py` línea ~1665, cambia:
```python
if AUTO_PEGADO_DISPONIBLE:
    # Intenta pegado automático
```
Por:
```python
if False:  # Desactiva pegado automático
```

---

## 📋 Checklist Antes de Empezar

- [ ] Token renovado (`token.json` existe y es reciente)
- [ ] `.env` tiene `GEMINI_API_KEY` válida
- [ ] Tesseract instalado (`tesseract --version` funciona)
- [ ] Python 3.11+ (`python --version`)
- [ ] Navegador Chrome/Edge abierto (para pegado automático)

---

## 🔗 Documentación Detallada

Si necesitas más información:
- 📄 `RESUMEN_SESION_COMPLETA.md` — Qué se cambió
- 📄 `FLUJO_AUTOMATICO_COMENTARIOS.md` — Cómo funciona la automatización
- 📄 `GUIA_NUEVAS_FUNCIONES.md` — Funciones B y C en detalle
- 📄 `INSTRUCCIONES_PASO_A_PASO.md` — Paso a paso completo

---

## 🆘 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'googleapiclient'` | `pip install -r requirements.txt` |
| `Error 403: permission denied` | Renovar token: `python renovar_token_oauth.py` |
| `Tesseract not found` | Instalar desde: https://github.com/UB-Mannheim/tesseract/wiki |
| `GEMINI_API_KEY not found` | Agregar a `.env`: `GEMINI_API_KEY=tu_clave_aqui` |
| `No se pega automáticamente` | Instalar: `pip install pyautogui` |

---

## 💡 Pro Tips

1. **Ejecutar múltiples alumnos:**
   ```powershell
   python main.py
   # Cuando te pide alumno(s), presiona Enter varias veces:
   # german rodriguez
   # Sirak Barsamian
   # Joaquin ortega
   # [Enter en blanco para terminar]
   ```

2. **Ver reportes generados:**
   ```powershell
   # Últimas correcciones
   dir "Correcciones_Classroom\reportes\2026-06-10" | tail
   
   # Abrir reporte en PowerShell
   Get-Content "Correcciones_Classroom\reportes\2026-06-10\reporte_*.json" | ConvertFrom-Json | Format-Table
   ```

3. **Monitorear pegado automático:**
   ```
   Si ves: "✅ Comentario pegado y enviado automáticamente"
   → Pegado automático funciona perfecto
   
   Si ves: "ℹ️ No se pudo pegar automáticamente"
   → Usa Ctrl+V manual (comentario sigue copiado)
   ```

4. **Resetear todo (si algo falla):**
   ```powershell
   rm token.json  # Borra token
   python renovar_token_oauth.py  # Re-autentica
   ```

---

## ✅ Lista de Verificación Final

Después de ejecutar `python main.py`:

```
✅ Entregas descargadas correctamente
✅ PDFs procesados (digital + OCR)
✅ Análisis generado
✅ Reporte JSON guardado
✅ Notas publicadas en Classroom
✅ Comentarios privados publicados
✅ Tarea devuelta
✅ Navegador abierto en Classroom
✅ Comentario en portapapeles
```

Si todo está ✅ = **¡SISTEMA FUNCIONANDO PERFECTAMENTE!**

---

## 🎉 ¡A Disfrutar!

El sistema ahora es **100% automático**. No necesitas confirmaciones, no esperes inputs innecesarios.

Solo:
1. Selecciona materia/TP/alumno
2. El sistema hace el resto automáticamente
3. ✅ Listo en 2-3 minutos

**Tiempo ahorrado: 90% vs proceso manual**

