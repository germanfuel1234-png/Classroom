"""
SISTEMA INTEGRADO DE CORRECCIÓN PEDAGÓGICA MASIVA
Script maestro que ejecuta la cadena completa:
1. Evaluación de entregas vs consigna
2. Generación de JSON con criterios pedagógicos
3. Creación de planilla Excel por materia
"""

import json
import os
import sys
import glob
from datetime import datetime
from pathlib import Path
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


class SistemaPedagogicoCorrecciones:
    """Sistema completo de corrección pedagógica automatizada."""
    
    def __init__(self, ruta_base="Correcciones_Classroom/probando"):
        self.ruta_base = ruta_base
        self.evaluaciones = []
        self.materias_hojas = {}
        self.estadisticas = {}
        
    # ╔════════════════════════════════════════════════════════════╗
    # ║ FASE 1: EVALUACIÓN DE ENTREGAS
    # ╚════════════════════════════════════════════════════════════╝
    
    def leer_consigna(self, ruta_consigna):
        """Lee la consigna de referencia."""
        if os.path.exists(ruta_consigna):
            with open(ruta_consigna, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def leer_entrega_docx(self, ruta_docx):
        """Extrae texto de archivo .docx"""
        try:
            doc = Document(ruta_docx)
            texto = "\n".join([p.text for p in doc.paragraphs])
            return texto.strip()
        except Exception as e:
            return f"[Error: {str(e)}]"
    
    def leer_informe_json(self, ruta_informe):
        """Lee informe técnico previo en JSON."""
        if os.path.exists(ruta_informe):
            try:
                with open(ruta_informe, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def analizar_entrega(self, nombre_alumno, consigna, entrega_texto, informe_json):
        """
        Análisis pedagógico estricto de entrega vs consigna.
        Retorna evaluación con campos obligatorios.
        """
        criterios = self._extraer_criterios_consigna(consigna)
        
        # Evaluar estado técnico
        if "[Error" in entrega_texto or "no legible" in entrega_texto.lower():
            return self._crear_evaluacion_problema_tecnico(nombre_alumno, informe_json)
        
        if not entrega_texto.strip() or len(entrega_texto) < 50:
            return self._crear_evaluacion_vacia(nombre_alumno, informe_json)
        
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
    
    def _crear_evaluacion_problema_tecnico(self, nombre_alumno, informe_json):
        """Evaluación para problemas técnicos de lectura."""
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": informe_json.get("trabajo_practico", "Actividad 1") if informe_json else "Actividad 1",
            "nota": 2,
            "descripcion": "Entrega con problema técnico: archivo no legible o no procesable.",
            "comentario_privado": (
                "He revisado tu entrega, pero el archivo no puede procesarse correctamente "
                "(posible PDF escaneado o imagen). Por favor, re-entrega tu trabajo en formato "
                "digital editable (Word .docx, Google Docs o .txt) para que pueda evaluarse apropiadamente."
            )
        }
    
    def _crear_evaluacion_vacia(self, nombre_alumno, informe_json):
        """Evaluación para entregas vacías o incompletas."""
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": informe_json.get("trabajo_practico", "Actividad 1") if informe_json else "Actividad 1",
            "nota": 1,
            "descripcion": "Entrega vacía o incompleta.",
            "comentario_privado": (
                "Tu entrega está vacía o es demasiado breve. No hay contenido para evaluar. "
                "Por favor, completa el trabajo según todos los requisitos de la consigna."
            )
        }
    
    def _extraer_criterios_consigna(self, consigna):
        """Extrae criterios clave de la consigna."""
        return {
            "infografia": "infografía" in consigna.lower(),
            "justificacion": any(p in consigna.lower() for p in ["justificad", "expliq", "por qué"]),
            "temas_especificos": any(t in consigna.lower() for t in ["electrónica", "circuitos", "digital"]),
            "herramienta": "herramienta" in consigna.lower() or "plataforma" in consigna.lower(),
            "presentacion": "exposición" in consigna.lower() or "presentación" in consigna.lower(),
            "link": "link" in consigna.lower() or "url" in consigna.lower(),
            "archivo_adjunto": "archivo adjunto" in consigna.lower()
        }
    
    def _evaluar_cumplimiento(self, entrega_texto, criterios):
        """
        Evalúa cumplimiento de criterios en la entrega.
        Retorna: (nota_numerica, dict_cumplimiento)
        """
        entrega_lower = entrega_texto.lower()
        
        cumplimiento = {
            "infografia": "infografía" in entrega_lower or "gráfico" in entrega_lower or "visual" in entrega_lower,
            "justificacion": any(p in entrega_lower for p in ["justific", "porque", "motivo", "razón"]),
            "temas_especificos": any(t in entrega_lower for t in ["electrónica", "circuito", "digital"]),
            "presentacion": "exposición" in entrega_lower or "present" in entrega_lower,
            "contenido_minimo": len(entrega_texto) > 200,
            "estructura": any(p in entrega_lower for p in ["introducción", "conclusión", "desarrollo"])
        }
        
        cumplidas = sum(1 for v in cumplimiento.values() if v)
        total = len(cumplimiento)
        porcentaje = (cumplidas / total) * 100
        
        # Escala de notas del 1 al 10
        nota = max(1, min(10, int(porcentaje / 10)))
        
        return nota, cumplimiento
    
    def _generar_descripcion(self, cumplimiento, criterios):
        """Descripción técnica breve del desempeño (máx 3 líneas)."""
        fortalezas = [k for k, v in cumplimiento.items() if v]
        debilidades = [k for k, v in cumplimiento.items() if not v]
        
        desc = f"Cumple {len(fortalezas)}/{len(cumplimiento)} criterios. "
        
        if fortalezas:
            desc += f"Fortalezas: {', '.join(fortalezas[:2])}. "
        
        if debilidades:
            desc += f"Mejoras: {', '.join(debilidades[:2])}."
        
        return desc[:200]  # Limitar a 200 caracteres máximo
    
    def _generar_comentario_pedagogico(self, cumplimiento, criterios, nombre_alumno):
        """Feedback pedagógico constructivo, claro y detallado."""
        fortalezas = [k for k, v in cumplimiento.items() if v]
        debilidades = [k for k, v in cumplimiento.items() if not v]
        
        comentario = f"Estimado/a {nombre_alumno.title()},\n\n"
        
        if fortalezas:
            comentario += f"✓ Lo que hiciste bien: {', '.join(fortalezas[:2])}.\n\n"
        
        if debilidades:
            comentario += "Puntos a mejorar:\n"
            mejoras = []
            if "justificacion" in debilidades:
                mejoras.append("- Incluye una justificación clara de tus decisiones")
            if "temas_especificos" in debilidades:
                mejoras.append("- Profundiza en los temas específicos de la consigna")
            if "estructura" in debilidades:
                mejoras.append("- Organiza con introducción, desarrollo y conclusión")
            if "contenido_minimo" in debilidades:
                mejoras.append("- Expande tu respuesta con más detalle y análisis")
            
            comentario += "\n".join(mejoras) + "\n\n"
        
        comentario += (
            "Próximos pasos:\n"
            "1. Revisa la consigna nuevamente\n"
            "2. Aborda todos los aspectos solicitados\n"
            "3. Si tienes dudas, consulta en clase o escribe un comentario\n\n"
            "¡Sigue adelante!"
        )
        
        return comentario
    
    def procesar_directorio(self, ruta_actividad):
        """
        Procesa todos los estudiantes en un directorio de actividad.
        Retorna lista de evaluaciones en JSON.
        """
        evaluaciones = []
        
        # Leer consigna
        ruta_consigna = os.path.join(ruta_actividad, "consigna_referencia.txt")
        consigna = self.leer_consigna(ruta_consigna)
        
        # Iterar sobre directorios de estudiantes
        for carpeta_estudiante in glob.glob(os.path.join(ruta_actividad, "*")):
            if not os.path.isdir(carpeta_estudiante):
                continue
            
            nombre_alumno = os.path.basename(carpeta_estudiante)
            
            # Buscar archivos de entrega
            archivos_entrega = glob.glob(os.path.join(carpeta_estudiante, "entrega_*.docx"))
            
            if archivos_entrega:
                # Procesar entrega
                entrega_texto = self.leer_entrega_docx(archivos_entrega[0])
                ruta_informe = os.path.join(carpeta_estudiante, "informe_tecnico_pedagogico.json")
                informe_json = self.leer_informe_json(ruta_informe)
                
                evaluacion = self.analizar_entrega(nombre_alumno, consigna, entrega_texto, informe_json)
                evaluaciones.append(evaluacion)
            else:
                # Usar informe JSON existente
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
        
        return evaluaciones
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ FASE 2: GENERACIÓN DE PLANILLA EXCEL
    # ╚════════════════════════════════════════════════════════════╝
    
    def crear_hoja_materia(self, materia, wb):
        """Crea una nueva hoja para una materia en el workbook."""
        if materia in self.materias_hojas:
            return self.materias_hojas[materia]
        
        ws = wb.create_sheet(title=materia[:31])
        self.materias_hojas[materia] = ws
        
        # Encabezados
        encabezados = [
            "Apellido y Nombre",
            "Actividad",
            "Nota (1-10)",
            "Descripción Técnica",
            "Comentario Pedagógico"
        ]
        
        for col, enc in enumerate(encabezados, start=1):
            celda = ws.cell(row=1, column=col)
            celda.value = enc
            celda.font = Font(bold=True, color="FFFFFF", size=11)
            celda.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Anchos
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 50
        ws.row_dimensions[1].height = 30
        
        return ws
    
    def agregar_evaluacion_a_hoja(self, materia, evaluacion, wb):
        """Agrega una evaluación a la hoja de la materia."""
        ws = self.crear_hoja_materia(materia, wb)
        
        fila = ws.max_row + 1
        
        datos = [
            evaluacion.get("apellido_nombre", ""),
            evaluacion.get("actividad", ""),
            evaluacion.get("nota", ""),
            evaluacion.get("descripcion", ""),
            evaluacion.get("comentario_privado", "")
        ]
        
        for col, dato in enumerate(datos, start=1):
            celda = ws.cell(row=fila, column=col)
            celda.value = dato
            
            if col == 3:  # Columna de nota
                celda.alignment = Alignment(horizontal="center", vertical="top")
                celda.font = Font(bold=True, size=11)
                
                # Color según nota
                if isinstance(dato, (int, float)):
                    if dato >= 8:
                        celda.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    elif dato >= 6:
                        celda.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                    else:
                        celda.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            else:
                celda.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            # Bordes
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            celda.border = border
        
        ws.row_dimensions[fila].height = 60
    
    def agregar_hoja_resumen(self, wb):
        """Crea hoja de resumen con estadísticas."""
        ws = wb.create_sheet("Resumen", 0)
        
        ws['A1'] = "REPORTE PEDAGÓGICO DE EVALUACIONES"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        ws.merge_cells('A1:D1')
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws['A2'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(italic=True, size=10)
        
        # Tabla de estadísticas
        fila = 4
        headers = ["Materia", "Total Estudiantes", "Promedio de Notas", "Aprobados (≥6)"]
        for col, header in enumerate(headers, 1):
            celda = ws.cell(row=fila, column=col)
            celda.value = header
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        fila = 5
        for materia, ws_materia in self.materias_hojas.items():
            notas = []
            for fila_datos in range(2, ws_materia.max_row + 1):
                nota = ws_materia.cell(row=fila_datos, column=3).value
                if isinstance(nota, (int, float)):
                    notas.append(nota)
            
            aprobados = sum(1 for n in notas if n >= 6)
            promedio = sum(notas) / len(notas) if notas else 0
            
            ws[f'A{fila}'] = materia
            ws[f'B{fila}'] = len(notas)
            ws[f'C{fila}'] = f"{promedio:.2f}"
            ws[f'D{fila}'] = aprobados
            
            fila += 1
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
    
    def generar_excel(self, evaluaciones, ruta_salida):
        """Genera planilla Excel con todas las evaluaciones."""
        wb = Workbook()
        wb.remove(wb.active)
        
        # Agrupar evaluaciones por materia
        evaluaciones_por_materia = {}
        for eval_dict in evaluaciones:
            materia = eval_dict.get("actividad", "General")
            if materia not in evaluaciones_por_materia:
                evaluaciones_por_materia[materia] = []
            evaluaciones_por_materia[materia].append(eval_dict)
        
        # Crear hojas por materia
        for materia, evals in evaluaciones_por_materia.items():
            for eval_dict in evals:
                self.agregar_evaluacion_a_hoja(materia, eval_dict, wb)
        
        # Agregar resumen
        if self.materias_hojas:
            self.agregar_hoja_resumen(wb)
        
        wb.save(ruta_salida)
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ EJECUCIÓN COMPLETA DEL SISTEMA
    # ╚════════════════════════════════════════════════════════════╝
    
    def ejecutar_proceso_completo(self, ruta_actividad, ruta_json_salida, ruta_excel_salida):
        """
        Ejecuta todo el proceso:
        1. Evalúa entregas
        2. Genera JSON
        3. Crea Excel
        """
        print("\n" + "="*70)
        print("SISTEMA DE CORRECCIÓN PEDAGÓGICA MASIVA")
        print("="*70)
        
        # Fase 1: Evaluación
        print("\n[FASE 1] Evaluando entregas...")
        self.evaluaciones = self.procesar_directorio(ruta_actividad)
        print(f"✓ {len(self.evaluaciones)} estudiantes evaluados")
        
        # Guardar JSON
        print("\n[FASE 2] Generando JSON de evaluaciones...")
        with open(ruta_json_salida, 'w', encoding='utf-8') as f:
            json.dump(self.evaluaciones, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON guardado: {ruta_json_salida}")
        
        # Crear Excel
        print("\n[FASE 3] Creando planilla Excel...")
        self.generar_excel(self.evaluaciones, ruta_excel_salida)
        print(f"✓ Excel generado: {ruta_excel_salida}")
        
        # Resumen final
        print("\n" + "="*70)
        print("RESUMEN DE EVALUACIONES")
        print("="*70)
        
        for eval_dict in self.evaluaciones:
            print(f"\n{eval_dict['apellido_nombre']}")
            print(f"  Actividad: {eval_dict['actividad']}")
            print(f"  Nota: {eval_dict['nota']}/10")
            print(f"  Descripción: {eval_dict['descripcion']}")
        
        print("\n" + "="*70)
        print(f"PROCESO COMPLETADO: {len(self.evaluaciones)} evaluaciones generadas")
        print("="*70 + "\n")


if __name__ == "__main__":
    # Configuración
    ruta_base = "Correcciones_Classroom/probando"
    ruta_actividad = os.path.join(ruta_base, "actividad 1")
    ruta_json = "evaluaciones_masivas.json"
    ruta_excel = "evaluaciones_estudiantes.xlsx"
    
    # Ejecutar
    sistema = SistemaPedagogicoCorrecciones(ruta_base)
    sistema.ejecutar_proceso_completo(ruta_actividad, ruta_json, ruta_excel)
