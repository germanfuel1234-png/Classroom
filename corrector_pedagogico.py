import json
import datetime
import re
from googleapiclient.errors import HttpError


# ──────────────────────────────────────────────
#  AGENTE EXPERTO EN CORRECCIÓN PEDAGÓGICA
#  Y REDACCIÓN EMPÁTICA AVANZADA
# ──────────────────────────────────────────────

class CorrectorPedagogico:
    """
    Procesa datos crudos de corrección y genera reportes JSON estructurados
    con redacciones personalizadas, empáticas y contextualmente informadas.
    
    Utiliza criterios de exigencia y matriz de tono para adaptar cada devolución.
    """
    
    def __init__(self, materia, tp):
        """
        Inicializa el corrector con los datos de contexto.
        
        Args:
            materia (str): Nombre de la materia
            tp (str): Nombre del TP / Actividad
        """
        self.materia = materia
        self.tp = tp
        self.contexto_deducido = self._inferir_contexto_desde_tp(tp)
        self.fecha_correccion = datetime.datetime.now().strftime("%Y-%m-%d")
        self.reporte_entregas = []

    def _inferir_contexto_desde_tp(self, tp):
        """Deduce objetivos técnicos esperados a partir del nombre del TP."""
        tp_lower = (tp or "").lower()

        reglas = [
            (["interfaz", "gui", "ux", "ui", "ventana", "eventos"],
             "se evalúa diseño de interfaz, experiencia de usuario, interacción de componentes y manejo de eventos"),
            (["base de datos", "sql", "mysql", "postgres", "crud"],
             "se evalúa modelado de datos, consultas SQL, integridad y operaciones CRUD"),
            (["poo", "objetos", "clases", "herencia", "polimorfismo"],
             "se evalúa uso correcto de clases, encapsulamiento, herencia y modularidad del código"),
            (["api", "rest", "http", "endpoint", "json"],
             "se evalúa consumo y diseño de servicios, manejo de requests/responses y estructura de datos JSON"),
            (["red", "network", "tcp", "ip", "router"],
             "se evalúa comprensión de protocolos, direccionamiento, conectividad y diagnóstico de red"),
            (["sistema operativo", "procesos", "hilos", "memoria", "planificación"],
             "se evalúa gestión de procesos, memoria, concurrencia y conceptos de planificación del sistema"),
            (["hardware", "microcontrolador", "arduino", "circuito", "electrónica"],
             "se evalúa integración hardware-software, lectura de componentes y validación técnica del montaje"),
            (["web", "frontend", "backend", "html", "css", "javascript"],
             "se evalúa estructura de aplicación web, lógica de interacción y buenas prácticas de desarrollo"),
        ]

        for claves, contexto in reglas:
            if any(clave in tp_lower for clave in claves):
                return contexto

        return "se evalúa dominio conceptual del tema, calidad técnica de la resolución y fundamentación de decisiones"
    
    def clasificar_entrega(self, nombre_alumno, feedback_docente):
        """
        Clasifica una entrega según el feedback del docente.
        Retorna un diccionario con los campos del reporte.
        
        Args:
            nombre_alumno (str): Nombre y apellido del alumno
            feedback_docente (str): Feedback crudo del docente
            
        Returns:
            dict: Diccionario con campos estado_interno, nota, motivo_correccion, devolucion_alumno
        """
        feedback_lower = feedback_docente.lower()
        
        # CASO C: Detectar Adeuda Entrega (no entregó)
        if any(palabra in feedback_lower for palabra in ["no entregó", "adeuda", "no entrega", "falta entrega", "sin entregar"]):
            return self._generar_adeuda_entrega(nombre_alumno)
        
        # CASO B: Detectar Reentrega Técnica (hojas en blanco, archivo dañado, no legible)
        if any(palabra in feedback_lower for palabra in ["hojas en blanco", "en blanco", "no legible", "archivo dañado", "corrupto", "no se puede leer", "páginas en blanco", "archivo vacío", "vacío", "no corresponde", "página en blanco"]):
            return self._generar_reentrega_tecnica(nombre_alumno)
        
        # CASO A: Detectar Entrega Válida (buscar nota numérica)
        nota = self._extraer_nota(feedback_docente)
        if nota is not None:
            return self._generar_aprobado(nombre_alumno, nota, feedback_docente)
        
        # CASO A: Si hay feedback positivo pero sin nota numérica explícita, usar 7 (aprobado por defecto)
        if any(palabra in feedback_lower for palabra in ["excelente", "muy bien", "perfecto", "bien", "correcto", "aprobado", "aprueba"]):
            # Determinar nota según intensidad del feedback
            if any(palabra in feedback_lower for palabra in ["excelente", "perfecto", "muy bien"]):
                nota = 9
            elif any(palabra in feedback_lower for palabra in ["bien", "correcto"]):
                nota = 8
            else:
                nota = 7
            return self._generar_aprobado(nombre_alumno, nota, feedback_docente)
        
        # Por defecto, si no se puede clasificar, requiere revisión/reentrega técnica.
        return self._generar_reentrega_tecnica(nombre_alumno)
    
    def _extraer_nota(self, texto):
        """
        Extrae una nota numérica del texto (busca patrones como '8/10', 'nota 8', etc).
        
        Args:
            texto (str): Texto con posible nota
            
        Returns:
            int or None: Nota extraída (1-10) o None si no encuentra
        """
        # Patrones: "nota 8", "8/10", "calificación: 8", etc
        patrones = [
            r'nota\s+(\d+)',
            r'(\d+)\s*/\s*10',
            r'calificación\s*:\s*(\d+)',
            r'nota\s*:\s*(\d+)',
            r'=\s*(\d+)',
        ]
        
        for patron in patrones:
            match = re.search(patron, texto.lower())
            if match:
                nota = int(match.group(1))
                if 1 <= nota <= 10:
                    return nota
        
        return None
    
    def _extraer_primer_nombre(self, nombre_completo):
        """
        Extrae el primer nombre de un nombre completo.
        
        Args:
            nombre_completo (str): Nombre completo del alumno
            
        Returns:
            str: Primer nombre del alumno
        """
        partes = nombre_completo.strip().split()
        return partes[0] if partes else "Estimado/a"
    
    def _determinar_tono(self, nota):
        """
        Determina el tono y contexto de redacción según la nota.
        
        Args:
            nota (int): Calificación numérica (1-10)
            
        Returns:
            dict: Diccionario con características de tono
        """
        if nota >= 9:
            return {
                "categoria": "excelente",
                "nivel_motivacion": "alto",
                "enfoque": "reconocimiento_profundidad",
                "desafio": True
            }
        elif nota >= 7:
            return {
                "categoria": "regular",
                "nivel_motivacion": "medio",
                "enfoque": "equilibrio_constructivo",
                "desafio": False
            }
        else:
            return {
                "categoria": "alerta",
                "nivel_motivacion": "apoyo",
                "enfoque": "reflexion_guiada",
                "desafio": False
            }
    
    def _redactar_devolucion_aprobado(self, nombre_alumno, nota, feedback_docente):
        """
        Redacta una devolución pedagógica personalizada sin plantillas.
        Se adapta según el tono, nota y criterios de exigencia.
        
        Args:
            nombre_alumno (str): Nombre del alumno
            nota (int): Calificación
            feedback_docente (str): Feedback original del docente
            
        Returns:
            str: Devolución redactada de forma fluida y contextual
        """
        primer_nombre = self._extraer_primer_nombre(nombre_alumno)
        tono = self._determinar_tono(nota)
        
        # Extraer elementos del feedback para redacción nativa
        fortalezas = self._extraer_fortalezas(feedback_docente)
        debilidades = self._extraer_debilidades(feedback_docente)
        observaciones = self._extraer_observaciones(feedback_docente)
        
        # Construir devolución según tono
        if tono["categoria"] == "excelente":
            return self._redactar_tono_excelente(
                primer_nombre, nota, fortalezas, debilidades, observaciones
            )
        elif tono["categoria"] == "regular":
            return self._redactar_tono_regular(
                primer_nombre, nota, fortalezas, debilidades, observaciones
            )
        else:  # alerta
            return self._redactar_tono_alerta(
                primer_nombre, nota, fortalezas, debilidades, observaciones
            )
    
    def _redactar_tono_excelente(self, primer_nombre, nota, fortalezas, debilidades, observaciones):
        """
        Redacta en tono de alta motivación y reconocimiento profundo.
        """
        redaccion = f"Estimado/a {primer_nombre},\n\n"
        redaccion += "He revisado tu entrega y quiero felicitarte genuinamente por el excelente trabajo realizado. "
        
        # Incluir fortalezas específicas
        if fortalezas:
            redaccion += f"Destaca el hecho de que {fortalezas[0].lower()}"
            if len(fortalezas) > 1:
                redaccion += f" y, además, {fortalezas[1].lower()}"
            redaccion += ". "
        else:
            redaccion += "Has demostrado un dominio integral de los conceptos solicitados. "
        
        redaccion += f"Además, en esta actividad {self.contexto_deducido}. Esta es la clase de entrega que refleja compromiso y profundidad de comprensión.\n\n"
        
        # Si hay debilidades menores, mencionarlas
        if debilidades:
            redaccion += f"Como único detalle menor para seguir afinando tu desempeño, considera: {debilidades[0].lower()}. "
            redaccion += "No afecta el resultado final, pero es valioso tenerlo en cuenta en futuros trabajos.\n\n"
        
        redaccion += "Te desafío a mantener este ritmo y a seguir profundizando en los temas más complejos. "
        redaccion += f"Tu dedicación es un ejemplo para tus compañeros.\n\n"
        redaccion += f"Calificación: {nota}/10."
        
        return redaccion
    
    def _redactar_tono_regular(self, primer_nombre, nota, fortalezas, debilidades, observaciones):
        """
        Redacta en tono constructivo equilibrado, con explicación pedagógica.
        """
        redaccion = f"Estimado/a {primer_nombre},\n\n"
        redaccion += "He revisado tu trabajo y puedo confirmar que has cumplido satisfactoriamente con la entrega. "
        redaccion += f"En este TP {self.contexto_deducido}. "
        
        # Fortalezas
        if fortalezas:
            redaccion += f"Los puntos fuertes de tu trabajo son: {fortalezas[0].lower()}"
            if len(fortalezas) > 1:
                redaccion += f" y {fortalezas[1].lower()}"
            redaccion += ". Estos elementos demuestran que comprendiste bien la materia.\n\n"
        else:
            redaccion += "Has abordado adecuadamente los conceptos principales.\n\n"
        
        # Debilidades y recomendaciones pedagógicas
        if debilidades:
            redaccion += f"Para que el próximo trabajo sea aún más sólido, te recomiendo: {debilidades[0].lower()}. "
            if len(debilidades) > 1:
                redaccion += f"Además, es importante que profundices en {debilidades[1].lower()}. "
            redaccion += "Estos puntos son fundamentales para consolidar tu aprendizaje.\n\n"
        else:
            redaccion += "Mantén esta consistencia en tus futuras entregas.\n\n"
        
        redaccion += "Continúa con el trabajo que has venido haciendo; estamos en buen camino.\n\n"
        redaccion += f"Calificación: {nota}/10."
        
        return redaccion
    
    def _redactar_tono_alerta(self, primer_nombre, nota, fortalezas, debilidades, observaciones):
        """
        Redacta en tono asertivo pero de apoyo, invitando a la reflexión.
        """
        redaccion = f"Estimado/a {primer_nombre},\n\n"
        redaccion += "He revisado tu trabajo y te propongo reflexionar sobre los siguientes puntos. "
        
        # Áreas débiles
        if debilidades:
            redaccion += f"Se evidencia que requiere mayor atención: {debilidades[0].lower()}"
            if len(debilidades) > 1:
                redaccion += f" y {debilidades[1].lower()}"
            redaccion += ". "
        else:
            redaccion += "Hay aspectos que necesitan revisión. "
        
        redaccion += f"Esto impactó directamente en la calificación final, especialmente porque en esta actividad {self.contexto_deducido}.\n\n"
        
        # Ruta de mejora
        redaccion += "Te propongo un plan de acción para las próximas entregas:\n"
        redaccion += "1. Revisa cuidadosamente los criterios de la actividad antes de comenzar.\n"
        redaccion += "2. Profundiza en los conceptos que resultaron débiles en este trabajo.\n"
        redaccion += "3. Consulta con docentes o compañeros si algo no queda claro.\n\n"
        
        # Apoyo institucional
        redaccion += "Queremos apoyarte para que mejores tu desempeño. No dudes en acercarte si necesitas orientación. "
        redaccion += "La regularidad de la materia es importante para tu desarrollo académico.\n\n"
        redaccion += f"Calificación: {nota}/10."
        
        return redaccion
    
    def _extraer_fortalezas(self, texto):
        """
        Extrae fortalezas mencionadas en el feedback.
        """
        palabras_clave = {
            "bien": "resolvió bien",
            "excelente": "demostró excelencia",
            "correcto": "respondió correctamente",
            "claro": "fue claro en la exposición",
            "ordenado": "organizó de manera ordenada",
            "completo": "completó adecuadamente",
            "estructurado": "estructuró correctamente",
            "justificado": "justificó sus respuestas",
            "profundo": "profundizó en el tema",
            "detallado": "fue detallado en el análisis"
        }
        
        fortalezas = []
        for palabra, descripcion in palabras_clave.items():
            if palabra in texto.lower():
                fortalezas.append(descripcion)
        
        return fortalezas[:2]  # Máximo 2 fortalezas
    
    def _extraer_debilidades(self, texto):
        """
        Extrae debilidades mencionadas en el feedback.
        """
        palabras_clave = {
            "falta": "faltó profundizar",
            "dejó por la mitad": "dejó incompleto",
            "incompleto": "no completó todo",
            "no profundizó": "no profundizó en los detalles",
            "variable global": "revisar el alcance de las variables",
            "error": "revisar los errores cometidos",
            "mejorar": "optimizar el enfoque",
            "superficial": "necesita mayor profundidad",
            "confuso": "clarificar los conceptos",
            "no se entiende": "revisar la presentación"
        }
        
        debilidades = []
        for palabra, descripcion in palabras_clave.items():
            if palabra in texto.lower():
                debilidades.append(descripcion)
        
        return debilidades[:2]  # Máximo 2 debilidades
    
    def _extraer_observaciones(self, texto):
        """
        Extrae observaciones técnicas específicas.
        """
        # Buscar detalles técnicos específicos
        return texto
    
    def _generar_aprobado(self, nombre_alumno, nota, feedback_docente):
        """
        Genera entrada de entrega válida (aprobada o desaprobada).
        """
        estado = "Aprobado" if nota >= 7 else "Desaprobado"
        
        # Redactar devolución contextual
        devolucion = self._redactar_devolucion_aprobado(nombre_alumno, nota, feedback_docente)
        
        # Generar motivo técnico conciso
        motivo = self._generar_motivo_tecnico(nota, feedback_docente)
        
        return {
            "alumno": nombre_alumno,
            "estado_interno": estado,
            "nota": nota,
            "motivo_correccion": motivo,
            "devolucion_alumno": devolucion
        }
    
    def _generar_motivo_tecnico(self, nota, feedback_docente):
        """
        Genera un resumen técnico conciso de la corrección.
        """
        estado = "aprobación" if nota >= 7 else "desaprobación"
        resumen_feedback = feedback_docente[:120] + ("..." if len(feedback_docente) > 120 else "")
        return f"{estado} por desempeño técnico en TP donde {self.contexto_deducido}; observación docente: {resumen_feedback}"
    
    def _generar_reentrega_tecnica(self, nombre_alumno):
        """
        Genera entrada de reentrega técnica (archivo dañado, en blanco, etc).
        """
        primer_nombre = self._extraer_primer_nombre(nombre_alumno)
        
        devolucion = (
            f"Estimado/a {primer_nombre}: Al proceder a la corrección de tu entrega para la actividad "
            f"'{self.tp}', hemos detectado que el documento presenta páginas en blanco o no es legible de manera "
            f"completa. Para poder asignarte la calificación correspondiente, te solicito que vuelvas a subir el "
            f"archivo corregido a la brevedad. Asegúrate de que el archivo se descarga correctamente antes de confirmar la entrega."
        )
        
        return {
            "alumno": nombre_alumno,
            "estado_interno": "Reentrega Técnica",
            "nota": None,
            "motivo_correccion": "Archivo con hojas en blanco o no legible",
            "devolucion_alumno": devolucion
        }
    
    def _generar_adeuda_entrega(self, nombre_alumno):
        """
        Genera entrada de alumno que adeuda entrega.
        """
        primer_nombre = self._extraer_primer_nombre(nombre_alumno)
        
        devolucion = (
            f"Estimado/a {primer_nombre}: Según el registro actual de Classroom, no figura una entrega adjunta "
            f"válida para la actividad '{self.tp}'. Te solicito revisar tu envío y, si corresponde, volver a "
            f"adjuntar el archivo para poder corregirlo correctamente."
        )
        
        return {
            "alumno": nombre_alumno,
            "estado_interno": "Adeuda Entrega",
            "nota": None,
            "motivo_correccion": "Alumno no entregó la actividad",
            "devolucion_alumno": devolucion
        }
    
    def procesar_lote(self, lista_alumnos):
        """
        Procesa un lote de alumnos con sus respectivos feedbacks.
        
        Args:
            lista_alumnos (list): Lista de tuplas (nombre_alumno, feedback_docente)
        """
        for nombre_alumno, feedback_docente in lista_alumnos:
            entrada = self.clasificar_entrega(nombre_alumno, feedback_docente)
            self.reporte_entregas.append(entrada)
    
    def generar_json(self):
        """
        Genera el JSON estructurado final con todos los datos procesados.
        
        Returns:
            str: JSON válido con indentación
        """
        reporte_dict = {
            "materia": self.materia,
            "tp": self.tp,
            "fecha_correccion": self.fecha_correccion,
            "reporte_entregas": self.reporte_entregas
        }
        
        return json.dumps(reporte_dict, ensure_ascii=False, indent=2)
    
    def generar_json_compacto(self):
        """
        Genera el JSON sin espacios ni saltos (versión compacta).
        """
        reporte_dict = {
            "materia": self.materia,
            "tp": self.tp,
            "fecha_correccion": self.fecha_correccion,
            "reporte_entregas": self.reporte_entregas
        }
        
        return json.dumps(reporte_dict, ensure_ascii=False, separators=(',', ':'))


