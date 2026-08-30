"""Carga los Contenidos Mínimos del Diseño Curricular (DGCyE Buenos Aires,
Técnico en Informática Personal y Profesional) en la memoria compartida,
para que los agentes que generan contenido pedagógico (Mejorador, Consultas,
Publicador) lo tengan siempre presente vía panel_control.memoria.contexto_curricular().

Fuente: dos resoluciones de Diseño Curricular provincial (PDFs entregados por
el profesor) — el texto de cada materia se transcribió tal cual del PDF con
mejor calidad de extracción para esa materia (la mayoría del Anexo 3, más
prolijo; un par de materias del otro expediente, que sí tenía texto digital
limpio en esas páginas puntuales aunque el resto del documento está
escaneado).

No parsea los PDF en tiempo de ejecución (uno de los dos tiene páginas
fotografiadas/escaneadas de calidad dispareja, poco confiables para un
regex automático) — el texto ya viene verificado a mano acá abajo.

Matchea contra los cursos de Classroom EN VIVO (no contra el Excel de
horarios, que es solo una estimación) para que el nombre guardado en
`memoria.curso` sea idéntico al que usan los agentes al llamar
contexto_curricular(nombre_materia).

Uso: python -m panel_control.scripts.cargar_diseno_curricular
Se puede volver a correr sin duplicar (borra e inserta de nuevo por clave).
"""
from googleapiclient.discovery import build

import main as classroom
from panel_control import memoria

AGENTE = "Carga Diseño Curricular"

# ---------------------------------------------------------------------------
# Contenidos Mínimos transcriptos de los PDF (Técnico en Informática
# Personal y Profesional, DGCyE Buenos Aires)
# ---------------------------------------------------------------------------

LAB_PROGRAMACION_4TO = """Laboratorio de Programación — 4° año (Contenidos mínimos)
Se abordan a continuación los contenidos divididos por núcleos temáticos teniendo en cuenta el
paradigma de programación estructurada. El orden es sólo una forma de presentación, tratando
de incrementar los niveles de abstracción a medida que se avanza, los temas propuestos se
exponen de manera general sin hacer referencia a ningún lenguaje de programación específico,
aunque se recomienda el trabajo sobre el ANSI C/C++.

Interpretación y resolución de problemas. Interpretación de enunciados. Identificación de datos,
problema a resolver, resultados. Resolución de problemas identificando los datos, planteo y
prueba de la solución. Definición de algoritmo y programa. Concepto de compilador y enlazador.
Entornos de desarrollo integrados (IDE). Concepto de código fuente, objeto y binario.

Algoritmos de resolución lineal. Algoritmos de resolución mediante métodos lineales. Aplicación
del criterio top down en la resolución de problemas. Concepto de variable y constante. Asignación
del tipo de dato. Diagramación lógica. Modelos y estándares de diagramación. Resolución de
problemas simples mediante diagramación lógica. Concepto de Contador y Acumulador.

Tipos de datos y modificadores. Tipos de datos aplicados a la programación. Determinación del
tipo de dato. Variables enteras, reales booleanas, doble precisión y de caracteres. Rango de
datos. Variables locales y globales. Modificadores de tipos. Palabras reservadas.

Operadores y su precedencia. Operadores aritméticos, relacionales y lógicos. Operadores
unarios. Operadores a nivel de bytes y a nivel de bits. Precedencia de operadores.

Estructuras condicionales. Toma de decisiones. La estructura condicional if…else. Resolución de
algoritmos en los que se apliquen estructuras condicionales. Condicionales simples y anidadas.
Estructuras condicionales de selección múltiple switch…case. Resolución de problemas mediante
el diseño y desarrollo de programas. Prueba de escritorio.

Estructuras de repetición. Concepto de estructura de repetición. Repetición controlada por
contador y por centinela. Estructura de repetición for. Estructuras de repetición while y
do…while. Condiciones de corte y salida de programa. Resolución de problemas mediante el
desarrollo de algoritmos donde se apliquen estructuras condicionales y de repetición.

Diseño de programas, técnicas para la construcción, documentación y seguimiento. Clasificación
de los lenguajes de programación. Selección de la herramienta adecuada según la plataforma
sobre la cual se realizará la solución. Confección de la documentación. Ventajas de comentar los
programas realizados. Implementación y seguimiento de la solución desarrollada. Asistencia
básica al usuario."""

LAB_PROGRAMACION_5TO = """Laboratorio de Programación — 5° año (Contenidos mínimos)
Se propone mediante los siguientes contenidos el abordaje a la programación en un segundo
nivel de complejidad. Si bien la presente propuesta es factible de desarrollarse con cualquier
lenguaje de programación, se sugiere, así como en el año anterior, el trabajo con ANSI C/C++.

Ventajas de dividir la problemática en problemas menores. Aplicación del criterio top down.
Concepto de biblioteca y funciones. Definición de funciones. Prototipos de función. Pasaje de
parámetros por valor y por referencia. Concepto de recursividad. Diferencias y similitudes entre
recursividad e iteración. Arreglos unidimensionales (vectores) y bidimensionales (matrices).
Declaración y ejemplos. Métodos de búsqueda y ordenamiento. Pasaje de arreglos a una función.
Arreglos de caracteres. Bibliotecas para la manipulación de caracteres y cadenas. Funciones de
conversión, comparación y de memoria. Concepto de Punteros, representación de la memoria de
la computadora. Definición e inicialización de punteros. Operadores. Llamadas a funciones y
pasajes por referencia. Expresiones con punteros. Aritmética de punteros. Relación entre
punteros y arreglos. Arreglos de punteros. Punteros a funciones."""

