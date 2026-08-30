"""Agente Mejorador de Actividades.

Toma un Trabajo Práctico YA PUBLICADO en Classroom y genera una versión
mejorada (más didáctica, más técnica, respetando el diseño curricular) como
documento .docx aparte. Nunca modifica ni reemplaza la actividad original:
el profesor decide después si la usa.

Uso interactivo: python -m panel_control.agente_mejorador
"""
import datetime
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from googleapiclient.discovery import build

import main as classroom  # reutiliza OAuth, listados y extracción de consignas ya probados
from panel_control import memoria, proveedor_ia
from panel_control.identidad import NOMBRE_PROFESOR
from panel_control.rubrica_entrega import REQUISITOS_FORMATO_ENTREGA

AGENTE = "Agente Mejorador"
AREA = "Publicaciones"
CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "Actividades_Mejoradas")


def _limpiar_nombre(nombre):
    return re.sub(r'[\\/:*?"<>|]+', "_", (nombre or "").strip())


def construir_prompt_mejora(nombre_materia, texto_original, contexto_curricular=""):
    seccion_curricular = ""
    if contexto_curricular.strip():
        seccion_curricular = (
            "\n---- DISEÑO CURRICULAR DE REFERENCIA (respetalo al mejorar) ----\n"
            f"{contexto_curricular}\n"
        )

    return (
        "Sos un especialista en diseño curricular y didáctica de la educación técnica secundaria.\n"
        f"Te paso el enunciado ORIGINAL de un Trabajo Práctico de la materia \"{nombre_materia}\".\n\n"
        "Generá una VERSIÓN MEJORADA de ESA MISMA actividad: mismo objetivo de aprendizaje, mismo tema "
        "y mismo alcance, pero redactada de forma más didáctica, más técnica y mejor organizada, "
        "respetando el diseño curricular vigente para esta materia. NO es un TP nuevo ni de otro tema: "
        "es el mismo TP, prolijo y mejor explicado.\n\n"
        "No inventes contenido ajeno al original ni cambies el tema del trabajo.\n"
        + seccion_curricular +
        "\nDevolvé el resultado con esta estructura:\n"
        "1. Título\n"
        "2. Objetivos de aprendizaje (2-4 puntos)\n"
        "3. Consigna mejorada (redacción clara, pasos numerados si aplica)\n"
        "4. Contenidos técnicos/conceptuales involucrados\n"
        "5. Criterios de evaluación / rúbrica breve\n"
        "6. Forma de entrega — copiá TAL CUAL esta lista, es una exigencia fija del profesor para "
        "toda entrega, no la resumas ni la cambies:\n"
        f"{REQUISITOS_FORMATO_ENTREGA}\n\n"
        "---- ENUNCIADO ORIGINAL ----\n"
        f"{texto_original}\n"
    )


def generar_mejora(nombre_materia, texto_original, contexto_curricular=""):
    """Devuelve (texto_mejorado, proveedor_usado). Prueba DeepSeek (gratis) y
    cae a Gemini si falla, según panel_control.proveedor_ia."""
    prompt = construir_prompt_mejora(nombre_materia, texto_original, contexto_curricular)
    return proveedor_ia.generar_texto(prompt)


