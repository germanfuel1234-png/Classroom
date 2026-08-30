"""Agente Evaluador.

Arma una evaluación (parte teórica y, si corresponde, parte práctica) a
partir de un conjunto de actividades YA DADAS que el profesor elige, para
una materia y un año curricular puntual (4to/5to/6to/7mo — la misma materia
de Classroom puede tener contenidos mínimos distintos según el año). Genera
un documento .docx local, igual que el Agente Mejorador — no toca Classroom
ni pasa por la cola de Aprobaciones, porque no publica nada.

Uso interactivo: python -m panel_control.agente_evaluador
"""
import datetime
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from panel_control import memoria, proveedor_ia
from panel_control.identidad import NOMBRE_PROFESOR

AGENTE = "Agente Evaluador"
AREA = "Evaluaciones"
CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "Evaluaciones")

MAX_CHARS_POR_ACTIVIDAD = 4000
TITULO_SECCION_TEORIA = "Parte Teórica"
TITULO_SECCION_PRACTICA = "Parte Práctica"

ANIOS_DISPONIBLES = {"4to": "4º año", "5to": "5º año", "6to": "6º año", "7mo": "7º año"}


def _limpiar_nombre(nombre):
    return re.sub(r'[\\/:*?"<>|]+', "_", (nombre or "").strip())


def _resumir_actividad_para_prompt(actividad, max_chars=MAX_CHARS_POR_ACTIVIDAD):
    """Título + enunciado truncado. Hace falta: hay enunciados reales de
    hasta ~600.000 caracteres (PDFs pesados) — mandar varios completos
    reventaría el prompt."""
    enunciado = (actividad.get("enunciado") or "").strip()
    if len(enunciado) > max_chars:
        enunciado = enunciado[:max_chars] + "\n[...truncado...]"
    texto = f"### {actividad['titulo']}"
    if enunciado:
        texto += f"\n{enunciado}"
    return texto


def construir_prompt_evaluacion(nombre_materia, anio_legible, actividades, contexto_curricular="", incluir_practica=True):
    seccion_curricular = ""
    if contexto_curricular.strip():
        seccion_curricular = (
            "\n---- DISEÑO CURRICULAR DE REFERENCIA (respetalo, define el nivel esperado) ----\n"
            f"{contexto_curricular}\n"
        )

    seccion_actividades = "\n\n".join(_resumir_actividad_para_prompt(a) for a in actividades)

    estructura = f"## {TITULO_SECCION_TEORIA}\n(preguntas teóricas numeradas, con su respuesta esperada breve al lado o debajo de cada una)\n"
    if incluir_practica:
        estructura += f"\n## {TITULO_SECCION_PRACTICA}\n(uno o más ejercicios prácticos aplicados, coherentes con las actividades dadas)\n"

    return (
        f"Sos el profesor de \"{nombre_materia}\" ({anio_legible}) en una escuela técnica secundaria.\n"
        "Tenés que armar una EVALUACIÓN (prueba/examen) para tomarles a tus alumnos, basada en los "
        "Trabajos Prácticos que ya les diste (abajo tenés el enunciado de cada uno) y respetando el "
        "diseño curricular de referencia como marco de nivel/profundidad esperado — no repitas "
        "textualmente los enunciados, usalos para saber qué temas y qué nivel de dificultad ya vieron.\n"
        + seccion_curricular +
        "\nDevolvé el resultado con ESTA estructura exacta (respetá los encabezados '## ' tal cual, "
        "los necesito para separar las secciones del documento final):\n\n"
        f"{estructura}\n"
        "---- ACTIVIDADES YA DADAS (base de la evaluación) ----\n"
        f"{seccion_actividades}\n"
    )


def generar_evaluacion(nombre_materia, anio_legible, actividades, contexto_curricular="", incluir_practica=True):
    """Devuelve (texto_generado, proveedor_usado)."""
    prompt = construir_prompt_evaluacion(nombre_materia, anio_legible, actividades, contexto_curricular, incluir_practica)
    return proveedor_ia.generar_texto(prompt)


def _agregar_seccion_al_docx(doc, titulo, cuerpo):
    doc.add_heading(titulo, level=2)
    for linea in cuerpo.strip("\n").split("\n"):
        doc.add_paragraph(linea)