LAB_PROGRAMACION_6TO = """Laboratorio de Programación — 6° año (Contenidos mínimos)
Se propone mediante los siguientes contenidos el abordaje a la programación en un segundo
nivel de complejidad. Si bien la presente propuesta es factible de desarrollarse con cualquier
lenguaje, se sugiere, así como en el año anterior, el trabajo con ANSI C/C++.

Estructuras de datos. Definición e inicialización de estructuras. Acceso a los miembros de la
estructura. Funciones y estructuras. Definición de tipos. Uniones. Procesamiento de archivos.
Jerarquía de datos. Archivos y flujos. Acceso secuencial. Acceso aleatorio. Archivos de texto y
binarios. Introducción a las estructuras dinámicas en programación. Estructuras
autorreferenciadas. Asignación dinámica de memoria. Listas. Listas enlazadas. Pilas. Colas.
Árboles. Concepto de Shell. Shells y sistemas operativos. Operación de los shells y conceptos
de sintaxis. Variables utilizadas y establecidas por el shell. Procesamiento en segundo plano y
control de procesos. Sustitución de comandos. Creación de alias de comandos. Programación de
shell. Generación de archivos de inicio de shell. Scripting."""

LAB_HARDWARE_4TO = """Laboratorio de Hardware — 4° año (Contenidos mínimos)
Esta descripción presenta aquellos contenidos que podrían desarrollarse en el transcurso de las
actividades formativas. La misma no indica secuencia, será el equipo docente a cargo del
módulo quien resuelva en qué momento y a través de qué actividades los desarrollará.

Contenidos generales. Introducción a los sistemas computacionales. Organización y arquitectura
de una computadora. Estructura y funcionamiento. Concepto de Hardware y Software. Breves
antecedentes históricos. El sistema computadora personal basado en microprocesador. Los
principales componentes de una computadora. Ejemplo de un sistema actual. Desarrollo histórico
(generaciones). Niveles de jerarquía de una computadora. El modelo de von Neumann. Otras
arquitecturas.

Introducción a la arquitectura de computadoras. Introducción: Organización básica de un CPU –
Registros y Buses – Clocks – Subsistema de Entrada / Salida – Organización y direccionamiento
de la memoria. Interrupciones. Ejemplos de arquitecturas reales: Modelo de von Neumann –
Modelo de Harvard. Concepto de microprocesador y microcontrolador. Ejemplos. Instalaciones
eléctricas. Montaje. Cálculo. Normas de seguridad. Protecciones. Disyuntores. Fusibles.
Estabilizadores. Unidades de energía ininterrumpidas. Tipos, capacidades y características.
Estructura de un equipo de computo, instalación y conexión. Microprocesador. Placa madre.
Memoria. Fuentes de alimentación. Gabinetes. Cableado. Tarjeta de expansión. Buses. Normas.
Configuración básica (setup). Instalación de memorias. Discos rígidos. Discos flexibles.
Controladoras. Dispositivos ópticos, etc. Tarjeta de sonido. Tarjeta de vídeo. Tarjeta de Red.
Principios de funcionamiento. Configuraciones básicas y soluciones de errores. Drivers. Puesta en
marcha. Otros dispositivos de almacenamiento. Dispositivos de entrada y salida. Teclado.
Impresoras. Monitores. Scanners. Módems. Principios de funcionamiento. Configuraciones básicas
y soluciones de errores. Drivers. Puesta en marcha. Otros dispositivos de entrada y salida.
Identificación de especificaciones para la conexión de periféricos. Su compatibilidad. Testeo,
análisis y seguimiento de fallas. Identificación de fallas. Reemplazo de componentes defectuosos.
Renovación o actualización de equipos y partes. Mantenimiento Básico de Computadoras y
Periféricos. Diagnóstico y solución de fallas comunes. Mantenimiento preventivo, correctivo y
predictivo. Utilización de instrumental y herramental acorde a la práctica profesional del sector."""

LAB_HARDWARE_5TO = """Laboratorio de Hardware — 5° año (Contenidos mínimos)
El orden de los contenidos propuestos a continuación es sólo una forma de presentación,
correspondiendo a la institución su organización pedagógico-didáctica al elaborar el Proyecto
Curricular Institucional. Los mismos no se presentan como unidades temáticas para ser
desarrolladas por el equipo docente, sino como fundamentos para el desarrollo de las capacidades
profesionales mencionadas.

Introducción a las redes. Cobertura de las redes. Interoperatividad. Razones para instalar una
red de computadoras. Clasificación, WAN, MAN, LAN, Redes Cliente Servidor, Peer to Peer. LAN,
topología física y lógica. Especificaciones LAN, Ethernet, IEEE 802.x, FDDI. Comparación con las
capas del modelo OSI. Placa de red, dirección MAC, unicast, multicast y broadcast.
Encapsulación, MTU. Cableado, cable UTP, conectorización, Normas EIA/TIA 568B. Dispositivos de
red, hub, switch, router. Características, limitaciones. Dominio de colisión, dominio de
broadcast. Segmentación. Ethernet 100BaseTX, Gigabit Ethernet. Switching, métodos, store and
forward, cut-trhough y fragment free, operación a N2, redundancia, Spanning Tree Protocol.
Configuración de switches, modo usuario y modo privilegiado, comandos. Nociones de Cableado
Estructurado, Cuarto de comunicaciones, Racks, Cableado horizontal, elementos que lo componen.
Análisis del tráfico en una LAN. Sniffing, analizadores de protocolo, captura del tráfico, filtros
de captura, análisis."""

