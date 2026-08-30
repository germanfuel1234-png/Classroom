"""Agente Consultas.

Classroom NO permite leer los comentarios que los alumnos escriben en el
muro (investigado y confirmado: no hay endpoint de lectura ni notificación
push para comentarios). Por eso el canal de entrada es un Google Form
propio ("Consultas — <materia>"), uno por materia:

  1. El alumno escribe su pregunta en el Form.
  2. El agente lee las respuestas nuevas (Forms API, sin Sheets de por medio).
  3. Genera una respuesta con panel_control.proveedor_ia.
  4. La manda por Gmail directo al alumno (mismo mecanismo que ya usa
     main.py para las devoluciones de notas).

Uso interactivo: python -m panel_control.agente_consultas
"""
import base64
import json
from email.mime.text import MIMEText

from googleapiclient.discovery import build

import main as classroom  # reutiliza OAuth ya probado
from panel_control import memoria, proveedor_ia
from panel_control.identidad import ESCUELA

AGENTE = "Agente Consultas"
AREA = "Consultas"


def _crear_formulario(nombre_materia, creds):
    """Crea el Form con 3 preguntas (nombre, email, consulta) y devuelve
    (form_id, responder_uri, mapa_preguntas) donde mapa_preguntas mapea
    'nombre'/'email'/'consulta' -> questionId real que asignó Google."""
    service_forms = build("forms", "v1", credentials=creds)

    creado = service_forms.forms().create(
        body={"info": {"title": f"Consultas — {nombre_materia}", "documentTitle": f"Consultas — {nombre_materia}"}}
    ).execute()
    form_id = creado["formId"]

    items = [
        ("nombre", {"title": "Tu nombre", "questionItem": {"question": {"required": True, "textQuestion": {}}}}),
        ("email", {"title": "Tu email", "questionItem": {"question": {"required": True, "textQuestion": {}}}}),
        ("consulta", {"title": "Tu consulta", "questionItem": {"question": {"required": True, "textQuestion": {"paragraph": True}}}}),
    ]
    requests_batch = [
        {"createItem": {"item": item, "location": {"index": idx}}} for idx, (_, item) in enumerate(items)
    ]
    resultado = service_forms.forms().batchUpdate(
        formId=form_id, body={"requests": requests_batch}
    ).execute()

    mapa_preguntas = {}
    for (clave, _), reply in zip(items, resultado.get("replies", [])):
        question_id = reply.get("createItem", {}).get("questionId")
        mapa_preguntas[clave] = question_id

    info = service_forms.forms().get(formId=form_id).execute()
    responder_uri = info.get("responderUri", "")

    return form_id, responder_uri, mapa_preguntas


def listar_materias_con_formulario():
    """Materias que YA tienen un Form de consultas creado (no crea nada
    nuevo). Se usa para el chequeo masivo 'revisar novedades' del panel,
    así no crea Forms de sorpresa en materias que el profesor no abrió
    todavía desde Agente Consultas."""
    with memoria.conexion() as con:
        filas = con.execute(
            "SELECT DISTINCT curso FROM memoria WHERE tipo = 'formulario_consultas' ORDER BY curso"
        ).fetchall()
    return [f["curso"] for f in filas]


def obtener_o_crear_formulario(nombre_materia, creds):
    """Devuelve (form_id, responder_uri, mapa_preguntas) para la materia,
    creando el Form la primera vez y reutilizándolo después."""
    with memoria.conexion() as con:
        fila = con.execute(
            "SELECT valor FROM memoria WHERE tipo = 'formulario_consultas' AND curso = ? "
            "ORDER BY creado_en DESC LIMIT 1",
            (nombre_materia,),
        ).fetchone()

    if fila:
        datos = json.loads(fila["valor"])
        return datos["form_id"], datos["responder_uri"], datos["preguntas"]

    form_id, responder_uri, mapa_preguntas = _crear_formulario(nombre_materia, creds)
    memoria.agregar_memoria(
        "formulario_consultas",
        clave=nombre_materia,
        valor=json.dumps({"form_id": form_id, "responder_uri": responder_uri, "preguntas": mapa_preguntas}),
        curso=nombre_materia,
        agente=AGENTE,
    )
    return form_id, responder_uri, mapa_preguntas


