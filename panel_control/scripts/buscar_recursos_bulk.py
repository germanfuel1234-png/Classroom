"""Procesa la cola de tareas (tabla recursos_bulk, encolada por
sincronizar_actividades.py) buscando bibliografía/videos/manuales reales con
Gemini para cada una, y guarda lo encontrado en la base como sugerencia —
no adjunta ni publica nada en Classroom por su cuenta, eso lo revisa el
profesor después desde el panel.

Pensado para cortarse y retomarse: si Gemini devuelve un error de cuota
agotada (RESOURCE_EXHAUSTED / 429 / "quota"), para ahí mismo sin tocar las
tareas que todavía dicen 'pendiente' — se pueden retomar más tarde
volviendo a correr este mismo script, sin repetir lo ya buscado. Si el
error es puntual de una sola actividad (por ejemplo un tema raro que
Gemini no pudo procesar), esa queda marcada 'error' y se sigue con las
demás — no bloquea la cola entera.

Uso: python -m panel_control.scripts.buscar_recursos_bulk [max_items]
"""
import sys

from panel_control import memoria, recursos_educativos

PISTAS_CUOTA = ("resource_exhausted", "429", "quota", "rate limit", "rate_limit")
PISTAS_TRANSITORIO = ("503", "unavailable", "overloaded", "high demand")


def _es_error_de_cuota(excepcion: Exception) -> bool:
    texto = str(excepcion).lower()
    return any(pista in texto for pista in PISTAS_CUOTA)


def _es_error_transitorio(excepcion: Exception) -> bool:
    """Gemini a veces devuelve 503 por sobrecarga momentánea del modelo — no
    es que se acabó la cuota ni que esa actividad puntual tenga un problema
    real. La dejamos 'pendiente' (no 'error') para que se reintente sola la
    próxima vez, en vez de quedar descartada para siempre."""
    texto = str(excepcion).lower()
    return any(pista in texto for pista in PISTAS_TRANSITORIO)


def procesar(max_items: int | None = None):
    memoria.init_db()
    pendientes = memoria.listar_recursos_bulk(estado="pendiente")
    if not pendientes:
        print("No hay tareas pendientes en la cola de recursos — nada para buscar.")
        return

    if max_items:
        pendientes = pendientes[:max_items]

    print(f"{len(pendientes)} tarea(s) pendiente(s) de buscar (de {memoria.contar_pendientes_recursos_bulk()} en total en la cola).\n")

    procesadas, con_error, cortado_por_cuota = 0, 0, False
    for item in pendientes:
        print(f"🔎 [{item['materia']}] {item['titulo']}...", end=" ", flush=True)
        try:
            recursos = recursos_educativos.buscar_recursos(item["materia"], item["titulo"])
        except Exception as e:
            if _es_error_de_cuota(e):
                print(f"\n\n⛔ Cuota de Gemini agotada ({str(e)[:150]}).")
                cortado_por_cuota = True
                break
            if _es_error_transitorio(e):
                print(f"↩️ Gemini saturado momentáneamente, la dejo pendiente para reintentar: {str(e)[:100]}")
                continue
            memoria.resolver_recursos_bulk(item["work_id"], estado="error", error=str(e)[:300])
            con_error += 1
            print(f"⚠️ error puntual, sigo con las demás: {str(e)[:100]}")
            continue

        memoria.resolver_recursos_bulk(item["work_id"], estado="completado", recursos=recursos)
        procesadas += 1
        print(f"✅ {len(recursos)} recurso(s)")

    restantes = memoria.contar_pendientes_recursos_bulk()
    print(f"\n{procesadas} completada(s), {con_error} con error puntual, {restantes} siguen pendientes en la cola.")
    if cortado_por_cuota:
        print("Se cortó por cuota agotada — retomá más tarde con el mismo comando, no repite lo ya hecho.")
    elif restantes:
        print(f"Quedaron {restantes} por límite de este lote — volvé a correr el comando para seguir.")


if __name__ == "__main__":
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None
    procesar(limite)
