"""Calendario de fechas patrias y fechas especiales de Argentina.

No hace falta IA para esto — es un calendario fijo, igual que `horario.py`.
El mensaje de cada fecha es un texto curado una sola vez (no lo escribe
ningún modelo), para que no haya riesgo de que se invente o mezcle un dato
histórico en un saludo que van a ver todos los alumnos de todas las
materias.

Para agregar o cambiar una fecha, se edita directo la lista CALENDARIO de
acá abajo.
"""
import datetime

CALENDARIO = [
    {
        "mes": 3, "dia": 24, "clave": "dia_memoria",
        "nombre": "Día Nacional de la Memoria por la Verdad y la Justicia",
        "mensaje": (
            "Hoy conmemoramos el Día Nacional de la Memoria por la Verdad y la Justicia, "
            "en recuerdo de las víctimas del terrorismo de Estado en nuestro país. Memoria, "
            "verdad y justicia son valores que como comunidad educativa reafirmamos cada 24 de marzo."
        ),
    },
    {
        "mes": 4, "dia": 2, "clave": "dia_malvinas",
        "nombre": "Día del Veterano y de los Caídos en la Guerra de Malvinas",
        "mensaje": (
            "Hoy recordamos a los veteranos y caídos en la Guerra de Malvinas. Un homenaje "
            "a quienes defendieron la soberanía nacional y a sus familias."
        ),
    },
    {
        "mes": 5, "dia": 1, "clave": "dia_trabajador",
        "nombre": "Día del Trabajador",
        "mensaje": "Feliz Día del Trabajador para todas las familias de nuestra comunidad educativa.",
    },
    {
        "mes": 5, "dia": 25, "clave": "revolucion_mayo",
        "nombre": "Día de la Revolución de Mayo",
        "mensaje": (
            "Hoy conmemoramos un nuevo aniversario de la Revolución de Mayo de 1810, el "
            "primer paso hacia nuestra independencia. ¡Feliz 25 de Mayo!"
        ),
    },
    {
        "mes": 6, "dia": 20, "clave": "dia_bandera",
        "nombre": "Día de la Bandera",
        "mensaje": (
            "Hoy es el Día de la Bandera, en homenaje a su creador, el General Manuel "
            "Belgrano. ¡Feliz Día de la Bandera!"
        ),
    },
    {
        "mes": 7, "dia": 9, "clave": "dia_independencia",
        "nombre": "Día de la Independencia",
        "mensaje": (
            "Hoy celebramos un nuevo aniversario de la Declaración de la Independencia "
            "Argentina, firmada en Tucumán en 1816. ¡Feliz Día de la Independencia!"
        ),
    },
    {
        "mes": 8, "dia": 17, "clave": "san_martin",
        "nombre": "Paso a la inmortalidad del General José de San Martín",
        "mensaje": (
            "Hoy recordamos al General José de San Martín, Libertador de Argentina, Chile "
            "y Perú, en un nuevo aniversario de su paso a la inmortalidad."
        ),
    },
    {
        "mes": 9, "dia": 11, "clave": "dia_maestro",
        "nombre": "Día del Maestro",
        "mensaje": (
            "Hoy es el Día del Maestro, en homenaje a Domingo Faustino Sarmiento. Un "
            "saludo a todos los docentes de nuestra comunidad educativa."
        ),
    },
    {
        "mes": 10, "dia": 12, "clave": "diversidad_cultural",
        "nombre": "Día del Respeto a la Diversidad Cultural",
        "mensaje": (
            "Hoy es el Día del Respeto a la Diversidad Cultural, una fecha para valorar la "
            "pluralidad de culturas que conforman nuestra identidad como nación."
        ),
    },
    {
        "mes": 11, "dia": 20, "clave": "soberania_nacional",
        "nombre": "Día de la Soberanía Nacional",
        "mensaje": (
            "Hoy conmemoramos el Día de la Soberanía Nacional, en homenaje a la Batalla de "
            "la Vuelta de Obligado."
        ),
    },
    {
        "mes": 12, "dia": 25, "clave": "navidad",
        "nombre": "Navidad",
        "mensaje": "¡Feliz Navidad para vos y toda tu familia! Que este tiempo sirva para compartir en familia.",
    },
    {
        "mes": 1, "dia": 1, "clave": "anio_nuevo",
        "nombre": "Año Nuevo",
        "mensaje": "¡Feliz Año Nuevo! Que este nuevo año esté lleno de aprendizajes y logros.",
    },
]


def fecha_de_hoy(fecha: datetime.date | None = None) -> dict | None:
    """Devuelve la entrada del calendario que coincide con `fecha` (hoy por
    defecto), o None si no es una fecha patria."""
    fecha = fecha or datetime.date.today()
    for entrada in CALENDARIO:
        if entrada["mes"] == fecha.month and entrada["dia"] == fecha.day:
            return entrada
    return None