def procesar_correccion(materia, tp, datos_crudos):
    """
    Función utilitaria para procesar correcciones de forma simple.
    
    Args:
        materia (str): Nombre de la materia
        tp (str): Nombre del TP/Actividad
        datos_crudos (str): String con datos en formato "Nombre: feedback\nNombre2: feedback2"
    Returns:
        str: JSON estructurado generado
    """
    corrector = CorrectorPedagogico(materia, tp)
    
    # Parsear datos crudos
    lineas = datos_crudos.strip().split('\n')
    lista_alumnos = []
    
    for linea in lineas:
        if ':' in linea:
            nombre, feedback = linea.split(':', 1)
            lista_alumnos.append((nombre.strip(), feedback.strip()))
    
    corrector.procesar_lote(lista_alumnos)
    return corrector.generar_json()


def calificar_y_comentar_alumno(service, course_id, course_work_id, student_id, nota, comentario_texto):
    """
    Actualiza la calificación en borrador (draftGrade) de una entrega y crea
    un comentario privado en la studentSubmission del alumno.

    Parámetros:
        service: Cliente autenticado de Google Classroom API.
        course_id (str): ID del curso.
        course_work_id (str): ID de la actividad/TP.
        student_id (str): ID del alumno (userId de Classroom).
        nota (int | float | None): Nota interna en escala 1-10. Si es None, no se actualiza nota.
        comentario_texto (str): Devolución a enviar como comentario privado.

    Retorna:
        dict: Resultado de operación con estado, IDs y errores si aplica.
    """
    try:
        # 1) Buscar la entrega del alumno para obtener submission_id.
        submissions_resp = (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .list(
                courseId=course_id,
                courseWorkId=course_work_id,
                userId=student_id,
                pageSize=1,
            )
            .execute()
        )

        submissions = submissions_resp.get("studentSubmissions", [])
        if not submissions:
            return {
                "ok": False,
                "student_id": student_id,
                "mensaje": "No se encontró entrega para el alumno en la actividad.",
            }

        submission_id = submissions[0].get("id")

        # 2) Actualizar draftGrade si hay nota (escala 1-10 -> 0-100).
        draft_grade_100 = None
        grade_updated = False
        if nota is not None:
            draft_grade_100 = max(0.0, min(float(nota) * 10.0, 100.0))

            (
                service.courses()
                .courseWork()
                .studentSubmissions()
                .patch(
                    courseId=course_id,
                    courseWorkId=course_work_id,
                    id=submission_id,
                    updateMask="draftGrade",
                    body={"draftGrade": draft_grade_100},
                )
                .execute()
            )
            grade_updated = True

        # 3) Crear comentario privado usando el recurso Comments.
        comment_updated = False
        comment_error = None
        if comentario_texto and comentario_texto.strip():
            try:
                (
                    service.courses()
                    .courseWork()
                    .studentSubmissions()
                    .comments()
                    .create(
                        courseId=course_id,
                        courseWorkId=course_work_id,
                        submissionId=submission_id,
                        body={"text": comentario_texto.strip()},
                    )
                    .execute()
                )
                comment_updated = True
            except HttpError as e:
                # No romper todo el flujo si falla solo el comentario.
                comment_error = str(e)

        return {
            "ok": True,
            "student_id": student_id,
            "submission_id": submission_id,
            "draft_grade_100": draft_grade_100,
            "grade_updated": grade_updated,
            "comment_updated": comment_updated,
            "comment_error": comment_error,
        }

    except HttpError as e:
        return {
            "ok": False,
            "student_id": student_id,
            "mensaje": "Error de API al calificar/comentar la entrega.",
            "error": str(e),
        }


if __name__ == "__main__":
    # Ejemplo de uso
    print("Módulo corrector_pedagogico.py cargado correctamente.")