def _valor_de_respuesta(answers, question_id):
    if not question_id or question_id not in answers:
        return ""
    text_answers = answers[question_id].get("textAnswers", {}).get("answers", [])
    return text_answers[0].get("value", "") if text_answers else ""


def _ids_ya_procesados():
    """Consultas que ya tienen un borrador generado (aprobado, rechazado o
    todavía esperando aprobación) — no hay que volver a generarles otro."""
    with memoria.conexion() as con:
        filas = con.execute(
            "SELECT clave FROM memoria WHERE tipo IN ('consulta_procesada', 'consulta_respondida')"
        ).fetchall()
    return {f["clave"] for f in filas}


def listar_consultas_nuevas(form_id, mapa_preguntas, creds):
    service_forms = build("forms", "v1", credentials=creds)
    resultado = service_forms.forms().responses().list(formId=form_id).execute()
    respuestas = resultado.get("responses", [])

    procesadas = _ids_ya_procesados()
    nuevas = []
    for r in respuestas:
        if r["responseId"] in procesadas:
            continue
        answers = r.get("answers", {})
        nuevas.append({
            "response_id": r["responseId"],
            "nombre": _valor_de_respuesta(answers, mapa_preguntas.get("nombre")),
            "email": _valor_de_respuesta(answers, mapa_preguntas.get("email")),
            "consulta": _valor_de_respuesta(answers, mapa_preguntas.get("consulta")),
        })
    return nuevas


def construir_prompt_respuesta(nombre_materia, pregunta, contexto_curricular=""):
    seccion_curricular = ""
    if contexto_curricular.strip():
        seccion_curricular = (
            "\n---- DISEÑO CURRICULAR DE REFERENCIA (usalo si aplica) ----\n"
            f"{contexto_curricular}\n"
        )
    return (
        f"Sos el profesor de \"{nombre_materia}\" en una escuela técnica secundaria, respondiendo por email "
        "la consulta de un alumno. Respondé de forma clara, técnica y pedagógica, en un tono cercano pero "
        "profesional. Si la pregunta no se puede responder con certeza a partir de lo que sabés, decilo "
        "honestamente y sugerí que lo consulte en la próxima clase en vez de inventar una respuesta.\n"
        + seccion_curricular +
        "\n---- CONSULTA DEL ALUMNO ----\n"
        f"{pregunta}\n"
    )


def generar_respuesta(nombre_materia, pregunta, contexto_curricular=""):
    prompt = construir_prompt_respuesta(nombre_materia, pregunta, contexto_curricular)
    return proveedor_ia.generar_texto(prompt)


def _enviar_respuesta_email(creds, email_destino, nombre_alumno, nombre_materia, pregunta, respuesta):
    if not email_destino:
        return False
    try:
        service_gmail = build("gmail", "v1", credentials=creds)
        sep = "=" * 54
        cuerpo = "\n".join([
            sep,
            "  RESPUESTA A TU CONSULTA",
            sep,
            "",
            f"Hola {nombre_alumno}!".strip() if nombre_alumno else "Hola!",
            "",
            "Tu consulta:",
            f"  {pregunta}",
            "",
            "Respuesta:",
            respuesta.strip(),
            "",
            sep,
            "Prof. Rodríguez G.",
            ESCUELA,
            sep,
        ])
        mensaje = MIMEText(cuerpo, "plain", "utf-8")
        mensaje["To"] = email_destino
        mensaje["Subject"] = f"[Consulta respondida] {nombre_materia}"
        raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
        service_gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        print(f"      ⚠️ Gmail: no se pudo enviar respuesta a {email_destino}: {str(e)[:120]}")
        return False