LAB_HARDWARE_6TO = """Laboratorio de Hardware — 6° año (Contenidos mínimos)
Ruteo de la Información. Ruteo estático. Ruta default. Protocolos de ruteo dinámico. RIP.
Comandos Ping, Traceroute, Netstat, Arp. Formato del Datagrama IP versión 4.0. Protocolo no
orientado a la conexión. Protocolo no fiable. Tipo de servicios. Time to live. Fragmentación.
Cheksum. Protocolo de control de trasmisión TCP/UDP. Transferencia básica. Formato del
segmento TCP. Fiabilidad. Control de flujo. Multiplexación. Conexiones. Sincronización de N4.
Establecimiento y finalización de la conexión. Números de puerto de TCP. Well Know Port.
Ventana de recepción. Gestión de la ventana. Protocolo UDP. Formato. Diferencia con TCP.
Aplicaciones en TFTP y aplicaciones en tiempo real como videoconferencia y telefonía IP.
Protocolo Frame Relay. Orientado a la conexión y no fiable. Líneas digitales. Formato de trama
de nivel 2. Concepto de congestión. BECN. FECN. DE. CIR. Concepto de circuito virtual
permanente. PVC. Redes MPLS Multi-Protocol Label Switching. Redes full malla. Calidad de
servicio (QoS). Análisis del datagrama IP de capa 3 para priorización de tráfico. Clases de
servicio. Real time, Assured forwarding y Best effort. Parámetros de performance. Paquetes
perdidos. Delay y Jitter. Normas G.711 y G.729 (compresión de voz). Cálculo de ancho de banda
de Voz sobre IP en LAN y WAN para diferentes tiempos de muestro. Retardo de serialización. RTP
(Real Time Protocol). Tecnologías XDSL. ADSL Asymetric Digital Suscriber Line, SDSL Symetric
Digital Suscriber Line, Bucle de abonado, Distancias. Modulación, Espectro en frecuencia. Módem
ATU-R (Terminal remota). Módem ATU-C (Terminal central). Multiplexor DSLAM. Spliter pasa alto
y pasa bajo. Multiplexor por División de Frecuencia. Concepto de subportadoras de bajada y
subida. Principios básicos de ATM."""

SIST_OPERATIVOS_4TO = """Laboratorio de Sistemas Operativos — 4° año (Contenidos mínimos)
Contenidos generales:
- Concepto de sistema operativo (sus funciones y estructura, descripción elemental de cómo
  trabaja y de las herramientas de diagnóstico que brinda).
- Instalación y manejo del sistema operativo (visualizaciones que brinda, comandos que permiten
  operar, instalación o actualización de elementos optativos, personalizaciones que ayudan al
  usuario).
- Introducción a aspectos de conectividad.

Contenidos específicos:
- Concepto de sistema operativo. Manejo de archivos; de entrada/salida; de la memoria.
  Conceptos de cómo funciona: núcleo, interrupciones y llamadas al sistema, su utilidad para
  situaciones de error. Panel de control, sus posibilidades de configuración. Arranque y carga
  del sistema operativo.
- La función de imprimir en forma diferida al procesamiento. Utilidad práctica de administrar
  la impresión, programa que lo realiza y comandos que la gobiernan. La utilización de varias
  impresoras y la preparación de salidas para impresoras no necesariamente conectadas.
  Controladores de impresión (drivers), su instalación y actualización. Tipografías (fonts), su
  instalación y funcionamiento.
- La interface con el usuario. Principios de claridad y mejor utilización, posibilidades de
  organización y apagado de la pantalla. Incidencia en la operatoria y los errores del usuario;
  cómo personalizarla.
- Tipos y organización de la memoria real; su asignación, administración y protección. Formas
  de administrar la memoria y su incidencia en el comportamiento de la ejecución de programas.
  Programas residentes. Herramientas para diagnóstico del uso y reasignación de la memoria.
  Memoria virtual y su administración; el problema del swapping y sus efectos sobre la rapidez
  de ejecución.
- Concepto de proceso. Prioridades y esquemas de ejecución, recursos que utilizan los
  programas. Tipos de interrupción. Formas de recabar información y alterar las prioridades de
  ejecución, efectos de hacerlo. Procesos con líneas de ejecución paralelas para aprovechar la
  disponibilidad de múltiples procesadores. Problemas de comportamiento y herramientas para
  diagnóstico.
- La extensión de los límites de la máquina a un grupo o al mundo. Concepto de grupo, acceso a
  recursos compartidos. Concepto de Internet, browser y funciones que brinda; su interacción con
  el sistema operativo, problemas de ajuste (setting) y compatibilidad con aplicaciones.
- Conceptos de seguridad. Instalación del sistema operativo. Parámetros de instalación y
  posibilidades de configuración en función de la máquina y el entorno de aplicaciones.
- Distintos tipos de Arquitecturas. Sistemas abiertos y cerrados o propietarios,
  características, instalación, comparación, dll's, scripts, sistemas de archivos,
  compatibilidad, núcleo de un SO, modularidad, etc."""

