"""Cuaderno de comunicados y planillas institucionales.

A diferencia de los `agente_*.py`, este módulo no genera nada con IA — es
carga y organización de datos estructurados (observaciones de alumnos,
asistencia, notas por período), igual que ya hacen `materiales.py` y
`horario.py`. Nada de esto toca Classroom ni pasa por Aprobaciones: todo lo
carga y descarga el profesor a mano.
"""
import datetime
import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from panel_control import horario, memoria

CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "Planillas_Institucionales")

DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

PERIODOS = ("1er_cuatrimestre", "2do_cuatrimestre", "dic_feb", "final")
PERIODOS_LABEL = {
    "1er_cuatrimestre": "1er Cuatrimestre",
    "2do_cuatrimestre": "2do Cuatrimestre",
    "dic_feb": "Diciembre y Febrero",
    "final": "Final",
}
# Qué columna de %asistencia corresponde a cada período (dic_feb no tiene "proc").
COLUMNA_ASIST_POR_PERIODO = {
    "1er_cuatrimestre": "c1_asist",
    "2do_cuatrimestre": "c2_asist",
    "dic_feb": "dic_asist",
    "final": "final_asist",
}


def sugerir_fecha_clase(materia_classroom: str, anio_lectivo_id: int | None = None) -> datetime.date:
    """Busca en el horario qué día(s) de la semana se dicta esta materia y
    devuelve la fecha más reciente (hoy o hacia atrás) que caiga en alguno
    de esos días. Si no encuentra nada en el horario, devuelve hoy — el
    profesor la puede cambiar a mano igual."""
    dias_de_la_materia = {
        b["dia"] for b in horario.cargar_bloques(anio_lectivo_id) if b["curso_classroom"] == materia_classroom
    }
    if not dias_de_la_materia:
        return datetime.date.today()

    hoy = datetime.date.today()
    for delta in range(7):
        candidata = hoy - datetime.timedelta(days=delta)
        if DIAS_ES[candidata.weekday()] in dias_de_la_materia:
            return candidata
    return hoy


def recalcular_columnas_asistencia(materia: str, anio_lectivo_id: int | None = None) -> int:
    """Para cada alumno y cada período ya definido en periodos_evaluacion,
    recalcula el %asistencia y lo guarda en planillas_notas. Devuelve
    cuántas celdas actualizó."""
    periodos = memoria.listar_periodos(anio_lectivo_id)
    if not periodos:
        return 0
    alumnos = memoria.listar_alumnos(materia=materia, anio_lectivo_id=anio_lectivo_id)
    actualizadas = 0
    for alumno in alumnos:
        valores = {}
        for periodo, columna in COLUMNA_ASIST_POR_PERIODO.items():
            rango = periodos.get(periodo)
            if not rango:
                continue
            pct = memoria.calcular_pct_asistencia(
                materia, alumno["nombre"], rango["fecha_inicio"], rango["fecha_fin"], anio_lectivo_id
            )
            valores[columna] = pct
            actualizadas += 1
        if valores:
            memoria.guardar_fila_planilla(materia, alumno["nombre"], valores, anio_lectivo_id)
    return actualizadas


def texto_notas_finales(materia: str, anio_lectivo_id: int | None = None) -> str:
    """Arma el texto plano "Nombre — Nota" para pegar como anuncio en
    Classroom. Solo incluye alumnos que ya tienen final_nota cargada."""
    filas = memoria.listar_planilla(materia, anio_lectivo_id)
    lineas = [f"{f['alumno_nombre']} — {f['final_nota']}" for f in filas if f["final_nota"]]
    if not lineas:
        return ""
    return f"Notas finales — {materia}\n\n" + "\n".join(lineas)


def _limpiar_nombre(nombre):
    return re.sub(r'[\\/:*?"<>|]+', "_", (nombre or "").strip())


def exportar_planilla_excel(materia: str, anio_lectivo_id: int | None = None) -> str:
    """Arma el .xlsx con el formato institucional real (encabezados
    combinados por período). Devuelve la ruta del archivo generado."""
    alumnos = memoria.listar_alumnos(materia=materia, anio_lectivo_id=anio_lectivo_id)
    filas_planilla = {f["alumno_nombre"]: f for f in memoria.listar_planilla(materia, anio_lectivo_id)}

    wb = Workbook()
    ws = wb.active
    ws.title = "Planilla"

    negrita_centrada = Font(bold=True)
    centrado = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.merge_cells("A1:A2")
    ws["A1"] = "Alumno/a"
    ws.merge_cells("B1:B2")
    ws["B1"] = "Diagnóstico"

    # (título, cantidad de sub-columnas, [labels de sub-columnas])
    grupos = [
        ("1er Cuatrimestre", ["Proc.", "Nota", "%(Asist.)"]),
        ("2do Cuatrimestre", ["Proc.", "Nota", "%(Asist.)"]),
        ("Diciembre y Febrero", ["Nota", "%(Asist.)"]),
        ("Final", ["Proc.", "Nota", "%(Asist.)"]),
    ]
    col = 3  # A=1, B=2, arranca en C
    for titulo, sublabels in grupos:
        col_inicio = col
        col_fin = col + len(sublabels) - 1
        ws.merge_cells(start_row=1, start_column=col_inicio, end_row=1, end_column=col_fin)
        ws.cell(row=1, column=col_inicio, value=titulo)
        for i, label in enumerate(sublabels):
            ws.cell(row=2, column=col_inicio + i, value=label)
        col = col_fin + 1

    for c in range(1, col):
        celda1 = ws.cell(row=1, column=c)
        celda2 = ws.cell(row=2, column=c)
        celda1.font = negrita_centrada
        celda2.font = negrita_centrada
        celda1.alignment = centrado
        celda2.alignment = centrado

    orden_columnas = ["c1_proc", "c1_nota", "c1_asist", "c2_proc", "c2_nota", "c2_asist",
                       "dic_nota", "dic_asist", "final_proc", "final_nota", "final_asist"]

    fila = 3
    for alumno in alumnos:
        ws.cell(row=fila, column=1, value=alumno["nombre"])
        ws.cell(row=fila, column=2, value=alumno["diagnostico"] or "")
        datos = filas_planilla.get(alumno["nombre"])
        for i, clave in enumerate(orden_columnas):
            valor = datos[clave] if datos else ""
            ws.cell(row=fila, column=3 + i, value=valor or "")
        fila += 1

    for c in range(1, col):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.column_dimensions["A"].width = 28

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    ruta = os.path.join(CARPETA_SALIDA, f"Planilla - {_limpiar_nombre(materia)} - {marca}.xlsx")
    wb.save(ruta)
    return ruta
