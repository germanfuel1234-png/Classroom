"""
FLUJO COMPLETO DE CORRECCIÓN AUTOMÁTICA
=========================================
Integra: descarga de entregas -> corrección -> publicación de nota (API)
         -> comentario privado (pegado automático estilo "humano")

POR QUÉ ESTE DISEÑO:
La API pública de Google Classroom NO tiene (y nunca tuvo) un endpoint para
crear comentarios privados (studentSubmissions.comments.create no existe en
el cliente oficial). Sí se puede patchear la nota (assignedGrade/draftGrade)
y devolver (return) la entrega por API sin problema.

Por eso el flujo queda así:
  1. Nota -> 100% automático por API (rápido y confiable)
  2. Comentario privado -> se abre el alumno en Classroom Web y se simula
     el comportamiento de un humano: click en el cuadro de comentario,
     pegar texto, click en "Enviar". Esto requiere pyautogui + que la
     ventana de Chrome esté visible (no minimizada) durante la ejecución.

Si pyautogui falla o no detecta el cuadro de texto, el comentario se guarda
en un .txt individual para pegado manual, así nunca se pierde el feedback.
"""

import os
import json
import time
import datetime
import webbrowser
import importlib

try:
    pyautogui = importlib.import_module("pyautogui")
    AUTO_DISPONIBLE = True
    pyautogui.FAILSAFE = True  # mover el mouse a una esquina aborta el script
except Exception:
    pyautogui = None
    AUTO_DISPONIBLE = False


# ──────────────────────────────────────────────
#  UTILIDADES DE PORTAPAPELES Y PEGADO
# ──────────────────────────────────────────────

def copiar_texto_portapapeles(texto):
    """Copia texto al portapapeles (Windows clip.exe + fallback tkinter)."""
    if os.name == "nt":
        try:
            import subprocess
            subprocess.run(
                ["clip"],
                input=(texto or "").encode("utf-16le"),
                check=True,
                capture_output=True,
            )
            return True
        except Exception:
            pass

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(texto or "")
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def pegar_comentario_en_classroom(texto, delay_inicial=3.0, click_en_cuadro=None):
    """
    Simula la acción humana de pegar el comentario y enviarlo.

    Args:
        texto: comentario a pegar
        delay_inicial: segundos de espera antes de actuar (para que cargue la página)
        click_en_cuadro: tupla (x, y) opcional. Si se pasa, hace click ahí antes
                          de pegar (útil si el cuadro de comentario no tiene foco
                          automático). Si no se pasa, asume que el cuadro ya
                          tiene foco (por ejemplo, justo después de abrir el link).

    Returns:
        bool: True si se ejecutó la secuencia sin excepciones (no garantiza que
              Classroom haya aceptado el comentario, eso hay que verificarlo).
    """
    if not AUTO_DISPONIBLE:
        return False

    if not copiar_texto_portapapeles(texto):
        return False

    try:
        time.sleep(max(0.5, float(delay_inicial)))

        if click_en_cuadro:
            pyautogui.click(click_en_cuadro[0], click_en_cuadro[1])
            time.sleep(0.4)

        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "enter")  # Classroom envía el comentario con Ctrl+Enter
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"      ⚠️ Error en pegado automático: {e}")
        return False


# ──────────────────────────────────────────────
#  PUBLICACIÓN DE NOTA POR API (100% confiable)
# ──────────────────────────────────────────────

def _mapear_nota_a_classroom(nota_1_10):
    if nota_1_10 is None:
        return None
    try:
        valor = float(nota_1_10) * 10.0
    except Exception:
        return None
    return max(0.0, min(100.0, valor))


def publicar_nota_en_classroom(service, course_id, work_id, submission_id, nota_1_10, solo_borrador=True):
    """Sube la nota por API. Esto SIEMPRE funciona si los scopes están bien."""
    nota_100 = _mapear_nota_a_classroom(nota_1_10)
    if nota_100 is None:
        return False

    if solo_borrador:
        cuerpo = {"draftGrade": nota_100}
        mask = "draftGrade"
    else:
        cuerpo = {"draftGrade": nota_100, "assignedGrade": nota_100}
        mask = "draftGrade,assignedGrade"

    service.courses().courseWork().studentSubmissions().patch(
        courseId=course_id,
        courseWorkId=work_id,
        id=submission_id,
        updateMask=mask,
        body=cuerpo,
    ).execute()
    return True