SIST_OPERATIVOS_5TO = """Laboratorio de Sistemas Operativos — 5° año (Contenidos mínimos)
El orden de los contenidos propuestos a continuación es sólo una forma de presentación,
correspondiendo a la institución su organización pedagógico-didáctica al elaborar el Proyecto
Curricular Institucional. Los mismos no se presentan como unidades temáticas para ser
desarrolladas por el equipo docente, sino como fundamentos para el logro de las capacidades
profesionales mencionadas.

Redes, modelo cliente servidor y peer to peer. Sistemas Operativos de Red. Conceptos de Nodo,
Estación de Trabajo o Cliente, Servidor y Periféricos. Aspectos del Diseño, Formas de Seleccionar
el Sistema Operativo más adecuado para una red. Sistemas Operativos propietarios del tipo Server
y Workstation: características, similitudes y diferencias. Requerimientos mínimos para su
instalación. Soluciones similares de software libre, preferentemente en distintas distribuciones.
Protocolos de las capas superiores: HTTP, DHCP, DNS, SMTP, POP, IMAP, Control remoto y Nodo
Remoto, Autentificación y Seguridad, Correo Electrónico: características distintivas de los
protocolos. Conexiones a Internet. IP, Protocolo de Internet. Direcciones IP públicas.
Direcciones IP privadas (reservadas). ARP (Address Resolution Protocol). Mapeo de una MAC a
dirección IP. Comando Ping. Traceroute. Instalación y configuración de una red igualitaria con
Sistemas Operativos Propietarios y Libres (i.e. bajo distintas distribuciones) del tipo
Workstation. Recursos compartidos. Gestión de usuarios. Directivas del sistema. Auditoría. Copias
de seguridad."""

SIST_OPERATIVOS_6TO = """Laboratorio de Sistemas Operativos — 6° año (Contenidos mínimos)
El orden de los contenidos propuestos a continuación es sólo una forma de presentación,
correspondiendo a la institución su organización pedagógico-didáctica al elaborar el Proyecto
Curricular Institucional. Los mismos no se presentan como unidades temáticas para ser
desarrolladas por el equipo docente, sino como fundamentos para el logro de las capacidades
profesionales mencionadas.

Planificar y configurar la red. Planificación de redes. Identificación de las necesidades de una
red local. Evaluación de las necesidades de equipo y rendimiento. Almacenamiento en disco.
Sistemas de copia de seguridad. Estaciones sin disco. Cableado. Equipo de protección del
sistema. Identificación de los requisitos de las aplicaciones. Selección de un servidor.
Rendimiento y cuellos de botella. El microprocesador. El bus del servidor. El sistema de discos.
Superservidores. Sistemas multiprocesador simétricos y asimétricos. Protección de los datos y
equipos de la red. Protección de la red y sus datos. Técnicas de copia de seguridad y
protección de los datos. Procedimientos de copia de seguridad. Problemas de alimentación y
soluciones. Dispositivos de protección. Configuración de los equipos. Preparación de la
ubicación. Configuración del servidor. Supresión de conflictos de interrupciones y puertos de
E/S. Instalación de unidades y controladores de disco. Instalación de las placas de red.
Instalación de un SAI. Configuración de estaciones de trabajo. Estaciones sin disco. Instalación
y verificación del cableado. Equipos de verificación del cableado.

Instalación de la Red. Preparación de la instalación. Instalación de nuevos servidores. Carga
del sistema operativo de red en el servidor. Denominación del servidor. Asignación del número
interno de la red. Especificación de unidades de disco. Particionamiento de la unidad.
Establecimiento de la duplicación de disco y de canal. Carga de controladores de red. Proceso de
actualización. Preparación de una actualización a distancia. Preparación de una actualización
sobre el mismo servidor. Opciones de instalación. Instalación del sistema operativo de red.
Instalación de estaciones de trabajo. Otras opciones y utilidades. Personalización de las
sesiones. Instalación de soporte para interconexión de redes. Configuración de placas.
Configuración de protocolos. Asignación del TCP/IP a la placa de red. Información general sobre
nodos. Instalación del soporte TCP/IP en las estaciones. Configuración de Sistemas Operativos
propietarios y libres: IP, Máscara de Red, Puerta de Enlace, DNS, Nombre de Equipo, Nombre de
Grupo de Trabajo. Instalación y configuración de Firewall. Acceso Remoto, Aplicaciones.
Introducción al diseño, instalación, configuración y personalización de Intranets. Dominios.
Dominios vs Grupos de Trabajo. Gestionar y usar la Red. Actividades posteriores a la instalación.
Entrada en el sistema. Personalización de los procedimientos de conexión a la red. La orden
LOGIN. Salida del sistema. El sistema de archivos. Organización de directorios. Secuencias de
conexión. Tareas futuras para administradores y supervisores. Jerarquía y seguridad en una red.
Privilegios. Jerarquía de usuarios. Estudio de los derechos. Cómo asignar derechos sobre
archivos y directorios. Cómo asignar derechos de acceso. Administración del sistema de
archivos. Gestión de archivos y directorios. Utilidades y órdenes para usuarios. Asignación de
unidades. Conexiones de impresoras. Conexión de servidores. Servicios de impresión. Colas de
impresión. Servidores de impresión. Configuración de los servicios de impresión. Configuración
de impresoras remotas. Secuencias de conexión. Tipos de secuencias de conexión. Cómo y cuándo se
ejecutan las secuencias de conexión. Opciones de conexión. Visualización de información sobre la
estación y la conexión. Sistemas de copia de seguridad en la red. Compresión. Información
adicional sobre archivos de registro. Sistema de facturación. Sistema de auditoría. Introducción
al monitoreo y mantenimiento. Técnicas y herramientas para gestión de redes. Consola remota.
Información sobre conexiones. Información sobre la red LAN/WAN. Información sobre discos.
Información el sistema. Actividad de archivos abiertos y bloqueos. Utilización de caché.
Utilización del procesador. Estadísticas sobre recursos. Estadísticas de memoria. Información
sobre planificación. Ordenes del servidor y opciones para mejorar el rendimiento. Visualización
de información sobre el servidor. Modificación de la configuración del servidor. Archivos de
inicialización del servidor. Parámetros del servidor. Información sobre usuarios y conexiones.
Supresión de conexiones. Registro de errores del servidor. Desconexión del servidor. Gestión del
almacenamiento en disco. Visualización de información sobre el sistema de archivos. Montaje y
desmontaje de volúmenes. Proceso de reparación. Servidores. Instalación, configuración,
personalización, administración y mantenimiento de servidores: DNS, DHCP, Web, FTP, Correo
Electrónico, etc. Implementación definitiva: Prueba piloto. Ajustes finales. Adecuación al marco
de la realidad y practicidad. Transmitir y demostrar la funcionalidad del producto."""

