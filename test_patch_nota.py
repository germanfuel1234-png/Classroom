#!/usr/bin/env python3
"""
Script de diagnóstico: Intenta hacer SOLO patch(draftGrade) en una entrega.
Objetivo: Aislar si el problema es el permiso del proyecto OAuth o la configuración.
"""

import os
import sys
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

CREDENTIALS_FILE = "classroom_nuevo.json"
TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/classroom.coursework.students",
]


def obtener_credenciales_simples():
    """Obtiene credenciales usando el token.json existente."""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ No se encontró {TOKEN_FILE}")
        return None

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.valid:
            print(f"✅ Token válido cargado desde {TOKEN_FILE}")
            return creds
        else:
            print("❌ Token inválido o expirado")
            return None
    except Exception as e:
        print(f"❌ Error cargando token: {e}")
        return None


def listar_entregas_de_prueba(service, course_id, work_id):
    """Obtiene la primera entrega de un TP para hacer prueba de patch."""
    try:
        print(f"\n🔍 Buscando entregas en curso {course_id}, TP {work_id}...")
        respuesta = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=work_id,
            pageSize=5,
        ).execute()

        entregas = respuesta.get("studentSubmissions", [])
        if not entregas:
            print("⚠️ No hay entregas para este TP.")
            return None

        print(f"✅ Se encontraron {len(entregas)} entrega(s).")
        return entregas[0]
    except Exception as e:
        print(f"❌ Error listando entregas: {e}")
        return None


def intentar_patch_draftgrade(service, course_id, work_id, submission_id, nota_100=75):
    """Intenta hacer patch(draftGrade) en una entrega."""
    print(f"\n📝 Intentando patch(draftGrade={nota_100}) en entrega {submission_id}...")

    try:
        respuesta = service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=work_id,
            id=submission_id,
            updateMask="draftGrade",
            body={"draftGrade": nota_100},
        ).execute()

        print(f"✅ ¡ÉXITO! Patch ejecutado sin errores.")
        print(f"   Response: {respuesta}")
        return True

    except HttpError as e:
        status = e.resp.status
        error_msg = str(e)
        print(f"❌ HttpError {status}: {error_msg[:200]}")

        if status == 403:
            print("\n📋 DIAGNÓSTICO 403:")
            print("   - El proyecto OAuth NO tiene permisos de escritura en Classroom.")
            print("   - Classroom API puede NO estar habilitada en Google Cloud.")
            print("   - La app OAuth puede estar en modo 'Testing' sin scopes de escritura autorizados.")
            print("   - O el usuario no tiene permisos suficientes en el curso.")

        return False

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def main():
    print("=" * 70)
    print("  DIAGNÓSTICO: Prueba de patch(draftGrade) en Classroom")
    print("=" * 70)

    # Paso 1: Obtener credenciales
    print("\n[PASO 1] Cargando credenciales...")
    creds = obtener_credenciales_simples()
    if not creds:
        print("❌ No se pudo cargar credenciales. Abortando.")
        return 1

    # Paso 2: Conectar a Classroom API
    print("\n[PASO 2] Conectando a Classroom API...")
    try:
        service = build("classroom", "v1", credentials=creds)
        print("✅ Classroom API conectada.")
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return 1

    # Paso 3: Obtener cursos activos
    print("\n[PASO 3] Listando cursos activos...")
    try:
        cursos_respuesta = service.courses().list(courseStates="ACTIVE", pageSize=5).execute()
        cursos = cursos_respuesta.get("courses", [])
        if not cursos:
            print("⚠️ No hay cursos activos disponibles.")
            return 1

        print(f"✅ Se encontraron {len(cursos)} curso(s):")
        for i, curso in enumerate(cursos, start=1):
            print(f"   [{i}] {curso['name']} (ID: {curso['id']})")

        # Seleccionar primer curso por defecto
        curso = cursos[0]
        course_id = curso["id"]
        print(f"\n   → Usando primer curso: {curso['name']}")

    except Exception as e:
        print(f"❌ Error listando cursos: {e}")
        return 1

    # Paso 4: Obtener TPs del curso
    print("\n[PASO 4] Listando trabajos prácticos del curso...")
    try:
        trabajos_respuesta = service.courses().courseWork().list(
            courseId=course_id,
            pageSize=5,
        ).execute()
        trabajos = trabajos_respuesta.get("courseWork", [])
        if not trabajos:
            print("⚠️ No hay trabajos prácticos en este curso.")
            return 1

        print(f"✅ Se encontraron {len(trabajos)} TP(s):")
        for i, tp in enumerate(trabajos, start=1):
            print(f"   [{i}] {tp['title']} (ID: {tp['id']})")

        # Seleccionar primer TP por defecto
        trabajo = trabajos[0]
        work_id = trabajo["id"]
        print(f"\n   → Usando primer TP: {trabajo['title']}")

    except Exception as e:
        print(f"❌ Error listando TPs: {e}")
        return 1

    # Paso 5: Obtener entregas del TP
    print("\n[PASO 5] Buscando entregas en el TP...")
    entrega = listar_entregas_de_prueba(service, course_id, work_id)
    if not entrega:
        print("❌ No hay entregas para probar.")
        return 1

    student_id = entrega.get("userId", "Desconocido")
    submission_id = entrega.get("id")
    print(f"   📌 Alumno: {student_id}")
    print(f"   📌 Entrega ID: {submission_id}")

    # PASO CRÍTICO 6: Intentar patch
    print("\n[PASO 6] Intentando patch(draftGrade=75)...")
    exito = intentar_patch_draftgrade(service, course_id, work_id, submission_id, nota_100=75)

    # Resumen final
    print("\n" + "=" * 70)
    if exito:
        print("✅ ÉXITO: El proyecto OAuth TIENE permisos de escritura en Classroom.")
        print("   El problema no es la configuración de Google Cloud.")
        print("   Verifica que el código esté usando el method correcto.")
    else:
        print("❌ FALLO: El proyecto OAuth NO tiene permisos de escritura en Classroom.")
        print("\n   SOLUCIÓN: En Google Cloud Console:")
        print("   1. Abrí: https://console.cloud.google.com/apis/library/classroom.googleapis.com")
        print("   2. Asegurate que Classroom API esté HABILITADA (azul)")
        print("   3. Vá a OAuth consent screen y revisá que tenga estos scopes:")
        print("      - classroom.coursework.students (lectura y escritura)")
        print("      - classroom.coursework.me (lectura)")
        print("   4. Si está en 'Testing', cambiá a 'Production' o agregá tu email como test user")
        print("   5. Publicá/Guardá la app")
        print("   6. Borrá token.json localmente")
        print("   7. Corrí renovar_token_oauth.py para reautenticar")
        print("=" * 70)
    return 0 if exito else 1


if __name__ == "__main__":
    sys.exit(main())
