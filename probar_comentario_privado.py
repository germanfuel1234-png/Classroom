import argparse
import json
import os
import sys
import time
import webbrowser
from typing import Dict, List, Optional, Tuple

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = "classroom_nuevo.json"
TOKEN_FILE = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
]


def obtener_credenciales() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds.has_scopes(SCOPES):
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"No se encontró {CREDENTIALS_FILE}."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, prompt="select_account")
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def normalizar(s: str) -> str:
    return " ".join((s or "").lower().strip().split())


def buscar_curso_por_nombre(service, nombre_objetivo: str) -> Optional[Dict]:
    cursos = service.courses().list(courseStates="ACTIVE").execute().get("courses", [])
    n_obj = normalizar(nombre_objetivo)

    # 1) match exacto normalizado
    for c in cursos:
        if normalizar(c.get("name", "")) == n_obj:
            return c

    # 2) match por contiene
    for c in cursos:
        if n_obj in normalizar(c.get("name", "")):
            return c

    return None


def buscar_actividad_por_titulo(service, course_id: str, titulo_objetivo: str) -> Optional[Dict]:
    trabajos: List[Dict] = []
    token = None
    while True:
        resp = service.courses().courseWork().list(courseId=course_id, pageToken=token, pageSize=100).execute()
        trabajos.extend(resp.get("courseWork", []))
        token = resp.get("nextPageToken")
        if not token:
            break

    t_obj = normalizar(titulo_objetivo)

    for t in trabajos:
        if normalizar(t.get("title", "")) == t_obj:
            return t

    for t in trabajos:
        if t_obj in normalizar(t.get("title", "")):
            return t

    return None


def obtener_mapa_alumnos(service, course_id: str) -> Dict[str, str]:
    alumnos = []
    token = None
    while True:
        resp = service.courses().students().list(courseId=course_id, pageToken=token, pageSize=100).execute()
        alumnos.extend(resp.get("students", []))
        token = resp.get("nextPageToken")
        if not token:
            break

    out = {}
    for a in alumnos:
        uid = a.get("userId")
        nombre = a.get("profile", {}).get("name", {}).get("fullName", "")
        if uid:
            out[uid] = nombre
    return out


def buscar_submission_alumno(service, course_id: str, work_id: str, nombre_alumno: str) -> Tuple[Optional[Dict], Dict[str, str]]:
    mapa_alumnos = obtener_mapa_alumnos(service, course_id)
    token = None
    submissions = []
    while True:
        resp = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=work_id,
            pageToken=token,
            pageSize=100,
        ).execute()
        submissions.extend(resp.get("studentSubmissions", []))
        token = resp.get("nextPageToken")
        if not token:
            break

    objetivo_tokens = set(normalizar(nombre_alumno).split())
    for sub in submissions:
        uid = sub.get("userId")
        nom = normalizar(mapa_alumnos.get(uid, ""))
        tokens_nom = set(nom.split())
        if objetivo_tokens.issubset(tokens_nom):
            return sub, mapa_alumnos

    return None, mapa_alumnos


def probar_post_comentario_rest(creds: Credentials, course_id: str, work_id: str, submission_id: str, texto: str) -> Tuple[int, str]:
    session = AuthorizedSession(creds)
    url = (
        f"https://classroom.googleapis.com/v1/courses/{course_id}"
        f"/courseWork/{work_id}/studentSubmissions/{submission_id}/comments"
    )

    resp = session.post(url, json={"text": texto}, timeout=30)
    try:
        body = resp.text
    except Exception:
        body = ""
    return resp.status_code, body


def copiar_portapapeles(texto: str) -> bool:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(texto)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba aislada de comentario privado en Classroom")
    parser.add_argument("--materia", default="Sist. Operativos")
    parser.add_argument("--actividad", default="Trabajo Practico Numero 6.-Rol")
    parser.add_argument("--alumno", default="rodriguez german")
    parser.add_argument("--comentario", default="Comentario de prueba desde script aislado.")
    args = parser.parse_args()

    print("[1/6] Autenticando...")
    creds = obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)

    print(f"[2/6] Buscando curso: {args.materia}")
    curso = buscar_curso_por_nombre(service, args.materia)
    if not curso:
        print("❌ No se encontró la materia.")
        return 1
    course_id = curso.get("id")
    print(f"   ✅ Curso: {curso.get('name')} (id={course_id})")

    print(f"[3/6] Buscando actividad: {args.actividad}")
    actividad = buscar_actividad_por_titulo(service, course_id, args.actividad)
    if not actividad:
        print("❌ No se encontró la actividad.")
        return 1
    work_id = actividad.get("id")
    print(f"   ✅ Actividad: {actividad.get('title')} (id={work_id})")

    print(f"[4/6] Buscando submission de alumno: {args.alumno}")
    submission, mapa = buscar_submission_alumno(service, course_id, work_id, args.alumno)
    if not submission:
        print("❌ No se encontró submission del alumno en esa actividad.")
        print("   Alumnos detectados en el curso:")
        for uid, nombre in sorted(mapa.items(), key=lambda x: normalizar(x[1])):
            print(f"   - {nombre} ({uid})")
        return 1

    submission_id = submission.get("id")
    user_id = submission.get("userId")
    nom_real = mapa.get(user_id, "Desconocido")
    print(f"   ✅ Alumno: {nom_real} (userId={user_id}, submissionId={submission_id})")

    print("[5/6] Probando POST REST de comentario privado...")
    code, body = probar_post_comentario_rest(creds, course_id, work_id, submission_id, args.comentario)

    debug = {
        "curso": {"id": course_id, "name": curso.get("name")},
        "actividad": {"id": work_id, "title": actividad.get("title")},
        "alumno": {"userId": user_id, "name": nom_real, "submissionId": submission_id},
        "http_status": code,
        "response": body[:4000],
    }
    with open("debug_comentario_privado.json", "w", encoding="utf-8") as f:
        json.dump(debug, f, ensure_ascii=False, indent=2)

    print(f"[6/6] HTTP status: {code}")
    if 200 <= code < 300:
        print("✅ Comentario enviado por API.")
        print("Se guardó detalle en debug_comentario_privado.json")
        return 0

    print("❌ No se pudo enviar comentario por API.")
    print("Revisá debug_comentario_privado.json para ver el mensaje exacto de Classroom.")

    alternate_link = submission.get("alternateLink", "")
    if alternate_link:
        print("\n🧩 Fallback manual:")
        if copiar_portapapeles(args.comentario):
            print("✅ Comentario copiado al portapapeles.")
        else:
            print("⚠️ No se pudo copiar al portapapeles; copialo manualmente desde la consola.")
            print("-" * 40)
            print(args.comentario)
            print("-" * 40)

        print(f"🌐 Abriendo Classroom en: {alternate_link}")
        try:
            webbrowser.open(alternate_link)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ No se pudo abrir el navegador: {e}")

        print("\nPegalo en Comentarios privados y publicalo manualmente.")

    return 2


if __name__ == "__main__":
    sys.exit(main())
