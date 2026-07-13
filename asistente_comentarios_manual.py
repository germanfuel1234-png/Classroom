import argparse
import glob
import json
import os
import subprocess
import sys
import time
import webbrowser


def _copiar_portapapeles(texto: str) -> bool:
    """Copia texto al portapapeles usando clip.exe en Windows y tkinter como fallback."""
    if os.name == "nt":
        try:
            proceso = subprocess.run(
                ["clip"],
                input=texto.encode("utf-16le"),
                check=True,
                capture_output=True,
                shell=True,
            )
            return True
        except Exception:
            pass

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(texto)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def _buscar_archivo_pendientes(path_opcional: str = "") -> str:
    if path_opcional and os.path.exists(path_opcional):
        return path_opcional

    candidatos = []
    candidatos.extend(glob.glob("comentarios_privados_pendientes_*.json"))
    candidatos.extend(glob.glob(os.path.join("Correcciones_Classroom", "reportes", "*", "comentarios_privados_pendientes_*.json")))
    candidatos = sorted(candidatos)
    if not candidatos:
        raise FileNotFoundError(
            "No se encontró archivo comentarios_privados_pendientes_*.json ni en la carpeta actual ni en Correcciones_Classroom/reportes/<fecha>."
        )
    return candidatos[-1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Asistente manual: abre links de Classroom y copia comentario al portapapeles"
    )
    parser.add_argument(
        "--archivo",
        default="",
        help="Ruta del JSON de pendientes. Si se omite, toma el más reciente.",
    )
    parser.add_argument(
        "--espera",
        type=float,
        default=1.2,
        help="Segundos de espera después de abrir cada link.",
    )
    args = parser.parse_args()

    try:
        archivo = _buscar_archivo_pendientes(args.archivo)
    except Exception as e:
        print(f"❌ {e}")
        return 1

    with open(archivo, "r", encoding="utf-8") as f:
        pendientes = json.load(f)

    if not isinstance(pendientes, list) or not pendientes:
        print("⚠️ El archivo no tiene comentarios pendientes.")
        return 0

    print(f"\n📄 Archivo de pendientes: {archivo}")
    print(f"👥 Comentarios a procesar: {len(pendientes)}")
    print("\nInstrucciones:")
    print("1) El script abre el link del alumno.")
    print("2) Copia el comentario al portapapeles.")
    print("3) En Classroom, pegá (Ctrl+V) y hacé clic en Publicar.")
    print("4) Volvé a esta consola y presioná Enter para seguir.")

    procesados = 0
    saltados = 0

    for i, item in enumerate(pendientes, start=1):
        alumno = item.get("alumno", "Alumno")
        link = item.get("link", "")
        nota = item.get("nota")
        comentario = (item.get("comentario_privado") or "").strip()

        print("\n" + "=" * 70)
        print(f"[{i}/{len(pendientes)}] {alumno}")
        print(f"Nota sugerida: {nota if nota is not None else 'Sin nota'}")
        print("=" * 70)

        if not comentario:
            print("⚠️ Sin comentario para este alumno. Se omite.")
            saltados += 1
            continue

        copiado = _copiar_portapapeles(comentario)
        if copiado:
            print("✅ Comentario copiado al portapapeles.")
        else:
            print("⚠️ No se pudo copiar al portapapeles. Mostrando comentario:")
            print("-" * 40)
            print(comentario)
            print("-" * 40)

        if link:
            print(f"🌐 Abriendo link: {link}")
            try:
                webbrowser.open(link)
                time.sleep(max(0.0, args.espera))
            except Exception as e:
                print(f"⚠️ No se pudo abrir el navegador: {e}")
        else:
            print("⚠️ Este registro no tiene link.")

        accion = input("Enter=continuar | s=saltar | q=salir: ").strip().lower()
        if accion == "q":
            print("⏹️ Proceso interrumpido por usuario.")
            break
        if accion == "s":
            saltados += 1
            continue

        procesados += 1

    print("\n" + "=" * 70)
    print("Resumen")
    print("=" * 70)
    print(f"✅ Marcados como procesados: {procesados}")
    print(f"⏭️ Saltados: {saltados}")
    print("\nTip: si querés repetir, ejecutá el script indicando --archivo con el JSON correcto.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
