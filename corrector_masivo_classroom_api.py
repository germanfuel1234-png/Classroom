"""
CORRECTOR MASIVO CON GOOGLE CLASSROOM API
Procesa TODAS las materias, actividades y alumnos REALES de Classroom.
"""

import json
import os
import re
import io
from datetime import datetime
from pathlib import Path
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from googleapiclient.http import MediaIoBaseDownload

try:
    import PyPDF2
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False


# ╔════════════════════════════════════════════════════════════╗
# ║ FUNCIONES AUXILIARES PARA DESCARGAR ARCHIVOS
# ╚════════════════════════════════════════════════════════════╝

def _obtener_drive_file_desde_attachment(adj):
    """Normaliza el objeto de adjunto de Classroom para extraer metadatos de Drive."""
    if not isinstance(adj, dict) or "driveFile" not in adj:
        return None

    df = adj.get("driveFile")
    if not isinstance(df, dict):
        return None

    if df.get("id"):
        return df

    anidado = df.get("driveFile")
    if isinstance(anidado, dict) and anidado.get("id"):
        return anidado

    return None


def descargar_adjunto_drive(service_drive, file_id, mime_type_original=None):
    """Descarga un archivo de Google Drive en memoria y devuelve sus bytes."""
    try:
        if not mime_type_original:
            try:
                file_metadata = service_drive.files().get(fileId=file_id, fields='mimeType').execute()
                mime_type_original = file_metadata.get('mimeType', '')
            except Exception:
                mime_type_original = ''
        
        # Manejar archivos nativos de Google
        if mime_type_original and mime_type_original.startswith('application/vnd.google-apps.'):
            export_mapping = {
                'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }
            export_mime_type = export_mapping.get(mime_type_original, 'application/pdf')
            
            try:
                request = service_drive.files().export_media(fileId=file_id, mimeType=export_mime_type)
                file_stream = io.BytesIO()
                downloader = MediaIoBaseDownload(file_stream, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                return file_stream.getvalue()
            except Exception:
                return None
        
        # Descargar archivo normal
        request = service_drive.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return file_stream.getvalue()
            
    except Exception as e:
        return None


def extraer_texto_de_docx(contenido_bytes):
    """Lee un archivo .docx desde bytes y extrae su texto."""
    try:
        fichero = io.BytesIO(contenido_bytes)
        doc = Document(fichero)
        texto_completo = []
        for parrafo in doc.paragraphs:
            if parrafo.text.strip():
                texto_completo.append(parrafo.text.strip())
        return "\n".join(texto_completo)
    except Exception:
        return ""


def extraer_texto_de_pdf(contenido_bytes):
    """Extrae texto de un PDF desde bytes."""
    if not PDF_DISPONIBLE:
        return ""
    
    try:
        pdf_file = io.BytesIO(contenido_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        texto_completo = []
        
        for num_pagina, pagina in enumerate(pdf_reader.pages):
            texto_pagina = (pagina.extract_text() or "").strip()
            if texto_pagina:
                texto_completo.append(texto_pagina)
        
        return "\n".join(texto_completo)
    except Exception:
        return ""


def descargar_y_extraer_entrega(attachments, service_drive):
    """Descarga archivos adjuntos de Classroom y extrae su texto."""
    if not service_drive:
        return ""
    
    if not attachments:
        return ""

    textos = []
    for adj in attachments[:5]:  # Procesar hasta 5 archivos
        drive_file = _obtener_drive_file_desde_attachment(adj)
        if not drive_file:
            continue
        
        file_id = drive_file.get("id")
        file_name = drive_file.get("title", "archivo").lower()
        
        if not file_id:
            continue

        try:
            metadata = service_drive.files().get(fileId=file_id, fields="mimeType,name").execute()
            mime_type = metadata.get("mimeType", "")
            file_name = metadata.get("name", file_name).lower()
        except Exception:
            mime_type = ""

        contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
        if not contenido:
            continue

        texto = ""
        if file_name.endswith(".docx") or "wordprocessingml" in mime_type:
            texto = extraer_texto_de_docx(contenido)
        elif file_name.endswith(".pdf") or mime_type == "application/pdf":
            texto = extraer_texto_de_pdf(contenido)
        elif file_name.endswith(".txt") or mime_type == "text/plain":
            try:
                texto = contenido.decode('utf-8', errors='ignore')
            except:
                texto = ""
        
        if texto and len(texto.strip()) > 10:
            textos.append(texto)

    return "\n".join(textos)


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
    
    palabras_clave = palabras_clave[:20]
    
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
    
    if largo_entrega < 50:
        nota_base -= 2
    elif largo_entrega < 100:
        nota_base -= 1
    elif largo_entrega > 500:
        nota_base = min(10, nota_base + 0.5)
    
    nota_final = round(nota_base)
    nota_final = max(1, min(10, nota_final))
    
    return nota_final


class CorrectorMasivoClassroomAPI:
    """
    Sistema de corrección que se conecta a Google Classroom API.
    Descarga entregas reales de Classroom y las evalúa.
    """
    
    def __init__(self):
        self.evaluaciones_por_materia = {}
        self.total_evaluaciones = 0
        self.cache_perfiles = {}  # Cache para nombres de usuarios
    
    def obtener_nombre_alumno_real(self, user_id, service):
        """
        Obtiene el nombre real del alumno desde Google Classroom.
        Utiliza cache para evitar llamadas repetidas.
        """
        if user_id in self.cache_perfiles:
            return self.cache_perfiles[user_id]
        
        try:
            perfil = service.userProfiles().get(userId=user_id).execute()
            nombre = perfil.get("name", {}).get("fullName", f"Usuario {user_id}")
            self.cache_perfiles[user_id] = nombre
            return nombre
        except Exception as e:
            nombre = f"Usuario {user_id}"
            self.cache_perfiles[user_id] = nombre
            return nombre
    
    def obtener_consigna_actividad(self, service, course_id, work_id):
        """
        Obtiene la descripción completa de una actividad.
        """
        try:
            trabajo = service.courses().courseWork().get(
                courseId=course_id,
                id=work_id,
                fields="id,title,description,materials"
            ).execute()
            
            descripcion = trabajo.get("description", "")
            titulo = trabajo.get("title", "")
            
            # Combinar título + descripción
            consigna = f"{titulo}\n\n{descripcion}" if descripcion else titulo
            
            return consigna.strip()
        except Exception as e:
            return ""
    
    def leer_entrega_texto(self, ruta_archivo):
        """Lee texto de archivo .txt, .docx, etc."""
        try:
            if ruta_archivo.endswith('.docx'):
                doc = Document(ruta_archivo)
                texto = "\n".join([p.text for p in doc.paragraphs])
                return texto.strip()
            else:
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            return f"[Error: {str(e)}]"
    
    def evaluar_alumno(self, nombre_alumno, nombre_actividad, consigna_texto, entrega_texto):
        """
        Evalúa la entrega de un alumno basándose en concordancia real.
        """
        # Validar estado técnico
        if "[Error" in entrega_texto or "no legible" in entrega_texto.lower():
            return {
                "apellido_nombre": nombre_alumno.title(),
                "actividad": nombre_actividad,
                "nota": 2,
                "descripcion": "Problema técnico: archivo no legible.",
                "comentario_privado": "El archivo no puede procesarse. Por favor, re-entrega en formato editable."
            }
        
        if not entrega_texto.strip() or len(entrega_texto) < 50:
            return {
                "apellido_nombre": nombre_alumno.title(),
                "actividad": nombre_actividad,
                "nota": 1,
                "descripcion": "Entrega vacía o incompleta.",
                "comentario_privado": "Tu entrega está vacía. Por favor, completa el trabajo según la consigna."
            }
        
        # ANÁLISIS DE CONCORDANCIA REAL
        concordancia_score, temas_cubiertos, temas_faltantes, obs_concordancia = \
            analizar_concordancia_consigna_entrega(consigna_texto, entrega_texto, nombre_actividad)
        
        # Generar nota
        largo_entrega = len(entrega_texto.split())
        nota = generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes)
        
        # Descripción técnica
        descripcion = f"Concordancia: {concordancia_score*100:.0f}%. {obs_concordancia}"
        
        # Comentario personalizado
        nombre_limpio = nombre_alumno.title()
        comentario = f"Estimado/a {nombre_limpio},\n\n"
        comentario += f"📋 EVALUACIÓN: {nombre_actividad}\n"
        comentario += f"{'─' * 40}\n\n"
        
        if nota >= 8:
            comentario += f"✓ ¡Excelente trabajo!\n"
            comentario += f"Tu entrega tiene muy buena concordancia (Cobertura: {concordancia_score*100:.0f}%).\n\n"
        elif nota >= 6:
            comentario += f"✓ Buen trabajo.\n"
            comentario += f"Tu entrega responde adecuadamente (Cobertura: {concordancia_score*100:.0f}%).\n\n"
        else:
            comentario += f"⚠️ Necesitas revisar tu entrega.\n"
            comentario += f"Cobertura parcial ({concordancia_score*100:.0f}%) de la consigna.\n\n"
        
        if temas_cubiertos:
            comentario += f"✓ Temas bien abordados:\n"
            for i, tema in enumerate(temas_cubiertos[:5], 1):
                comentario += f"  {i}. {tema}\n"
            comentario += "\n"
        
        if temas_faltantes:
            comentario += f"⚠️ Temas a desarrollar:\n"
            for i, tema in enumerate(temas_faltantes[:5], 1):
                comentario += f"  {i}. {tema}\n"
            comentario += "\n"
        
        comentario += "📌 Recomendaciones:\n1. Revisa la consigna nuevamente\n2. Profundiza en temas faltantes\n3. Amplía tu respuesta\n4. Consulta en clase\n\n¡Sigue adelante!"
        
        return {
            "apellido_nombre": nombre_limpio,
            "actividad": nombre_actividad,
            "nota": nota,
            "descripcion": descripcion,
            "comentario_privado": comentario
        }
    
    def crear_hoja_materia(self, materia, wb):
        """Crea una hoja para una materia."""
        nombre_hoja = materia[:31]
        ws = wb.create_sheet(title=nombre_hoja)
        
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
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 35
        ws.column_dimensions['E'].width = 50
        ws.row_dimensions[1].height = 30
        
        return ws
    
    def agregar_evaluacion_a_hoja(self, materia, evaluacion, wb):
        """Agrega una evaluación a la hoja de materia."""
        materia_normalizada = materia[:31]
        
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
            
            if col == 3:
                celda.alignment = Alignment(horizontal="center", vertical="top")
                celda.font = Font(bold=True, size=11)
                
                if isinstance(dato, (int, float)):
                    if dato >= 8:
                        celda.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    elif dato >= 6:
                        celda.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                    else:
                        celda.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            else:
                celda.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            celda.border = border
        
        ws.row_dimensions[fila].height = 60
    
    def generar_excel(self, ruta_salida):
        """Genera Excel con una hoja por materia."""
        wb = Workbook()
        wb.remove(wb.active)
        
        for materia in sorted(self.evaluaciones_por_materia.keys()):
            evaluaciones = self.evaluaciones_por_materia[materia]
            
            for evaluacion in evaluaciones:
                self.agregar_evaluacion_a_hoja(materia, evaluacion, wb)
        
        wb.save(ruta_salida)
        print(f"✓ Excel guardado: {ruta_salida}")
    
    def procesar_desde_api_classroom(self, materias_info, ruta_excel_salida="evaluaciones_completas.xlsx"):
        """
        Procesa todas las materias desde Google Classroom API.
        
        materias_info: Lista de dicts con keys:
            - "nombre": Nombre de la materia
            - "course_id": ID del curso en Classroom
            - "service": Servicio de Classroom API
            - "service_drive": Servicio de Drive API
        """
        print("\n" + "="*80)
        print(" 📊 CORRECTOR MASIVO - GOOGLE CLASSROOM API ")
        print("="*80)
        
        # Procesar cada materia
        total_evaluaciones = 0
        
        for i, materia_info in enumerate(materias_info, 1):
            nombre_materia = materia_info.get("nombre", "Materia desconocida")
            course_id = materia_info.get("course_id")
            service = materia_info.get("service")
            
            if not course_id or not service:
                print(f"\n[{i}/{len(materias_info)}] ⚠️  {nombre_materia} - SIN CREDENCIALES")
                continue
            
            print(f"\n[{i}/{len(materias_info)}] 📚 {nombre_materia}")
            
            try:
                # Obtener trabajos/actividades de Classroom
                trabajos_result = service.courses().courseWork().list(courseId=course_id).execute()
                trabajos = trabajos_result.get("courseWork", [])
                
                if not trabajos:
                    print(f"         └─ ⚠️  Sin actividades")
                    continue
                
                print(f"         ├─ {len(trabajos)} actividades detectadas")
                
                evaluaciones_materia = []
                
                for j, trabajo in enumerate(trabajos, 1):
                    titulo_trabajo = trabajo.get("title", "Actividad sin título")
                    work_id = trabajo.get("id")
                    
                    is_last = (j == len(trabajos))
                    prefix = "         └─" if is_last else "         ├─"
                    print(f"{prefix} 📝 '{titulo_trabajo}'")
                    
                    try:
                        # ✅ OBTENER LA CONSIGNA REAL DE LA ACTIVIDAD
                        consigna_texto = self.obtener_consigna_actividad(service, course_id, work_id)
                        
                        # Obtener alumnos de esta actividad (SIN FIELDS para obtener TODOS los datos)
                        alumnos_result = service.courses().courseWork().studentSubmissions().list(
                            courseId=course_id,
                            courseWorkId=work_id,
                            states=['TURNED_IN', 'CREATED', 'RETURNED']
                        ).execute()
                        
                        alumnos = alumnos_result.get("studentSubmissions", [])
                        
                        if not alumnos:
                            print(f"            └─ ⚠️  Sin entregas")
                            continue
                        
                        print(f"            ├─ {len(alumnos)} estudiante(s) encontrado(s)")
                        
                        # Procesar cada alumno
                        for alumno_submission in alumnos:
                            estado = alumno_submission.get("state", "UNKNOWN")
                            
                            # Obtener nombre del usuario
                            user_id = alumno_submission.get("userId")
                            nombre_alumno = self.obtener_nombre_alumno_real(user_id, service)
                            
                            print(f"            │  → {nombre_alumno}...", end=" ", flush=True)
                            
                            # ✅ DESCARGAR Y PROCESAR LA ENTREGA REAL
                            service_drive = materia_info.get("service_drive")
                            
                            # Obtener attachments de múltiples fuentes
                            attachments = alumno_submission.get("attachments", [])
                            
                            # Si no hay attachments directos, buscar en submissionHistory
                            if not attachments:
                                submission_history = alumno_submission.get("submissionHistory", [])
                                if submission_history and len(submission_history) > 0:
                                    attachments = submission_history[0].get("submission", {}).get("attachments", [])
                            
                            # Debugging
                            if not attachments:
                                print(f"[sin adjuntos]", end=" ", flush=True)
                            
                            entrega_texto = descargar_y_extraer_entrega(attachments, service_drive)
                            
                            if not entrega_texto or len(entrega_texto.strip()) < 10:
                                entrega_texto = ""
                            
                            evaluacion = self.evaluar_alumno(
                                nombre_alumno,
                                titulo_trabajo,
                                consigna_texto,
                                entrega_texto
                            )
                            
                            evaluaciones_materia.append(evaluacion)
                            print("✓")
                        
                        print(f"            └─ ✓ {len(alumnos)} evaluado(s)")
                        
                    except Exception as e:
                        error_msg = str(e)
                        # Extraer solo la parte importante del error
                        if "HttpError" in error_msg:
                            error_msg = error_msg.split("returned ")[1].split(".")[0] if "returned" in error_msg else "Error HTTP"
                        print(f"            ✗ Problema: {error_msg[:60]}")
                        continue
                
                self.evaluaciones_por_materia[nombre_materia] = evaluaciones_materia
                total_evaluaciones += len(evaluaciones_materia)
                
            except Exception as e:
                print(f"         ✗ Error al procesar: {e}")
        
        # Generar Excel
        print(f"\n[FASE 2] 📄 Generando Excel...")
        self.generar_excel(ruta_excel_salida)
        
        print(f"\n" + "="*80)
        print(f" ✅ PROCESO COMPLETADO")
        print(f" • Total de estudiantes evaluados: {total_evaluaciones}")
        print(f" • Materias: {len(materias_info)}")
        print(f" • Excel generado: {ruta_excel_salida}")
        print("="*80 + "\n")
        
        return total_evaluaciones


if __name__ == "__main__":
    print("Este módulo debe ser importado desde main.py con las credenciales de Classroom.")
