"""
Script de exploración de entregas reales en Google Classroom.
Muestra materias, actividades y contenido de entregas.
"""
import sys, os, io, json
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from main import (
    obtener_credenciales,
    listar_materias_activas,
    listar_trabajos_del_curso,
    listar_alumnos_por_actividad,
    descargar_adjunto_drive,
    extraer_texto_de_docx,
    _obtener_drive_file_desde_attachment,
)
from googleapiclient.discovery import build

def ver_texto_entrega(adjuntos, service_drive):
    """Intenta extraer texto de hasta 2 adjuntos."""
    textos = []
    for adj in adjuntos[:2]:
        drive_file = _obtener_drive_file_desde_attachment(adj)
        if not drive_file:
            # intentar link externo
            link = adj.get("link", {})
            if link:
                textos.append(f"[LINK EXTERNO] {link.get('url', '')}")
            form = adj.get("form", {})
            if form:
                textos.append(f"[FORMULARIO] {form.get('title', '')} — {form.get('formUrl', '')}")
            youtubeVideo = adj.get("youTubeVideo", {})
            if youtubeVideo:
                textos.append(f"[YOUTUBE] {youtubeVideo.get('title', '')} — {youtubeVideo.get('alternateLink', '')}")
            continue

        file_id    = drive_file.get("id")
        file_title = drive_file.get("title", "sin_nombre")
        try:
            meta      = service_drive.files().get(fileId=file_id, fields="mimeType,name,size").execute()
            mime_type = meta.get("mimeType", "")
            size_bytes = int(meta.get("size", 0) or 0)
        except Exception:
            mime_type  = ""
            size_bytes = 0

        tipo = mime_type.split("/")[-1].replace("vnd.google-apps.", "Google ")
        textos.append(f"[ARCHIVO] {file_title}  ({tipo}, {size_bytes//1024} KB)")

        # Intentar leer contenido
        contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
        if contenido:
            nombre_l = file_title.lower()
            if nombre_l.endswith(".docx") or "document" in mime_type:
                texto = extraer_texto_de_docx(contenido)
                if texto and not texto.startswith("[Error"):
                    textos.append("  CONTENIDO (primeros 500 chars):\n  " + texto[:500].replace("\n", "\n  "))
            elif nombre_l.endswith(".txt"):
                try:
                    textos.append("  CONTENIDO TXT:\n  " + contenido.decode("utf-8", errors="ignore")[:500])
                except Exception:
                    pass
            elif nombre_l.endswith(".pdf"):
                textos.append(f"  [PDF — {len(contenido)//1024} KB, no se puede leer texto directamente]")
    return textos


def main():
    print("\n" + "="*70)
    print("  EXPLORADOR DE ENTREGAS — Google Classroom")
    print("="*70)

    print("\n🔐 Autenticando...")
    creds         = obtener_credenciales()
    service       = build("classroom", "v1", credentials=creds)
    service_drive = build("drive",     "v3", credentials=creds)
    print("   ✅ Autenticado\n")

    # Listar materias
    cursos = listar_materias_activas(service)
    if not cursos:
        print("❌ Sin materias activas.")
        return

    print("📚 MATERIAS ACTIVAS:")
    for i, c in enumerate(cursos, 1):
        print(f"  [{i}] {c['name']}")

    try:
        idx_c = int(input("\nElegí número de materia: ").strip()) - 1
        curso = cursos[idx_c]
    except (ValueError, IndexError):
        print("❌ Opción inválida.")
        return

    course_id    = curso["id"]
    nombre_curso = curso["name"]
    print(f"\n✅ Materia: {nombre_curso}")

    # Listar actividades
    trabajos = listar_trabajos_del_curso(service, course_id)
    if not trabajos:
        print("❌ Sin actividades.")
        return

    print(f"\n📝 ACTIVIDADES ({len(trabajos)}):")
    for i, t in enumerate(trabajos, 1):
        pts = t.get("maxPoints", "?")
        estado = t.get("state", "?")
        print(f"  [{i:>2}] {t.get('title','?'):<55} /{pts}  [{estado}]")

    try:
        idx_t = int(input("\nElegí número de actividad: ").strip()) - 1
        trabajo = trabajos[idx_t]
    except (ValueError, IndexError):
        print("❌ Opción inválida.")
        return

    work_id        = trabajo["id"]
    titulo_trabajo = trabajo.get("title", "?")
    max_points     = trabajo.get("maxPoints", 100)
    print(f"\n✅ Actividad: {titulo_trabajo}  (/{max_points} pts)")

    # Listar entregas
    print("\n👥 Obteniendo entregas...")
    alumnos = listar_alumnos_por_actividad(service, course_id, work_id)

    if not alumnos:
        print("❌ Sin entregas.")
        return

    print(f"\n{'─'*70}")
    print(f"  {'#':<4} {'Alumno':<35} {'Estado':<20} {'Adjuntos'}")
    print(f"{'─'*70}")
    for i, a in enumerate(alumnos, 1):
        n_adj = len(a.get("attachments", []) or [])
        estado = a.get("estado", "?")
        link   = "✓ link" if a.get("alternate_link") else ""
        print(f"  {i:<4} {a.get('nombre','?'):<35} {estado:<20} {n_adj} adj  {link}")
    print(f"{'─'*70}")
    print(f"  Total: {len(alumnos)} alumno(s)\n")

    # Ver entrega de un alumno
    resp = input("¿Querés ver el contenido de alguna entrega? (número o Enter para saltar): ").strip()
    if resp.isdigit():
        idx_a = int(resp) - 1
        if 0 <= idx_a < len(alumnos):
            alumno = alumnos[idx_a]
            nombre = alumno.get("nombre", "?")
            adj    = alumno.get("attachments", []) or []

            print(f"\n{'='*70}")
            print(f"  ENTREGA DE: {nombre}")
            print(f"{'='*70}")
            print(f"  Estado Classroom : {alumno.get('estado','?')}")
            print(f"  submission_id    : {alumno.get('submission_id','?')}")
            print(f"  alternate_link   : {alumno.get('alternate_link','?')}")
            print(f"  Adjuntos         : {len(adj)}")

            if adj:
                print(f"\n  Adjuntos crudos (primer adjunto):")
                print(f"  {json.dumps(adj[0], indent=4, ensure_ascii=False, default=str)}")

                print(f"\n  Extrayendo contenido...")
                textos = ver_texto_entrega(adj, service_drive)
                for linea in textos:
                    print(f"\n  {linea}")
            else:
                print("\n  ⚠️  Sin adjuntos en esta entrega.")
                # Ver submissionHistory
                try:
                    raw = service.courses().courseWork().studentSubmissions().get(
                        courseId=course_id,
                        courseWorkId=work_id,
                        id=alumno["submission_id"]
                    ).execute()
                    history = raw.get("submissionHistory", [])
                    print(f"  submissionHistory: {len(history)} entradas")
                    for h in history[-2:]:
                        print(f"    {json.dumps(h, indent=6, ensure_ascii=False, default=str)[:400]}")
                except Exception as e:
                    print(f"  Error obteniendo raw: {e}")

    print("\n✅ Exploración completada.")


if __name__ == "__main__":
    main()
