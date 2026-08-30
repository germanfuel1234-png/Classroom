"""Agente Licencias.

Le decís una fecha en la que vas a estar de licencia y arma un borrador de
aviso para CADA curso que te toca ese día según tu horario
(Horario_Clases.xlsx) — uno por materia/comisión, no un aviso genérico.

Reutiliza el mismo mecanismo de aprobación que el Agente Publicador
(panel_control.memoria.aprobaciones, tipo="publicacion_classroom"): no
publica nada solo. Cada aviso queda esperando tu aprobación en el panel,
en la pestaña "Aprobaciones", junto con el resto de las publicaciones.

Uso interactivo: python -m panel_control.agente_licencias
"""
import datetime

from googleapiclient.discovery import build

import main as classroom  # reutiliza OAuth y listados ya probados
from panel_control import horario, memoria, proveedor_ia

AGENTE = "Agente Licencias"
AREA = "Licencias"

DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


TIPOS_LICENCIA = {
    "medica": "licencia médica",
    "estudio": "licencia por estudio",
    "": "licencia",
}


def _actividades_pendientes(nombre_curso):
    """Trabajos del curso que todavía no entregaron todos los alumnos, para
    recordárselos en el aviso (así aprovechan el día para ponerse al día)."""
    for snap in memoria.listar_snapshots_materias():
        if snap["curso"] == nombre_curso:
            return [t["titulo"] for t in snap["trabajos"] if t["entregados"] < t["total_alumnos"]]
    return []


def construir_prompt_licencia(materia, fecha_str, tipo_licencia="", actividades_pendientes=None):
    motivo = TIPOS_LICENCIA.get(tipo_licencia, "licencia")
    seccion_pendientes = ""
    if actividades_pendientes:
        lista = ", ".join(actividades_pendientes)
        seccion_pendientes = (
            f"\nAdemás, recordales que tienen estos trabajos pendientes de entregar en Classroom "
            f"y que pueden aprovechar para avanzar: {lista}."
        )
    return (
        "Sos un profesor de una escuela técnica secundaria. Redactá un aviso breve (3-4 frases) "
        f"para el muro de Classroom de la materia \"{materia}\", avisando que el día {fecha_str} "
        f"no vas a poder dar clase por estar de {motivo}."
        + seccion_pendientes +
        " Tono cordial y profesional, sin firma. No inventes detalles del motivo más allá de lo dado."
    )


def _mensaje_por_defecto(materia, fecha_str, tipo_licencia="", actividades_pendientes=None):
    motivo = TIPOS_LICENCIA.get(tipo_licencia, "licencia")
    mensaje = (
        f"Buenas! Les aviso que el {fecha_str} voy a estar de {motivo}, así que no vamos a "
        f"tener clase de {materia} ese día."
    )
    if actividades_pendientes:
        lista = ", ".join(actividades_pendientes)
        mensaje += f" Aprovechen para avanzar con lo pendiente: {lista}."
    mensaje += " Cualquier novedad se las aviso por acá. Nos vemos en la próxima clase."
    return mensaje


def generar_mensaje_licencia(materia, fecha_str, tipo_licencia="", actividades_pendientes=None):
    """Intenta redactarlo con IA; si falla (sin proveedores disponibles),
    cae a una plantilla fija para no bloquear el aviso por eso."""
    try:
        prompt = construir_prompt_licencia(materia, fecha_str, tipo_licencia, actividades_pendientes)
        texto, proveedor = proveedor_ia.generar_texto(prompt)
        return texto.strip(), proveedor
    except Exception:
        return _mensaje_por_defecto(materia, fecha_str, tipo_licencia, actividades_pendientes), "plantilla"


def _buscar_curso(cursos_classroom, nombre_buscado):
    nombre_buscado_l = (nombre_buscado or "").strip().lower()
    for c in cursos_classroom:
        if (c.get("name") or "").strip().lower() == nombre_buscado_l:
            return c
    return None