LAB_APLICACIONES_4TO = """Laboratorio de Aplicaciones — 4° año (Contenidos mínimos)
Se detallan a continuación los núcleos temáticos divididos por aplicación, se sugiere el orden
propuesto. Aplicaciones para procesar y formatear texto. Ventana de la aplicación. Barra de menú
y de herramientas. Creación y modificación de documentos. Configuración de página, márgenes,
encabezado y pie de página. Herramientas para el formato de texto. Numeración y viñetas.
Inserción, modificación y formato de tablas. Inserción y modificación paratextos. Inserción de
imágenes. Documentos con hipervínculos. Impresión del documento. Aplicaciones para el trabajo
con planillas de cálculo. Ventana de la aplicación. Barra de menú y de herramientas. Concepto de
libro, hoja de cálculo, celda y rango. Formato de celdas. Fórmulas y funciones. Fórmulas que
vinculen varias hojas. Inserción de imágenes. Representación de datos mediante gráficos.
Aplicaciones para el diseño y desarrollo de presentaciones. Ventana de la aplicación. Barra de
menú y de herramientas. Creación de una presentación nueva. Formato de la presentación. Agregar
nuevas diapositivas. Insertar texto en la diapositiva. Formatear el texto. Insertar imágenes y
gráficos. Transición de la diapositiva. Efectos de animación. Insertar películas y sonidos.
Generar una presentación autoejecutable. Impresión de las diapositivas. Aplicaciones para la
gestión y administración de bases de datos. Concepto de base de datos. Archivo, registros y
campos. Motores de base de datos. Creación de una base de datos. Tablas, formularios, consultas
e informes. Utilidades de las bases de datos. Seguridad. Diseño y desarrollo de un ABM simple."""

SISTEMAS_DIGITALES_5TO = """Sistemas Digitales — 5° año (Contenidos mínimos)
Se detallan a continuación los núcleos temáticos del presente módulo, se sugiere el orden
propuesto. Variables, analógicas y digitales, características, ámbito de aplicación. Sistemas
físicos digitales combinacionales y con memoria. Sistemas de numeración. Base de un sistema.
Distintas bases: sistema decimal, sistema binario, sistema octal y hexadecimal. Cambios de base.
Operaciones aritméticas. Funciones lógicas, representación, tabla de estados. Álgebra de Boole,
postulados, propiedades y, teoremas. Circuitos combinacionales. Compuertas. Diagrama Circuital.
Implementación de funciones lógicas a través de circuitos de compuertas. Formas canónicas de una
función, minitérminos y maxitérminos, adyacencias, simplificación. Mapa de Karnaugh. Estructura,
simplificación aplicando el diagrama, limitaciones, funciones no totalmente definidas,
implementación de funciones con un sólo tipo de compuertas. Funciones aritméticas, números con
formato, suma de números signados, complemento a la base y a la base menos uno como forma de
obtener números signados. Circuitos sumador, sumador-restador en complemento a dos, comparador.
Códigos y circuitos asociados. Códigos BCD, distancia detección y corrección de errores,
códigos con redundancia, paridad, hamming. Códigos ASCII. Circuitos codificadores,
decodificadores, multiplexores, demultiplexores, conversores de código, suma BCD, corrección."""

