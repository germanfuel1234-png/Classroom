"""
🚀 MEJORADOR AUTOMÁTICO DE CONSIGNAS CRÍTICAS
Reemplaza consignas MUY CORTAS con versiones mejoradas
"""

import os
import json
from pathlib import Path


# Mejoras propuestas para cada consigna muy corta
MEJORAS = {
    r"Lab Hardware\Actividad 5.1(Chipset Norte Sur)": """╔════════════════════════════════════════════════════════════╗
║  ACTIVIDAD: Análisis de Chipset Norte y Sur
╚════════════════════════════════════════════════════════════╝

OBJETIVO:
Comprender la arquitectura y funciones del chipset en placas madre modernas,
identificando las diferencias entre el controlador norte (Northbridge) y sur
(Southbridge).

TAREAS OBLIGATORIAS:
1. Investigar la diferencia entre Northbridge y Southbridge
   - Funciones principales de cada uno
   - Componentes que controlan
   - Velocidades de comunicación

2. Explicar la comunicación entre componentes
   - Cómo se comunican CPU, RAM y periféricos
   - Función del bus del sistema
   - Rol del Front Side Bus (FSB)

3. Comparar al menos 2 modelos diferentes de chipsets
   - Intel vs AMD (generaciones similares)
   - Especificaciones técnicas
   - Ventajas y desventajas

4. Crear un diagrama esquemático
   - Mostrar posición de Northbridge y Southbridge
   - Indicar componentes conectados
   - Señalar buses principales

CRITERIOS DE EVALUACIÓN:
✓ Contenido: Mínimo 800 palabras, responde todos los puntos
✓ Precisión: Definiciones técnicas correctas y actualizadas
✓ Claridad: Explicación comprensible para estudiantes
✓ Diagrama: Esquema clara y bien identificado
✓ Fuentes: Cita al menos 2 fuentes confiables

FORMATO ENTREGA:
- PDF o DOCX
- Márgenes 2.5cm
- Fuente: Arial 11pt, interlineado 1.5
- Portada con nombre y materia
- Incluir índice si es más de 3 páginas

Plazo: Según especificación en Classroom""",

    r"Desarrollo de aplicaciones web (dinamicas)\Actividad Numero 8 PHP-HTML": """╔════════════════════════════════════════════════════════════╗
║  ACTIVIDAD: Aplicación Web Dinámica con PHP
╚════════════════════════════════════════════════════════════╝

OBJETIVO:
Crear una aplicación web funcional que integre HTML, CSS y PHP para gestionar
datos de manera dinámica.

REQUISITOS TÉCNICOS:
1. Interfaz de usuario (HTML + CSS)
   - Formulario funcional con validación cliente
   - Diseño responsivo (mobile-friendly)
   - Menú de navegación clara

2. Backend en PHP
   - Procesar datos del formulario (POST)
   - Conexión a base de datos SQLite/MySQL
   - Al menos 3 operaciones CRUD (CREATE, READ, UPDATE)

3. Almacenamiento de datos
   - Tabla con al menos 5 campos
   - Validación de datos en backend
   - Manejo de errores

4. Seguridad básica
   - Validar entrada de datos (evitar SQL injection)
   - Escapar salida HTML (XSS protection)
   - Usar prepared statements

ESTRUCTURA ESPERADA:
- index.php → página principal
- formulario.php → procesa datos
- listar.php → muestra registro
- editar.php → modifica datos
- eliminar.php → borra datos
- estilos.css → diseño

ENTREGA:
- Archivo .zip con toda la estructura
- README.md con instrucciones de instalación
- Script SQL para crear base de datos

CRITERIOS DE EVALUACIÓN:
✓ Funcionalidad: Todas las operaciones funcionan correctamente
✓ Código: Limpio, comentado, bien organizado
✓ Diseño: Interfaz intuitiva y atractiva
✓ Seguridad: Implementa validaciones y protecciones
✓ Documentación: README claro con ejemplos de uso""",

    r"Lab. Programacion  2026\Actividad Numero 2(Mensaje en pantalla,expresion logica)": """╔════════════════════════════════════════════════════════════╗
║  ACTIVIDAD: Expresiones Lógicas en Python
╚════════════════════════════════════════════════════════════╝

OBJETIVO:
Practicar la creación y evaluación de expresiones lógicas en Python, usando
operadores booleanos (and, or, not) y condicionales.

TAREAS:
1. Crear un programa que solicite dos números enteros
   - Mostrar mensaje introductorio
   - Validar que sean números válidos

2. Implementar expresiones lógicas para:
   - Verificar si ambos números son positivos
   - Verificar si al menos uno es par
   - Verificar si están en rango 1-100
   - Verificar si uno es divisible por el otro

3. Mostrar resultados con mensajes claros
   - "Ambos son positivos: Si/No"
   - "Al menos uno es par: Si/No"
   - etc.

4. Usar estructuras de control (if/else)
   - No usar solo print, combinar con condicionales
   - Manejar casos especiales (número 0, negativos)

EJEMPLO DE SALIDA:
```
Ingrese primer número: 15
Ingrese segundo número: 24

═══ ANÁLISIS LÓGICO ═══
¿Ambos positivos? Sí ✓
¿Ambos pares? No ✗
¿Suma > 30? Sí ✓
¿Primero divisible por segundo? No ✗
```

ENTREGA:
- Archivo .py con nombre: actividad_logica_[NOMBRE].py
- Mínimo 50 líneas de código
- Comentarios explicativos en puntos clave

CRITERIOS:
✓ Corrección: Expresiones lógicas evaluadas correctamente
✓ Validación: Maneja entradas inválidas sin error
✓ Claridad: Mensajes comprensibles para usuario
✓ Estructura: Código organizado con funciones auxiliares
✓ Pruebas: Probado con al menos 5 casos diferentes""",

    r"Sist. Operativos\Trabajo Practico N° 1.3": """╔════════════════════════════════════════════════════════════╗
║  TRABAJO PRÁCTICO: Gestión de Procesos en Sistemas Operativos
╚════════════════════════════════════════════════════════════╝

OBJETIVO:
Comprender cómo el sistema operativo gestiona procesos, threads, prioridades
y recursos del sistema.

CONTENIDO REQUERIDO:
1. Concepto de Proceso vs Thread
   - Definición clara de cada uno
   - Diferencias fundamentales
   - Ejemplos prácticos del SO actual

2. Estados de un Proceso
   - Nuevo, Listo, Ejecutándose, Bloqueado, Terminado
   - Diagrama de transiciones
   - Cuándo ocurre cada cambio

3. Planificación de Procesos
   - Algoritmos: FIFO, Round Robin, Prioridades
   - Ventajas y desventajas de cada uno
   - Caso de uso real

4. Deadlock (Interbloqueo)
   - Condiciones necesarias
   - Ejemplo de deadlock en sistema real
   - Estrategias de prevención

5. Experiencia práctica
   - Captura de pantalla de Task Manager/Monitor del sistema
   - Analizar procesos en ejecución
   - Cambiar prioridades de un proceso
   - Incluir explicación de lo observado

FORMATO:
- Documento PDF o DOCX
- Mínimo 2000 palabras
- Incluir diagramas
- Mínimo 3 capturas de pantalla anotadas
- Referencias bibliográficas

CRITERIOS DE EVALUACIÓN:
✓ Completitud: Responde todas las preguntas
✓ Profundidad: Análisis detallado de cada tema
✓ Claridad: Explicación comprensible
✓ Diagramas: Esquemas claros y bien rotulados
✓ Evidencia: Capturas reales del sistema
✓ Referencias: Cita autores y fuentes""",

    r"Procesos Industriales\Actividad Numero 5(Cadesimu)": """╔════════════════════════════════════════════════════════════╗
║  ACTIVIDAD: Simulación de Procesos Industriales (CADESIMU)
╚════════════════════════════════════════════════════════════╝

OBJETIVO:
Utilizar el software CADESIMU para simular y analizar un proceso industrial,
identificando puntos críticos y propuestas de mejora.

ACTIVIDADES REQUERIDAS:
1. Seleccionar un proceso industrial
   - Producción (ejemplo: fabricación textil, ensamblaje)
   - Línea de montaje
   - Procesamiento de materia prima

2. Crear el modelo en CADESIMU
   - Definir recursos (máquinas, operarios, espacio)
   - Establecer secuencia de procesos
   - Configurar tiempos de operación

3. Realizar simulación
   - Ejecutar mínimo 10 ciclos productivos
   - Registrar datos de eficiencia
   - Tomar capturas del software en ejecución

4. Análisis de resultados
   - Tasa de producción actual
   - Cuellos de botella identificados
   - Tiempo de ciclo promedio
   - Utilización de recursos (%)

5. Propuesta de mejora
   - Modificar parámetros (recursos, tiempos)
   - Simular nueva configuración
   - Comparar resultados antes/después
   - Justificar mejora propuesta

ENTREGA:
- Archivo CADESIMU (.sim o .cadesimu)
- Reporte PDF con:
  * Descripción del proceso
  * 5+ capturas del software
  * Tabla comparativa de resultados
  * Gráficos de eficiencia
  * Conclusiones

CRITERIOS:
✓ Complejidad: Modelo con mínimo 4 procesos
✓ Funcionamiento: Simulación sin errores
✓ Análisis: Identificación clara de problemas
✓ Mejora: Propuesta justificada y cuantificada
✓ Documentación: Reporte completo y claro""",
}


