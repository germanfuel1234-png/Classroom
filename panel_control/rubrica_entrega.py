"""Requisitos fijos de presentación que el profesor exige en TODA entrega,
más allá de lo que pida cada consigna puntual. Fuente única para que:

- el Agente Corrector (main.py, verificar_formato_entrega) los CHEQUEE contra
  lo que el alumno realmente entregó, y
- el Agente Mejorador (panel_control.agente_mejorador) los ESCRIBA como
  sección "Forma de entrega" dentro de la consigna mejorada,

usen exactamente el mismo texto y no se desincronicen con el tiempo.
"""

REQUISITOS_FORMATO_ENTREGA = (
    "1. CARÁTULA: la primera hoja debe ser una carátula/portada (diseño libre del alumno); "
    "el documento no debe arrancar directamente con las preguntas.\n"
    "2. PREGUNTAS TRANSCRITAS: en la segunda hoja deben estar transcriptas las preguntas/consignas "
    "de la actividad, antes de empezar a responder.\n"
    "3. FORMATO DE RESPUESTA APROPIADO: cada respuesta debe estar en el formato que esa pregunta "
    "puntual pide — texto si es una pregunta abierta, tabla si pide comparar/tabular datos, o una "
    "imagen/captura de código si pide programar o mostrar código.\n"
    "4. IMAGEN ILUSTRATIVA: en algún punto del trabajo debe haber al menos una imagen o foto que "
    "ayude a la comprensión lectora del tema (ej. una foto de un capacitor si el tema es capacitores, "
    "una captura de Linux/Windows si el tema es sistemas operativos, una foto de un componente de "
    "hardware, etc.), relacionada de verdad con el tema."
)
