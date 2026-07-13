"""
DESCARGAR TODAS LAS ENTREGAS DE CLASSROOM A CARPETAS LOCALES ORGANIZADAS
Estructura: Correcciones_Classroom/[Materia]/[Actividad]/[Alumno]/archivo.ext
"""

import os
import io
from pathlib import Path
from docx import Document
from googleapiclient.http import MediaIoBaseDownload

try:
    import PyPDF2
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False


def obtener_nombre_alumno_real(user_id, service):
    """Obtiene el nombre real del alumno desde Google Classroom."""
    try:
        perfil = service.userProfiles().get(userId=user_id).execute()
        nombre = perfil.get("name", {}).get("fullName", f"Usuario {user_id}")
        return nombre
    except Exception:
        return f"Usuario {user_id}"


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
            
    except Exception:
        return None


def guardar_archivo(contenido, ruta_archivo):
    """Guarda contenido en archivo, creando carpetas si es necesario."""
    try:
        ruta_dir = os.path.dirname(ruta_archivo)
        if ruta_dir and not os.path.exists(ruta_dir):
            os.makedirs(ruta_dir, exist_ok=True)
        
        with open(ruta_archivo, 'wb') as f:
            f.write(contenido)
        return True
    except Exception as e:
        print(f"Error al guardar {ruta_archivo}: {e}")
        return False


