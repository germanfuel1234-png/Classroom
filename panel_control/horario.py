"""Horario de clases del profesor, guardado en la base (tabla `horarios`,
acotada por año lectivo) y editable desde la pestaña "📅 Año lectivo" del
panel — ya no se lee Horario_Clases.xlsx en la operación normal, solo se
importó una vez desde ahí al migrar (ver memoria.init_db()).

Lo usa el Agente Licencias para saber qué materias tocan un día dado.

Uso interactivo: python -m panel_control.horario
"""
from pathlib import Path

from panel_control import anios, memoria

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes"]


def cargar_bloques(anio_lectivo_id: int | None = None):
    """Devuelve una lista de dicts: dia, hora_inicio, hora_fin, materia,
    curso_grupo, curso_classroom, verificar — del año lectivo dado (o el
    activo si no se especifica)."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    with memoria.conexion() as con:
        filas = con.execute(
            """SELECT id, dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar
               FROM horarios WHERE anio_lectivo_id = ? ORDER BY dia, hora_inicio""",
            (anio_lectivo_id,),
        ).fetchall()
    return [
        {
            "id": f["id"],
            "dia": f["dia"],
            "hora_inicio": f["hora_inicio"],
            "hora_fin": f["hora_fin"],
            "materia": f["materia"],
            "curso_grupo": f["curso_grupo"] or "",
            "curso_classroom": f["curso_classroom"],
            "verificar": bool(f["verificar"]),
        }
        for f in filas
    ]


def materias_del_dia(dia: str, anio_lectivo_id: int | None = None):
    dia = (dia or "").strip().lower()
    return [b for b in cargar_bloques(anio_lectivo_id) if b["dia"] == dia]


def guardar_bloques(filas: list[dict], anio_lectivo_id: int | None = None):
    """Reemplaza TODAS las filas de horario del año dado por `filas` (lo que
    haya en la grilla editable del panel al momento de guardar). Filas sin
    materia o sin día se descartan (quedaron vacías en la edición)."""
    if anio_lectivo_id is None:
        anio_lectivo_id = anios.anio_activo_id()
    with memoria.conexion() as con:
        con.execute("DELETE FROM horarios WHERE anio_lectivo_id = ?", (anio_lectivo_id,))
        for f in filas:
            dia = (f.get("dia") or "").strip().lower()
            materia = (f.get("materia") or "").strip()
            if not dia or not materia:
                continue
            curso_classroom = (f.get("curso_classroom") or "").strip() or materia
            con.execute(
                """INSERT INTO horarios
                   (anio_lectivo_id, dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    anio_lectivo_id, dia,
                    (f.get("hora_inicio") or "").strip(),
                    (f.get("hora_fin") or "").strip(),
                    materia,
                    (f.get("curso_grupo") or "").strip(),
                    curso_classroom,
                    1 if f.get("verificar") else 0,
                ),
            )


def eliminar_bloque(bloque_id: int):
    with memoria.conexion() as con:
        con.execute("DELETE FROM horarios WHERE id = ?", (bloque_id,))


def _parsear_xlsx_legacy(ruta_xlsx: Path):
    """Lee un Horario_Clases.xlsx con el formato viejo (hoja "Horario", columnas
    dia/hora_inicio/hora_fin/materia/curso_grupo/curso_classroom/verificar).
    Solo se usa una vez, desde memoria.init_db(), para importar el horario
    existente a la base la primera vez que corre esta versión del panel."""
    import openpyxl

    wb = openpyxl.load_workbook(ruta_xlsx, data_only=True)
    ws = wb["Horario"] if "Horario" in wb.sheetnames else wb.active

    bloques = []
    for fila in ws.iter_rows(min_row=2, values_only=True):
        if not fila or not fila[0]:
            continue
        dia, hora_inicio, hora_fin, materia, curso_grupo, curso_classroom, verificar = (list(fila) + [None] * 7)[:7]
        if not materia:
            continue
        bloques.append({
            "dia": str(dia).strip().lower(),
            "hora_inicio": str(hora_inicio).strip(),
            "hora_fin": str(hora_fin).strip(),
            "materia": str(materia).strip(),
            "curso_grupo": str(curso_grupo).strip() if curso_grupo else "",
            "curso_classroom": str(curso_classroom).strip() if curso_classroom else str(materia).strip(),
            "verificar": str(verificar).strip().upper() == "SI" if verificar else False,
        })
    return bloques


if __name__ == "__main__":
    memoria.init_db()
    activo = anios.anio_activo()
    print(f"Año lectivo activo: {activo['anio'] if activo else '(ninguno)'}\n")
    for dia in DIAS:
        print(f"\n{dia.upper()}")
        for b in materias_del_dia(dia):
            flag = " ⚠️ VERIFICAR" if b["verificar"] else ""
            print(f"  {b['hora_inicio']}-{b['hora_fin']}  {b['materia']} ({b['curso_grupo']}) -> {b['curso_classroom']}{flag}")
