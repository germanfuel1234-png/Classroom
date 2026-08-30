"""Agente Director.

Lee la actividad reciente de los demás agentes (tabla `tareas`, que ya
funciona como canal compartido: cada agente deja ahí una descripción en
lenguaje natural de lo que hizo) y los riesgos detectados (aprobaciones
esperando hace rato, entregas sin corregir), y publica un resumen de
supervisión breve en ese mismo canal. Nunca actúa por su cuenta ni dispara
nada de otro agente — solo lee y escribe un mensaje de texto, igual que
cualquier otro aporte al canal. Se llama SOLO cuando el profesor lo pide
(botón en el dashboard), nunca automático, para no gastar cuota de IA sin
que él lo decida.

Uso interactivo: python -m panel_control.agente_director
"""
from datetime import datetime

from panel_control import memoria, proveedor_ia

AGENTE = "Director"
AREA = "Dirección"

LIMITE_TAREAS_RECIENTES = 30


def _calcular_riesgos():
    """Misma lógica que ya usa el Top de riesgos de Centro de Operaciones
    (dashboard.py) — aprobaciones esperando hace más de 1h y materias con
    entregas sin corregir. Se recalcula acá en vez de importar del
    dashboard para no acoplar el agente a la UI."""
    riesgos = []
    for snap in memoria.listar_snapshots_materias():
        sin_calif = sum(t["sin_calificar"] for t in snap["trabajos"])
        if sin_calif > 0:
            riesgos.append(f"{snap['curso']}: {sin_calif} entregas sin corregir")

    for ap in memoria.listar_aprobaciones(estado="pendiente"):
        try:
            dt = datetime.fromisoformat(ap["creado_en"])
            espera_h = (datetime.now() - dt).total_seconds() / 3600
        except ValueError:
            espera_h = 0
        if espera_h >= 1:
            materia_ap = ap["datos"].get("materia", "")
            riesgos.append(f"Aprobación de {materia_ap} esperando hace {espera_h:.0f}h")

    return riesgos


def construir_prompt_supervision(tareas_recientes, riesgos):
    lineas_tareas = "\n".join(
        f"- [{t['agente_nombre']}] ({t['curso'] or 'general'}) {t['descripcion']} — estado: {t['estado']}"
        for t in tareas_recientes
    ) or "(sin actividad reciente)"
    lineas_riesgos = "\n".join(f"- {r}" for r in riesgos) or "(sin riesgos detectados)"

    return (
        "Sos el Director de un equipo de agentes de IA que ayudan a un profesor de escuela técnica "
        "a gestionar Google Classroom (Corrector, Publicador, Mejorador, Consultas, Licencias, Evaluador). "
        "Tu trabajo es supervisar, NO ejecutar nada vos mismo.\n\n"
        "Te paso lo que hicieron los agentes últimamente y los riesgos ya detectados. Escribí un parte "
        "de situación breve (3 a 6 líneas, tono directo y cercano, como si le hablaras al profesor) que "
        "resuma qué se hizo, qué está esperando su revisión, y si algo llama la atención (por ejemplo un "
        "proveedor de IA fallando seguido, o algo acumulándose). No inventes datos que no estén acá.\n\n"
        "---- ACTIVIDAD RECIENTE ----\n"
        f"{lineas_tareas}\n\n"
        "---- RIESGOS DETECTADOS ----\n"
        f"{lineas_riesgos}\n"
    )


def generar_supervision():
    """Devuelve (texto, proveedor_usado)."""
    tareas_recientes = memoria.listar_tareas(limite=LIMITE_TAREAS_RECIENTES)
    riesgos = _calcular_riesgos()
    prompt = construir_prompt_supervision(tareas_recientes, riesgos)
    return proveedor_ia.generar_texto(prompt)


def publicar_supervision():
    """Genera el resumen y lo deja publicado en el canal (tabla `tareas`,
    agente='Director'). Devuelve (texto, proveedor)."""
    memoria.agregar_agente(AGENTE, "Lee la actividad de los demás agentes y publica un parte de situación", AREA)
    texto, proveedor = generar_supervision()
    memoria.registrar_tarea(AGENTE, texto, estado="completada")
    print(f"🧭 Supervisión publicada (vía {proveedor}).")
    return texto, proveedor


def menu():
    memoria.init_db()
    publicar_supervision()


if __name__ == "__main__":
    menu()