def descargar_todas_las_entregas(materias_info, ruta_base="Correcciones_Classroom", debug=False):
    """
    Descarga TODAS las entregas de Classroom a carpetas locales organizadas.
    
    Estructura creada:
        Correcciones_Classroom/
            [Materia]/
                [Actividad]/
                    [Alumno]/
                        archivo1.docx
                        archivo2.pdf
                        consigna_referencia.txt
                        estado_descarga.txt
    
    Args:
        materias_info: Información de materias con credenciales
        ruta_base: Ruta base para guardar entregas
        debug: Si True, muestra estructura JSON de submisiones
    """
    print("\n" + "=" * 80)
    print(" 📥 DESCARGANDO ENTREGAS DE CLASSROOM A CARPETAS LOCALES ")
    print("=" * 80)
    
    total_archivos = 0
    total_alumnos = 0
    
    for i, materia_info in enumerate(materias_info, 1):
        nombre_materia = materia_info.get("nombre", "Materia desconocida")
        course_id = materia_info.get("course_id")
        service = materia_info.get("service")
        service_drive = materia_info.get("service_drive")
        
        if not course_id or not service:
            continue
        
        print(f"\n[{i}/{len(materias_info)}] 📚 {nombre_materia}")
        
        try:
            # Obtener actividades
            trabajos_result = service.courses().courseWork().list(courseId=course_id).execute()
            trabajos = trabajos_result.get("courseWork", [])
            
            if not trabajos:
                print(f"         └─ ⚠️  Sin actividades")
                continue
            
            print(f"         ├─ {len(trabajos)} actividades")
            
            for j, trabajo in enumerate(trabajos, 1):
                titulo_trabajo = trabajo.get("title", "Actividad sin título")
                work_id = trabajo.get("id")
                descripcion = trabajo.get("description", "")
                
                is_last = (j == len(trabajos))
                prefix = "         └─" if is_last else "         ├─"
                print(f"{prefix} 📝 '{titulo_trabajo}'")
                
                try:
                    # Obtener alumnos de esta actividad
                    alumnos_result = service.courses().courseWork().studentSubmissions().list(
                        courseId=course_id,
                        courseWorkId=work_id,
                        states=['TURNED_IN', 'CREATED', 'RETURNED']
                    ).execute()
                    
                    alumnos = alumnos_result.get("studentSubmissions", [])
                    
                    if not alumnos:
                        print(f"            └─ ⚠️  Sin entregas")
                        continue
                    
                    print(f"            ├─ {len(alumnos)} estudiante(s)")
                    
                    # Procesar cada alumno
                    for alumno_submission in alumnos:
                        user_id = alumno_submission.get("userId")
                        nombre_alumno = obtener_nombre_alumno_real(user_id, service)
                        
                        print(f"            │  → {nombre_alumno}...", end=" ", flush=True)
                        
                        # Crear estructura de carpeta
                        # Normalizar nombres para carpetas
                        materia_dir = nombre_materia.replace("/", "-").replace("\\", "-")[:50]
                        actividad_dir = titulo_trabajo.replace("/", "-").replace("\\", "-")[:50]
                        alumno_dir = nombre_alumno.replace("/", "-").replace("\\", "-")[:50]
                        
                        ruta_alumno = os.path.join(ruta_base, materia_dir, actividad_dir, alumno_dir)
                        os.makedirs(ruta_alumno, exist_ok=True)
                        
                        # Guardar consigna (una sola vez por actividad)
                        ruta_consigna = os.path.join(ruta_base, materia_dir, actividad_dir, "consigna_referencia.txt")
                        if descripcion and not os.path.exists(ruta_consigna):
                            guardar_archivo(descripcion.encode('utf-8'), ruta_consigna)
                        
                        # Descargar adjuntos del alumno
                        # ✅ UBICACIÓN CORRECTA: assignmentSubmission.attachments
                        attachments = []
                        
                        # Ubicación 1: assignmentSubmission (PRINCIPAL)
                        assignment_submission = alumno_submission.get("assignmentSubmission", {})
                        if isinstance(assignment_submission, dict):
                            attachments = assignment_submission.get("attachments", [])
                        
                        # Ubicación 2: submissionHistory.assignmentSubmission (fallback)
                        if not attachments:
                            submission_history = alumno_submission.get("submissionHistory", [])
                            if submission_history:
                                for history_item in submission_history:
                                    if isinstance(history_item, dict):
                                        assignment_sub = history_item.get("assignmentSubmission", {})
                                        if assignment_sub and isinstance(assignment_sub, dict):
                                            attachments = assignment_sub.get("attachments", [])
                                            if attachments:
                                                break
                        
                        archivos_descargados = 0
                        if not attachments:
                            # Sin adjuntos detectados
                            nota_estado = f"Sin adjuntos en esta entrega\nEstado: {alumno_submission.get('state', 'UNKNOWN')}\nBúsqueda realizada en: assignmentSubmission.attachments"
                            guardar_archivo(nota_estado.encode('utf-8'), os.path.join(ruta_alumno, "estado_descarga.txt"))
                        
                        for adj in attachments[:10]:
                            drive_file = _obtener_drive_file_desde_attachment(adj)
                            if not drive_file:
                                continue
                            
                            file_id = drive_file.get("id")
                            file_name = drive_file.get("title", "archivo")
                            
                            if not file_id:
                                continue
                            
                            try:
                                metadata = service_drive.files().get(fileId=file_id, fields="mimeType,name").execute()
                                mime_type = metadata.get("mimeType", "")
                                file_name = metadata.get("name", file_name)
                            except Exception:
                                mime_type = ""
                            
                            contenido = descargar_adjunto_drive(service_drive, file_id, mime_type)
                            if not contenido:
                                continue
                            
                            # Guardar archivo
                            ruta_archivo = os.path.join(ruta_alumno, file_name)
                            if guardar_archivo(contenido, ruta_archivo):
                                archivos_descargados += 1
                                total_archivos += 1
                        
                        # Guardar estado
                        estado = f"Archivos descargados: {archivos_descargados}\nEstado: {'TURNED_IN' if alumno_submission.get('state') == 'TURNED_IN' else alumno_submission.get('state', 'UNKNOWN')}"
                        guardar_archivo(estado.encode('utf-8'), os.path.join(ruta_alumno, "estado_descarga.txt"))
                        
                        # DEBUG: Guardar estructura JSON si está habilitado
                        if debug and archivos_descargados == 0:
                            import json
                            debug_info = {
                                "submission_keys": list(alumno_submission.keys()),
                                "has_attachments": "attachments" in alumno_submission,
                                "has_submissionHistory": "submissionHistory" in alumno_submission,
                                "state": alumno_submission.get("state"),
                            }
                            if "submissionHistory" in alumno_submission:
                                hist = alumno_submission.get("submissionHistory", [])
                                debug_info["submissionHistory_count"] = len(hist)
                                if hist:
                                    debug_info["first_history_keys"] = list(hist[0].keys())
                            
                            guardar_archivo(
                                json.dumps(debug_info, indent=2, ensure_ascii=False).encode('utf-8'),
                                os.path.join(ruta_alumno, "debug_estructura.json")
                            )
                        
                        print(f"[{archivos_descargados} arch.]")
                        total_alumnos += 1
                    
                    print(f"            └─ ✓ {len(alumnos)} completado(s)")
                    
                except Exception as e:
                    print(f"            ✗ Error: {str(e)[:50]}")
        
        except Exception as e:
            print(f"         ✗ Error al procesar: {str(e)[:50]}")
    
    print(f"\n" + "=" * 80)
    print(f" ✅ DESCARGA COMPLETADA")
    print(f" • Total de alumnos procesados: {total_alumnos}")
    print(f" • Total de archivos descargados: {total_archivos}")
    print(f" • Ubicación: {os.path.abspath(ruta_base)}")
    print("=" * 80 + "\n")
    
    return total_alumnos, total_archivos


if __name__ == "__main__":
    print("Este módulo debe ser importado desde main.py o aux_correccion_masiva.py")