SISTEMAS_DIGITALES_6TO = """Sistemas Digitales — 6° año (Contenidos mínimos)
Se detallan a continuación los núcleos temáticos del presente módulo, se sugiere el orden
propuesto. Familias y subfamilias lógicas. Clasificación, características, comparación.
Circuitos secuenciales. Conceptos de memoria de un bit. Flip Flops. Contadores y Registros.
Lógica secuencial. Concepto de realimentación en un sistema lógico combinacional. Circuitos
biestables: R-S asincrónico. Tabla de verdad. Ecuación característica. Condición de restricción.
Biestable como elemento básico de memoria. Biestables sincrónicos: R-S, J-K, D y T. Tabla de
verdad. Ecuación característica. Diagramas temporales. Entradas asincrónicas o de fuerza.
Función. Utilidad. Biestable Master/Slave. Implementación de circuitos utilizando los diferentes
tipos de biestables. Registros. Implementación de registros utilizando biestables.
Restricciones. Registros de desplazamiento. Tipos de registros: serie/serie, serie/paralelo,
paralelo/serie, paralelo/paralelo. Diagramas temporales asociados. Concepto de memoria de "n"
bits. Contadores. Características de los circuitos contadores: tipo, módulo, secuencia.
Implementación de contadores utilizando biestables. Restricciones. Contadores en anillo:
memoria circulante. Implementación. Diagramas temporales. Contadores asincrónicos:
características. Síntesis de contadores asincrónicos progresivos y regresivos. Diagramas
temporales. Contadores sincrónicos: características. Síntesis de contadores sincrónicos
progresivos y regresivos de cualquier módulo. Diagramas temporales. Confección de la tabla de
transiciones de estado de entradas y salidas según el biestable utilizado. Memorias, Conceptos
básicos. Tipos de memoria. Clasificación. Diferentes tecnologías. Campo de utilización de cada
tipo. Bancos de memoria. Implementación y organización. Asignación de las líneas necesarias en
los buses de dirección y de datos. Identificación de los bloques de memoria utilizando notación
binaria y hexadecimal. Introducción a La Arquitectura de Computadoras. Organización básica de un
CPU – Registros y Buses – Clocks – Subsistema de Entrada / Salida – Organización y
direccionamiento de la memoria. Interrupciones. Ejemplos de arquitecturas reales: Modelo de von
Neumann – Modelo de Harvard. Concepto de microprocesador y microcontrolador. Ejemplos.

Arquitectura de Computadoras. Arquitectura de un microprocesador. Circuitos LSI / VLSI.
Evolución histórica de los sistemas computacionales en relación al avance científico
tecnológico de los microprocesadores. Registros y buses. Ciclos de lectura y escritura. Tiempos
de acceso. Áreas de datos, código y pila. Interrupciones enmascarables y no enmascarables.
Interrupciones por hardware y por software. El modelo de programación. Nociones de
direccionamiento de memoria en modo real y modo protegido. Nociones de paginación de memoria.
Modos de direccionamiento. Concepto de DMA. Direcciones de periféricos: Ports de E/S.
Estructuras de interconexión. Interconexión con buses. Concepto de Instrucción. Código de
operación. Operandos. Tipo de instrucciones. Ejecución de instrucciones por parte del CPU.
Ciclos de instrucción, máquina y reloj. Ejecución de programas básicos. Introducción al lenguaje
Assembler x86. Concepto de Firmware. ALU. Operaciones aritméticas y lógicas. Registro de
estado. Operaciones con números enteros y punto flotante. Desarrollo de algoritmos básicos en
lenguaje Assembler."""

REDES_INFORMATICAS_7MO = """Instalación, Mantenimiento y Reparación de Redes Informáticas — 7° año (Contenidos mínimos)
El orden de los contenidos propuestos a continuación es sólo una forma de presentación,
correspondiendo a la institución su organización pedagógico-didáctica al elaborar el Proyecto
Curricular Institucional. Los mismos no se presentan como unidades temáticas para ser
desarrolladas por el equipo docente, sino como fundamentos para el logro de las capacidades
profesionales mencionadas.

Mantenimiento de redes informáticas: concepto, clasificación, documentación del proceso de
mantenimiento. Protocolos de mantenimiento estandarizados. Instalación de redes: Cableado
estructurado. Horizontal y vertical. Normas Internacionales: EIA/TIA 568B, Cables, Conectores y
distancias. Conectorizado de Plug, Jack y Patcheras. Cableado Horizontal UTP Cat 5e, 6 y 6a.
Diferentes tipos de cables: UTP, STP, FTP, PIMF. Fibra óptica monomodo y multimodo. Reflexión.
Refracción. Índice refractivo. Core/Cladding. Apertura numérica. Backbone Vertical. EIA/TIA 569B.
Canalizaciones y espacios. Bandejas portacables. Recorridos. Criterios para ductos de datos y
energía. Cálculo del tamaño de ductos. EIA/TIA 606A: Administración y rotulación. El estándar
EIA/TIA 606A. EIA/TIA 607: Toma de tierra y anclaje. Necesidad de la puesta a tierra. Protección
de las personas y del equipamiento. Definición de una resistencia de tierra. Instalación de una
toma de tierra. Cálculo de resistencia. Jabalina vertical. EIA/TIA 942: Data Center. Cuarto de
Telecomunicaciones. Criterios de diseño. Introducción al Decibel. Definición. Ganancia.
Atenuación. Mediciones de cableado. Mapa de cableado. Longitud. Tiempo de propagación.
Diferencia de retardo. Atenuación. Pérdida de retorno. Near End Crosstalk (NEXT), paradiafonía
en el extremo cercano. FEXT paradiafonía en el extremo lejano. ACR (Atenuación Crostalk Ratio).
ELFEXT (Equal Level FEXT). Montaje de equipos: en laboratorio, en campo, pruebas parciales y
totales, mediciones, certificaciones según las normas técnicas vigentes. Carga inicial de
software: configuración, performance, licencias. Instalación, mantenimiento, configuración,
personalización y administración de redes informáticas. Instalación, mantenimiento,
configuración, personalización y administración de servidores de: correo, Web, ftp, bases de
datos, etc. Integración de Sistemas. Virtualización. Nuevos productos tecnológicos del área.
Análisis de costos. Presupuestos. Garantías."""

