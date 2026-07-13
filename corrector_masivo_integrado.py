"""
CORRECTOR MASIVO INTEGRADO - VERSIÓN EMPRESARIAL
Procesa TODAS las materias y actividades en un único archivo Excel
con una hoja por materia y múltiples actividades dentro.
"""

import json
import os
import re
import glob
from datetime import datetime
from pathlib import Path
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ╔════════════════════════════════════════════════════════════╗
# ║ FUNCIONES AUXILIARES DE EVALUACIÓN (Concordancia Real)
# ╚════════════════════════════════════════════════════════════╝

def _normalizar_tokens(texto):
    """Extrae tokens de 4+ caracteres para análisis de concordancia."""
    return re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}", (texto or "").lower())


def analizar_concordancia_consigna_entrega(consigna_texto, entrega_texto, tp_nombre):
    """
    Analiza concordancia REAL entre consigna y entrega del alumno.
    Retorna: (concordancia_score, temas_cubiertos, temas_faltantes, observaciones)
    """
    if not entrega_texto or len(entrega_texto.strip()) < 50:
        return 0.0, [], [], "Entrega insuficiente en longitud."
    
    if not consigna_texto or len(consigna_texto.strip()) < 10:
        return 0.5, [], [], "Consigna vacía o muy breve."
    
    # Stopwords a ignorar
    stopwords = {
        "trabajo", "practico", "práctico", "numero", "consigna", "actividad", "responder",
        "sistema", "operativo", "pregunta", "preguntas", "de", "del", "la", "el", "los", "las",
        "para", "con", "que", "una", "por", "sobre", "como", "desde", "hasta",
        "es", "son", "está", "están", "fue", "fueron", "sea", "sean", "deben", "debe", "debería"
    }
    
    # Extraer palabras clave
    tokens_consigna = [t for t in _normalizar_tokens(consigna_texto) if t not in stopwords and len(t) >= 4]
    
    # Eliminar duplicados
    palabras_clave = []
    vistos = set()
    for t in tokens_consigna:
        if t not in vistos:
            vistos.add(t)
            palabras_clave.append(t)
    
    palabras_clave = palabras_clave[:20]  # Limitar a 20
    
    if not palabras_clave:
        return 0.5, [], [], "No se pudieron extraer palabras clave."
    
    # Buscar coincidencias en entrega
    entrega_l = entrega_texto.lower()
    temas_cubiertos = [p for p in palabras_clave if p in entrega_l]
    temas_faltantes = [p for p in palabras_clave if p not in entrega_l]
    
    # Calcular cobertura
    cobertura = len(temas_cubiertos) / len(palabras_clave) if palabras_clave else 0.0
    
    # Análisis de calidad
    largo_entrega = len(entrega_texto.split())
    puntos_calidad = 0
    observaciones = []
    
    if largo_entrega < 100:
        observaciones.append("Entrega muy breve.")
        puntos_calidad -= 2
    elif largo_entrega < 200:
        observaciones.append("Entrega moderadamente desarrollada.")
        puntos_calidad += 1
    else:
        observaciones.append("Entrega con desarrollo adecuado.")
        puntos_calidad += 2
    
    if cobertura < 0.3:
        observaciones.append("Muy baja cobertura de temas.")
        puntos_calidad -= 3
    elif cobertura < 0.5:
        observaciones.append("Cobertura parcial de temas.")
        puntos_calidad -= 1
    elif cobertura < 0.7:
        observaciones.append("Buena cobertura de temas.")
        puntos_calidad += 1
    else:
        observaciones.append("Excelente cobertura de temas.")
        puntos_calidad += 2
    
    concordancia_score = min(1.0, max(0.0, cobertura + (puntos_calidad * 0.1)))
    
    return concordancia_score, temas_cubiertos, temas_faltantes, " ".join(observaciones)


def generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes):
    """
    Convierte score de concordancia (0-1) a nota (1-10).
    """
    nota_base = 1 + (concordancia_score * 9)
    
    # Ajustes por longitud
    if largo_entrega < 50:
        nota_base -= 2
    elif largo_entrega < 100:
        nota_base -= 1
    elif largo_entrega > 500:
        nota_base = min(10, nota_base + 0.5)
    
    nota_final = round(nota_base)
    nota_final = max(1, min(10, nota_final))
    
    return nota_final


class CorrectorMasivoIntegrado:
    """
    Sistema completo de corrección pedagógica automatizada.
    Procesa múltiples materias y actividades en un único Excel.
    """
    
    # Materias configuradas
    MATERIAS = [
        "probando",
        "Sistemas Digitales 5to",
        "Inst. Mant. De Redes Inf.",
        "Sist. Operativos",
        "Sistemas Digitales",
        "Procesos Industriales",
        "Desarrollo de aplicaciones web (dinamicas)",
        "Lab Hardware",
        "DES. SOFT. PLAT. MOVILES",
        "Lab. Aplicaciones 2026 4to",
        "Lab. Programacion 4to 2026",
        "Lab. Programacion 2026"
    ]
    
    def __init__(self, ruta_base="Correcciones_Classroom"):
        self.ruta_base = ruta_base
        self.evaluaciones_por_materia = {}
        self.estadisticas = {}
        
    # ╔════════════════════════════════════════════════════════════╗
    # ║ LECTURA DE ARCHIVOS
    # ╚════════════════════════════════════════════════════════════╝
    
    def leer_consigna(self, ruta_consigna):
        """Lee la consigna de referencia."""
        if os.path.exists(ruta_consigna):
            with open(ruta_consigna, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def leer_entrega(self, directorio_alumno):
        """Lee entrega en cualquier formato (.docx, .txt, .pdf, etc.)"""
        # Buscar archivos de entrega
        patrones = [
            os.path.join(directorio_alumno, "entrega_*.docx"),
            os.path.join(directorio_alumno, "entrega_*.txt"),
            os.path.join(directorio_alumno, "entrega_*.pdf"),
            os.path.join(directorio_alumno, "*.docx"),
            os.path.join(directorio_alumno, "*.txt"),
        ]
        
        for patron in patrones:
            archivos = glob.glob(patron)
            if archivos:
                ruta_entrega = archivos[0]
                return self._leer_archivo_entrega(ruta_entrega)
        
        return None  # No hay entrega
    
    def _leer_archivo_entrega(self, ruta_archivo):
        """Lee archivo de entrega según su extensión"""
        try:
            if ruta_archivo.endswith('.docx'):
                doc = Document(ruta_archivo)
                texto = "\n".join([p.text for p in doc.paragraphs])
                return texto.strip()
            
            elif ruta_archivo.endswith('.txt'):
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            
            elif ruta_archivo.endswith('.pdf'):
                # Para PDF, intentamos extraer texto básico
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(ruta_archivo)
                    texto = ""
                    for page in reader.pages:
                        texto += page.extract_text() + "\n"
                    return texto.strip()
                except:
                    return "[Error: No se pudo leer PDF]"
            
            else:
                return f"[Formato no soportado: {ruta_archivo}]"
        
        except Exception as e:
            return f"[Error al leer: {str(e)}]"
    
    def leer_entrega_docx(self, ruta_docx):
        """Extrae texto de archivo .docx (DEPRECATED - usar leer_entrega)"""
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
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ ANÁLISIS Y EVALUACIÓN (CON CONCORDANCIA REAL)
    # ╚════════════════════════════════════════════════════════════╝
    
    def analizar_entrega(self, nombre_alumno, consigna, entrega_texto, informe_json, actividad):
        """
        Análisis pedagógico con concordancia REAL entre consigna y entrega.
        Genera nota basada en análisis de temas y cobertura.
        """
        # Validar estado técnico
        if "[Error" in entrega_texto or "no legible" in entrega_texto.lower():
            return self._crear_evaluacion_problema_tecnico(nombre_alumno, actividad)
        
        if not entrega_texto.strip() or len(entrega_texto) < 50:
            return self._crear_evaluacion_vacia(nombre_alumno, actividad)
        
        # ANÁLISIS DE CONCORDANCIA REAL
        concordancia_score, temas_cubiertos, temas_faltantes, obs_concordancia = \
            analizar_concordancia_consigna_entrega(consigna, entrega_texto, actividad)
        
        # Generar nota desde concordancia
        largo_entrega = len(entrega_texto.split())
        nota = generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes)
        
        # Generar descripción técnica
        descripcion = f"Concordancia: {concordancia_score*100:.0f}%. {obs_concordancia}"
        
        # Generar comentario pedagógico personalizado
        comentario = self._generar_comentario_desde_concordancia(
            nombre_alumno, nota, concordancia_score, temas_cubiertos, temas_faltantes, actividad
        )
        
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": actividad,
            "nota": nota,
            "descripcion": descripcion,
            "comentario_privado": comentario
        }
    
    def _crear_evaluacion_problema_tecnico(self, nombre_alumno, actividad):
        """Evaluación para problemas técnicos."""
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": actividad,
            "nota": 2,
            "descripcion": "Problema técnico: archivo no legible.",
            "comentario_privado": (
                "He revisado tu entrega, pero el archivo no puede procesarse correctamente. "
                "Por favor, re-entrega en formato digital editable (Word .docx, Google Docs o .txt)."
            )
        }
    
    def _crear_evaluacion_vacia(self, nombre_alumno, actividad):
        """Evaluación para entregas vacías."""
        return {
            "apellido_nombre": nombre_alumno.title(),
            "actividad": actividad,
            "nota": 1,
            "descripcion": "Entrega vacía o incompleta.",
            "comentario_privado": (
                "Tu entrega está vacía o es muy breve. Por favor, completa el trabajo "
                "según todos los requisitos de la consigna."
            )
        }
    
    def _generar_comentario_desde_concordancia(self, nombre_alumno, nota, concordancia_score, temas_cubiertos, temas_faltantes, actividad):
        """
        Genera feedback pedagógico personalizado basado en concordancia real.
        Incluye nombre del alumno y actividad de forma explícita.
        """
        nombre_limpio = nombre_alumno.title()
        
        comentario = f"Estimado/a {nombre_limpio},\n\n"
        comentario += f"📋 EVALUACIÓN: {actividad}\n"
        comentario += f"{'─' * 40}\n\n"
        
        # Evaluar estado
        if nota >= 8:
            comentario += f"✓ ¡Excelente trabajo en '{actividad}'!\n"
            comentario += f"Tu entrega tiene muy buena concordancia con la consigna (Cobertura: {concordancia_score*100:.0f}%).\n\n"
        elif nota >= 6:
            comentario += f"✓ Buen trabajo en '{actividad}'.\n"
            comentario += f"Tu entrega responde adecuadamente a la consigna (Cobertura: {concordancia_score*100:.0f}%).\n\n"
        else:
            comentario += f"⚠️ Necesitas revisar tu entrega en '{actividad}'.\n"
            comentario += f"Tu trabajo tiene cobertura parcial ({concordancia_score*100:.0f}%) de la consigna.\n\n"
        
        # Temas cubiertos
        if temas_cubiertos:
            comentario += f"✓ Temas bien abordados:\n"
            for i, tema in enumerate(temas_cubiertos[:5], 1):
                comentario += f"  {i}. {tema}\n"
            comentario += "\n"
        
        # Temas faltantes
        if temas_faltantes:
            comentario += f"⚠️ Temas a desarrollar:\n"
            for i, tema in enumerate(temas_faltantes[:5], 1):
                comentario += f"  {i}. {tema}\n"
            comentario += "\n"
        
        comentario += (
            "📌 Recomendaciones:\n"
            "1. Revisa la consigna nuevamente y asegúrate de abordar todos los puntos\n"
            "2. Profundiza especialmente en los temas faltantes\n"
            "3. Amplía tu respuesta con más detalles y análisis\n"
            "4. Consulta en clase si tienes dudas\n\n"
            "¡Sigue adelante!"
        )
        
        return comentario
    
    def _extraer_criterios_consigna(self, consigna):
        """Extrae criterios clave de la consigna (DEPRECATED - usar concordancia)."""
        return {
            "infografia": "infografía" in consigna.lower(),
            "justificacion": any(p in consigna.lower() for p in ["justificad", "expliq", "por qué"]),
            "temas_especificos": any(t in consigna.lower() for t in ["electrónica", "circuitos", "digital", "código", "algoritmo"]),
            "herramienta": "herramienta" in consigna.lower() or "plataforma" in consigna.lower(),
            "presentacion": "exposición" in consigna.lower() or "presentación" in consigna.lower(),
            "link": "link" in consigna.lower() or "url" in consigna.lower(),
            "archivo_adjunto": "archivo adjunto" in consigna.lower()
        }
    
    def _evaluar_cumplimiento(self, entrega_texto, criterios):
        """Evalúa cumplimiento de criterios (DEPRECATED - usar concordancia)."""
        entrega_lower = entrega_texto.lower()
        
        cumplimiento = {
            "infografia": "infografía" in entrega_lower or "gráfico" in entrega_lower,
            "justificacion": any(p in entrega_lower for p in ["justific", "porque", "motivo", "razón"]),
            "temas_especificos": any(t in entrega_lower for t in ["electrónica", "circuito", "digital", "código", "algoritmo"]),
            "presentacion": "exposición" in entrega_lower or "present" in entrega_lower,
            "contenido_minimo": len(entrega_texto) > 200,
            "estructura": any(p in entrega_lower for p in ["introducción", "conclusión", "desarrollo"])
        }
        
        cumplidas = sum(1 for v in cumplimiento.values() if v)
        total = len(cumplimiento)
        porcentaje = (cumplidas / total) * 100
        
        nota = max(1, min(10, int(porcentaje / 10)))
        
        return nota, cumplimiento
    
    def _generar_descripcion(self, cumplimiento, criterios):
        """Descripción técnica breve (DEPRECATED - usar concordancia)."""
        fortalezas = [k for k, v in cumplimiento.items() if v]
        debilidades = [k for k, v in cumplimiento.items() if not v]
        
        desc = f"Cumple {len(fortalezas)}/{len(cumplimiento)} criterios. "
        
        if fortalezas:
            desc += f"Fortalezas: {', '.join(fortalezas[:2])}. "
        
        if debilidades:
            desc += f"Mejoras: {', '.join(debilidades[:2])}."
        
        return desc[:200]
    
    def _generar_comentario_pedagogico(self, cumplimiento, criterios, nombre_alumno):
        """Feedback pedagógico constructivo (DEPRECATED - usar concordancia)."""
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
            "3. Consulta en clase si tienes dudas\n\n"
            "¡Sigue adelante!"
        )
        
        return comentario
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ DESCUBRIMIENTO DE ESTRUCTURA
    # ╚════════════════════════════════════════════════════════════╝
    
    def detectar_materias(self):
        """Detecta todas las materias disponibles."""
        materias = []
        ruta_base_expandida = os.path.join(self.ruta_base)
        
        for item in os.listdir(ruta_base_expandida):
            ruta_item = os.path.join(ruta_base_expandida, item)
            if os.path.isdir(ruta_item):
                materias.append(item)
        
        return sorted(materias)
    
    def detectar_actividades(self, materia):
        """Detecta todas las actividades de una materia."""
        ruta_materia = os.path.join(self.ruta_base, materia)
        actividades = []
        
        if not os.path.exists(ruta_materia):
            return actividades
        
        for item in os.listdir(ruta_materia):
            ruta_item = os.path.join(ruta_materia, item)
            if os.path.isdir(ruta_item) and item.lower() not in ["reportes", "temp", ".git"]:
                actividades.append(item)
        
        return sorted(actividades)
    
    def procesar_actividad(self, materia, actividad):
        """
        Procesa una actividad completa (todos los estudiantes).
        Retorna lista de evaluaciones.
        """
        ruta_actividad = os.path.join(self.ruta_base, materia, actividad)
        evaluaciones = []
        
        # Leer consigna
        ruta_consigna = os.path.join(ruta_actividad, "consigna_referencia.txt")
        consigna = self.leer_consigna(ruta_consigna)
        
        # DEBUG: Verificar si la consigna se leyó correctamente
        if not consigna or len(consigna.strip()) < 10:
            print(f"    ⚠️  ADVERTENCIA: Consigna vacía o no encontrada en {ruta_consigna}")
        
        # Iterar sobre directorios de estudiantes
        for item in os.listdir(ruta_actividad):
            ruta_item = os.path.join(ruta_actividad, item)
            
            if not os.path.isdir(ruta_item) or item.lower() in ["reportes", "temp", ".git"]:
                continue
            
            nombre_alumno = item
            
            # DEBUG: Mostrar progreso
            print(f"         → Evaluando: {nombre_alumno}...", end=" ", flush=True)
            
            # Buscar archivo de entrega (cualquier formato)
            entrega_texto = self.leer_entrega(ruta_item)
            
            if entrega_texto:
                # Procesar entrega
                ruta_informe = os.path.join(ruta_item, "informe_tecnico_pedagogico.json")
                informe_json = self.leer_informe_json(ruta_informe)
                
                evaluacion = self.analizar_entrega(nombre_alumno, consigna, entrega_texto, informe_json, actividad)
                evaluaciones.append(evaluacion)
                print("✓")
            else:
                # Usar informe JSON existente
                ruta_informe = os.path.join(ruta_item, "informe_tecnico_pedagogico.json")
                informe_json = self.leer_informe_json(ruta_informe)
                
                if informe_json:
                    evaluacion = {
                        "apellido_nombre": nombre_alumno.title(),
                        "actividad": actividad,
                        "nota": informe_json.get("nota", 1),
                        "descripcion": informe_json.get("motivo_tecnico", "Problema técnico"),
                        "comentario_privado": informe_json.get("feedback", "Re-entrega requerida")
                    }
                    evaluaciones.append(evaluacion)
                    print("✓ (JSON)")
                else:
                    print("✗ (Sin entrega)")
        
        return evaluaciones
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ GENERACIÓN DE EXCEL
    # ╚════════════════════════════════════════════════════════════╝
    
    def crear_hoja_materia(self, materia, wb):
        """Crea una hoja para una materia (máximo 31 caracteres)."""
        # Normalizar nombre a 31 caracteres (límite de Excel)
        nombre_hoja = materia[:31]
        ws = wb.create_sheet(title=nombre_hoja)
        
        # Encabezados
        encabezados = [
            "Actividad",
            "Apellido y Nombre",
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
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 50
        ws.row_dimensions[1].height = 30
        
        return ws
    
    def agregar_evaluacion_a_hoja(self, materia, evaluacion, wb):
        """Agrega una evaluación a la hoja de materia."""
        # Normalizar nombre (Excel limita a 31 caracteres)
        materia_normalizada = materia[:31]
        
        # Crear hoja si no existe
        if materia_normalizada not in wb.sheetnames:
            ws = self.crear_hoja_materia(materia, wb)
        else:
            ws = wb[materia_normalizada]
        
        fila = ws.max_row + 1
        
        datos = [
            evaluacion.get("actividad", ""),
            evaluacion.get("apellido_nombre", ""),
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
        """Crea hoja de resumen con estadísticas por materia."""
        ws = wb.create_sheet("Resumen", 0)
        
        ws['A1'] = "REPORTE PEDAGÓGICO - CORRECCIÓN MASIVA"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        ws.merge_cells('A1:E1')
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws['A2'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(italic=True, size=10)
        
        # Tabla de estadísticas
        fila = 4
        headers = ["Materia", "Total Estudiantes", "Actividades", "Promedio", "Aprobados (≥6)"]
        for col, header in enumerate(headers, 1):
            celda = ws.cell(row=fila, column=col)
            celda.value = header
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        fila = 5
        for materia in sorted(self.evaluaciones_por_materia.keys()):
            evaluaciones_materia = self.evaluaciones_por_materia[materia]
            notas = [e['nota'] for e in evaluaciones_materia if isinstance(e.get('nota'), (int, float))]
            actividades = set(e['actividad'] for e in evaluaciones_materia)
            
            aprobados = sum(1 for n in notas if n >= 6)
            promedio = sum(notas) / len(notas) if notas else 0
            
            ws[f'A{fila}'] = materia
            ws[f'B{fila}'] = len(notas)
            ws[f'C{fila}'] = len(actividades)
            ws[f'D{fila}'] = f"{promedio:.2f}"
            ws[f'E{fila}'] = aprobados
            
            fila += 1
        
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 18
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ EJECUCIÓN COMPLETA
    # ╚════════════════════════════════════════════════════════════╝
    
    def ejecutar_correccion_masiva(self, ruta_excel_salida):
        """
        Ejecuta corrección masiva de TODAS las materias y actividades.
        """
        print("\n" + "="*80)
        print(" 📊 CORRECTOR MASIVO INTEGRADO - TODAS LAS MATERIAS ")
        print("="*80)
        
        # Detectar materias
        print("\n[FASE 1] Detectando materias y actividades...")
        materias = self.detectar_materias()
        print(f"✓ {len(materias)} materias encontradas\n")
        
        # Procesar cada materia
        total_evaluaciones = 0
        
        for i, materia in enumerate(materias, 1):
            print(f"[{i}/{len(materias)}] 📚 {materia}")
            
            actividades = self.detectar_actividades(materia)
            if actividades:
                print(f"         ├─ {len(actividades)} actividades detectadas")
            else:
                print(f"         └─ ⚠️  Sin actividades")
                continue
            
            evaluaciones_materia = []
            
            for j, actividad in enumerate(actividades, 1):
                is_last = (j == len(actividades))
                prefix = "         └─" if is_last else "         ├─"
                print(f"{prefix} 📝 '{actividad}'")
                
                evals = self.procesar_actividad(materia, actividad)
                evaluaciones_materia.extend(evals)
                
                if evals:
                    print(f"            ✓ {len(evals)} estudiante(s) evaluado(s)")
            
            self.evaluaciones_por_materia[materia] = evaluaciones_materia
            total_evaluaciones += len(evaluaciones_materia)
            print()
        
        # Generar Excel
        print(f"[FASE 2] 📄 Generando Excel con {len(materias)} hojas...")
        self.generar_excel(ruta_excel_salida)
        
        print(f"\n" + "="*80)
        print(f" ✅ PROCESO COMPLETADO EXITOSAMENTE ")
        print(f" • Total de estudiantes evaluados: {total_evaluaciones}")
        print(f" • Materias: {len(materias)}")
        print(f" • Excel generado: {ruta_excel_salida}")
        print("="*80 + "\n")
        
        return total_evaluaciones
    
    def generar_excel(self, ruta_salida):
        """Genera Excel con una hoja por materia."""
        wb = Workbook()
        wb.remove(wb.active)
        
        # Crear hojas por materia
        for materia in sorted(self.evaluaciones_por_materia.keys()):
            evaluaciones = self.evaluaciones_por_materia[materia]
            
            for evaluacion in evaluaciones:
                self.agregar_evaluacion_a_hoja(materia, evaluacion, wb)
        
        # Agregar resumen al inicio
        if self.evaluaciones_por_materia:
            self.agregar_hoja_resumen(wb)
        
        wb.save(ruta_salida)
        print(f"✓ Excel guardado: {ruta_salida}")


if __name__ == "__main__":
    # Ejecutar corrección masiva
    corrector = CorrectorMasivoIntegrado()
    corrector.ejecutar_correccion_masiva("evaluaciones_completas.xlsx")
