<!--
Este archivo ES el prompt que se le manda a Gemini para buscar bibliografía,
videos y manuales — panel_control/recursos_educativos.py lo lee de acá
(no está harcodeado en el código Python). Si querés cambiar QUÉ le pedís
que busque, editá el texto de abajo; los {materia} y {tema} se reemplazan
solos por los datos reales de cada actividad antes de mandarlo.
-->

# Qué datos recibe Gemini antes de buscar

Hoy, antes de cada búsqueda, solo se le pasan **dos datos** — nada más:

| Dato | De dónde sale | Ejemplo real |
|---|---|---|
| `{materia}` | Nombre del curso tal cual figura en Classroom | `Sistemas Digitales 6to` |
| `{tema}` | Título de la actividad tal cual está en Classroom | `TP 3 - Multiplexores` |

**Lo que NO se le pasa hoy** (y podría afinar más los resultados si algún
día se agrega):
- El **enunciado completo** de la consigna — ya lo tenemos guardado en la
  base (`actividades_classroom.enunciado`), pero `buscar_recursos()` no lo
  usa todavía. Ayudaría cuando el título es genérico (ej. "TP 3") y el tema
  real está solo en el enunciado.
- El **diseño curricular** de la materia/año (`memoria.contexto_curricular`)
  — lo usan otros agentes (Evaluador, Publicador) para no salirse de los
  contenidos mínimos, pero la búsqueda de bibliografía no lo consulta.
- El **año curricular** (4to/5to/6to/7mo) — para ajustar el nivel de
  complejidad de lo que se busca.

Si en algún momento se quiere sumar el enunciado o el contexto curricular a
esta búsqueda, avisá y se agrega como un dato más acá abajo.

---

# Instrucciones que se le mandan a Gemini (el prompt real)

El código solo toma el texto entre las dos marcas de abajo (`PROMPT:INICIO`
/ `PROMPT:FIN`) y le reemplaza `{materia}` y `{tema}` — todo lo demás de
este archivo es documentación para vos, no se le manda a Gemini.

<!-- PROMPT:INICIO -->
Sos un profesor de una escuela técnica secundaria armando un Trabajo
Práctico de la materia "{materia}" sobre el tema: "{tema}".

Buscá en internet (no respondas de memoria) y encontrá:
1. Una fuente bibliográfica confiable sobre el tema.
2. Uno o dos videos de YouTube en español que expliquen el tema con
   claridad.
3. Si el tema es de programación o tiene documentación oficial (por
   ejemplo un lenguaje como C++ o Python), un manual o documentación
   oficial de referencia. Si el tema no tiene un manual oficial
   aplicable, omitilo.
<!-- PROMPT:FIN -->

---

# Cómo se valida lo que trae (para que no invente links)

- Se usa **grounding real de Google Search** (`google_search` tool de
  Gemini) — no texto libre. Sin esto, cualquier modelo de texto puede
  "alucinar" una URL que suena real pero no existe.
- Solo se confía en las URLs que vienen en los metadatos de grounding
  (evidencia real de que Gemini efectivamente encontró esa página) —
  nunca en URLs que el modelo haya escrito como texto dentro de la
  respuesta, esas sí pueden inventarse aunque la búsqueda haya sido real.
- Cada URL se clasifica sola por dominio: YouTube → video, dominios de
  documentación oficial (docs.python.org, developer.mozilla.org, etc.) →
  manual, el resto → bibliografía general.

# Qué pasa con el resultado

Nada se publica solo: cada resultado queda guardado como sugerencia
pendiente (cola `recursos_bulk` o borrador de aprobación), y el profesor
lo revisa —tildando cuáles sí y cuáles no— antes de que se adjunte de
verdad a la actividad en Classroom.
