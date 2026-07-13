#!/usr/bin/env python3
"""
Script para renovar el token OAuth con la cuenta del profesor.

Qué hace:
1. Borra token.json viejo (fuerza re-autenticación)
2. Ejecuta main.py que abre navegador pidiendo seleccionar cuenta
3. Selecciona automaticamente germanrodriguezciclo2026@gmail.com
4. Autoriza y guarda nuevo token.json

⚠️ IMPORTANTE: 
   - Asegúrate de tener Chrome abierto con la cuenta del profesor
   - O deja que se abra una pestaña nueva automáticamente
"""

import os
import sys
import subprocess

def renovar_token():
    """Borra token viejo y ejecuta main.py para obtener uno nuevo."""
    
    token_file = "token.json"
    
    print("=" * 70)
    print("🔐 RENOVAR TOKEN OAUTH")
    print("=" * 70)
    
    # Paso 1: Borrar token viejo
    if os.path.exists(token_file):
        print(f"\n[1/3] Borrando token viejo: {token_file}")
        try:
            os.remove(token_file)
            print(f"      ✅ Borrado exitosamente")
        except Exception as e:
            print(f"      ❌ Error al borrar: {e}")
            sys.exit(1)
    else:
        print(f"\n[1/3] No hay token viejo (primera ejecución)")
    
    # Paso 2: Informar al usuario
    print(f"\n[2/3] 📌 INSTRUCCIONES:")
    print(f"      • Se abrirá un navegador solicitando seleccionar cuenta")
    print(f"      • Selecciona: germanrodriguezciclo2026@gmail.com")
    print(f"      • Autoriza todos los permisos")
    print(f"      • NO cierres el navegador después (mantén sesión abierta)")
    print(f"      • El token guardado válido durará meses")
    
    # Paso 3: Ejecutar main.py (solo el módulo de autenticación)
    print(f"\n[3/3] Abriendo navegador para autenticación...")
    print("      Presiona Enter para continuar...")
    input()
    
    # Ejecutar Python con el módulo que trae la autenticación
    try:
        # Importar y ejecutar la función de obtener credenciales
        sys.path.insert(0, os.getcwd())
        from main import obtener_credenciales
        
        print("\n⏳ Iniciando flujo OAuth...\n")
        creds = obtener_credenciales()
        
        if creds:
            print("\n" + "=" * 70)
            print("✅ ÉXITO: Token renovado correctamente")
            print("=" * 70)
            print(f"📝 Token guardado en: token.json")
            print(f"   Email autenticado: germanrodriguezciclo2026@gmail.com")
            print(f"   Validez: ~6 meses (o hasta que cambies contraseña)")
            print(f"\n🚀 Ahora puedes ejecutar main.py normalmente:")
            print(f"   python main.py")
            print("=" * 70)
        else:
            print("❌ Error: No se pudo obtener credenciales")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error durante autenticación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    renovar_token()