LAB_PROCESOS_INDUSTRIALES_6TO = """Laboratorio de Procesos Industriales — 6° año (Contenidos mínimos)
Introducción a la Arquitectura de microcontroladores. Diferencia entre microprocesador y
microcontrolador, modelo de Von Neuman y Modelo Harvard. Memoria de programa. Memoria de Datos.
Descripción de los registros del microcontrolador. Descripción de las líneas de entrada/salida,
entradas/salidas dedicadas. Líneas de interrupción. Pila, concepto de subrutina. Repertorio de
instrucciones del microcontrolador. Programación en lenguaje assembler, diagramas de flujo,
desarrollo de programas básicos en lenguaje assembler. Noción de programa Compilador, directivas
básicas, noción de utilización de programa Simulador, noción de programa Programador.

Noción de PLC. Utilización, características, entradas/salidas. Programación básica en lenguaje
Ladder, Elementos de la programación: variables, contactos, bobinas, words, bits del sistema,
flags sin retención, flags con retención, bloques operación, bloques comparación, bloque
temporizador (timer), bloque monoestable, bloque contador, bloque programador cíclico, bloque
PID, bloque encoder. Edición de un programa ladder: ubicación de símbolos gráficos, contactos,
bobinas, bloques timer, monoestables, etc., bloques operación y comparación. Edición de un
programa grafcet. Lenguaje ladder - procesamiento y limitaciones. Lenguaje grafcet -
procesamiento y limitaciones, interacción ladder/grafcet.

Programa Compilador, compilación de programas tipo para generar los archivos .hex., utilización
de programa Simulador para verificar su correcto funcionamiento, utilización de programa
Programador para transferir archivo .hex al circuito microcontrolador.

Utilización de programa EDITOR para carga de programa Ladder, compilación del mismo y
transmisión del programa al PLC. Utilización de programa Debug para observación y modificación
de las variables de programa.

Sensores varios (de presencia, lumínicos, de posición, de temperatura, de humedad, etc).
Actuadores (Motores paso a paso -PAP-, de Corriente continua y alterna CC y CA), Lámparas de
incandescencia, Leds, Timbres o alarmas, Buzzers, Relevadores, Electroimanes, Pulsadores,
Interruptores, etc.

Circuitos Integrados sencillos y económicos tales como Reguladores, divisores de frecuencia,
Bloques de compuertas, Drivers para Corriente continua, Diacs y Triacs, Diodos y Transistores
varios (de baja señal y de potencia). Optoacopladores."""

DESARROLLO_WEB_DINAMICAS_6TO = """Desarrollo de Aplicaciones Web Dinámicas — 6° año (Contenidos mínimos)
Introducción a los lenguajes de clientes. Definición de scripts. Programación de scripts.
Tratamiento, definición y tipos de variables. Operadores aritméticos, relacionales y lógicos.
Estructuras condicionales y de repetición. Objetos, funciones y métodos. Objetos y funciones
predefinidas. Los objetos del navegador. Formularios avanzados. Concepto de cookie. Las cookies
y los lenguajes de clientes. Lenguajes de servidor. Diferencias con lenguaje de cliente.
Introducción a los lenguajes que ejecutan en el servidor y generan contenidos dinámicos.
Declaración de variables, constantes y tipos de datos. Funciones básicas. Operadores
aritméticos, relacionales y lógicos. Estructuras condicionales. Estructuras de repetición.
Funciones de usuario, pasajes por valor y por referencia. Vectores y matrices. Manipulación de
cadenas de caracteres. Entorno MySQL. Transferencia de datos entre un lenguaje en el servidor y
MySQL. Creación de etiquetas y jerarquías. Métodos de convertir un protocolo estático (http) en
un sistema dinámico."""

