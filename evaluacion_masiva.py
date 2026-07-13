"""
EVALUADOR EXPERTO EN CORRECCIÓN PEDAGÓGICA MASIVA
Genera evaluaciones en JSON siguiendo criterios estrictos de comparación
entre entregas de estudiantes y consigna del docente.
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path
from docx import Document


class EvaluadorMasivo:
    """
    Procesa entregas de estudiantes, compara con consigna
    y genera evaluaciones pedagógicas en formato JSON.
    """
    
    def __init__(self, ruta_base="Correcciones_Classroom/probando"):
        """
        Inicializa el evaluador.
        
        Args:
            ruta_base (str): Ruta base donde están organizadas las entregas
        """
        self.ruta_base = ruta_base
        self.evaluaciones = []
        
    def leer_consigna(self, ruta_consigna):
        """Lee la consigna de referencia."""
        if os.path.exists(ruta_consigna):
            with open(ruta_consigna, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def leer_entrega_docx(self, ruta_docx):
        """Extrae texto de un archivo .docx"""
        try:
            doc = Document(ruta_docx)
            texto = "\n".join([parrafo.text for parrafo in doc.paragraphs])
            return texto.strip()
        except Exception as e:
            return f"[Error al leer archivo: {str(e)}]"
    
    def leer_informe_json(self, ruta_informe):
        """Lee el informe técnico pedagógico en JSON"""
        if os.path.exists(ruta_informe):
            try:
                with open(ruta_informe, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def analizar_entrega(self, nombre_alumno, consigna, entrega_texto, informe_json):
        """
        Analiza una entrega comparándola con la consigna.
        
        Args:
            nombre_alumno (str): Nombre del alumno
            consigna (str): Texto de la consigna
            entrega_texto (str): Texto de la entrega
            informe_json (dict): Informe técnico previo
            
        Returns:
            dict: Evaluación con criterios pedagógicos
        """
        
        # Criterios de evaluación basados en la consigna
        criterios = self._extraer_criterios_consigna(consigna)
        
        # Determinar si hay contenido evaluable
        if "[Error" in entrega_texto or "no legible" in entrega_texto.lower():
            nota = 2
            descripcion = "Entrega con problema técnico: archivo no legible o no procesable."
            comentario = (
                "He revisado tu entrega, pero el archivo no puede procesarse (posible PDF escaneado o imagen). "
                "Por favor, re-entrega tu trabajo en formato digital editable (Word .docx, Google Docs o .txt) "
                "para que pueda evaluarse correctamente."
            )
        elif not entrega_texto.strip() or len(entrega_texto) < 50:
            nota = 1
            descripcion = "Entrega vacía o incompleta."
            comentario = (
                "Tu entrega está vacía o es demasiado breve. No hay contenido para evaluar. "
                "Por favor, completa el trabajo según los requisitos de la consigna."
            )
        else:
            # Evaluar cumplimiento de criterios
            nota, cumplimiento = self._evaluar_cumplimiento(entrega_texto, criterios)
            descripcion = self._generar_descripcion(cumplimiento, criterios)
            comentario = self._generar_comentario_pedagogico(cumplimiento, criterios, nombre_alumno)
        
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": informe_json.get("trabajo_practico", "Actividad 1") if informe_json else "Actividad 1",
            "nota": nota,
            "descripcion": descripcion,
            "comentario_privado": comentario
        }
    
    def _extraer_criterios_consigna(self, consigna):
        """Extrae los criterios clave de la consigna."""
        criterios = {
            "infografia": "infografía" in consigna.lower(),
            "justificacion": "justificad" in consigna.lower() or "expliq" in consigna.lower(),
            "temas_especificos": any(tema in consigna.lower() for tema in ["electrónica", "circuitos", "digital"]),
            "herramienta": "herramienta" in consigna.lower() or "plataforma" in consigna.lower(),
            "presentacion": "exposición" in consigna.lower() or "presentación" in consigna.lower(),
            "link": "link" in consigna.lower() or "url" in consigna.lower(),
            "archivo_adjunto": "archivo adjunto" in consigna.lower()
        }
        return criterios
    
    def _evaluar_cumplimiento(self, entrega_texto, criterios):
        """
        Evalúa el cumplimiento de criterios en la entrega.
        Retorna: (nota, diccionario de cumplimiento)
        """
        entrega_lower = entrega_texto.lower()
        
        cumplimiento = {
            "infografia": "infografía" in entrega_lower or "gráfico" in entrega_lower or "visual" in entrega_lower,
            "justificacion": "justific" in entrega_lower or "porque" in entrega_lower or "motivo" in entrega_lower,
            "temas_especificos": any(tema in entrega_lower for tema in ["electrónica", "circuito", "digital"]),
            "presentacion": "exposición" in entrega_lower or "present" in entrega_lower,
            "contenido_minimo": len(entrega_texto) > 200,
            "estructura": any(palabra in entrega_lower for palabra in ["introducción", "conclusión", "desarrollo"])
        }
        
        # Calcular nota basada en cumplimiento
        cumplidas = sum(1 for v in cumplimiento.values() if v)
        total_criterios = len(cumplimiento)
        
        porcentaje = (cumplidas / total_criterios) * 100
        
        if porcentaje >= 90:
            nota = 10
        elif porcentaje >= 80:
            nota = 9
        elif porcentaje >= 70:
            nota = 8
        elif porcentaje >= 60:
            nota = 7
        elif porcentaje >= 50:
            nota = 6
        elif porcentaje >= 40:
            nota = 5
        elif porcentaje >= 30:
            nota = 4
        elif porcentaje >= 20:
            nota = 3
        elif porcentaje >= 10:
            nota = 2
        else:
            nota = 1
        
        return nota, cumplimiento
    
    def _generar_descripcion(self, cumplimiento, criterios):
        """Genera una descripción técnica breve del desempeño."""
        fortalezas = [k for k, v in cumplimiento.items() if v]
        debilidades = [k for k, v in cumplimiento.items() if not v]
        
        desc = f"Cumple {len(fortalezas)}/{len(cumplimiento)} criterios. "
        
        if fortalezas:
            desc += f"Fortalezas: {', '.join(fortalezas[:2])}. "
        
        if debilidades:
            desc += f"Áreas de mejora: {', '.join(debilidades[:2])}."
        
        return desc
    
    def _generar_comentario_pedagogico(self, cumplimiento, criterios, nombre_alumno):
        """Genera un feedback pedagógico constructivo."""
        
        fortalezas = [k for k, v in cumplimiento.items() if v]
        debilidades = [k for k, v in cumplimiento.items() if not v]
        
        comentario = f"Estimado/a {nombre_alumno.title()},\n\n"
        
        if fortalezas:
            comentario += f"Lo que hiciste bien: "
            comentario += f"presentaste {', '.join(fortalezas[:2])} adecuadamente. "
        
        if debilidades:
            comentario += f"\nPuntos a mejorar: "
            mejoras = []
            if "justificacion" in debilidades:
                mejoras.append("incluye una justificación clara de por qué seleccionaste esos temas")
            if "temas_especificos" in debilidades:
                mejoras.append("profundiza en los temas específicos de la consigna")
            if "estructura" in debilidades:
                mejoras.append("organiza mejor tu respuesta con introducción y conclusión")
            
            comentario += " y ".join(mejoras) + ".\n"
        
        comentario += (
            "\nPróximos pasos: "
            "Revisa la consigna nuevamente y asegúrate de abordar todos los aspectos solicitados. "
            "Si tienes dudas, consulta en clase o escribe un comentario.\n\n"
            "¡Sigue adelante!"
        )
        
        return comentario
    
    def procesar_directorio(self, ruta_actividad):
        """
        Procesa todos los estudiantes en un directorio de actividad.
        
        Args:
            ruta_actividad (str): Ruta a la carpeta de actividad
            
        Returns:
            list: Lista de evaluaciones en JSON
        """
        evaluaciones = []
        
        # Leer consigna si existe
        ruta_consigna = os.path.join(ruta_actividad, "consigna_referencia.txt")
        consigna = self.leer_consigna(ruta_consigna)
        
        # Iterar sobre directorios de estudiantes
        for carpeta_estudiante in glob.glob(os.path.join(ruta_actividad, "*")):
            if not os.path.isdir(carpeta_estudiante):
                continue
            
            nombre_alumno = os.path.basename(carpeta_estudiante)
            
            # Buscar archivos de entrega
            archivos_entrega = glob.glob(os.path.join(carpeta_estudiante, "entrega_*.docx"))
            
            if not archivos_entrega:
                # Si no hay entrega, usar informe JSON existente
                ruta_informe = os.path.join(carpeta_estudiante, "informe_tecnico_pedagogico.json")
                informe_json = self.leer_informe_json(ruta_informe)
                
                if informe_json:
                    evaluacion = {
                        "apellido_nombre": nombre_alumno.title(),
                        "actividad": informe_json.get("trabajo_practico", "Actividad 1"),
                        "nota": informe_json.get("nota", 1),
                        "descripcion": informe_json.get("motivo_tecnico", "Problema técnico"),
                        "comentario_privado": informe_json.get("feedback", "Re-entrega requerida")
                    }
                    evaluaciones.append(evaluacion)
                continue
            
            # Procesar la primera entrega disponible
            ruta_entrega = archivos_entrega[0]
            entrega_texto = self.leer_entrega_docx(ruta_entrega)
            
            # Leer informe previo si existe
            ruta_informe = os.path.join(carpeta_estudiante, "informe_tecnico_pedagogico.json")
            informe_json = self.leer_informe_json(ruta_informe)
            
            # Generar evaluación
            evaluacion = self.analizar_entrega(
                nombre_alumno,
                consigna,
                entrega_texto,
                informe_json
            )
            
            evaluaciones.append(evaluacion)
        
        return evaluaciones
    
    def guardar_evaluaciones_json(self, evaluaciones, ruta_salida):
        """Guarda las evaluaciones en formato JSON."""
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(evaluaciones, f, ensure_ascii=False, indent=2)
        print(f"✓ Evaluaciones guardadas en: {ruta_salida}")


if __name__ == "__main__":
    # Configurar rutas
    ruta_base = "Correcciones_Classroom/probando"
    ruta_actividad = os.path.join(ruta_base, "actividad 1")
    ruta_salida_json = "evaluaciones_masivas.json"
    
    # Procesar evaluaciones
    evaluador = EvaluadorMasivo(ruta_base)
    evaluaciones = evaluador.procesar_directorio(ruta_actividad)
    
    # Guardar JSON
    evaluador.guardar_evaluaciones_json(evaluaciones, ruta_salida_json)
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print(f"EVALUACIÓN MASIVA - RESUMEN")
    print(f"{'='*60}")
    print(f"Total de estudiantes evaluados: {len(evaluaciones)}")
    
    for eval_dict in evaluaciones:
        print(f"\n{eval_dict['apellido_nombre']}")
        print(f"  Actividad: {eval_dict['actividad']}")
        print(f"  Nota: {eval_dict['nota']}/10")
        print(f"  Descripción: {eval_dict['descripcion']}")
