import datetime
import json
import os
from docx import Document
from docx.shared import Pt


def _texto_seguro(valor, default=""):
    if valor is None:
        return default
    return str(valor)


def guardar_reportes_locales(
    carpeta_destino,
    contexto_consigna,
    evaluacion,
    alumno_nombre="",
    nombre_materia="",
    nombre_tp="",
):
    """
    Guarda archivos de respaldo por alumno:
    - consigna_referencia.txt
    - comentario_privado.txt
    - informe_tecnico_pedagogico.json
    - informe_tecnico_pedagogico.docx
    """
    os.makedirs(carpeta_destino, exist_ok=True)

    consigna = _texto_seguro(contexto_consigna).strip()
    feedback = _texto_seguro((evaluacion or {}).get("feedback", "")).strip()
    estado = _texto_seguro((evaluacion or {}).get("estado", "No definido"), "No definido")
    nota = (evaluacion or {}).get("nota")
    motivo = _texto_seguro((evaluacion or {}).get("motivo", ""))

    if consigna:
        with open(os.path.join(carpeta_destino, "consigna_referencia.txt"), "w", encoding="utf-8") as f:
            f.write(consigna)

    if feedback:
        with open(os.path.join(carpeta_destino, "comentario_privado.txt"), "w", encoding="utf-8") as f:
            f.write(feedback)

    reporte_detallado = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alumno": _texto_seguro(alumno_nombre),
        "materia": _texto_seguro(nombre_materia),
        "trabajo_practico": _texto_seguro(nombre_tp),
        "estado_resultado": estado,
        "nota": nota,
        "motivo_tecnico": motivo,
        "feedback": feedback,
    }

    ruta_json = os.path.join(carpeta_destino, "informe_tecnico_pedagogico.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(reporte_detallado, f, indent=4, ensure_ascii=False)

    _guardar_informe_docx(carpeta_destino, reporte_detallado, consigna)


def _guardar_informe_docx(carpeta_destino, reporte, consigna):
    """Genera una versión DOCX del informe técnico-pedagógico."""
    doc = Document()

    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(11)

    doc.add_heading("Informe Técnico Pedagógico", level=1)

    doc.add_paragraph(f"Fecha: {_texto_seguro(reporte.get('fecha'))}")
    doc.add_paragraph(f"Alumno: {_texto_seguro(reporte.get('alumno'))}")
    doc.add_paragraph(f"Materia: {_texto_seguro(reporte.get('materia'))}")
    doc.add_paragraph(f"Trabajo práctico: {_texto_seguro(reporte.get('trabajo_practico'))}")
    doc.add_paragraph(f"Estado: {_texto_seguro(reporte.get('estado_resultado'))}")
    doc.add_paragraph(f"Nota: {_texto_seguro(reporte.get('nota'))}")

    doc.add_heading("Motivo técnico", level=2)
    doc.add_paragraph(_texto_seguro(reporte.get("motivo_tecnico"), "Sin detalle."))

    doc.add_heading("Comentario privado", level=2)
    doc.add_paragraph(_texto_seguro(reporte.get("feedback"), "Sin comentario."))

    doc.add_heading("Consigna de referencia", level=2)
    doc.add_paragraph(_texto_seguro(consigna, "No disponible."))

    ruta_docx = os.path.join(carpeta_destino, "informe_tecnico_pedagogico.docx")
    doc.save(ruta_docx)


def guardar_estado_descarga(carpeta_destino, alumno_nombre, archivos_descargados, errores_descarga=None):
    """
    Escribe estado_descarga.txt con el resumen por alumno de la descarga de adjuntos.
    """
    os.makedirs(carpeta_destino, exist_ok=True)
    errores_descarga = errores_descarga or []
    archivos_descargados = archivos_descargados or []

    lineas = [
        f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Alumno: {_texto_seguro(alumno_nombre, 'Sin nombre')}",
        "",
        f"Archivos descargados: {len(archivos_descargados)}",
    ]

    if archivos_descargados:
        lineas.append("Listado de archivos:")
        for ruta in archivos_descargados:
            lineas.append(f"- {os.path.basename(_texto_seguro(ruta))}")

    lineas.append("")
    lineas.append(f"Errores de descarga: {len(errores_descarga)}")

    if errores_descarga:
        lineas.append("Detalle de errores:")
        for err in errores_descarga:
            lineas.append(f"- {_texto_seguro(err)}")

    with open(os.path.join(carpeta_destino, "estado_descarga.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas).strip() + "\n")