PLATAFORMAS_MOVILES_7MO = """Proyecto de Desarrollo de Software para Plataformas Móviles — 7° año (Contenidos mínimos)
Conceptos básicos para crear una página web, siguiendo los estándares marcados por el W3C y
utilizando HTML y CSS. Se podrá utilizar como herramienta principal Dreamweaver u otra a
elección de cada escuela. Nociones básicas de los lenguajes de programación involucrados en la
creación de páginas web dinámicas: JavaScript, PHP y MySQL, abriendo así la posibilidad de crear
aplicaciones creativas en línea. Introduce también la programación para plataformas móviles. Se
aplicará la programación a la creación de formas audiovisuales generativas. Se estudiarán
diferentes algoritmos que, aplicados a Processing, producirán gráficos y sonidos producidos como
resultado de su ejecución. Se introducirán una serie de herramientas que se pueden instalar y
configurar fácil y rápidamente para crear aplicaciones web dinámicas de todo tipo: blogs, wikis y
más. Introducción a Web dinámica, haciendo prácticas de desarrollo sobre sus interfaces de
programación para crear nuevas aplicaciones."""

# ---------------------------------------------------------------------------
# Reglas de mapeo: nombre del curso real de Classroom (matcheo por
# keywords, insensible a mayúsculas) -> lista de (clave, texto) a guardar.
# El orden importa: se evalúa de arriba hacia abajo y se usa la primera
# regla cuyos keywords estén TODOS presentes en el nombre del curso.
# ---------------------------------------------------------------------------

REGLAS = [
    (("lab", "programacion", "4to"), [("Laboratorio de Programación 4º año", LAB_PROGRAMACION_4TO)]),
    (("lab", "programacion"), [
        ("Laboratorio de Programación 5º año", LAB_PROGRAMACION_5TO),
        ("Laboratorio de Programación 6º año", LAB_PROGRAMACION_6TO),
    ]),
    (("lab", "aplicaciones"), [("Laboratorio de Aplicaciones 4º año", LAB_APLICACIONES_4TO)]),
    (("procesos", "industriales"), [("Laboratorio de Procesos Industriales 6º año", LAB_PROCESOS_INDUSTRIALES_6TO)]),
    (("plat", "moviles"), [("Proyecto de Desarrollo de Software para Plataformas Móviles 7º año", PLATAFORMAS_MOVILES_7MO)]),
    (("lab", "hardware"), [
        ("Laboratorio de Hardware 4º año", LAB_HARDWARE_4TO),
        ("Laboratorio de Hardware 5º año", LAB_HARDWARE_5TO),
        ("Laboratorio de Hardware 6º año", LAB_HARDWARE_6TO),
    ]),
    (("aplicaciones", "web"), [("Desarrollo de Aplicaciones Web Dinámicas 6º año", DESARROLLO_WEB_DINAMICAS_6TO)]),
    (("sist", "operativos"), [
        ("Laboratorio de Sistemas Operativos 4º año", SIST_OPERATIVOS_4TO),
        ("Laboratorio de Sistemas Operativos 5º año", SIST_OPERATIVOS_5TO),
        ("Laboratorio de Sistemas Operativos 6º año", SIST_OPERATIVOS_6TO),
    ]),
    (("sistemas", "digitales", "5to"), [("Sistemas Digitales 5º año", SISTEMAS_DIGITALES_5TO)]),
    (("sistemas", "digitales"), [("Sistemas Digitales 6º año", SISTEMAS_DIGITALES_6TO)]),
    (("redes", "inf"), [("Instalación, Mantenimiento y Reparación de Redes Informáticas 7º año", REDES_INFORMATICAS_7MO)]),
]


def _normalizar(texto: str) -> str:
    reemplazos = str.maketrans("áéíóúñ", "aeioun")
    return texto.lower().translate(reemplazos)


def _matchear(nombre_curso: str):
    normalizado = _normalizar(nombre_curso)
    for keywords, entradas in REGLAS:
        if all(kw in normalizado for kw in keywords):
            return entradas
    return None


def cargar():
    memoria.init_db()
    creds = classroom.obtener_credenciales()
    service = build("classroom", "v1", credentials=creds)
    cursos = classroom.listar_materias_activas(service)
    if not cursos:
        print("No se encontraron materias activas en Classroom — nada para cargar.")
        return

    print(f"{len(cursos)} materia(s) activa(s) en Classroom:\n")
    cargadas, sin_match = [], []
    for curso in cursos:
        nombre = curso.get("name", "")
        entradas = _matchear(nombre)
        if not entradas:
            sin_match.append(nombre)
            continue
        for clave, texto in entradas:
            # idempotente: borra la entrada anterior con la misma clave/curso antes de reinsertar
            with memoria.conexion() as con:
                con.execute(
                    "DELETE FROM memoria WHERE tipo = 'diseno_curricular' AND curso = ? AND clave = ?",
                    (nombre, clave),
                )
            memoria.agregar_memoria("diseno_curricular", clave=clave, valor=texto, curso=nombre, agente=AGENTE)
        cargadas.append((nombre, [c for c, _ in entradas]))

    print("Cargado diseño curricular en:")
    for nombre, claves in cargadas:
        print(f"  ✅ {nombre}")
        for clave in claves:
            print(f"      - {clave}")
    if sin_match:
        print("\nSin diseño curricular disponible para (no matcheó ninguna regla):")
        for nombre in sin_match:
            print(f"  ⚪ {nombre}")


if __name__ == "__main__":
    cargar()