def resolver_materias_del_dia(fecha: datetime.date, cursos_classroom):
    """Mira el horario para el día de la semana de `fecha` y lo cruza con
    los cursos reales de Classroom. Devuelve una lista de dicts
    {"materia_horario": ..., "curso": {...}} (curso = objeto de Classroom),
    deduplicada por curso. No genera ni deja pendiente nada todavía — es
    el paso "qué materias te tocan ese día", para que el panel lo muestre
    editable ANTES de redactar ningún aviso."""
    dia_semana = DIAS_ES[fecha.weekday()]
    bloques = horario.materias_del_dia(dia_semana)

    resueltas = []
    vistos = set()
    for bloque in bloques:
        nombre_curso = bloque["curso_classroom"]
        if nombre_curso in vistos:
            continue
        curso = _buscar_curso(cursos_classroom, nombre_curso)
        if not curso:
            continue
        vistos.add(nombre_curso)
        resueltas.append({"materia_horario": bloque["materia"], "curso": curso})
    return resueltas


def generar_aviso_para_materia(materia_horario, curso, fecha: datetime.date, tipo_licencia=""):
    """Redacta y deja pendiente de aprobación UN aviso para UNA materia ya
    resuelta contra Classroom (`curso` = {"id":..., "name":...}). Se usa
    una vez que el profesor ya confirmó (o editó) qué materias avisar.
    Devuelve (tarea_id, mensaje, proveedor)."""
    fecha_str = fecha.strftime("%d/%m/%Y")
    pendientes = _actividades_pendientes(curso["name"])
    mensaje, proveedor = generar_mensaje_licencia(materia_horario, fecha_str, tipo_licencia, pendientes)

    tarea_id = memoria.registrar_tarea(
        AGENTE,
        f"Aviso de licencia para {curso['name']} el {fecha_str} — esperando tu aprobación",
        curso=curso["name"], estado="pendiente_aprobacion",
    )
    memoria.crear_aprobacion(tarea_id, tipo="publicacion_classroom", datos={
        "course_id": curso["id"],
        "materia": curso["name"],
        "tipo_publicacion": "anuncio",
        "titulo": f"Aviso: licencia el {fecha_str}",
        "descripcion": mensaje,
        "fecha_entrega": None,
        "puntos": None,
        "proveedor": proveedor,
        "agente": AGENTE,
    })
    print(f"📝 Aviso listo para {curso['name']} (vía {proveedor}) — esperando tu aprobación en el panel")
    return tarea_id, mensaje, proveedor


def generar_avisos_licencia(fecha: datetime.date, service, tipo_licencia=""):
    """Crea un borrador de aviso (pendiente de aprobación) por cada curso
    que el profesor tiene ese día según el horario. `tipo_licencia`:
    "medica", "estudio" o "" (genérica). Devuelve la lista de ids de tarea
    creados. Uso directo (CLI); el panel usa resolver_materias_del_dia +
    generar_aviso_para_materia por separado para poder mostrar y editar
    la selección de materias antes de generar los avisos."""
    cursos_classroom = classroom.listar_materias_activas(service)
    resueltas = resolver_materias_del_dia(fecha, cursos_classroom)
    if not resueltas:
        dia_semana = DIAS_ES[fecha.weekday()]
        print(f"No encontré materias para el {dia_semana} según el horario (o no coinciden con Classroom).")
        return []

    creadas = []
    for r in resueltas:
        tarea_id, _, _ = generar_aviso_para_materia(r["materia_horario"], r["curso"], fecha, tipo_licencia)
        creadas.append(tarea_id)
    return creadas


def menu():
    memoria.init_db()
    memoria.agregar_agente(
        AGENTE,
        "Avisa a cada curso correspondiente cuando el profesor va a estar de licencia",
        AREA,
    )

    fecha_str = input("¿Qué día vas a tomar licencia? (YYYY-MM-DD): ").strip()
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
    except ValueError:
        print("Fecha inválida. Usá el formato YYYY-MM-DD.")
        return

    tipo_licencia = input("¿Tipo de licencia? [medica/estudio/Enter para no especificar]: ").strip().lower()
    if tipo_licencia not in ("medica", "estudio"):
        tipo_licencia = ""

    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)

    generar_avisos_licencia(fecha, service, tipo_licencia)


if __name__ == "__main__":
    menu()
