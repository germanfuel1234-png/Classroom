"""Trae de Classroom, para cada materia activa, qué actividades hay
publicadas y cuántas entregas están calificadas vs pendientes.

Guarda el resultado en la base local (panel_control.memoria); el dashboard
solo LEE ese snapshot, nunca llama a la API de Classroom directamente
(así la página carga rápido y no depende de que el OAuth esté vivo en ese
momento). Corré este script cada vez que quieras refrescar los datos.

Uso: python -m panel_control.sync_materias
"""
from googleapiclient.discovery import build

import main as classroom  # reutiliza OAuth y listados ya probados
from panel_control import memoria


def _resumen_trabajo(service, course_id, trabajo):
    work_id = trabajo["id"]
    try:
        entregas = (
            service.courses().courseWork().studentSubmissions()
            .list(courseId=course_id, courseWorkId=work_id)
            .execute()
            .get("studentSubmissions", [])
        )
    except Exception as e:
        print(f"      ⚠️ No se pudieron leer entregas de '{trabajo.get('title')}': {str(e)[:100]}")
        entregas = []

    entregados = sum(1 for e in entregas if e.get("state") in ("TURNED_IN", "RETURNED"))
    calificados = sum(1 for e in entregas if e.get("assignedGrade") is not None)

    return {
        "titulo": trabajo.get("title", "Sin título"),
        "work_type": trabajo.get("workType", ""),
        "topic_id": trabajo.get("topicId"),
        "total_alumnos": len(entregas),
        "entregados": entregados,
        "calificados": calificados,
        "sin_calificar": max(entregados - calificados, 0),
        "link": trabajo.get("alternateLink", ""),
    }


def _resumen_alumnos(service, course_id):
    alumnos_raw = classroom.listar_alumnos_del_curso(service, course_id)
    alumnos = []
    for a in alumnos_raw:
        perfil = a.get("profile", {})
        alumnos.append({
            "nombre": perfil.get("name", {}).get("fullName", "Sin nombre"),
            "email": perfil.get("emailAddress", ""),
        })
    return alumnos


def _resumen_temas(service, course_id):
    temas_raw = classroom.obtener_temas_del_curso(service, course_id)
    return [
        {"topic_id": t.get("topicId"), "nombre": t.get("name", "Sin nombre")}
        for t in temas_raw
    ]


def _snapshot_actual(nombre_curso):
    """Lo que ya tenemos guardado de esta materia (o vacío si nunca se sincronizó)."""
    for snap in memoria.listar_snapshots_materias():
        if snap["curso"] == nombre_curso:
            return snap
    return {"trabajos": [], "temas": [], "alumnos": []}


def sincronizar_materia(nombre_curso, course_id, service,
                         actividades=True, temas=True, alumnos=True):
    """Actualiza una materia. Por defecto trae todo, pero cada parte se puede
    desactivar para no volver a pedirle a Classroom lo que ya tenemos y no
    cambia seguido (alumnos, temas) — así una actualización pesa solo lo que
    realmente hace falta refrescar (típicamente actividades/entregas, que sí
    cambian todo el tiempo)."""
    anterior = _snapshot_actual(nombre_curso)

    if actividades:
        trabajos_raw = classroom.listar_trabajos_del_curso(service, course_id)
        resumen = [_resumen_trabajo(service, course_id, t) for t in trabajos_raw]
    else:
        resumen = anterior["trabajos"]

    temas_resumen = _resumen_temas(service, course_id) if temas else anterior["temas"]
    alumnos_resumen = _resumen_alumnos(service, course_id) if alumnos else anterior["alumnos"]

    memoria.guardar_snapshot_materia(nombre_curso, resumen, temas_resumen, alumnos_resumen)
    return resumen, temas_resumen, alumnos_resumen


def main():
    memoria.init_db()
    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)

    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        print("No se encontraron materias activas.")
        return

    for c in cursos:
        nombre = c.get("name")
        print(f"Sincronizando '{nombre}'...")
        resumen, temas, alumnos = sincronizar_materia(nombre, c["id"], service)
        sin_calificar_total = sum(t["sin_calificar"] for t in resumen)
        print(f"   {len(resumen)} actividades · {sin_calificar_total} entregas sin calificar · "
              f"{len(temas)} temas · {len(alumnos)} alumnos")

    print("\nListo. El panel ya puede mostrar estos datos en la pestaña 'Materias'.")


if __name__ == "__main__":
    main()