def guardar_docx(nombre_materia, titulo_tp, texto_mejorado, link_original=None):
    carpeta_materia = os.path.join(CARPETA_SALIDA, _limpiar_nombre(nombre_materia))
    os.makedirs(carpeta_materia, exist_ok=True)
    ruta = os.path.join(carpeta_materia, f"Mejora - {_limpiar_nombre(titulo_tp)}.docx")

    doc = Document()

    # Encabezado de página (se repite en todas las hojas del documento).
    header_para = doc.sections[0].header.paragraphs[0]
    header_run = header_para.add_run(f"{nombre_materia} — {NOMBRE_PROFESOR}")
    header_run.bold = True
    header_run.font.size = Pt(9)
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading(f"Mejora — {titulo_tp}", level=1)
    doc.add_paragraph(f"Materia: {nombre_materia}")
    doc.add_paragraph(f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if link_original:
        doc.add_paragraph(f"Actividad original: {link_original}")
    doc.add_paragraph(
        "Esta es una PROPUESTA de mejora. No reemplaza la actividad original en Classroom: "
        "revisala y publicala manualmente si te sirve."
    )
    doc.add_paragraph("")
    for linea in texto_mejorado.split("\n"):
        doc.add_paragraph(linea)
    doc.save(ruta)
    return ruta


def mejorar_actividad(nombre_materia, course_id, trabajo, service, service_drive):
    """Orquesta una mejora: registra la tarea en la cola, genera el texto y
    guarda el docx. Devuelve (ruta_docx, texto_mejorado, proveedor) — el
    texto se necesita aparte del archivo para poder ofrecer después
    'Subir y sustituir' sin tener que volver a generarlo."""
    titulo_tp = trabajo.get("title", "Trabajo práctico")
    link_original = trabajo.get("alternateLink")
    tarea_id = memoria.registrar_tarea(
        AGENTE, f"Mejorando: {titulo_tp}", curso=nombre_materia, estado="en_curso"
    )
    try:
        texto_original = classroom.obtener_contexto_consigna(
            service, service_drive, course_id, trabajo["id"], trabajo
        )
        if not texto_original.strip():
            raise RuntimeError(
                "No se pudo extraer texto de la consigna original "
                "(sin descripción ni materiales legibles)."
            )
        contexto_curricular = memoria.contexto_curricular(nombre_materia)
        texto_mejorado, proveedor = generar_mejora(nombre_materia, texto_original, contexto_curricular)
        ruta = guardar_docx(nombre_materia, titulo_tp, texto_mejorado, link_original)
        memoria.agregar_memoria(
            "actividad_mejorada", clave=titulo_tp, valor=ruta, curso=nombre_materia, agente=AGENTE
        )
        memoria.actualizar_estado_tarea(tarea_id, "completada")
        print(f"✅ Copia mejorada guardada en: {ruta} (generado con {proveedor})")
        return ruta, texto_mejorado, proveedor
    except Exception as e:
        memoria.actualizar_estado_tarea(tarea_id, "error")
        print(f"❌ Error mejorando '{titulo_tp}': {e}")
        raise


def crear_borrador_reemplazo(nombre_materia, course_id, trabajo, texto_mejorado):
    """Deja pendiente de aprobación reemplazar la consigna ORIGINAL de esta
    actividad en Classroom por la versión mejorada. No toca Classroom
    todavía — recién al aprobar, en aprobar_y_reemplazar()."""
    titulo_original = trabajo.get("title", "Trabajo práctico")
    tarea_id = memoria.registrar_tarea(
        AGENTE,
        f"Reemplazar consigna de '{titulo_original}' por la versión mejorada — esperando tu aprobación",
        curso=nombre_materia, estado="pendiente_aprobacion",
    )
    aprobacion_id = memoria.crear_aprobacion(tarea_id, tipo="actualizar_actividad", datos={
        "course_id": course_id,
        "work_id": trabajo["id"],
        "materia": nombre_materia,
        "titulo_original": titulo_original,
        "descripcion_original": trabajo.get("description", ""),
        "descripcion_nueva": texto_mejorado,
        "agente": AGENTE,
    })
    return aprobacion_id


def aprobar_y_reemplazar(aprobacion_id, creds, descripcion_final=None):
    """Se llama desde el panel cuando el profesor aprueba: recién acá se
    sobreescribe la consigna de verdad en Classroom. Devuelve (ok, mensaje)."""
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap:
        return False, "No se encontró esa aprobación."
    if ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."

    datos = ap["datos"]
    texto_final = descripcion_final if descripcion_final is not None else datos["descripcion_nueva"]

    service = build("classroom", "v1", credentials=creds)
    try:
        service.courses().courseWork().patch(
            courseId=datos["course_id"], id=datos["work_id"],
            updateMask="description",
            body={"description": texto_final},
        ).execute()
    except Exception as e:
        return False, f"No se pudo actualizar en Classroom: {str(e)[:200]}"

    memoria.resolver_aprobacion(aprobacion_id, estado="aprobada", tarea_estado="completada")
    memoria.agregar_memoria(
        "actividad_reemplazada", clave=datos["titulo_original"], valor="reemplazada en Classroom",
        curso=datos["materia"], agente=AGENTE,
    )
    return True, f"Listo, se reemplazó la consigna de '{datos['titulo_original']}' en Classroom."


def rechazar_reemplazo(aprobacion_id):
    ap = memoria.obtener_aprobacion(aprobacion_id)
    if not ap or ap["estado"] != "pendiente":
        return False, "Esta aprobación ya fue resuelta."
    memoria.resolver_aprobacion(aprobacion_id, estado="rechazada", tarea_estado="rechazada")
    return True, "Rechazada."


def menu():
    memoria.init_db()
    memoria.agregar_agente(AGENTE, "Genera copias mejoradas de actividades ya publicadas", AREA)

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
    idx2 = int(input("Elegí un trabajo para mejorar: ")) - 1
    trabajo = trabajos[idx2]

    mejorar_actividad(curso.get("name"), curso["id"], trabajo, service, service_drive)


if __name__ == "__main__":
    menu()
