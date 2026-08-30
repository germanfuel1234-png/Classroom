"""Agente Corrector.

Evalúa automáticamente TODAS las entregas de una actividad (nota +
feedback pedagógico), reutilizando el mismo motor de corrección que ya
usa main.py (evaluar_entrega_automatica / construir_lote_automatico:
concordancia consigna-entrega, chequeo de formato, etc.).

A diferencia de correccion_automatica_por_lote() / calificar_y_devolver_actividad()
en main.py (que publican directo tras una confirmación por consola), acá
el lote generado queda pendiente de aprobación en el panel
(panel_control.memoria.aprobaciones, tipo="lote_calificaciones"): el
profesor ve nota y feedback por alumno, puede editarlos o destildar a
quien no quiera calificar todavía, y recién ahí se publica de verdad
(nota en Classroom + email de feedback + devolución de la entrega).

Uso interactivo: python -m panel_control.agente_corrector
"""
from googleapiclient.discovery import build

import main as classroom  # reutiliza el motor de corrección ya probado
from panel_control import memoria

AGENTE = "Agente Corrector"
AREA = "Corrección"

# Estados de studentSubmissions que indican que el alumno entregó algo de
# verdad — solo esos vienen pre-tildados para publicar, así una actividad
# con alumnos que todavía no entregaron no les pone un 1 por accidente.
ESTADOS_CON_ENTREGA = ("TURNED_IN", "RETURNED")


def generar_lote_correccion(nombre_curso, course_id, trabajo, service, service_drive):
    """Evalúa automáticamente a todos los alumnos de una actividad y deja
    el lote esperando aprobación. No toca Classroom todavía. Devuelve
    (tarea_id, lote) — lote puede ser [] si no hay alumnos."""
    titulo_trabajo = trabajo.get("title", "Trabajo práctico")
    max_points = float(trabajo.get("maxPoints") or 100)

    tarea_id = memoria.registrar_tarea(
        AGENTE, f"Corrigiendo: {titulo_trabajo}", curso=nombre_curso, estado="en_curso"
    )
    try:
        contexto_consigna = classroom.obtener_contexto_consigna(
            service, service_drive, course_id, trabajo["id"], trabajo
        )
        alumnos_tp = classroom.listar_alumnos_por_actividad(service, course_id, trabajo["id"])
        if not alumnos_tp:
            memoria.actualizar_estado_tarea(tarea_id, "completada")
            return tarea_id, []

        lote = classroom.construir_lote_automatico(
            alumnos_tp, titulo_trabajo, service_drive, contexto_consigna, nombre_curso
        )

        memoria.actualizar_estado_tarea(tarea_id, "pendiente_aprobacion")
        memoria.crear_aprobacion(tarea_id, tipo="lote_calificaciones", datos={
            "course_id": course_id,
            "work_id": trabajo["id"],
            "materia": nombre_curso,
            "titulo_trabajo": titulo_trabajo,
            "max_points": max_points,
            "lote": lote,
            "agente": AGENTE,
        })
        print(f"📝 {len(lote)} corrección(es) lista(s) para '{titulo_trabajo}' — esperando tu aprobación en el panel")
        return tarea_id, lote
    except Exception as e:
        memoria.actualizar_estado_tarea(tarea_id, "error")
        print(f"❌ Error corrigiendo '{titulo_trabajo}': {e}")
        raise