def procesar_consultas(nombre_materia, creds):
    """Revisa el Form de la materia y genera un BORRADOR de respuesta para
    cada consulta nueva. No manda nada todavía: cada borrador queda en la
    cola de aprobaciones del panel, esperando que el profesor lo revise
    (y edite si hace falta) antes de que salga por Gmail — el agente no
    ejecuta acciones críticas hacia el exterior por su cuenta."""
    form_id, responder_uri, mapa_preguntas = obtener_o_crear_formulario(nombre_materia, creds)
    nuevas = listar_consultas_nuevas(form_id, mapa_preguntas, creds)

    if not nuevas:
        print(f"Sin consultas nuevas para '{nombre_materia}'. Form: {responder_uri}")
        return []

    contexto_curricular = memoria.contexto_curricular(nombre_materia)
    creadas = []
    for c in nuevas:
        tarea_id = memoria.registrar_tarea(
            AGENTE, f"Consulta de {c['nombre'] or c['email']} — esperando tu aprobación",
            curso=nombre_materia, estado="pendiente_aprobacion",
        )
        try:
            respuesta_texto, proveedor = generar_respuesta(nombre_materia, c["consulta"], contexto_curricular)
            memoria.crear_aprobacion(tarea_id, tipo="email_consulta", datos={
                "response_id": c["response_id"],
                "materia": nombre_materia,
                "nombre": c["nombre"],
                "email": c["email"],
                "pregunta": c["consulta"],
                "respuesta": respuesta_texto,
                "proveedor": proveedor,
            })
            memoria.agregar_memoria(
                "consulta_procesada", clave=c["response_id"], valor="borrador_creado",
                curso=nombre_materia, agente=AGENTE,
            )
            print(f"📝 Borrador listo para {c['nombre'] or c['email']} (vía {proveedor}) — esperando tu aprobación en el panel")
            creadas.append(tarea_id)
        except Exception as e:
            memoria.actualizar_estado_tarea(tarea_id, "error")
            print(f"❌ Error generando respuesta para {c['email']}: {e}")

    return creadas


def aprobar_y_enviar(aprobacion_id, creds, texto_editado=None):
    """Se llama desde el panel cuando el profesor aprueba un borrador.
    Recién acá se manda el email de verdad. Devuelve (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = ap["datos"]
    texto_final = texto_editado if texto_editado is not None else datos["respuesta"]

    enviado = _enviar_respuesta_email(
        creds, datos["email"], datos["nombre"], datos["materia"], datos["pregunta"], texto_final
    )
    if not enviado:
        return False, f"No se pudo enviar el email a {datos['email']}."

    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada", texto_final=texto_final)
    memoria.agregar_memoria(
        "consulta_respondida", clave=datos["response_id"], valor=texto_final[:2000],
        curso=datos["materia"], agente=AGENTE,
    )
    return True, "Enviado."


def rechazar(aprobacion_id):
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap or ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."
    memoria.resolver_aprobacion(aprobacion_id, estado="rechazada", tarea_estado="rechazada")
    return True, "Rechazada."


def menu():
    memoria.init_db()
    memoria.agregar_agente(AGENTE, "Responde consultas de alumnos vía Google Form + Gmail", AREA)

    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)

    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        return
    print("\nMaterias activas:")
    for i, c in enumerate(cursos, start=1):
        print(f"  [{i}] {c.get('name')}")
    idx = int(input("Elegí una materia: ")) - 1
    nombre_materia = cursos[idx].get("name")

    form_id, responder_uri, _ = obtener_o_crear_formulario(nombre_materia, creds)
    print(f"\nForm de consultas para '{nombre_materia}':")
    print(f"  {responder_uri}")
    print("Compartiselo a tus alumnos (podés pegarlo como material en Classroom).\n")

    procesar_consultas(nombre_materia, creds)


if __name__ == "__main__":
    menu()