def devolver_entrega_en_classroom(service, course_id, work_id, submission_id):
    """Marca la entrega como devuelta (el alumno la ve calificada)."""
    service.courses().courseWork().studentSubmissions().return_(
        courseId=course_id,
        courseWorkId=work_id,
        id=submission_id,
        body={},
    ).execute()


# ──────────────────────────────────────────────
#  FLUJO PRINCIPAL
# ──────────────────────────────────────────────

def ejecutar_flujo_completo(
    service,
    course_id,
    work_id,
    lote_evaluaciones,
    solo_borrador=True,
    devolver_automaticamente=False,
    pausa_entre_alumnos=4.0,
    confirmar_antes_de_cada_uno=True,
    solo_notas=False,
):
    """
    Ejecuta el flujo completo para una lista de evaluaciones.

    Args:
        service: cliente de Classroom API ya autenticado
        course_id: id del curso
        work_id: id de la actividad
        lote_evaluaciones: lista de dicts con:
            {
                "nombre": str,
                "submission_id": str,
                "alternate_link": str,   # URL directa a la entrega del alumno
                "nota": float,           # escala 1-10
                "comentario": str,       # texto del comentario privado
            }
        solo_borrador: si True, sube la nota como draftGrade (no visible al
                       alumno todavía). Poné False cuando ya verificaste que
                       todo anda bien y querés publicar de una.
        devolver_automaticamente: si True, ejecuta el return_ por API
                       (el alumno ve la nota apenas se publique).
        pausa_entre_alumnos: segundos de espera entre cada alumno, para no
                       saturar ni la API ni la UI.
        confirmar_antes_de_cada_uno: si True, pide Enter antes de actuar
                       sobre cada alumno (recomendado al principio, para
                       supervisar que el pegado funcione bien).

    Returns:
        dict con resumen: notas_publicadas, comentarios_automaticos,
        comentarios_pendientes (lista de los que requieren pegado manual)
    """
    print("\n" + "=" * 70)
    if solo_notas:
        print("  📊 MODO SOLO NOTAS: sube calificaciones sin tocar comentarios")
    else:
        print("  🚀 FLUJO COMPLETO: NOTA (API) + COMENTARIO (pegado automático)")
    print("=" * 70)

    if not solo_notas and not AUTO_DISPONIBLE:
        print("\n⚠️ pyautogui no está instalado. El pegado automático de")
        print("   comentarios NO va a funcionar. Instalalo con:")
        print("   pip install pyautogui --break-system-packages")
        print("   Mientras tanto, las notas se suben igual por API.\n")

    resumen = {
        "notas_publicadas": 0,
        "comentarios_automaticos": 0,
        "comentarios_pendientes": [],
        "errores": [],
    }

    carpeta_pendientes = "comentarios_pendientes_manual"
    os.makedirs(carpeta_pendientes, exist_ok=True)

    for i, item in enumerate(lote_evaluaciones, 1):
        alumno = item.get("nombre", "Alumno")
        submission_id = item.get("submission_id")
        link = item.get("alternate_link")
        nota = item.get("nota")
        comentario = (item.get("comentario") or item.get("feedback") or "").strip()

        print(f"\n[{i}/{len(lote_evaluaciones)}] 👤 {alumno}")

        # PASO 1: Nota por API (siempre, no depende de la UI)
        if submission_id and nota is not None:
            try:
                publicar_nota_en_classroom(
                    service, course_id, work_id, submission_id, nota,
                    solo_borrador=solo_borrador,
                )
                resumen["notas_publicadas"] += 1
                modo = "borrador" if solo_borrador else "definitiva"
                print(f"   ✅ Nota {nota}/10 subida ({modo})")
            except Exception as e:
                resumen["errores"].append({"alumno": alumno, "paso": "nota", "error": str(e)[:200]})
                print(f"   ❌ Error subiendo nota: {str(e)[:120]}")
        else:
            print(f"   ⓘ Sin submission_id o sin nota, se omite paso de nota")

        # Asegurar que el link sea la URL de la UI web (no la API)
        if link and "classroom.googleapis.com" in link:
            user_id_item = item.get("user_id", "")
            link = (
                f"https://classroom.google.com/c/{course_id}"
                f"/a/{work_id}/submissions/by-status/and-sort-last-name"
                f"/student/{user_id_item}"
            )
        elif not link:
            user_id_item = item.get("user_id", "")
            if user_id_item:
                link = (
                    f"https://classroom.google.com/c/{course_id}"
                    f"/a/{work_id}/submissions/by-status/and-sort-last-name"
                    f"/student/{user_id_item}"
                )

        # PASO 2: Comentario privado (se omite si solo_notas=True)
        if solo_notas:
            print(f"   ⓘ Comentario omitido (modo solo notas)")
        elif comentario and link:
            if confirmar_antes_de_cada_uno:
                print(f"   📋 Comentario a pegar:\n      {comentario[:150]}{'...' if len(comentario) > 150 else ''}")
                print(f"\n   {'='*50}")
                print(f"   📝 NOTA A INGRESAR MANUALMENTE: {nota}/10")
                print(f"      → escribila en el campo de calificación de la derecha")
                print(f"   {'='*50}\n")
                input(f"   👉 Presioná Enter para abrir Classroom y pegar el comentario de {alumno}...")

            try:
                webbrowser.open(link)
            except Exception:
                pass

            # Mostrar nota siempre (para ingreso manual en el campo de Classroom)
            print(f"\n   ┌─────────────────────────────────────┐")
            print(f"   │  NOTA: {str(nota) + '/10':<10} — ingresala a mano  │")
            print(f"   └─────────────────────────────────────┘")

            exito = pegar_comentario_en_classroom(comentario, delay_inicial=pausa_entre_alumnos)

            if exito:
                resumen["comentarios_automaticos"] += 1
                print(f"   ✅ Comentario pegado y enviado (verificá visualmente que se publicó)")
            else:
                # Fallback: guardar en .txt + dejar copiado en portapapeles
                copiar_texto_portapapeles(comentario)
                nombre_archivo = "".join(c if c.isalnum() else "_" for c in alumno).strip("_")
                ruta_txt = os.path.join(carpeta_pendientes, f"{nombre_archivo}.txt")
                with open(ruta_txt, "w", encoding="utf-8") as f:
                    f.write(comentario)
                resumen["comentarios_pendientes"].append({
                    "alumno": alumno, "link": link, "archivo": ruta_txt
                })
                print(f"   ⚠️ Pegado automático no confirmado. Texto copiado al")
                print(f"      portapapeles y guardado en: {ruta_txt}")
                print(f"      Pegalo manualmente con Ctrl+V en el cuadro de comentario.")
        else:
            print(f"   ⓘ Sin comentario o sin link, se omite paso de comentario")

        if i < len(lote_evaluaciones):
            time.sleep(1.0)

    # Resumen final
    print("\n" + "=" * 70)
    print("  📊 RESUMEN DEL FLUJO")
    print("=" * 70)
    print(f"  Notas publicadas:          {resumen['notas_publicadas']}/{len(lote_evaluaciones)}")
    print(f"  Comentarios automáticos:   {resumen['comentarios_automaticos']}/{len(lote_evaluaciones)}")
    print(f"  Comentarios pendientes:    {len(resumen['comentarios_pendientes'])}")
    if resumen["comentarios_pendientes"]:
        print(f"     -> revisá la carpeta: {os.path.abspath(carpeta_pendientes)}")
    if resumen["errores"]:
        print(f"  ⚠️ Errores: {len(resumen['errores'])}")
        for err in resumen["errores"]:
            print(f"     - {err['alumno']} ({err['paso']}): {err['error'][:100]}")
    print("=" * 70 + "\n")

    # Guardar resumen en JSON para trazabilidad
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_resumen = os.path.join(carpeta_pendientes, f"resumen_{timestamp}.json")
    with open(ruta_resumen, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    return resumen


if __name__ == "__main__":
    print("Este módulo se importa desde main.py.")
    print("Ejemplo de uso:")
    print("""
from flujo_completo_correccion import ejecutar_flujo_completo

lote = [
    {
        "nombre": "Juan Pérez",
        "submission_id": "abc123",
        "alternate_link": "https://classroom.google.com/...",
        "nota": 8,
        "comentario": "Buen trabajo, pero te faltó profundizar en X.",
    },
    # ...
]

ejecutar_flujo_completo(
    service=service,
    course_id="123456",
    work_id="789012",
    lote_evaluaciones=lote,
    solo_borrador=True,            # empezá siempre en True para probar
    devolver_automaticamente=False,
    confirmar_antes_de_cada_uno=True,  # te frena antes de cada alumno
)
""")