def guardar_docx(nombre_materia, anio_legible, actividades, texto_generado):
    carpeta_materia = os.path.join(CARPETA_SALIDA, _limpiar_nombre(nombre_materia))
    os.makedirs(carpeta_materia, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    ruta = os.path.join(carpeta_materia, f"Evaluacion - {_limpiar_nombre(anio_legible)} - {marca}.docx")

    doc = Document()

    header_para = doc.sections[0].header.paragraphs[0]
    header_run = header_para.add_run(f"{nombre_materia} — {NOMBRE_PROFESOR}")
    header_run.bold = True
    header_run.font.size = Pt(9)
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading(f"Evaluación — {nombre_materia} ({anio_legible})", level=1)
    doc.add_paragraph(f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph("Basada en las siguientes actividades ya dadas:")
    for a in actividades:
        doc.add_paragraph(f"• {a['titulo']}", style="List Bullet")
    doc.add_paragraph("")

    # Trocea el texto generado por los encabezados '## ' que le pedimos al prompt.
    secciones = re.split(r"^##\s+", texto_generado.strip(), flags=re.MULTILINE)
    huerfano = secciones[0].strip()
    if huerfano:
        doc.add_paragraph(huerfano)
    for bloque in secciones[1:]:
        if not bloque.strip():
            continue
        primera_linea, _, resto = bloque.partition("\n")
        _agregar_seccion_al_docx(doc, primera_linea.strip(), resto)

    doc.save(ruta)
    return ruta


def crear_evaluacion(nombre_materia, anio_clave, actividades_seleccionadas, incluir_practica=True):
    """Orquesta: registra la tarea, genera el texto con IA y guarda el docx.
    `anio_clave` es una clave corta ("4to", "5to", "6to", "7mo").
    Devuelve (ruta_docx, texto_generado, proveedor)."""
    anio_legible = ANIOS_DISPONIBLES.get(anio_clave, anio_clave)
    memoria.agregar_agente(AGENTE, "Arma evaluaciones (teoría + práctica) desde actividades ya dadas", AREA)
    tarea_id = memoria.registrar_tarea(
        AGENTE, f"Armando evaluación de {nombre_materia} ({anio_legible})",
        curso=nombre_materia, estado="en_curso",
    )
    try:
        if not actividades_seleccionadas:
            raise RuntimeError("No se eligió ninguna actividad como base de la evaluación.")
        contexto_curricular = memoria.contexto_curricular(nombre_materia, anio=anio_legible)
        texto, proveedor = generar_evaluacion(
            nombre_materia, anio_legible, actividades_seleccionadas, contexto_curricular, incluir_practica
        )
        ruta = guardar_docx(nombre_materia, anio_legible, actividades_seleccionadas, texto)
        memoria.agregar_memoria(
            "evaluacion_generada", clave=f"{nombre_materia} — {anio_legible}", valor=ruta,
            curso=nombre_materia, agente=AGENTE,
        )
        memoria.actualizar_estado_tarea(tarea_id, "completada")
        print(f"✅ Evaluación guardada en: {ruta} (generada con {proveedor})")
        return ruta, texto, proveedor
    except Exception as e:
        memoria.actualizar_estado_tarea(tarea_id, "error")
        print(f"❌ Error armando la evaluación: {e}")
        raise


def menu():
    memoria.init_db()
    memoria.agregar_agente(AGENTE, "Arma evaluaciones (teoría + práctica) desde actividades ya dadas", AREA)

    materias = sorted({a["materia"] for a in memoria.listar_actividades_cache()})
    if not materias:
        print("No hay actividades sincronizadas todavía — corré primero sincronizar_actividades.")
        return
    print("\nMaterias disponibles:")
    for i, m in enumerate(materias, start=1):
        print(f"  [{i}] {m}")
    materia = materias[int(input("Elegí una materia: ")) - 1]

    print("\nAño curricular:")
    claves_anio = list(ANIOS_DISPONIBLES.keys())
    for i, a in enumerate(claves_anio, start=1):
        print(f"  [{i}] {a}")
    anio_clave = claves_anio[int(input("Elegí un año: ")) - 1]

    candidatas = [a for a in memoria.listar_actividades_cache(materia) if a.get("tipo") == "ASSIGNMENT"]
    if not candidatas:
        print("Esta materia no tiene actividades tipo tarea sincronizadas.")
        return
    print("\nActividades (separá los números con comas, ej: 1,3,4):")
    for i, a in enumerate(candidatas, start=1):
        print(f"  [{i}] {a['titulo']}")
    indices = [int(x.strip()) - 1 for x in input("Elegidas: ").split(",") if x.strip()]
    seleccionadas = [candidatas[i] for i in indices if 0 <= i < len(candidatas)]

    incluir_practica = input("¿Incluir parte práctica? [S/n]: ").strip().lower() != "n"

    crear_evaluacion(materia, anio_clave, seleccionadas, incluir_practica)


if __name__ == "__main__":
    menu()
