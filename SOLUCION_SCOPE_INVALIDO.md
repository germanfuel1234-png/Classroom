# ⚡ Solución Rápida: Error 400 invalid_scope

## ❌ Problema
```
Error 400: invalid_scope
Some requested scopes were invalid. {invalid=[https://www.googleapis.com/auth/classroom.coursework.me.modify]}
```

## ✅ Solución Implementada

### 1️⃣ SCOPE Eliminado
El SCOPE `classroom.coursework.me.modify` **NO EXISTE** en Google Classroom API.

**YA NO ESTÁ** en `main.py` — Removido automáticamente ✅

Los SCOPES que tienes **YA PERMITEN** hacer patch() en calificaciones:
```python
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.topics.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",  # ← ESTE permite patch
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
```

### 2️⃣ Obtener Token NUEVO

```powershell
# Opción A: Script automático
python renovar_token_oauth.py

# Opción B: Manual
rm token.json
python main.py
# → Se abrirá navegador automáticamente pidiendo seleccionar cuenta
```

### 3️⃣ En el Navegador
1. Google preguntará: "Selecciona una cuenta"
2. **SELECCIONA:** `germanrodriguezciclo2026@gmail.com` (la del profesor)
3. Autoriza todos los permisos
4. **NO cierres el navegador** (mantén la sesión abierta)

### 4️⃣ Verificar Token
```powershell
# Confirmar que token.json existe
ls token.json
```

---

## 🎯 Flujo Simplificado

```
❌ Error "invalid_scope"
    ↓
✅ SCOPE removido de main.py
    ↓
🚀 Ejecutar: python renovar_token_oauth.py
    ↓
🌐 Navegador abre automáticamente
    ↓
✅ Selecciona cuenta del profesor
    ↓
✅ Autoriza permisos
    ↓
💾 Token guardado: token.json
    ↓
✅ LISTO para usar main.py
```

---

## 🔍 Por qué tu solución es correcta

> "una de las formas que encontre para evadir esta parte fue abrir un navegador con la cuenta que es la de profe para que me valide el token. y nunca lo cierro"

**Exacto.** Eso es la solución correcta porque:

1. **`prompt="select_account"`** → Fuerza seleccionar cuenta (no usa la predeterminada)
2. **`login_hint=EXPECTED_OAUTH_EMAIL`** → Preselecciona el email del profesor
3. **`open_browser=True`** → Abre navegador con la URL de autenticación
4. **Mantener sesión abierta** → Token válido ~6 meses sin volver a autenticar

---

## 📋 SCOPES Válidos para Classroom (Referencia)

| SCOPE | Uso |
|-------|-----|
| `classroom.courses.readonly` | Leer cursos |
| `classroom.coursework.students` | Leer/escribir calificaciones y entregas |
| `classroom.coursework.me` | Leer entregas propias |
| `classroom.announcements` | Anuncios |
| `classroom.rosters` | Listas de alumnos |
| `classroom.profile.emails` | Emails |
| `classroom.topics` | Temas del curso |

**❌ NO EXISTEN:** `classroom.coursework.me.modify`, `classroom.coursework.modify`, etc.

---

## 🚀 Próximos Pasos

1. ✅ Ejecuta: `python renovar_token_oauth.py`
2. ✅ Selecciona cuenta del profesor en navegador
3. ✅ Mantén el navegador abierto (o la sesión activa)
4. ✅ Verifica que `token.json` se creó
5. 🚀 Ejecuta correcciones: `python main.py`

---

## 📞 Si aún hay error

Si aparece otro error:

```powershell
# 1. Borra token viejo
rm token.json

# 2. Borra el cache de Chrome
# Settings → Privacy → Clear browsing data

# 3. Vuelve a ejecutar
python renovar_token_oauth.py
```