def aprobar_y_publicar_lote(aprobacion_id, creds, lote_final):
    """Se llama desde el panel cuando el profesor aprueba (con nota/feedback
    ya editados y solo los alumnos tildados como 'incluir'). Para cada uno:
    publica la nota, manda el feedback por Gmail y devuelve la entrega —
    igual que hace calificar_y_devolver_actividad() en main.py, pero
    dirigido por la selección del profesor en vez de por input() en consola.
    Devuelve (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = ap["datos"]
    course_id = datos["course_id"]
    work_id = datos["work_id"]
    nombre_curso = datos["materia"]
    titulo_trabajo = datos["titulo_trabajo"]
    max_points = float(datos.get("max_points") or 100)

    incluidos = [f for f in (lote_final or []) if f.get("incluir")]
    if not incluidos:
        return False, "No tildaste ningún alumno para publicar."

    service = build("classroom", "v1", credentials=creds)

    publicados, emails_ok, devueltos, errores = 0, 0, 0, 0

    for item in incluidos:
        nombre_alumno = item.get("nombre", "Alumno")
        submission_id = item.get("submission_id")
        user_id = item.get("user_id")
        nota_1_10 = item.get("nota")
        feedback_txt = (item.get("feedback") or "").strip()

        if not submission_id:
            errores += 1
            continue

        if nota_1_10 is not None:
            try:
                nota_classroom = round((float(nota_1_10) / 10.0) * max_points, 1)
                classroom._ejecutar_con_reintentos_api(
                    lambda sid=submission_id, nc=nota_classroom: service.courses().courseWork().studentSubmissions().patch(
                        courseId=course_id, courseWorkId=work_id, id=sid,
                        updateMask="assignedGrade,draftGrade",
                        body={"assignedGrade": nc, "draftGrade": nc},
                    ).execute(),
                    etiqueta=f"patch nota {nombre_alumno}",
                )
                publicados += 1
            except Exception as e:
                print(f"   ❌ Error publicando nota de {nombre_alumno}: {str(e)[:120]}")
                errores += 1
        else:
            print(f"   ⓘ {nombre_alumno}: sin nota, se omite la calificación")

        email_alumno = classroom._obtener_email_alumno(service, user_id)
        if email_alumno and feedback_txt:
            try:
                if classroom._enviar_feedback_gmail(
                    creds, email_alumno, nombre_alumno, titulo_trabajo, nombre_curso, feedback_txt, nota_1_10
                ):
                    emails_ok += 1
            except Exception as e:
                print(f"   ⚠️ No se pudo enviar feedback a {nombre_alumno}: {str(e)[:120]}")

        try:
            classroom._ejecutar_con_reintentos_api(
                lambda sid=submission_id: service.courses().courseWork().studentSubmissions().return_(
                    courseId=course_id, courseWorkId=work_id, id=sid, body={},
                ).execute(),
                etiqueta=f"return {nombre_alumno}",
            )
            devueltos += 1
        except Exception as e:
            print(f"   ❌ Error devolviendo entrega de {nombre_alumno}: {str(e)[:120]}")
            errores += 1

    try:
        classroom.actualizar_excel_evaluaciones(nombre_curso, titulo_trabajo, incluidos, max_points)
    except Exception as e:
        print(f"   ⚠️ No se pudo actualizar el Excel maestro: {str(e)[:120]}")

    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada")
    memoria.agregar_memoria(
        "correccion_publicada", clave=titulo_trabajo,
        valor=f"{publicados} nota(s), {emails_ok} email(s), {devueltos} entrega(s) devuelta(s)",
        curso=nombre_curso, agente=AGENTE,
    )

    mensaje = (
        f"Listo: {publicados} nota(s) publicada(s), {emails_ok} email(s) de feedback enviado(s), "
        f"{devueltos} entrega(s) devuelta(s)."
    )
    if errores:
        mensaje += f" ⚠️ {errores} con error (revisá la consola)."
    return True, mensaje


def rechazar_lote(aprobacion_id):
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap or ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."
    memoria.resolver_aprobacion(aprobacion_id, estado="rechazada", tarea_estado="rechazada")
    return True, "Rechazada."


def menu():
    memoria.init_db()
    memoria.agregar_agente(AGENTE, "Evalúa entregas automáticamente y deja las notas esperando tu aprobación", AREA)

    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)
    service_drive = build("drive", "v3", credentials=creds)

    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        return
    print("\nMaterias activas:")
    for i, c in enumerate(cursos, start=1):
        print(f"  [{i}] {c.get('name')}")
    idx = int(input("Elegí una materia: ")) - 1
    curso = cursos[idx]

    trabajos = classroom.listar_trabajos_del_curso(service, curso["id"])
    if not trabajos:
        return
    print("\nTrabajos prácticos:")
    for i, t in enumerate(trabajos, start=1):
        print(f"  [{i}] {t.get('title')}")
    idx2 = int(input("Elegí un trabajo para corregir: ")) - 1
    trabajo = trabajos[idx2]

    generar_lote_correccion(curso.get("name"), curso["id"], trabajo, service, service_drive)


if __name__ == "__main__":
    menu()