def mejorar_consignas():
    """Reemplaza consignas muy cortas con versiones mejoradas."""
    
    print("\n" + "="*70)
    print("  🚀 MEJORADOR AUTOMÁTICO DE CONSIGNAS")
    print("="*70 + "\n")
    
    ruta_base = "Correcciones_Classroom"
    mejoradas = 0
    errores = 0
    
    # Cargar diagnóstico
    try:
        with open(os.path.join(ruta_base, "DIAGNOSTICO_CONSIGNAS.json"), 'r', encoding='utf-8') as f:
            diagnostico = json.load(f)
    except:
        print("❌ No encontré DIAGNOSTICO_CONSIGNAS.json")
        print("Ejecuta primero: python diagnosticar_consignas.py")
        return
    
    # Procesar cada mejora propuesta
    for clave, contenido_nuevo in MEJORAS.items():
        # Normalizar clave (reemplazar barras)
        clave_normalizada = clave.replace("\\", os.sep)
        ruta_consigna = os.path.join(ruta_base, clave_normalizada, "consigna_referencia.txt")
        
        # Intentar variantes de mayúscula
        if not os.path.exists(ruta_consigna):
            ruta_consigna = os.path.join(ruta_base, clave_normalizada, "CONSIGNA_REFERENCIA.txt")
        
        if os.path.exists(ruta_consigna):
            try:
                # Leer archivo actual
                with open(ruta_consigna, 'r', encoding='utf-8') as f:
                    contenido_actual = f.read()
                
                tam_actual = len(contenido_actual.encode('utf-8'))
                
                # Si está muy corta, reemplazar
                if tam_actual < 100:
                    with open(ruta_consigna, 'w', encoding='utf-8') as f:
                        f.write(contenido_nuevo)
                    
                    print(f"✅ MEJORADA: {clave}")
                    print(f"   Antes: {tam_actual} bytes → Después: {len(contenido_nuevo.encode('utf-8'))} bytes\n")
                    mejoradas += 1
                else:
                    print(f"⏭️  SALTADA: {clave} (ya tiene {tam_actual} bytes)\n")
            
            except Exception as e:
                print(f"❌ ERROR en {clave}: {e}\n")
                errores += 1
        else:
            print(f"⚠️  NO ENCONTRADA: {clave}\n")
    
    # Resumen
    print("="*70)
    print(f"📊 RESUMEN: {mejoradas} consignas mejoradas, {errores} errores")
    print("="*70)
    print(f"\n✅ Ahora ejecuta: python main.py → Opción [6]")
    print("   Las evaluaciones serán MÁS PRECISAS 📈\n")


if __name__ == "__main__":
    mejorar_consignas()
