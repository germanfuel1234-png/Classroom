"""Inicializa el panel: crea la DB, da de alta áreas/agentes e importa el
historial real de Correcciones_Classroom/reportes/*.json como tareas
completadas, para que el panel no arranque vacío.

Uso: python -m panel_control.seed
"""
import json
from pathlib import Path

from panel_control import memoria

REPORTES_DIR = Path(__file__).parent.parent / "Correcciones_Classroom" / "reportes"

AGENTES = [
    ("Director", "Lee la actividad de los demás agentes y publica un parte de situación en el Canal IA", "Dirección"),
    ("Agente Corrector", "Corrige entregas con IA (corrector_pedagogico.py + OCR)", "Corrección"),
    ("Agente Publicador", "Redacta tareas/anuncios nuevos y los deja para tu aprobación", "Publicaciones"),
    ("Agente Consultas", "Responde consultas de alumnos vía Google Form + Gmail", "Consultas"),
    ("Agente Licencias", "Avisa a cada curso correspondiente cuando el profesor va a estar de licencia", "Licencias"),
]


def sembrar_agentes():
    for nombre, rol, area in AGENTES:
        memoria.agregar_agente(nombre, rol, area)


def sembrar_historial_correcciones():
    if not REPORTES_DIR.exists():
        return 0
    importadas = 0
    for archivo in sorted(REPORTES_DIR.glob("*/*.json")):
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        registros = datos if isinstance(datos, list) else [datos]
        fecha_sesion = archivo.parent.name  # carpeta con formato YYYY-MM-DD
        for reg in registros:
            if not isinstance(reg, dict):
                continue
            nombre_alumno = reg.get("nombre", "alumno sin nombre")
            nota = reg.get("nota", "s/n")
            estado = reg.get("estado", "")
            descripcion = f"Corrigió entrega de {nombre_alumno} · nota {nota} · {estado}"
            memoria.registrar_tarea(
                agente_nombre="Agente Corrector",
                descripcion=descripcion,
                curso="Corrección Classroom",
                estado="completada",
                creado_en=f"{fecha_sesion}T00:00:00",
            )
            importadas += 1
    return importadas


def main():
    memoria.init_db()
    sembrar_agentes()
    n = sembrar_historial_correcciones()
    print(f"Panel inicializado. {n} tareas históricas importadas desde Correcciones_Classroom/reportes.")


if __name__ == "__main__":
    main()
