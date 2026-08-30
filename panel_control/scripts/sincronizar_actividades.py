"""Descarga UNA VEZ, para todas las materias, la lista de actividades de
Classroom junto con su enunciado completo (extraído de los adjuntos de
Drive si hace falta) y las guarda en panel.db. Después de correr esto, el
dashboard lee todo directo de la base — no hace falta apretar ningún botón
de "Cargar actividades" por materia ni volver a pedirle nada a Classroom.

Mayormente no usa IA — es API de Classroom/Drive (cuota generosa, sin
riesgo real de agotarla). La única excepción: si un PDF adjunto es un
escaneo sin capa de texto (no un PDF digital), main.obtener_contexto_consigna
cae a un fallback que sí manda esa página a Gemini para leerla — poco
frecuente, pero consume la misma cuota diaria de Gemini que
recursos_educativos. Para la búsqueda de bibliografía/videos/manuales con
IA (que sí depende de esa cuota), ver
panel_control/scripts/buscar_recursos_bulk.py — este script solo deja
encoladas las tareas nuevas para que ese otro las procese.

Se puede volver a correr cuando se agreguen actividades nuevas: es
idempotente (actualiza por work_id, no duplica).

Uso: python -m panel_control.scripts.sincronizar_actividades
"""
from googleapiclient.discovery import build

import main as classroom
from panel_control import memoria

TIPOS_PARA_RECURSOS = ("ASSIGNMENT",)


def sincronizar_una_materia(service, service_drive, nombre_curso: str, course_id: str) -> int:
    """Trae todas las actividades de UNA materia (con enunciado) y las
    cachea en la base. Devuelve cuántas se guardaron. La reutiliza tanto la
    sincronización completa de acá abajo como el botón de refresco puntual
    del dashboard."""
    trabajos = classroom.listar_trabajos_del_curso(service, course_id)
    for t in trabajos:
        work_id, titulo = t["id"], t.get("title", "Sin título")
        try:
            enunciado = classroom.obtener_contexto_consigna(service, service_drive, course_id, work_id, t)
        except Exception:
            enunciado = None
        memoria.guardar_actividad_cache(
            work_id=work_id, course_id=course_id, materia=nombre_curso, titulo=titulo,
            tipo=t.get("workType"), materials=t.get("materials"), enunciado=enunciado,
        )
        if t.get("workType") in TIPOS_PARA_RECURSOS:
            memoria.encolar_recursos_bulk(work_id, nombre_curso, titulo)
    return len(trabajos)


def sincronizar():
    memoria.init_db()
    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)
    service_drive = build("drive", "v3", credentials=creds)

    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        print("No se encontraron materias activas en Classroom.")
        return

    total_actividades = 0
    for curso in cursos:
        nombre_curso, course_id = curso["name"], curso["id"]
        print(f"\n📚 {nombre_curso}...", end=" ", flush=True)
        cantidad = sincronizar_una_materia(service, service_drive, nombre_curso, course_id)
        total_actividades += cantidad
        print(f"{cantidad} actividad(es) ✅")

    print(f"\n{total_actividades} actividad(es) guardadas en la base (con enunciado incluido).")
    pendientes = memoria.contar_pendientes_recursos_bulk()
    print(f"{pendientes} tarea(s) en cola para buscar bibliografía/videos/manuales con IA "
          f"(correr: python -m panel_control.scripts.buscar_recursos_bulk).")


if __name__ == "__main__":
    sincronizar()
