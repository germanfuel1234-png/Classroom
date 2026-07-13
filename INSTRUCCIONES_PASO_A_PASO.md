# 🔧 Instrucciones Paso a Paso: Fijar Error 400 invalid_scope

## Estado Actual ✅
- ❌ SCOPE inválido removido de main.py
- ✅ token.json borrado (para forzar re-autenticación)
- ✅ Script `renovar_token_oauth.py` creado
- ✅ Función `obtener_credenciales()` mejorada con mensajes claros

---

## Opción 1: RÁPIDA (Recomendado) ⭐

### Paso 1: Ejecutar script de renovación
```powershell
python renovar_token_oauth.py
```

### Paso 2: Seguir instrucciones en pantalla
Verás:
```
🔐 RENOVAR TOKEN OAUTH
================================================================================
[1/3] Token.json no existe (primera ejecución)
[2/3] 📌 INSTRUCCIONES:
      • Se abrirá un navegador solicitando seleccionar cuenta
      • Selecciona: germanrodriguezciclo2026@gmail.com
      • Autoriza todos los permisos
      • NO cierres el navegador después (mantén sesión abierta)
      • El token guardado válido durará meses
[3/3] Abriendo navegador para autenticación...
      Presiona Enter para continuar...
```

### Paso 3: Presiona Enter

Se abrirá el navegador con pantalla de selección de cuenta:

```
Google
┌─────────────────────────────────────┐
│  Selecciona tu cuenta               │
├─────────────────────────────────────┤
│                                     │
│  ☐ germanrodriguezciclo2026@gmail   │ ← HACECLICK AQUÍ
│                                     │
│  ☐ Otra cuenta                      │
│                                     │
└─────────────────────────────────────┘
```

### Paso 4: Selecciona la cuenta del profesor
Haz clic en: `germanrodriguezciclo2026@gmail.com`

### Paso 5: Autoriza los permisos
Google pide aprobación de permisos. Haz clic en: `"Permitir"` o `"Autorizar"`

### Paso 6: Espera confirmación en terminal
Verás:
```
✅ ÉXITO: Token renovado correctamente
================================================================================
📝 Token guardado en: token.json
   Email autenticado: germanrodriguezciclo2026@gmail.com
   Validez: ~6 meses (o hasta que cambies contraseña)

🚀 Ahora puedes ejecutar main.py normalmente:
   python main.py
```

### Paso 7: ¡LISTO!
Token renovado. Ahora puedes ejecutar:
```powershell
python main.py
```

---

## Opción 2: MANUAL

Si prefieres hacer todo manualmente:

### Paso 1: Borra token
```powershell
rm token.json
```

### Paso 2: Ejecuta main.py
```powershell
python main.py
```

### Paso 3: El script abrirá navegador automáticamente
Se abrirá pediendo seleccionar cuenta.

### Paso 4: Sigue pasos 4-6 de Opción 1

---

## 🔍 Qué hace el código internamente

```python
# En main.py → obtener_credenciales()

flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
creds = flow.run_local_server(
    port=0,
    prompt="select_account",           # ← Fuerza seleccionar cuenta (no usa default)
    login_hint=EXPECTED_OAUTH_EMAIL,   # ← Preselecciona: germanrodriguezciclo2026@gmail.com
    open_browser=True,                 # ← Abre navegador automáticamente
)
```

---

## ✅ Verificación

Después de ejecutar el script, verifica que token.json existe:

```powershell
ls token.json
```

Deberías ver:
```
    Directorio: C:\Users\Gernet\Desktop\2026NET\Classroom

Modo                 LastWriteTime         Length Name
----                 -------               ------ ----
-a---           6/10/2026 19:45           1234   token.json  ← ✅ CREADO
```

---

## ⚠️ Si aparece error OTRA VEZ

### Error: "invalid_scope"
→ El token.json aún tiene el SCOPE viejo
→ Solución: Borra token.json y repite Opción 1

### Error: "El navegador no abre"
→ Chrome no está en PATH
→ Solución manual:
```powershell
# Abre Chrome manualmente con esta URL
# (El script mostrará la URL a copiar)
```

### Error: "Selecciona mi otra cuenta, no la del profesor"
→ Borra cookies/caché de Chrome
→ Chrome → Settings → Privacy → Clear browsing data
→ Repite Opción 1

---

## 📝 Notas Importantes

1. **No cierres el navegador:** El token durará ~6 meses con sesión activa
2. **Email del profesor:** Siempre debe ser `germanrodriguezciclo2026@gmail.com`
3. **SCOPE válido:** `classroom.coursework.students` permite escribir calificaciones
4. **Token.json:** Nunca lo compartas (contiene credenciales sensibles)

---

## 🚀 Próximos Pasos Después de Esto

Una vez que tengas token.json renovado:

```powershell
# 1. Prueba que funciona
python main.py

# 2. Selecciona una materia y TP
# 3. Las correcciones se publicarán automáticamente con nota + comentario + devolución
```

---

## 📞 Ayuda Rápida

| Problema | Solución |
|----------|----------|
| "Error 400: invalid_scope" | ✅ YA SOLUCIONADO (SCOPE removido) |
| No abre navegador | `python renovar_token_oauth.py` |
| Selecciona cuenta equivocada | Borra `token.json` y repite |
| Error "ProjectPermissionDenied" | Token tiene permisos insuficientes (repite paso de autorización) |

