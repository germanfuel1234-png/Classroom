"""Panel de control del "equipo" de agentes de Classroom.

Ejecutar con: streamlit run panel_control/dashboard.py
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# streamlit run resuelve sys.path según la carpeta del script (panel_control/),
# no la carpeta desde donde se invoca, así que sin esto el import de abajo falla.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from streamlit_agraph import agraph, Config, Edge, Node
from streamlit_autorefresh import st_autorefresh

import main as classroom  # reutiliza OAuth y listados ya probados
from panel_control import agente_consultas, agente_corrector, agente_director, agente_evaluador, agente_licencias, agente_mejorador, agente_publicador, anios, cuaderno, horario, ia_local, materiales, memoria, sync_materias
from panel_control.scripts import buscar_recursos_bulk, sincronizar_actividades
from panel_control.estilos import CSS
from panel_control.identidad import NOMBRE_PROFESOR

st.set_page_config(page_title="Classroom · Panel de Agentes", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

# Paleta tomada del mockup de referencia (index-design.html): verde neón como
# acento, ámbar para alerta, rojo para riesgo/ausencia.
COLOR_AREA = {
    "Dirección": "#E6AD30",
    "Corrección": "#3FA7FF",
    "Publicaciones": "#71EF8A",
    "Consultas": "#C084FC",
    "Licencias": "#FF6B6B",
}
COLOR_INACTIVO = "#5c6773"
COLOR_TIPO = {
    "actividad_mejorada": "#71EF8A",
    "diseno_curricular": "#E6AD30",
}
COLOR_TIPO_DEFAULT = "#3FA7FF"
COLOR_CURSO = "#E6AD30"
COLOR_AGENTE_MEMORIA = "#E0ECE9"

AGENTE_ICONOS = {
    "Director": "🧭",
    "Agente Corrector": "✅",
    "Agente Mejorador": "✨",
    "Agente Consultas": "💬",
    "Agente Publicador": "📣",
    "Agente Licencias": "🏖️",
    "Agente Evaluador": "📝",
}
ICONO_DEFAULT = "🤖"


def icono_agente(nombre: str) -> str:
    return AGENTE_ICONOS.get(nombre, ICONO_DEFAULT)


def hace(iso_ts: str) -> str:
    """Convierte un timestamp ISO guardado en la base a texto relativo
    ('hace 5 min'), para que el panel se lea de un vistazo en vez de tener
    que descifrar fechas ISO."""
    if not iso_ts:
        return ""
    try:
        dt = datetime.fromisoformat(iso_ts)
    except ValueError:
        return iso_ts
    segundos = (datetime.now() - dt).total_seconds()
    if segundos < 0:
        return dt.strftime("%d/%m %H:%M")
    if segundos < 60:
        return "recién"
    minutos = int(segundos // 60)
    if minutos < 60:
        return f"hace {minutos} min"
    horas = int(minutos // 60)
    if horas < 24:
        return f"hace {horas} h"
    dias = int(horas // 24)
    if dias < 7:
        return f"hace {dias} d"
    return dt.strftime("%d/%m/%Y")


def mensaje_error_amigable(e: Exception) -> str:
    """Traduce errores comunes de las APIs a algo entendible, en vez del
    traceback crudo. Distingue cuota diaria agotada (no se arregla esperando
    unos segundos) de un problema transitorio, y junta los dos motivos si
    fallaron los dos proveedores de IA a la vez."""
    texto = str(e)
    texto_l = texto.lower()

    sin_deepseek = "insufficient balance" in texto_l or ("402" in texto and "deepseek" in texto_l)
    cuota_diaria_gemini = (
        ("resource_exhausted" in texto_l or "429" in texto or "quota" in texto_l)
        and ("perday" in texto_l or "free_tier" in texto_l or "free tier" in texto_l)
    )
    gemini_saturado = ("resource_exhausted" in texto_l or "429" in texto or "quota" in texto_l) and not cuota_diaria_gemini

    if sin_deepseek and cuota_diaria_gemini:
        return (
            "Los dos proveedores de IA están sin disponibilidad ahora mismo: DeepSeek no tiene saldo "
            "cargado, y Gemini agotó su cuota GRATIS diaria (ej. 20 pedidos/día en gemini-2.5-flash). "
            "Esto NO se arregla esperando unos segundos — hay que cargarle saldo a DeepSeek en "
            "platform.deepseek.com (lo más rápido) o activar facturación en Gemini."
        )
    if sin_deepseek:
        return "DeepSeek no tiene saldo cargado — cargale unos dólares en platform.deepseek.com o va a seguir cayendo a Gemini."
    if cuota_diaria_gemini:
        return (
            "Se agotó la cuota GRATIS diaria de Gemini (ej. 20 pedidos/día en gemini-2.5-flash). "
            "Esto NO se arregla esperando unos segundos — hay que cargarle saldo a DeepSeek o "
            "activar facturación en Gemini para seguir probando hoy."
        )
    if gemini_saturado:
        return "Gemini está saturado o al límite de pedidos por minuto ahora mismo. Probá de nuevo en un rato."
    return texto[:300]


_ICONO_ADJUNTO = {"link": "🔗", "video": "🎥", "archivo": "📄", "form": "📝"}


def _resumir_materiales_classroom(materials):
    """Parsea (sin descargar nada, el campo `materials` ya viene incluido en
    el courseWork que devuelve Classroom) los adjuntos de una actividad en
    una lista de {"tipo", "titulo", "url"} — tipo en 'link'/'video'/'archivo'/'form'."""
    resumen = []
    for m in materials or []:
        if "link" in m:
            resumen.append({
                "tipo": "link",
                "titulo": m["link"].get("title") or m["link"].get("url", ""),
                "url": m["link"].get("url", ""),
            })
        elif "youtubeVideo" in m:
            yt = m["youtubeVideo"]
            resumen.append({
                "tipo": "video",
                "titulo": yt.get("title") or "Video de YouTube",
                "url": yt.get("alternateLink", ""),
            })
        elif "driveFile" in m:
            df = m["driveFile"].get("driveFile", {})
            resumen.append({
                "tipo": "archivo",
                "titulo": df.get("title", "Archivo"),
                "url": df.get("alternateLink", ""),
            })
        elif "form" in m:
            resumen.append({
                "tipo": "form",
                "titulo": m["form"].get("title") or "Formulario",
                "url": m["form"].get("formUrl", ""),
            })
    return resumen


def _contar_por_tipo(adjuntos):
    conteo = {}
    for a in adjuntos:
        conteo[a["tipo"]] = conteo.get(a["tipo"], 0) + 1
    return conteo


memoria.init_db()

col_titulo, col_refresh = st.columns([5, 1])
col_titulo.title("Panel de Agentes — Classroom")
with col_refresh:
    st.write("")
    auto = st.checkbox("Auto-actualizar", value=False, help="Refresca el panel solo cada 30s")
    if st.button("🔄 Actualizar ahora"):
        st.rerun()
if auto:
    st_autorefresh(interval=30_000, key="autorefresh")

m = memoria.metricas()
aprobaciones_pendientes = memoria.listar_aprobaciones(estado="pendiente")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Áreas", m["areas"])
c2.metric("Agentes", m["agentes"])
c3.metric("Tareas totales", m["total_tareas"])
c4.metric("Completadas", m["por_estado"].get("completada", 0))
c5.metric("Esperando tu aprobación", len(aprobaciones_pendientes))

if aprobaciones_pendientes:
    st.warning(
        f"⏳ Tenés **{len(aprobaciones_pendientes)}** borrador(es) esperando tu aprobación "
        "(notas, publicaciones, respuestas, avisos...). Nada de eso salió todavía — andá a la "
        "pestaña **Aprobaciones** para revisarlos."
    )

PAGINAS = [
    ("centro", "🏠", "Centro de Operaciones", None),
    ("canal", "📡", "Canal IA", None),
    ("ejecutar", "🚀", "Ejecutar agentes", None),
    ("org", "🗂️", "Organigrama", None),
    ("aprobaciones", "✅", "Aprobaciones", len(aprobaciones_pendientes)),
    ("materias", "📚", "Materias", None),
    ("cuaderno", "📓", "Cuaderno", None),
    ("cola", "📋", "Cola de tareas", None),
    ("memoria", "🧠", "Memoria compartida", None),
    ("anio", "📅", "Año lectivo", None),
]
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "centro"

with st.sidebar:
    st.markdown("### 🎓 Panel de Agentes")
    st.caption(NOMBRE_PROFESOR)
    st.divider()
    for clave, icono, etiqueta, badge in PAGINAS:
        activa = st.session_state["pagina_actual"] == clave
        texto_boton = f"{icono}  {etiqueta}" + (f"  · {badge}" if badge else "")
        if st.button(texto_boton, key=f"nav_{clave}", width="stretch", type="primary" if activa else "secondary"):
            st.session_state["pagina_actual"] = clave
            st.rerun()

pagina_actual = st.session_state["pagina_actual"]

if pagina_actual == "canal":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Acá cada agente va dejando, como si fuera un chat, qué hizo — un TP nuevo, una "
            "corrección, un aviso. Es solo para que veas la actividad de un vistazo, no hace "
            "falta que hagas nada acá.\n\n"
            "- El botón **🧭 Pedir resumen del Director** es el único que genera algo nuevo (con "
            "IA) — un parte de situación corto. No lo hace solo, se lo pedís cuando quieras.\n"
            "- Nada de lo que ves acá se publicó en Classroom todavía — eso pasa siempre en la "
            "pestaña **Aprobaciones**."
        )
    st.subheader("📡 Canal IA")
    st.caption(
        "Cada vez que un agente hace algo, deja acá su aporte — como un chat entre las IA. "
        "El Director no actúa por su cuenta: solo lee este mismo canal y, si se lo pedís, "
        "publica un parte de situación."
    )
    if st.button("🧭 Pedir resumen del Director", key="canal_pedir_director"):
        with st.spinner("El Director está revisando la actividad reciente..."):
            try:
                agente_director.publicar_supervision()
            except Exception as e:
                st.error(mensaje_error_amigable(e))
        st.rerun()

    st.divider()

    mensajes_canal = memoria.listar_tareas(limite=50)
    if not mensajes_canal:
        st.info("Todavía no hay actividad en el canal.")
    else:
        for t in reversed(mensajes_canal):  # más vieja arriba, como cualquier chat
            with st.chat_message(name=t["agente_nombre"], avatar=icono_agente(t["agente_nombre"])):
                st.write(t["descripcion"])
                partes_caption = [hace(t["creado_en"])]
                if t["curso"]:
                    partes_caption.append(t["curso"])
                partes_caption.append(t["estado"])
                st.caption(" · ".join(partes_caption))

elif pagina_actual == "centro":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "El punto de partida del día: acá escribís vos la prioridad del momento (nadie la "
            "inventa sola), ves qué tareas están sin resolver, prendés/apagás agentes puntuales "
            "(por ejemplo si querés enfocarte en mejorar actividades y no que Publicador/Licencias "
            "hagan nada mientras tanto), y controlás la IA local (Ollama) y cuánto usaste hoy de "
            "cada proveedor de IA."
        )
    st.subheader("🎯 Directiva actual")
    directiva_actual = memoria.obtener_directiva()
    nueva_directiva = st.text_area(
        "¿Cuál es la prioridad del momento? (la escribís vos, no la inventa el sistema)",
        value=directiva_actual, height=80, key="directiva_input",
    )
    if st.button("Guardar directiva") and nueva_directiva.strip() != directiva_actual.strip():
        memoria.set_directiva(nueva_directiva.strip())
        st.success("Directiva actualizada.")
        st.rerun()

    st.divider()

    col_riesgos, col_feed = st.columns([1, 1])

    with col_riesgos:
        st.subheader("📋 Tareas pendientes")

        ESTADOS_NO_TERMINALES = ("pendiente", "en_curso", "pendiente_aprobacion")
        pendientes_centro = [
            t for t in memoria.listar_tareas(limite=200) if t["estado"] in ESTADOS_NO_TERMINALES
        ]
        pendientes_centro.sort(key=lambda t: t["creado_en"])  # más vieja primero — la que más espera

        if not pendientes_centro:
            st.success("Sin tareas pendientes por ahora.")
        else:
            for t in pendientes_centro[:6]:
                st.warning(
                    f"{icono_agente(t['agente_nombre'])} **{t['agente_nombre']}** "
                    f"({t['curso'] or 'general'}) · {hace(t['creado_en'])} — {t['descripcion'][:80]}"
                )
            if len(pendientes_centro) > 6:
                st.caption(f"+ {len(pendientes_centro) - 6} más — mirá la pestaña 'Cola de tareas' para verlas todas.")

    with col_feed:
        st.subheader("📋 Últimos aportes de los agentes")
        ultimas = memoria.listar_tareas(limite=8)
        if not ultimas:
            st.info("Todavía no hay actividad registrada.")
        else:
            for t in ultimas:
                st.write(f"{icono_agente(t['agente_nombre'])} **{t['agente_nombre']}** · {hace(t['creado_en'])}")
                st.caption(t["descripcion"])

    st.divider()
    st.subheader("🔌 Agentes")
    st.caption(
        "Apagá los que no quieras usar por ahora (ej. mientras te dedicás a pulir actividades con "
        "Mejorador/Evaluador) — un agente apagado no deja generar trabajo nuevo desde 'Ejecutar "
        "agentes' hasta que lo prendas de nuevo. No pierde nada de lo que ya hizo."
    )
    AGENTES_TOGGLEABLES = [
        ("Agente Corrector", "✅"),
        ("Agente Publicador", "📣"),
        ("Agente Mejorador", "✨"),
        ("Agente Evaluador", "📝"),
        ("Agente Consultas", "💬"),
        ("Agente Licencias", "🏖️"),
    ]
    cols_agentes_toggle = st.columns(3)
    for i, (nombre_ag, icono_ag) in enumerate(AGENTES_TOGGLEABLES):
        activo_ag = memoria.agente_esta_activo(nombre_ag)
        with cols_agentes_toggle[i % 3]:
            nuevo_valor = st.toggle(f"{icono_ag} {nombre_ag}", value=activo_ag, key=f"toggle_agente_{nombre_ag}")
        if nuevo_valor != activo_ag:
            memoria.actualizar_estado_agente(nombre_ag, "activo" if nuevo_valor else "inactivo")
            st.rerun()

    st.divider()
    st.subheader("🖥️ IA Local (Ollama)")
    st.caption(
        "Corre en esta compu, gratis y sin límite de cuota — se usa como respaldo cuando DeepSeek/Gemini "
        "fallan. La calidad de redacción es más floja que la de Gemini (es un modelo chico para no "
        "sobrecargar la máquina). Apagala si querés liberar RAM/CPU cuando no la estés usando."
    )
    ia_corriendo = ia_local.esta_corriendo()
    col_estado, col_switch = st.columns([4, 1])
    col_estado.write("🟢 Corriendo" if ia_corriendo else "⚪ Apagada")
    if ia_corriendo:
        if col_switch.button("Apagar", key="ia_local_apagar"):
            with st.spinner("Apagando..."):
                apagada = ia_local.apagar()
            if apagada:
                st.success("IA local apagada.")
            else:
                st.warning("Pedí que se apague pero todavía responde — puede tardar un poco más.")
            st.rerun()
    else:
        if col_switch.button("Prender", key="ia_local_prender"):
            with st.spinner("Prendiendo IA local (puede tardar unos segundos)..."):
                try:
                    prendida = ia_local.prender()
                    if prendida:
                        st.success("IA local lista.")
                    else:
                        st.warning("La pedí prender pero todavía no responde — probá de nuevo en unos segundos.")
                except Exception as e:
                    st.error(str(e))
            st.rerun()

    st.divider()
    st.subheader("📊 Uso de IA hoy")
    st.caption(
        "Cuántas veces le pedimos algo a cada proveedor hoy. La mayoría de los proveedores gratuitos "
        "(Gemini incluido, el que más usamos) no dejan consultar por API cuánta cuota te queda — así "
        "que esto no es 'cuota restante', es tu propio conteo real de uso, para tener una idea de "
        "cuánto venís gastando. No incluye lo que usa el Agente Corrector para leer/OCR entregas de "
        "alumnos, solo lo que generan Publicador/Mejorador/Evaluador/Consultas/Director y la búsqueda "
        "de bibliografía."
    )
    uso_hoy = memoria.contar_uso_proveedores_hoy()
    if not uso_hoy:
        st.caption("Todavía no se usó ningún proveedor de IA hoy.")
    else:
        cols_uso = st.columns(len(uso_hoy))
        for col, (proveedor, cantidad) in zip(cols_uso, uso_hoy.items()):
            col.metric(proveedor.capitalize(), cantidad)

elif pagina_actual == "ejecutar":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Acá es donde ponés a trabajar a cada agente: corregir una actividad, redactar un "
            "TP o anuncio nuevo, mejorar una actividad existente, armar una evaluación, revisar "
            "consultas de alumnos, o avisar una licencia. **Ninguno de estos botones publica nada "
            "en Classroom directamente** — todos dejan un borrador esperando tu revisión en la "
            "pestaña **Aprobaciones**. Un agente apagado (desde Centro de Operaciones) no te va a "
            "dejar generar nada nuevo con él hasta que lo prendas."
        )
    st.caption(
        "Corré los agentes desde acá, sin abrir la terminal. Ninguno publica nada solo: "
        "los que generan contenido dejan el borrador esperando en Aprobaciones."
    )

    col_load, col_status = st.columns([1, 3])
    if col_load.button("🔄 Cargar mis materias de Classroom"):
        with st.spinner("Conectando con Classroom..."):
            try:
                creds = classroom.obtener_credenciales()
                service = build("classroom", "v1", credentials=creds)
                st.session_state["cursos_classroom"] = classroom.listar_materias_activas(service)
                st.session_state.pop("mej_trabajos", None)
            except Exception as e:
                st.error(f"No se pudo conectar: {e}")
        st.rerun()

    cursos = st.session_state.get("cursos_classroom")
    if not cursos:
        st.info("Hacé clic en '🔄 Cargar mis materias de Classroom' para empezar.")
    else:
        col_status.caption(f"{len(cursos)} materias cargadas.")
        nombres_cursos = [c["name"] for c in cursos]
        mensaje_agente_apagado = "🔌 Este agente está apagado — prendelo en 'Centro de Operaciones' para poder usarlo."

        if st.button("🔍 Revisar novedades ahora (consultas nuevas en todas mis materias)", key="revisar_todo"):
            with st.spinner("Revisando consultas nuevas materia por materia..."):
                try:
                    creds = classroom.obtener_credenciales()
                    materias_con_form = agente_consultas.listar_materias_con_formulario()
                    total_nuevas, revisadas = 0, 0
                    for nombre_materia in materias_con_form:
                        creadas = agente_consultas.procesar_consultas(nombre_materia, creds)
                        total_nuevas += len(creadas)
                        revisadas += 1
                    if revisadas == 0:
                        st.info(
                            "Ninguna materia tiene todavía un Form de consultas creado. "
                            "Creá uno desde '💬 Agente Consultas' más abajo y después este botón ya la va a incluir."
                        )
                    elif total_nuevas:
                        st.success(f"Revisé {revisadas} materia(s): {total_nuevas} consulta(s) nueva(s) — revisalas en Aprobaciones.")
                    else:
                        st.info(f"Revisé {revisadas} materia(s) con Form: sin consultas nuevas por ahora.")
                except Exception as e:
                    st.error(mensaje_error_amigable(e))
        st.caption(
            "Chequea todas las materias de una — no hace falta entrar agente por agente. "
            "(Solo consultas por ahora: corregir notas y avisos de licencia se dejan para cuando "
            "vos elijas la actividad o la fecha, abajo.)"
        )

        with st.expander("🔄 Sincronizar Materias (trae actividades/temas/alumnos)"):
            st.caption(
                "Actividades y entregas cambian todo el tiempo; alumnos y temas casi nunca. "
                "Desmarcá lo que no cambió para que la actualización sea más rápida (menos llamadas a Classroom)."
            )
            c1, c2, c3 = st.columns(3)
            incluir_actividades = c1.checkbox("Actividades y entregas", value=True, key="sync_incluir_act")
            incluir_temas = c2.checkbox("Temas", value=True, key="sync_incluir_temas")
            incluir_alumnos = c3.checkbox("Alumnos", value=True, key="sync_incluir_alumnos")

            modo = st.radio("Alcance", ["Todas las materias", "Una sola materia"], horizontal=True, key="sync_modo")
            curso_sync_una = None
            if modo == "Una sola materia":
                curso_sync_una = st.selectbox("Materia", nombres_cursos, key="sync_materia_una")

            if st.button("Actualizar ahora", key="run_sync", type="primary"):
                a_sincronizar = [c for c in cursos if c["name"] == curso_sync_una] if modo == "Una sola materia" else cursos
                barra = st.progress(0.0)
                completadas = 0
                try:
                    creds = classroom.obtener_credenciales()
                    service = build("classroom", "v1", credentials=creds)
                    for i, c in enumerate(a_sincronizar):
                        barra.progress((i + 1) / len(a_sincronizar), text=f"Actualizando '{c['name']}'...")
                        sync_materias.sincronizar_materia(
                            c["name"], c["id"], service,
                            actividades=incluir_actividades, temas=incluir_temas, alumnos=incluir_alumnos,
                        )
                        completadas += 1
                    st.success(f"Listo, {completadas} materia(s) actualizada(s) — mirá la pestaña Materias.")
                except Exception as e:
                    if completadas:
                        st.warning(f"Se actualizaron {completadas} de {len(a_sincronizar)} antes de fallar.")
                    st.error(mensaje_error_amigable(e))

        with st.expander("✅ Agente Corrector — corregir una actividad"):
            st.caption(
                "Evalúa automáticamente a todos los alumnos de una actividad (nota + feedback). "
                "No publica nada solo: te deja la tabla completa en Aprobaciones para que la revises, "
                "edites nota o feedback si hace falta, y recién ahí la publiques."
            )
            curso_cor = st.selectbox("Materia", nombres_cursos, key="cor_materia")

            if st.button("🔄 Ver actividades de esta materia", key="cor_cargar_trabajos"):
                curso_obj = next(c for c in cursos if c["name"] == curso_cor)
                with st.spinner("Buscando actividades..."):
                    try:
                        creds = classroom.obtener_credenciales()
                        service = build("classroom", "v1", credentials=creds)
                        st.session_state["cor_trabajos"] = classroom.listar_trabajos_del_curso(service, curso_obj["id"])
                        st.session_state["cor_trabajos_materia"] = curso_cor
                    except Exception as e:
                        st.error(mensaje_error_amigable(e))

            trabajos_cor = st.session_state.get("cor_trabajos")
            if trabajos_cor and st.session_state.get("cor_trabajos_materia") == curso_cor:
                opciones_cor = [f"{i+1}. {t.get('title', 'Sin título')}" for i, t in enumerate(trabajos_cor)]
                elegido_cor = st.selectbox("Actividad a corregir", opciones_cor, key="cor_actividad")
                idx_cor = opciones_cor.index(elegido_cor)
                trabajo_cor = trabajos_cor[idx_cor]

                activo_cor = memoria.agente_esta_activo(agente_corrector.AGENTE)
                if not activo_cor:
                    st.caption(mensaje_agente_apagado)
                if st.button("Generar correcciones", key="cor_generar", type="primary", disabled=not activo_cor):
                    curso_obj = next(c for c in cursos if c["name"] == curso_cor)
                    with st.spinner("Evaluando entregas (puede tardar si hay muchos alumnos)..."):
                        try:
                            creds = classroom.obtener_credenciales()
                            service = build("classroom", "v1", credentials=creds)
                            service_drive = build("drive", "v3", credentials=creds)
                            _, lote = agente_corrector.generar_lote_correccion(
                                curso_obj["name"], curso_obj["id"], trabajo_cor, service, service_drive
                            )
                            if lote:
                                st.success(f"{len(lote)} alumno(s) evaluado(s) — revisalos en Aprobaciones antes de publicar.")
                            else:
                                st.info("No hay alumnos para evaluar en esta actividad.")
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
            elif trabajos_cor is not None:
                st.caption("Cambiaste de materia — hacé clic en 'Ver actividades' de nuevo para esta.")

        with st.expander("📣 Agente Publicador — nueva tarea o anuncio"):
            curso_pub = st.selectbox("Materia", nombres_cursos, key="pub_materia")
            tipo_pub = st.radio("Tipo", ["tarea", "anuncio"], horizontal=True, key="pub_tipo")
            tema_pub = st.text_area("Tema / brief (de qué trata)", key="pub_tema", height=80)
            fecha_pub, puntos_pub = None, None
            buscar_recursos_pub = False
            if tipo_pub == "tarea":
                c1, c2 = st.columns(2)
                if c1.checkbox("Poner fecha de entrega", key="pub_usar_fecha"):
                    fecha_pub = c1.date_input("Fecha de entrega", key="pub_fecha").isoformat()
                if c2.checkbox("Poner puntaje", key="pub_usar_puntos"):
                    puntos_pub = c2.number_input("Puntaje máximo", min_value=1, value=100, key="pub_puntos")
                buscar_recursos_pub = st.checkbox(
                    "🔎 Buscar también bibliografía, videos y manual para adjuntar (usa 1 pedido extra de Gemini)",
                    value=False, key="pub_buscar_recursos",
                    help="Busca de verdad en internet (no inventa links) — vas a poder revisar cada recurso "
                         "antes de aprobar la publicación.",
                )
            activo_pub = memoria.agente_esta_activo(agente_publicador.AGENTE)
            if not activo_pub:
                st.caption(mensaje_agente_apagado)
            if st.button("Generar borrador", key="pub_generar", type="primary",
                         disabled=not tema_pub.strip() or not activo_pub):
                curso_obj = next(c for c in cursos if c["name"] == curso_pub)
                with st.spinner("Redactando con IA..." + (" y buscando recursos..." if buscar_recursos_pub else "")):
                    try:
                        agente_publicador.crear_borrador_publicacion(
                            curso_obj["name"], curso_obj["id"], tipo_pub, tema_pub, fecha_pub, puntos_pub,
                            buscar_recursos=buscar_recursos_pub,
                        )
                        st.success("Borrador listo — revisalo en la pestaña Aprobaciones.")
                    except Exception as e:
                        st.error(mensaje_error_amigable(e))

        with st.expander("✨ Agente Mejorador — mejorar una actividad existente"):
            curso_mej = st.selectbox("Materia", nombres_cursos, key="mej_materia")
            if st.button("🔄 Sincronizar actividades de esta materia", key="mej_cargar"):
                curso_obj = next(c for c in cursos if c["name"] == curso_mej)
                try:
                    creds = classroom.obtener_credenciales()
                    service = build("classroom", "v1", credentials=creds)
                    st.session_state["mej_trabajos"] = classroom.listar_trabajos_del_curso(service, curso_obj["id"])
                    st.session_state.pop("mej_resultado", None)
                    st.rerun()
                except Exception as e:
                    st.error(mensaje_error_amigable(e))

            trabajos_mej = st.session_state.get("mej_trabajos")
            if trabajos_mej:
                opciones_mej = [f"{i + 1}. {t.get('title', 'Sin título')}" for i, t in enumerate(trabajos_mej)]
                elegido_idx = st.selectbox(
                    "Número de actividad", range(len(opciones_mej)),
                    format_func=lambda i: opciones_mej[i], key="mej_trabajo_idx",
                )
                trabajo_elegido = trabajos_mej[elegido_idx]

                activo_mej = memoria.agente_esta_activo(agente_mejorador.AGENTE)
                if not activo_mej:
                    st.caption(mensaje_agente_apagado)
                if st.button("✨ Generar mejora", key="mej_generar", type="primary", disabled=not activo_mej):
                    curso_obj = next(c for c in cursos if c["name"] == curso_mej)
                    with st.spinner("Generando versión mejorada..."):
                        try:
                            creds = classroom.obtener_credenciales()
                            service = build("classroom", "v1", credentials=creds)
                            service_drive = build("drive", "v3", credentials=creds)
                            ruta, texto_mejorado, proveedor = agente_mejorador.mejorar_actividad(
                                curso_obj["name"], curso_obj["id"], trabajo_elegido, service, service_drive
                            )
                            st.session_state["mej_resultado"] = {
                                "curso": curso_obj, "trabajo": trabajo_elegido,
                                "ruta": ruta, "texto": texto_mejorado, "proveedor": proveedor,
                            }
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))

                resultado_mej = st.session_state.get("mej_resultado")
                if resultado_mej and resultado_mej["trabajo"]["id"] == trabajo_elegido["id"]:
                    st.success(f"Mejora lista (vía {resultado_mej['proveedor']}).")
                    with open(resultado_mej["ruta"], "rb") as f:
                        st.download_button(
                            "⬇️ Descargar la versión mejorada (.docx)",
                            data=f.read(),
                            file_name=os.path.basename(resultado_mej["ruta"]),
                            key="mej_descargar",
                        )
                    with st.expander("Vista previa del texto"):
                        st.text(resultado_mej["texto"])

                    st.caption(
                        "⚠️ Esto sobreescribe la consigna ORIGINAL de esta actividad en Classroom. "
                        "No se publica solo: queda pendiente en Aprobaciones para que lo revises antes."
                    )
                    if st.button("📤 Subir y sustituir la actividad actual", key="mej_reemplazar"):
                        agente_mejorador.crear_borrador_reemplazo(
                            resultado_mej["curso"]["name"], resultado_mej["curso"]["id"],
                            resultado_mej["trabajo"], resultado_mej["texto"],
                        )
                        st.success("Listo — revisalo y aprobalo en la pestaña Aprobaciones antes de que se suba de verdad.")
                        del st.session_state["mej_resultado"]
                        st.rerun()

        with st.expander("📝 Agente Evaluador — armar una evaluación"):
            st.caption(
                "Arma una evaluación (teoría + práctica) a partir de actividades que ya diste. "
                "Genera un .docx local — no toca Classroom, lo bajás y lo usás como quieras. "
                "Lee todo de tu base ya sincronizada, no hace falta cargar nada de Classroom acá."
            )
            materias_eval = sorted({a["materia"] for a in memoria.listar_actividades_cache()})
            if not materias_eval:
                st.info(
                    "Todavía no hay actividades sincronizadas. Corré "
                    "`python -m panel_control.scripts.sincronizar_actividades` primero."
                )
            else:
                col_mat_eval, col_anio_eval = st.columns(2)
                materia_eval = col_mat_eval.selectbox("Materia", materias_eval, key="eval_materia")
                anio_eval = col_anio_eval.selectbox(
                    "Año curricular", list(agente_evaluador.ANIOS_DISPONIBLES.keys()), key="eval_anio",
                    help="Define qué contenidos mínimos usar como referencia de nivel — la misma materia "
                         "puede tener contenidos distintos según el año.",
                )

                candidatas_eval = [
                    a for a in memoria.listar_actividades_cache(materia_eval) if a.get("tipo") == "ASSIGNMENT"
                ]
                if not candidatas_eval:
                    st.info("Esta materia no tiene actividades tipo tarea sincronizadas.")
                else:
                    st.caption("Elegí qué actividades ya dadas usar como base:")
                    seleccionadas_eval = []
                    for a in candidatas_eval:
                        if st.checkbox(a["titulo"], key=f"eval_check_{a['work_id']}"):
                            seleccionadas_eval.append(a)
                    st.caption(f"{len(seleccionadas_eval)} de {len(candidatas_eval)} actividad(es) tildada(s).")
                    incluir_practica_eval = st.checkbox(
                        "Incluir parte práctica además de la teórica", value=True, key="eval_practica"
                    )

                    activo_eval = memoria.agente_esta_activo(agente_evaluador.AGENTE)
                    if not activo_eval:
                        st.caption(mensaje_agente_apagado)
                    if st.button("📝 Generar evaluación", key="eval_generar", type="primary",
                                 disabled=not seleccionadas_eval or not activo_eval):
                        with st.spinner("Armando la evaluación con IA..."):
                            try:
                                ruta_eval, texto_eval, proveedor_eval = agente_evaluador.crear_evaluacion(
                                    materia_eval, anio_eval, seleccionadas_eval, incluir_practica_eval
                                )
                                st.session_state["eval_resultado"] = {"ruta": ruta_eval, "texto": texto_eval, "proveedor": proveedor_eval}
                            except Exception as e:
                                st.error(mensaje_error_amigable(e))

                    resultado_eval = st.session_state.get("eval_resultado")
                    if resultado_eval:
                        st.success(f"Evaluación lista (vía {resultado_eval['proveedor']}).")
                        with open(resultado_eval["ruta"], "rb") as f:
                            st.download_button(
                                "⬇️ Descargar la evaluación (.docx)",
                                data=f.read(),
                                file_name=os.path.basename(resultado_eval["ruta"]),
                                key="eval_descargar",
                            )
                        with st.expander("Vista previa del texto"):
                            st.text(resultado_eval["texto"])

        with st.expander("💬 Agente Consultas — revisar preguntas nuevas del Form"):
            st.caption(
                "El alumno pregunta en un Google Form propio de la materia (Classroom no deja leer "
                "comentarios del muro). Primero conseguí el link y compartíselo; después usá "
                "'Revisar consultas nuevas' para que el agente vea si contestó algo."
            )
            curso_con = st.selectbox("Materia", nombres_cursos, key="con_materia")

            activo_con = memoria.agente_esta_activo(agente_consultas.AGENTE)
            if not activo_con:
                st.caption(mensaje_agente_apagado)
            if st.button("🔗 Obtener/crear el link del Form para esta materia", key="con_link", disabled=not activo_con):
                curso_obj = next(c for c in cursos if c["name"] == curso_con)
                with st.spinner("Buscando o creando el Form..."):
                    try:
                        creds = classroom.obtener_credenciales()
                        _, responder_uri, _ = agente_consultas.obtener_o_crear_formulario(curso_obj["name"], creds)
                        st.session_state["con_link_url"] = responder_uri
                    except Exception as e:
                        st.error(mensaje_error_amigable(e))

            link_form = st.session_state.get("con_link_url")
            if link_form:
                st.code(link_form, language=None)
                st.caption("Compartiselo al alumno (podés pegarlo como material fijo en Classroom).")

            if st.button("Revisar consultas nuevas", key="con_revisar", type="primary", disabled=not activo_con):
                curso_obj = next(c for c in cursos if c["name"] == curso_con)
                with st.spinner("Buscando consultas nuevas en el Form..."):
                    try:
                        creds = classroom.obtener_credenciales()
                        creadas = agente_consultas.procesar_consultas(curso_obj["name"], creds)
                        if creadas:
                            st.success(f"{len(creadas)} borrador(es) nuevo(s) — revisalos en Aprobaciones.")
                        else:
                            st.info("No hay consultas nuevas por ahora.")
                    except Exception as e:
                        st.error(mensaje_error_amigable(e))

        with st.expander("🏖️ Agente Licencias — avisar una ausencia"):
            fecha_lic = st.date_input("Fecha de la licencia", key="lic_fecha")
            tipo_lic = st.selectbox(
                "Tipo", ["", "medica", "estudio"], key="lic_tipo",
                format_func=lambda x: {"": "No especificar", "medica": "Médica", "estudio": "Estudio"}[x],
            )

            dia_semana_lic = agente_licencias.DIAS_ES[fecha_lic.weekday()]
            resueltas_lic = agente_licencias.resolver_materias_del_dia(fecha_lic, cursos)
            mapa_materia_horario = {r["curso"]["name"]: r["materia_horario"] for r in resueltas_lic}
            sugeridas_lic = list(mapa_materia_horario.keys())

            if dia_semana_lic in ("sabado", "domingo"):
                st.caption(f"El {fecha_lic.strftime('%d/%m/%Y')} es {dia_semana_lic} — no debería tener clases.")
            elif not sugeridas_lic:
                st.caption(
                    f"No encontré materias para el {dia_semana_lic} {fecha_lic.strftime('%d/%m/%Y')} "
                    "en tu horario (o los nombres no coinciden con Classroom). Agregalas manualmente abajo si hace falta."
                )
            else:
                st.caption(f"Según tu horario, el {dia_semana_lic} {fecha_lic.strftime('%d/%m/%Y')} te tocan estas materias:")

            materias_lic = st.multiselect(
                "Materias a avisar — se completan solas según la fecha de arriba, agregá o sacá las que quieras",
                options=nombres_cursos, default=sugeridas_lic, key=f"lic_materias_{fecha_lic}",
            )

            activo_lic = memoria.agente_esta_activo(agente_licencias.AGENTE)
            if not activo_lic:
                st.caption(mensaje_agente_apagado)
            if st.button("Generar avisos", key="lic_generar", type="primary",
                         disabled=not materias_lic or not activo_lic):
                with st.spinner("Redactando los avisos..."):
                    try:
                        creadas = []
                        for nombre_materia in materias_lic:
                            curso_obj = next(c for c in cursos if c["name"] == nombre_materia)
                            materia_horario = mapa_materia_horario.get(nombre_materia, nombre_materia)
                            tarea_id, _, _ = agente_licencias.generar_aviso_para_materia(
                                materia_horario, curso_obj, fecha_lic, tipo_lic
                            )
                            creadas.append(tarea_id)
                        st.session_state["lic_ultima_tanda"] = fecha_lic.isoformat()
                        st.success(
                            f"{len(creadas)} aviso(s) generado(s) — andá a la pestaña Aprobaciones para "
                            "ver el texto completo, editarlo si querés, y recién ahí publicarlo en el muro."
                        )
                    except Exception as e:
                        st.error(mensaje_error_amigable(e))

elif pagina_actual == "org":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Un mapa de quién es quién: los agentes que trabajan para vos, con su rol y su área. "
            "Es solo para consulta — no hay nada para configurar acá. Si querés prender o apagar "
            "un agente, eso se hace en **Centro de Operaciones**."
        )
    if not st.session_state.get("ver_organigrama", False):
        st.info("El organigrama es un gráfico interactivo. Se carga recién al abrir esta pestaña (así el gráfico no se inicializa oculto y se rompe).")
        if st.button("▶ Mostrar organigrama", key="ver_organigrama_btn"):
            st.session_state["ver_organigrama"] = True
            st.rerun()
    else:
        agentes = memoria.listar_agentes()
        areas = memoria.listar_areas()
        if not agentes:
            st.info("Todavía no hay agentes cargados. Corré `python -m panel_control.seed` primero.")
        else:
            areas_por_nombre = {a["nombre"]: a for a in areas}
            agentes_por_area = {}
            for ag in agentes:
                agentes_por_area.setdefault(ag["area_nombre"], []).append(ag)

            nodes = []
            edges = []
            agentes_por_nodo = {}
            areas_por_nodo = {}

            # Si "Dirección" tiene un único agente (el caso normal, el Director),
            # lo usamos directamente como raíz del árbol en vez de un nodo genérico:
            # así queda un solo tronco (Director → áreas → agentes) sin ramas
            # paralelas, que es lo que el layout jerárquico dibuja bien.
            agentes_direccion = agentes_por_area.get("Dirección", [])
            if len(agentes_direccion) == 1:
                director = agentes_direccion[0]
                root_id = f"agente-{director['id']}"
                nodes.append(Node(id=root_id, label=director["nombre"], size=30, shape="hexagon", color="#E6AD30"))
                agentes_por_nodo[root_id] = director
                areas_a_dibujar = {k: v for k, v in areas_por_nombre.items() if k != "Dirección"}
            else:
                root_id = "root"
                nodes.append(Node(id=root_id, label="Panel Classroom", size=30, shape="hexagon", color="#e6edf3"))
                areas_a_dibujar = areas_por_nombre

            for area_nombre, area in areas_a_dibujar.items():
                area_id = f"area-{area['id']}"
                color_area = COLOR_AREA.get(area_nombre, "#7f8c8d")
                nodes.append(Node(id=area_id, label=area_nombre, size=22, shape="box", color=color_area))
                edges.append(Edge(source=root_id, target=area_id))
                areas_por_nodo[area_id] = area

                for ag in agentes_por_area.get(area_nombre, []):
                    agente_id = f"agente-{ag['id']}"
                    color = color_area if ag["estado"] == "activo" else COLOR_INACTIVO
                    nodes.append(Node(id=agente_id, label=ag["nombre"], size=16, shape="dot", color=color))
                    edges.append(Edge(source=area_id, target=agente_id))
                    agentes_por_nodo[agente_id] = ag

            col_grafo, col_detalle = st.columns([3, 1])

            with col_grafo:
                config = Config(
                    width="100%",
                    height=550,
                    directed=True,
                    physics=False,
                    hierarchical=True,
                    direction="UD",
                    sortMethod="directed",  # respeta la dirección de las flechas (el default "hubsize" no)
                    highlightColor="#71EF8A",
                    collapsible=False,
                )
                seleccionado = agraph(nodes=nodes, edges=edges, config=config)

            with col_detalle:
                st.subheader("Agente seleccionado")
                if seleccionado in agentes_por_nodo:
                    ag = agentes_por_nodo[seleccionado]
                    st.markdown(f"### {icono_agente(ag['nombre'])} {ag['nombre']}")
                    st.caption(ag["rol"])
                    st.write(f"**Área:** {ag['area_nombre']}")
                    estado_icon = "🟢" if ag["estado"] == "activo" else "⚪"
                    st.write(f"**Estado:** {estado_icon} {ag['estado']}")

                    tareas_agente = memoria.listar_tareas(agente=ag["nombre"], limite=500)
                    completadas = sum(1 for t in tareas_agente if t["estado"] == "completada")
                    pendientes = sum(1 for t in tareas_agente if t["estado"] in ("pendiente", "en_curso"))
                    m1, m2 = st.columns(2)
                    m1.metric("Completadas", completadas)
                    m2.metric("Pendientes", pendientes)

                    st.caption("Últimas tareas")
                    for t in tareas_agente[:5]:
                        st.write(f"- {hace(t['creado_en'])} · {t['descripcion']}")
                elif seleccionado in areas_por_nodo:
                    area = areas_por_nodo[seleccionado]
                    st.markdown(f"### {area['nombre']}")
                    st.write(f"**Agentes:** {len(agentes_por_area.get(area['nombre'], []))}")
                else:
                    st.info("Hacé clic en un nodo del organigrama para ver su detalle.")

elif pagina_actual == "aprobaciones":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Acá termina todo lo que un agente generó: correcciones, avisos, TPs nuevos, "
            "bibliografía para adjuntar. **Nada se publica en Classroom hasta que vos lo apruebes "
            "acá con un click** — antes de aprobar podés editar el texto o rechazarlo. Es el único "
            "lugar del panel donde una acción sale de verdad hacia afuera."
        )
    st.caption(
        "Human-in-the-loop: ningún agente manda nada hacia afuera (emails, publicaciones) sin que "
        "lo apruebes acá primero. Podés editar el borrador antes de aprobarlo."
    )
    if not aprobaciones_pendientes:
        st.info("No hay nada esperando tu aprobación por ahora.")
    else:
        for ap in aprobaciones_pendientes:
            datos = ap["datos"]
            with st.container(border=True):
                if ap["tipo"] == "email_consulta":
                    st.markdown(f"**{icono_agente('Agente Consultas')} {datos.get('materia', '')} — consulta de {datos.get('nombre') or datos.get('email')}**")
                    st.caption(f"Generado {hace(ap['creado_en'])} · vía {datos.get('proveedor', '?')} · se enviaría a {datos.get('email', '?')}")
                    st.write("**Pregunta del alumno:**")
                    st.write(datos.get("pregunta", ""))
                    texto_editado = st.text_area(
                        "Respuesta (podés editarla antes de aprobar)",
                        value=datos.get("respuesta", ""),
                        key=f"resp_{ap['id']}",
                        height=200,
                    )

                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprobar y enviar", key=f"aprobar_{ap['id']}", type="primary"):
                        try:
                            creds = classroom.obtener_credenciales()
                            ok, mensaje = agente_consultas.aprobar_y_enviar(ap["id"], creds, texto_editado)
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_consultas.rechazar(ap["id"])
                        st.rerun()

                elif ap["tipo"] == "publicacion_classroom":
                    tipo_pub = datos.get("tipo_publicacion", "tarea")
                    icono = icono_agente(datos.get("agente", "Agente Publicador"))
                    st.markdown(f"**{icono} {datos.get('materia', '')} — nuevo/a {tipo_pub}**")
                    detalles = f"Generado {hace(ap['creado_en'])} · vía {datos.get('proveedor', '?')}"
                    if datos.get("fecha_entrega"):
                        detalles += f" · entrega {datos['fecha_entrega']}"
                    if datos.get("puntos") is not None:
                        detalles += f" · {datos['puntos']} pts"
                    st.caption(detalles)

                    titulo_editado = st.text_input("Título", value=datos.get("titulo", ""), key=f"titulo_{ap['id']}")
                    descripcion_editada = st.text_area(
                        "Descripción (podés editarla antes de aprobar)",
                        value=datos.get("descripcion", ""),
                        key=f"desc_{ap['id']}",
                        height=220,
                    )

                    recursos_confirmados = []
                    recursos_sugeridos = datos.get("recursos_sugeridos") or []
                    if recursos_sugeridos:
                        st.caption("📎 Recursos sugeridos para adjuntar (revisalos antes de aprobar)")
                        icono_recurso = {"video": "🎥", "manual": "📖", "bibliografia": "📚"}
                        for i, r in enumerate(recursos_sugeridos):
                            incluir = st.checkbox(
                                f"{icono_recurso.get(r.get('tipo'), '🔗')} {r.get('titulo', r.get('url'))}",
                                value=True, key=f"recurso_{ap['id']}_{i}",
                            )
                            st.caption(r.get("url", ""))
                            if incluir:
                                recursos_confirmados.append(r)

                    col_a, col_b = st.columns(2)
                    if col_a.button(f"✅ Aprobar y publicar", key=f"aprobar_{ap['id']}", type="primary"):
                        try:
                            creds = classroom.obtener_credenciales()
                            ok, mensaje = agente_publicador.aprobar_y_publicar(
                                ap["id"], creds, titulo_editado, descripcion_editada,
                                recursos_confirmados=recursos_confirmados,
                            )
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_publicador.rechazar(ap["id"])
                        st.rerun()

                elif ap["tipo"] == "actualizar_actividad":
                    icono = icono_agente(datos.get("agente", "Agente Mejorador"))
                    st.markdown(f"**{icono} {datos.get('materia', '')} — reemplazar '{datos.get('titulo_original', '')}'**")
                    st.caption(f"Generado {hace(ap['creado_en'])} — esto sobreescribe la consigna original en Classroom")

                    with st.expander("Ver consigna ORIGINAL (la que se va a perder)"):
                        st.text(datos.get("descripcion_original", "") or "(sin descripción)")

                    descripcion_nueva_editada = st.text_area(
                        "Consigna nueva (podés editarla antes de aprobar)",
                        value=datos.get("descripcion_nueva", ""),
                        key=f"desc_actualizar_{ap['id']}",
                        height=220,
                    )

                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprobar y reemplazar en Classroom", key=f"aprobar_{ap['id']}", type="primary"):
                        try:
                            creds = classroom.obtener_credenciales()
                            ok, mensaje = agente_mejorador.aprobar_y_reemplazar(
                                ap["id"], creds, descripcion_nueva_editada
                            )
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_mejorador.rechazar_reemplazo(ap["id"])
                        st.rerun()

                elif ap["tipo"] == "reemplazar_material":
                    icono = icono_agente(datos.get("agente", "Agente Publicador"))
                    archivo_ap = materiales.obtener_material(datos["material_id"])
                    st.markdown(f"**{icono} {datos.get('materia', '')} — reemplazar archivo de '{datos.get('titulo_actividad', '')}'**")
                    st.caption(f"Generado {hace(ap['creado_en'])}")
                    if archivo_ap:
                        st.write(f"📄 {archivo_ap['nombre_archivo']} · {max(archivo_ap['tamano_bytes'] // 1024, 1)} KB")
                    else:
                        st.warning("El archivo local ya no existe (¿lo borraste?). No se puede aprobar.")
                    st.caption(
                        "⚠️ Esto SACA el/los archivo(s) que ya estaban adjuntos en Classroom para esta "
                        "actividad y deja solo este nuevo. Los links/videos ya adjuntos no se tocan."
                    )

                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprobar y reemplazar en Classroom", key=f"aprobar_{ap['id']}",
                                     type="primary", disabled=not archivo_ap):
                        try:
                            creds = classroom.obtener_credenciales()
                            ok, mensaje = agente_publicador.aprobar_y_reemplazar_material(ap["id"], creds)
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_publicador.rechazar(ap["id"])
                        st.rerun()

                elif ap["tipo"] == "adjuntar_bibliografia_existente":
                    icono = icono_agente(datos.get("agente", "Agente Publicador"))
                    st.markdown(f"**{icono} {datos.get('materia', '')} — adjuntar bibliografía a '{datos.get('titulo_actividad', '')}'**")
                    st.caption(f"Generado {hace(ap['creado_en'])}")

                    recursos_confirmados_bib = []
                    recursos_sugeridos_bib = datos.get("recursos_sugeridos") or []
                    if recursos_sugeridos_bib:
                        st.caption("📎 Recursos a adjuntar (revisalos antes de aprobar)")
                        icono_recurso_bib = {"video": "🎥", "manual": "📖", "bibliografia": "📚"}
                        for i, r in enumerate(recursos_sugeridos_bib):
                            incluir_bib = st.checkbox(
                                f"{icono_recurso_bib.get(r.get('tipo'), '🔗')} {r.get('titulo', r.get('url'))}",
                                value=True, key=f"recurso_bib_{ap['id']}_{i}",
                            )
                            st.caption(r.get("url", ""))
                            if incluir_bib:
                                recursos_confirmados_bib.append(r)
                    else:
                        st.info("No hay recursos sugeridos en este borrador.")

                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprobar y adjuntar en Classroom", key=f"aprobar_{ap['id']}",
                                     type="primary", disabled=not recursos_confirmados_bib):
                        try:
                            creds = classroom.obtener_credenciales()
                            ok, mensaje = agente_publicador.aprobar_y_adjuntar_bibliografia(
                                ap["id"], creds, recursos_confirmados_bib
                            )
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_publicador.rechazar(ap["id"])
                        st.rerun()

                elif ap["tipo"] == "lote_calificaciones":
                    icono = icono_agente(datos.get("agente", "Agente Corrector"))
                    lote_ap = datos.get("lote", [])
                    st.markdown(f"**{icono} {datos.get('materia', '')} — corrección de '{datos.get('titulo_trabajo', '')}'**")
                    st.caption(f"Generado {hace(ap['creado_en'])} · {len(lote_ap)} alumno(s) evaluado(s)")
                    st.caption(
                        "Revisá nota y feedback antes de aprobar. Los que no tienen entrega vienen "
                        "SIN tildar para que no les pongas nota por accidente — tildalos vos si igual querés calificarlos."
                    )

                    filas_lote = [{
                        "incluir": item.get("estado_entrega") in ("TURNED_IN", "RETURNED"),
                        "nombre": item.get("nombre", ""),
                        "entrega": item.get("estado_entrega", ""),
                        "nota": item.get("nota"),
                        "feedback": item.get("feedback", ""),
                        "estado": item.get("estado", ""),
                        "user_id": item.get("user_id"),
                        "submission_id": item.get("submission_id"),
                    } for item in lote_ap]
                    df_lote = pd.DataFrame(filas_lote)

                    df_editado = st.data_editor(
                        df_lote,
                        column_order=["incluir", "nombre", "entrega", "nota", "feedback"],
                        column_config={
                            "incluir": st.column_config.CheckboxColumn("Incluir"),
                            "nombre": st.column_config.TextColumn("Alumno", disabled=True),
                            "entrega": st.column_config.TextColumn("Entrega", disabled=True),
                            "nota": st.column_config.NumberColumn("Nota (1-10)", min_value=1, max_value=10, step=1),
                            "feedback": st.column_config.TextColumn("Feedback"),
                        },
                        hide_index=True,
                        width="stretch",
                        key=f"lote_editor_{ap['id']}",
                    )

                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ Aprobar y publicar notas", key=f"aprobar_{ap['id']}", type="primary"):
                        try:
                            creds = classroom.obtener_credenciales()
                            lote_final = df_editado.to_dict("records")
                            ok, mensaje = agente_corrector.aprobar_y_publicar_lote(ap["id"], creds, lote_final)
                            if ok:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        except Exception as e:
                            st.error(mensaje_error_amigable(e))
                    if col_b.button("🗑️ Rechazar", key=f"rechazar_{ap['id']}"):
                        agente_corrector.rechazar_lote(ap["id"])
                        st.rerun()

                else:
                    st.markdown(f"**{ap['tipo']}**")
                    st.json(datos)

elif pagina_actual == "materias":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "El detalle materia por materia: actividades ya publicadas, temas dados, alumnos y sus "
            "métricas. Empezá eligiendo la materia arriba. El botón **🔄 Traer de Classroom** trae lo "
            "último que hayas publicado o modificado allá — usalo después de cualquier cambio hecho "
            "directo en Classroom, para que el panel quede sincronizado.\n\n"
            "Desde acá también podés **editar una actividad** o **adjuntarle bibliografía** — ambas "
            "acciones dejan un borrador esperando aprobación en la pestaña **Aprobaciones**, nunca "
            "se publican solas."
        )
    st.subheader("📎 Actividades y materiales")
    st.caption(
        "Todo se lee directo de tu base local (panel.db) — no hace falta tocar Classroom para "
        "ver esto. Elegís una materia y ves todas sus actividades, enunciado completo, bibliografía/"
        "videos/manuales ya buscados, métricas y nómina. El botón de abajo solo hace falta si agregaste "
        "algo nuevo en Classroom y querés traerlo — trae actividades Y alumnos/temas/métricas juntos."
    )

    pendientes_recursos = memoria.contar_pendientes_recursos_bulk()
    if pendientes_recursos:
        col_banner, col_banner_btn = st.columns([4, 1])
        col_banner.warning(
            f"⏳ Quedan {pendientes_recursos} actividad(es) sin buscar bibliografía/videos/manuales "
            "todavía (se corta solo si se agota la cuota de Gemini del día — no hace falta hacer nada, "
            "se retoma solo la próxima vez que apretes el botón)."
        )
        if col_banner_btn.button("▶️ Buscar ahora", key="mat_resumir_recursos"):
            with st.spinner("Buscando bibliografía/videos/manuales con IA (puede tardar varios minutos)..."):
                buscar_recursos_bulk.procesar()
            st.rerun()

    actividades_todas = memoria.listar_actividades_cache()
    snapshots_todos = memoria.listar_snapshots_materias()
    materias_disponibles = sorted({a["materia"] for a in actividades_todas} | {s["curso"] for s in snapshots_todos})

    if not materias_disponibles:
        st.info(
            "Todavía no hay nada sincronizado. Corré una vez desde la terminal: "
            "`python -m panel_control.scripts.sincronizar_actividades` (trae actividades + enunciados "
            "de todas las materias, gratis — no usa IA)."
        )
    else:
        col_sel_mat, col_refresh_mat = st.columns([4, 1])
        materia_mat = col_sel_mat.selectbox("Materia", materias_disponibles, key="mat_materia_unica")
        col_refresh_mat.write("")
        if col_refresh_mat.button("🔄 Traer de Classroom", key="mat_refrescar_una", help="Trae actividades, alumnos, temas y métricas actualizadas de esta materia — solo hace falta si cambió algo en Classroom."):
            with st.spinner(f"Actualizando '{materia_mat}' desde Classroom..."):
                try:
                    creds = classroom.obtener_credenciales()
                    service = build("classroom", "v1", credentials=creds)
                    service_drive = build("drive", "v3", credentials=creds)
                    cursos_live = st.session_state.get("cursos_classroom") or classroom.listar_materias_activas(service)
                    st.session_state["cursos_classroom"] = cursos_live
                    curso_mat_obj = next(c for c in cursos_live if c["name"] == materia_mat)
                    sincronizar_actividades.sincronizar_una_materia(service, service_drive, materia_mat, curso_mat_obj["id"])
                    sync_materias.sincronizar_materia(materia_mat, curso_mat_obj["id"], service)
                except Exception as e:
                    st.error(mensaje_error_amigable(e))
            st.rerun()

        trabajos_mat = [a for a in actividades_todas if a["materia"] == materia_mat]
        if not trabajos_mat:
            st.info("Esta materia no tiene actividades sincronizadas todavía.")
        else:
            recursos_por_work_id = {r["work_id"]: r for r in memoria.listar_recursos_bulk(materia=materia_mat)}
            filas_mat = []
            for t in trabajos_mat:
                adjuntos = _resumir_materiales_classroom(t.get("materials"))
                resumen_adjuntos = " · ".join(
                    f"{_ICONO_ADJUNTO.get(tipo, '📄')} {cantidad}"
                    for tipo, cantidad in _contar_por_tipo(adjuntos).items()
                ) if adjuntos else "—"
                rec = recursos_por_work_id.get(t["work_id"])
                estado_recursos = {"completado": f"🤖 {len(rec['recursos'])} sugerido(s)", "pendiente": "⏳ pendiente",
                                    "error": "⚠️ error"}.get(rec["estado"], "—") if rec else "—"
                filas_mat.append({
                    "Título": t["titulo"],
                    "Tipo": t.get("tipo", ""),
                    "Adjuntos en Classroom": resumen_adjuntos,
                    "Bibliografía IA": estado_recursos,
                })
            st.dataframe(pd.DataFrame(filas_mat), hide_index=True, width="stretch")

            opciones_mat = [f"{i + 1}. {t['titulo']}" for i, t in enumerate(trabajos_mat)]
            elegida_mat = st.selectbox("Actividad", opciones_mat, key="mat_actividad_sel")
            trabajo_mat = trabajos_mat[opciones_mat.index(elegida_mat)]

            st.markdown(f"#### {trabajo_mat['titulo']}")

            if trabajo_mat.get("enunciado"):
                with st.expander("📄 Enunciado completo", expanded=False):
                    st.text_area("Enunciado", value=trabajo_mat["enunciado"], height=180,
                                  key=f"mat_enunciado_area_{trabajo_mat['work_id']}", label_visibility="collapsed")
            else:
                st.caption("📄 No se pudo extraer el enunciado de esta actividad (o todavía no se sincronizó).")

            adjuntos_mat = _resumir_materiales_classroom(trabajo_mat.get("materials"))
            st.caption("📚 Adjuntos ya publicados en Classroom (bibliografía/videos/links)")
            if not adjuntos_mat:
                st.caption("Esta actividad no tiene nada adjunto todavía.")
            else:
                for a in adjuntos_mat:
                    st.write(f"{_ICONO_ADJUNTO.get(a['tipo'], '📄')} [{a['titulo']}]({a['url']})" if a["url"] else f"{_ICONO_ADJUNTO.get(a['tipo'], '📄')} {a['titulo']}")

            recurso_bulk_actividad = recursos_por_work_id.get(trabajo_mat["work_id"])
            if recurso_bulk_actividad:
                st.caption("🤖 Bibliografía/videos/manuales sugeridos por IA (todavía no adjuntados en Classroom)")
                if recurso_bulk_actividad["estado"] == "pendiente":
                    st.caption("Esta actividad está en la cola, todavía sin buscar.")
                elif recurso_bulk_actividad["estado"] == "error":
                    st.caption(f"No se pudo buscar: {recurso_bulk_actividad.get('error', '')[:200]}")
                elif not recurso_bulk_actividad["recursos"]:
                    st.caption("Se buscó pero no se encontró nada confiable para adjuntar.")
                else:
                    for r in recurso_bulk_actividad["recursos"]:
                        icono = {"video": "🎥", "manual": "📖", "bibliografia": "📚"}.get(r["tipo"], "🔗")
                        st.write(f"{icono} [{r['titulo']}]({r['url']})")

            with st.expander("📤 Subir mejora (PDF/DOC) para esta actividad", expanded=False):
                col_num_mat, col_nombre_mat, col_file_mat = st.columns([1, 2, 3])
                numero_mat = col_num_mat.number_input("N° de actividad", min_value=1, step=1, key="mat_numero")
                nombre_previo = materiales.obtener_nombre_actividad(materia_mat, int(numero_mat)) or trabajo_mat["titulo"]
                nombre_act_mat = col_nombre_mat.text_input(
                    "Nombre de la actividad",
                    value=nombre_previo,
                    key=f"mat_nombre_act_{materia_mat}_{int(numero_mat)}_{trabajo_mat['work_id']}",
                    help="Se guarda en la tabla de actividades de esta materia. Se pre-completa con el título real de Classroom.",
                )
                archivo_mat = col_file_mat.file_uploader("Archivo", key="mat_file_uploader")
                if st.button("📤 Subir archivo", key="mat_subir", disabled=archivo_mat is None):
                    materiales.subir_material(
                        materia_mat, int(numero_mat),
                        nombre_act_mat.strip() or f"Actividad {int(numero_mat)}",
                        archivo_mat.name, archivo_mat.getvalue(), archivo_mat.type,
                    )
                    st.success(f"'{archivo_mat.name}' guardado para {materia_mat} — Actividad {int(numero_mat)}.")
                    st.rerun()

                materiales_guardados = materiales.listar_materiales(materia=materia_mat, numero_actividad=int(numero_mat))
                if not materiales_guardados:
                    st.caption(f"Todavía no subiste materiales para la Actividad {int(numero_mat)}.")
                else:
                    for m in materiales_guardados:
                        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                        c1.write(f"📄 {m['nombre_archivo']}")
                        c2.caption(f"{max(m['tamano_bytes'] // 1024, 1)} KB · {hace(m['subido_en'])}")
                        completo = materiales.obtener_material(m["id"])
                        c3.download_button(
                            "⬇️", data=completo["contenido"], file_name=m["nombre_archivo"],
                            key=f"mat_descargar_{m['id']}",
                        )
                        if c4.button("🗑️", key=f"mat_borrar_{m['id']}"):
                            materiales.eliminar_material(m["id"])
                            st.rerun()

        st.divider()
        snap = next((s for s in snapshots_todos if s["curso"] == materia_mat), None)
        if not snap:
            st.info(f"Todavía no sincronicé métricas/alumnos de '{materia_mat}' — usá '🔄 Traer de Classroom' arriba.")
        else:
            trabajos = snap["trabajos"]
            temas = snap.get("temas", [])
            # Nómina desde la tabla `alumnos` (no del JSON del snapshot) — es la
            # misma info, pero así queda en una sola fuente consultable aparte.
            alumnos = [{"nombre": a["nombre"], "email": a["email"]} for a in memoria.listar_alumnos(materia=materia_mat)]

            st.caption(f"Última sincronización: {hace(snap['actualizado_en'])} — usá el botón de arriba o '🚀 Ejecutar agentes' para actualizar")

            if not trabajos:
                st.info("Esta materia no tiene actividades publicadas todavía.")
            else:
                st.subheader("📂 Temas y actividades")
                st.caption(
                    "Por cada actividad: subí una mejora para reemplazar el archivo adjunto en Classroom, "
                    "o adjuntale la bibliografía que ya encontramos con IA. Ambas quedan esperando tu "
                    "aprobación, no se publican solas."
                )
                # Título → work_id/course_id, para poder tocar Classroom desde acá
                # (el snapshot de métricas no trae work_id, la cache de actividades sí).
                mapa_por_titulo = {a["titulo"]: a for a in actividades_todas if a["materia"] == materia_mat}

                def _render_actividad_con_botones(a):
                    estado_icon = "🟢" if a["sin_calificar"] == 0 else "🟡"
                    st.write(f"{estado_icon} **{a['titulo']}** · {a['entregados']} entregados, {a['calificados']} calificados")
                    info_a = mapa_por_titulo.get(a["titulo"])
                    if not info_a:
                        st.caption("(sincronizá actividades arriba para poder editar/adjuntar acá)")
                        return
                    work_id_a, course_id_a = info_a["work_id"], info_a["course_id"]

                    col_edit, col_bib = st.columns(2)
                    if col_edit.button("✏️ Editar actividad", key=f"tema_btn_editar_{work_id_a}"):
                        st.session_state[f"tema_editar_{work_id_a}"] = not st.session_state.get(f"tema_editar_{work_id_a}", False)
                    if col_bib.button("📚 Adjuntar bibliografías", key=f"tema_btn_bib_{work_id_a}"):
                        st.session_state[f"tema_bib_{work_id_a}"] = not st.session_state.get(f"tema_bib_{work_id_a}", False)

                    if st.session_state.get(f"tema_editar_{work_id_a}"):
                        with st.container(border=True):
                            st.caption(f"Subir mejora para '{a['titulo']}' y reemplazar el archivo en Classroom")
                            numero_edit = st.number_input("N° de actividad", min_value=1, step=1, key=f"tema_num_{work_id_a}")
                            nombre_edit = st.text_input("Nombre", value=a["titulo"], key=f"tema_nombre_{work_id_a}")
                            archivo_edit = st.file_uploader("Archivo", key=f"tema_file_{work_id_a}")
                            if st.button("📤 Generar borrador para Classroom", key=f"tema_generar_edit_{work_id_a}", disabled=archivo_edit is None):
                                material_id_nuevo = materiales.subir_material(
                                    materia_mat, int(numero_edit), nombre_edit.strip() or a["titulo"],
                                    archivo_edit.name, archivo_edit.getvalue(), archivo_edit.type,
                                )
                                agente_publicador.crear_borrador_reemplazo_material(
                                    materia_mat, course_id_a, work_id_a, a["titulo"], material_id_nuevo,
                                )
                                st.success("Borrador listo — revisalo en la pestaña Aprobaciones.")
                                st.session_state[f"tema_editar_{work_id_a}"] = False
                                st.rerun()

                    if st.session_state.get(f"tema_bib_{work_id_a}"):
                        with st.container(border=True):
                            recurso_bulk_a = next(
                                (r for r in memoria.listar_recursos_bulk(materia=materia_mat) if r["work_id"] == work_id_a), None
                            )
                            if not recurso_bulk_a or recurso_bulk_a["estado"] != "completado" or not recurso_bulk_a["recursos"]:
                                st.caption("No hay bibliografía encontrada todavía para esta actividad.")
                            else:
                                st.caption("Elegí qué recursos adjuntar:")
                                icono_recurso_tema = {"video": "🎥", "manual": "📖", "bibliografia": "📚"}
                                seleccion_bib = []
                                for i, r in enumerate(recurso_bulk_a["recursos"]):
                                    if st.checkbox(
                                        f"{icono_recurso_tema.get(r['tipo'], '🔗')} {r['titulo']}",
                                        value=True, key=f"tema_bib_check_{work_id_a}_{i}",
                                    ):
                                        seleccion_bib.append(r)
                                if st.button("📚 Generar borrador para Classroom", key=f"tema_generar_bib_{work_id_a}", disabled=not seleccion_bib):
                                    agente_publicador.crear_borrador_adjuntar_bibliografia(
                                        materia_mat, course_id_a, work_id_a, a["titulo"], seleccion_bib,
                                    )
                                    st.success("Borrador listo — revisalo en la pestaña Aprobaciones.")
                                    st.session_state[f"tema_bib_{work_id_a}"] = False
                                    st.rerun()

                if not temas:
                    st.caption("Esta materia no tiene temas creados en Classroom (o todavía no se sincronizó — usá '🔄 Traer de Classroom' arriba).")
                else:
                    trabajos_por_tema = {}
                    sin_tema = []
                    for t in trabajos:
                        tid = t.get("topic_id")
                        if tid:
                            trabajos_por_tema.setdefault(tid, []).append(t)
                        else:
                            sin_tema.append(t)

                    for tema in temas:
                        acts = trabajos_por_tema.get(tema["topic_id"], [])
                        if not acts:
                            continue
                        with st.expander(f"{tema['nombre']} ({len(acts)} actividad{'es' if len(acts) != 1 else ''})"):
                            for a in acts:
                                _render_actividad_con_botones(a)

                    if sin_tema:
                        with st.expander(f"Sin tema asignado ({len(sin_tema)} actividad{'es' if len(sin_tema) != 1 else ''})"):
                            for a in sin_tema:
                                _render_actividad_con_botones(a)

                st.divider()
                st.subheader("📊 Métricas y alumnos")
                total_sin_calificar = sum(t["sin_calificar"] for t in trabajos)
                total_calificados = sum(t["calificados"] for t in trabajos)
                total_entregados = sum(t["entregados"] for t in trabajos)
                pct_corregido = round(100 * total_calificados / total_entregados) if total_entregados else 0

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Actividades", len(trabajos))
                m2.metric("Entregas totales", total_entregados)
                m3.metric("Sin corregir", total_sin_calificar)
                m4.metric("% corregido", f"{pct_corregido}%")
                m5.metric("Alumnos", len(alumnos))

                if total_sin_calificar > 0:
                    st.warning(f"Hay {total_sin_calificar} entregas sin corregir en '{materia_mat}'.")
                else:
                    st.success("No hay entregas pendientes de corregir en esta materia.")

                df = pd.DataFrame(trabajos)
                df_vista = df[["titulo", "work_type", "total_alumnos", "entregados", "calificados", "sin_calificar"]].copy()
                df_vista.columns = ["Actividad", "Tipo", "Alumnos", "Entregados", "Calificados", "Sin calificar"]
                df_vista = df_vista.sort_values("Sin calificar", ascending=False)

                st.dataframe(df_vista, width="stretch", hide_index=True)

                st.divider()
                st.subheader(f"👥 Alumnos ({len(alumnos)})")
                if not alumnos:
                    st.caption("No se encontró nómina para esta materia (usá '🔄 Traer de Classroom' arriba para sincronizarla).")
                else:
                    with st.expander("Ver nómina completa"):
                        df_alumnos = pd.DataFrame(alumnos)
                        df_alumnos.columns = ["Nombre", "Email"]
                        df_alumnos = df_alumnos.sort_values("Nombre")
                        st.dataframe(df_alumnos, width="stretch", hide_index=True)

elif pagina_actual == "cuaderno":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Tu cuaderno de aula, pero digital: comunicados a las familias, asistencia por clase, y "
            "la planilla de notas con el mismo formato institucional que ya usás en papel. Todo se "
            "carga a mano y queda guardado en tu base local — no hay IA acá ni nada que se publique "
            "en Classroom. Desde la planilla podés exportar un Excel con el formato oficial."
        )
    st.subheader("📓 Cuaderno")
    st.caption(
        "Comunicados, asistencia y planilla institucional — todo se guarda en tu base local. "
        "Nada de esto toca Classroom ni pasa por Aprobaciones (salvo el texto de notas finales, "
        "que vos mismo copiás y pegás donde quieras)."
    )
    materias_cuaderno = sorted({a["materia"] for a in memoria.listar_alumnos()})
    if not materias_cuaderno:
        st.info(
            "Todavía no hay alumnos sincronizados. Sincronizá materias primero desde "
            "'🚀 Ejecutar agentes' → 'Sincronizar Materias'."
        )
    else:
        materia_cuad = st.selectbox("Materia", materias_cuaderno, key="cuad_materia")
        alumnos_cuad = memoria.listar_alumnos(materia=materia_cuad)
        vista_cuad = st.radio(
            "Vista", ["📝 Comunicados", "✅ Tomar asistencia", "📊 Planilla institucional"],
            horizontal=True, key="cuad_vista",
        )
        st.divider()

        ETIQUETA_TIPO_COM = {"tp_classroom": "TP/Classroom", "prueba": "Prueba", "carpeta": "Carpeta", "comportamiento": "Comportamiento"}

        if vista_cuad == "📝 Comunicados":
            if not alumnos_cuad:
                st.info("Esta materia no tiene alumnos sincronizados todavía.")
            else:
                col1, col2, col3 = st.columns([2, 1, 1])
                alumno_com = col1.selectbox("Alumno", [a["nombre"] for a in alumnos_cuad], key="com_alumno")
                tipo_com = col2.selectbox(
                    "Tipo", list(ETIQUETA_TIPO_COM.keys()), key="com_tipo",
                    format_func=lambda x: ETIQUETA_TIPO_COM[x],
                )
                fecha_com = col3.date_input("Fecha", key="com_fecha")
                obs_com = st.text_area("Observación", key="com_obs", height=80)
                if st.button("💾 Guardar comunicado", key="com_guardar", disabled=not obs_com.strip()):
                    memoria.agregar_comunicado(materia_cuad, alumno_com, tipo_com, fecha_com.isoformat(), obs_com.strip())
                    st.success("Comunicado guardado.")
                    st.rerun()

                st.divider()
                st.caption("Comunicados ya cargados")
                filtro_alumno_com = st.selectbox(
                    "Filtrar por alumno", ["Todos"] + [a["nombre"] for a in alumnos_cuad], key="com_filtro_alumno"
                )
                comunicados = memoria.listar_comunicados(
                    materia=materia_cuad,
                    alumno_nombre=None if filtro_alumno_com == "Todos" else filtro_alumno_com,
                )
                if not comunicados:
                    st.caption("Sin comunicados todavía.")
                else:
                    st.dataframe(pd.DataFrame([{
                        "Fecha": c["fecha"], "Alumno": c["alumno_nombre"],
                        "Tipo": ETIQUETA_TIPO_COM.get(c["tipo"], c["tipo"]), "Observación": c["observacion"],
                    } for c in comunicados]), hide_index=True, width="stretch")

        elif vista_cuad == "✅ Tomar asistencia":
            if not alumnos_cuad:
                st.info("Esta materia no tiene alumnos sincronizados todavía.")
            else:
                fecha_sugerida = cuaderno.sugerir_fecha_clase(materia_cuad)
                fecha_asist = st.date_input("Fecha de la clase", value=fecha_sugerida, key="asist_fecha")
                ya_guardadas = {
                    a["alumno_nombre"]: bool(a["presente"])
                    for a in memoria.listar_asistencias(materia_cuad, fecha_asist.isoformat())
                }
                if ya_guardadas:
                    st.caption(f"Ya hay {len(ya_guardadas)} de {len(alumnos_cuad)} registrados para esta fecha.")
                else:
                    st.caption("Ningún registro todavía para esta fecha — todos arrancan como ausentes.")

                presentes_marcados = {}
                for a in alumnos_cuad:
                    presentes_marcados[a["nombre"]] = st.checkbox(
                        a["nombre"], value=ya_guardadas.get(a["nombre"], False),
                        key=f"asist_check_{a['nombre']}_{fecha_asist}",
                    )
                if st.button("💾 Guardar asistencia de este día", key="asist_guardar", type="primary"):
                    for nombre, presente in presentes_marcados.items():
                        memoria.guardar_asistencia(materia_cuad, nombre, fecha_asist.isoformat(), presente)
                    st.success(f"Asistencia del {fecha_asist.strftime('%d/%m/%Y')} guardada.")
                    st.rerun()

        else:  # 📊 Planilla institucional
            with st.expander("⚙️ Períodos de evaluación (se cargan una vez por año, se reusan siempre)"):
                periodos_actuales = memoria.listar_periodos()
                for periodo in cuaderno.PERIODOS:
                    rango = periodos_actuales.get(periodo, {})
                    st.caption(cuaderno.PERIODOS_LABEL[periodo])
                    cp1, cp2, cp3 = st.columns([2, 2, 1])
                    ini = cp1.date_input(
                        "Inicio",
                        value=datetime.fromisoformat(rango["fecha_inicio"]).date() if rango.get("fecha_inicio") else datetime.now().date(),
                        key=f"periodo_ini_{periodo}",
                    )
                    fin = cp2.date_input(
                        "Fin",
                        value=datetime.fromisoformat(rango["fecha_fin"]).date() if rango.get("fecha_fin") else datetime.now().date(),
                        key=f"periodo_fin_{periodo}",
                    )
                    cp3.write("")
                    if cp3.button("Guardar", key=f"periodo_guardar_{periodo}"):
                        memoria.guardar_periodo(periodo, ini.isoformat(), fin.isoformat())
                        st.success(f"{cuaderno.PERIODOS_LABEL[periodo]} guardado.")
                        st.rerun()

            if not alumnos_cuad:
                st.info("Esta materia no tiene alumnos sincronizados todavía.")
            else:
                filas_planilla_dict = {f["alumno_nombre"]: f for f in memoria.listar_planilla(materia_cuad)}
                columnas_planilla = ["c1_proc", "c1_nota", "c1_asist", "c2_proc", "c2_nota", "c2_asist",
                                      "dic_nota", "dic_asist", "final_proc", "final_nota", "final_asist"]
                filas_editor = []
                for a in alumnos_cuad:
                    datos = filas_planilla_dict.get(a["nombre"])
                    fila_editor = {"nombre": a["nombre"], "diagnostico": a["diagnostico"] or ""}
                    for col in columnas_planilla:
                        fila_editor[col] = (datos[col] if datos and datos[col] else "")
                    filas_editor.append(fila_editor)

                df_editado_planilla = st.data_editor(
                    pd.DataFrame(filas_editor),
                    column_config={
                        "nombre": st.column_config.TextColumn("Alumno/a", disabled=True),
                        "diagnostico": st.column_config.SelectboxColumn("Diagnóstico", options=["", "TEA", "TEP", "TED"]),
                        "c1_proc": st.column_config.TextColumn("1°C Proc."),
                        "c1_nota": st.column_config.TextColumn("1°C Nota"),
                        "c1_asist": st.column_config.TextColumn("1°C %Asist."),
                        "c2_proc": st.column_config.TextColumn("2°C Proc."),
                        "c2_nota": st.column_config.TextColumn("2°C Nota"),
                        "c2_asist": st.column_config.TextColumn("2°C %Asist."),
                        "dic_nota": st.column_config.TextColumn("Dic/Feb Nota"),
                        "dic_asist": st.column_config.TextColumn("Dic/Feb %Asist."),
                        "final_proc": st.column_config.TextColumn("Final Proc."),
                        "final_nota": st.column_config.TextColumn("Final Nota"),
                        "final_asist": st.column_config.TextColumn("Final %Asist."),
                    },
                    hide_index=True, width="stretch", key="planilla_editor",
                )

                col_guardar, col_recalc, col_excel = st.columns(3)
                if col_guardar.button("💾 Guardar planilla", key="planilla_guardar", type="primary"):
                    for _, fila in df_editado_planilla.iterrows():
                        memoria.actualizar_diagnostico_alumno(materia_cuad, fila["nombre"], fila["diagnostico"] or None)
                        memoria.guardar_fila_planilla(materia_cuad, fila["nombre"], {c: fila[c] for c in columnas_planilla})
                    st.success("Planilla guardada.")
                    st.rerun()
                if col_recalc.button("🔄 Recalcular asistencia", key="planilla_recalc"):
                    n = cuaderno.recalcular_columnas_asistencia(materia_cuad)
                    if n:
                        st.success(f"Asistencia recalculada ({n} celda(s)).")
                    else:
                        st.warning("No hay períodos de evaluación cargados — definilos arriba en '⚙️ Períodos de evaluación'.")
                    st.rerun()
                if col_excel.button("⬇️ Generar Excel institucional", key="planilla_excel_generar"):
                    st.session_state["cuad_excel_ruta"] = cuaderno.exportar_planilla_excel(materia_cuad)

                ruta_excel_guardada = st.session_state.get("cuad_excel_ruta")
                if ruta_excel_guardada and os.path.exists(ruta_excel_guardada):
                    with open(ruta_excel_guardada, "rb") as f:
                        st.download_button(
                            "Descargar Excel", data=f.read(), file_name=os.path.basename(ruta_excel_guardada),
                            key="planilla_descargar",
                        )

                st.divider()
                st.caption("📋 Notas finales — para copiar y pegar como anuncio en Classroom")
                texto_final = cuaderno.texto_notas_finales(materia_cuad)
                if texto_final:
                    st.code(texto_final, language=None)
                else:
                    st.caption("Todavía no hay ninguna nota final cargada.")

elif pagina_actual == "cola":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "El historial completo de todo lo que hizo cada agente, con filtros por agente y por "
            "curso. Útil para auditar qué pasó y cuándo — no hay acciones para tomar acá, es solo "
            "consulta."
        )
    todos_los_agentes = ["todos"] + [a["nombre"] for a in memoria.listar_agentes()]
    todos_los_cursos = ["todas"] + sorted({t["curso"] for t in memoria.listar_tareas(limite=2000) if t["curso"]})

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_estado = col_f1.selectbox("Estado", ["todas"] + list(memoria.ESTADOS_TAREA))
    filtro_agente = col_f2.selectbox("Agente", todos_los_agentes)
    filtro_curso = col_f3.selectbox("Materia", todos_los_cursos)

    tareas = memoria.listar_tareas(
        estado=None if filtro_estado == "todas" else filtro_estado,
        agente=None if filtro_agente == "todos" else filtro_agente,
        curso=None if filtro_curso == "todas" else filtro_curso,
    )
    if not tareas:
        st.info("No hay tareas que coincidan con esos filtros.")
    else:
        df = pd.DataFrame([dict(t) for t in tareas])
        df["agente_nombre"] = df["agente_nombre"].apply(lambda n: f"{icono_agente(n)} {n}")
        df["creado_en"] = df["creado_en"].apply(hace)
        df = df[["creado_en", "area_nombre", "agente_nombre", "curso", "descripcion", "estado"]]
        df.columns = ["Cuándo", "Área", "Agente", "Curso", "Tarea", "Estado"]
        st.dataframe(df, width='stretch', hide_index=True)

elif pagina_actual == "memoria":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Un gráfico de qué agente tocó qué curso, para ver de un vistazo dónde se concentró el "
            "trabajo últimamente. Es solo para consulta, no hay nada para configurar acá."
        )
    if not st.session_state.get("ver_memoria", False):
        st.info("También es un gráfico interactivo, se carga recién al abrir esta pestaña.")
        if st.button("▶ Mostrar memoria compartida", key="ver_memoria_btn"):
            st.session_state["ver_memoria"] = True
            st.rerun()
    else:
        st.caption(
            "Todo lo que los agentes fueron aprendiendo, conectado por quién lo escribió y sobre qué curso. "
            "Se llena solo a medida que corren los agentes (memoria.agregar_memoria)."
        )
        entradas = memoria.listar_memoria()
        if not entradas:
            st.info("Todavía no hay nada guardado en la memoria compartida. Corré algún agente (ej. el Mejorador) para que empiece a llenarse.")
        else:
            nodes = []
            edges = []
            entradas_por_nodo = {}
            agentes_memoria_por_nodo = {}
            cursos_por_nodo = {}
            agentes_vistos = set()
            cursos_vistos = set()

            for e in entradas:
                entrada_id = f"mem-{e['id']}"
                color = COLOR_TIPO.get(e["tipo"], COLOR_TIPO_DEFAULT)
                nodes.append(Node(id=entrada_id, label=e["clave"][:24], size=12, shape="dot", color=color))
                entradas_por_nodo[entrada_id] = e

                if e["agente"]:
                    agente_id = f"mem-agente-{e['agente']}"
                    if e["agente"] not in agentes_vistos:
                        agentes_vistos.add(e["agente"])
                        nodes.append(Node(id=agente_id, label=e["agente"], size=22, shape="hexagon", color=COLOR_AGENTE_MEMORIA))
                        agentes_memoria_por_nodo[agente_id] = e["agente"]
                    edges.append(Edge(source=agente_id, target=entrada_id))

                if e["curso"]:
                    curso_id = f"mem-curso-{e['curso']}"
                    if e["curso"] not in cursos_vistos:
                        cursos_vistos.add(e["curso"])
                        nodes.append(Node(id=curso_id, label=e["curso"][:24], size=18, shape="diamond", color=COLOR_CURSO))
                        cursos_por_nodo[curso_id] = e["curso"]
                    edges.append(Edge(source=curso_id, target=entrada_id))

            m1, m2, m3 = st.columns(3)
            m1.metric("Nodos de memoria", len(entradas))
            m2.metric("Agentes que aportaron", len(agentes_vistos))
            m3.metric("Cursos cubiertos", len(cursos_vistos))

            col_grafo, col_detalle = st.columns([3, 1])

            with col_grafo:
                config = Config(
                    width="100%",
                    height=550,
                    directed=False,
                    physics=True,
                    hierarchical=False,
                    highlightColor="#71EF8A",
                    collapsible=False,
                )
                seleccionado = agraph(nodes=nodes, edges=edges, config=config)

            with col_detalle:
                st.subheader("Nodo seleccionado")
                if seleccionado in entradas_por_nodo:
                    e = entradas_por_nodo[seleccionado]
                    st.markdown(f"### {e['clave']}")
                    st.write(f"**Tipo:** {e['tipo']}")
                    if e["agente"]:
                        st.write(f"**Agente:** {icono_agente(e['agente'])} {e['agente']}")
                    if e["curso"]:
                        st.write(f"**Curso:** {e['curso']}")
                    st.write(f"**Cuándo:** {hace(e['creado_en'])}")
                    st.caption("Valor")
                    st.code(e["valor"], language=None)
                elif seleccionado in agentes_memoria_por_nodo:
                    nombre = agentes_memoria_por_nodo[seleccionado]
                    st.markdown(f"### {icono_agente(nombre)} {nombre}")
                    aportes = [e for e in entradas if e["agente"] == nombre]
                    st.metric("Aportes a la memoria", len(aportes))
                    for e in aportes[:5]:
                        st.write(f"- {e['clave']}")
                elif seleccionado in cursos_por_nodo:
                    curso = cursos_por_nodo[seleccionado]
                    st.markdown(f"### {curso}")
                    relacionadas = [e for e in entradas if e["curso"] == curso]
                    st.metric("Entradas sobre este curso", len(relacionadas))
                    for e in relacionadas[:5]:
                        st.write(f"- {e['clave']} ({e['tipo']})")
                else:
                    st.info("Hacé clic en un nodo para ver su detalle.")

            with st.expander("Ver todo como tabla"):
                df = pd.DataFrame([dict(f) for f in entradas])
                st.dataframe(df, width="stretch", hide_index=True)

elif pagina_actual == "anio":
    with st.expander("❓ ¿Cómo uso esta sección?"):
        st.markdown(
            "Acá se define qué año lectivo está activo (todo el resto del panel — actividades, "
            "alumnos, planillas — se filtra por este año) y se carga tu horario semanal, que "
            "después usan otras secciones (por ejemplo para sugerir la fecha de un aviso de "
            "licencia o de una clase en el Cuaderno)."
        )
    anio_activo_fila = anios.anio_activo()
    st.subheader(f"📅 Año lectivo activo: {anio_activo_fila['anio']}")

    otros_anios = [a for a in anios.listar_anios() if a["id"] != anio_activo_fila["id"]]
    if otros_anios:
        st.caption("Años cargados: " + ", ".join(
            f"**{anio_activo_fila['anio']}** (activo)" if a["id"] == anio_activo_fila["id"] else str(a["anio"])
            for a in anios.listar_anios()
        ))

    st.divider()
    st.markdown("#### Horario de clases")
    st.caption(
        "Editá acá el horario del año activo — agregá filas con el '+' de abajo, "
        "borrá con el tacho, y guardá cuando termines. Ya no hace falta tocar el Excel."
    )

    bloques_horario = horario.cargar_bloques()
    df_horario = pd.DataFrame(bloques_horario) if bloques_horario else pd.DataFrame(
        columns=["id", "dia", "hora_inicio", "hora_fin", "materia", "curso_grupo", "curso_classroom", "verificar"]
    )
    df_horario_editado = st.data_editor(
        df_horario,
        column_order=["dia", "hora_inicio", "hora_fin", "materia", "curso_grupo", "curso_classroom", "verificar"],
        column_config={
            "dia": st.column_config.SelectboxColumn("Día", options=horario.DIAS, required=True),
            "hora_inicio": st.column_config.TextColumn("Hora inicio", help="ej. 07:45"),
            "hora_fin": st.column_config.TextColumn("Hora fin", help="ej. 12:05"),
            "materia": st.column_config.TextColumn("Materia", required=True),
            "curso_grupo": st.column_config.TextColumn("Curso/Grupo"),
            "curso_classroom": st.column_config.TextColumn("Nombre exacto en Classroom"),
            "verificar": st.column_config.CheckboxColumn("Verificar"),
        },
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="horario_editor",
    )
    if st.button("💾 Guardar cambios de horario", key="horario_guardar", type="primary"):
        horario.guardar_bloques(df_horario_editado.to_dict("records"))
        st.success("Horario actualizado.")
        st.rerun()

    st.divider()
    st.markdown("#### 🆕 Iniciar año lectivo nuevo")
    st.caption(
        "Crea el año nuevo y le copia el horario del año activo tal cual, para que solo "
        "corrijas lo que cambió (el año dentro del nombre del curso de Classroom, cambios "
        "de grado, etc.). NO copia alumnos ni calificaciones — esos se traen frescos de "
        "Classroom cuando sincronices las materias del año nuevo."
    )
    anio_sugerido = anio_activo_fila["anio"] + 1
    nuevo_anio = st.number_input(
        "Año lectivo nuevo", min_value=2000, max_value=2100, value=anio_sugerido, step=1, key="anio_nuevo_input"
    )
    confirmar_anio_nuevo = st.checkbox(
        f"Confirmo iniciar el año {int(nuevo_anio)} y copiar el horario del {anio_activo_fila['anio']}",
        key="anio_nuevo_confirmar",
    )
    if st.button("Iniciar año nuevo", key="anio_nuevo_boton", type="primary", disabled=not confirmar_anio_nuevo):
        try:
            anios.iniciar_anio_nuevo(int(nuevo_anio))
            st.success(
                f"Año {int(nuevo_anio)} iniciado y activado. El horario se copió del "
                f"{anio_activo_fila['anio']} — revisalo arriba y editá lo que cambió."
            )
            st.rerun()
        except ValueError as e:
            st.error(str(e))
