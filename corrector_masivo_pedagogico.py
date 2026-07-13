"""
CORRECTOR MASIVO CON LÓGICA PEDAGÓGICA PROFUNDA
Aplica la MISMA evaluación automática profunda que opción [0]:
- Análisis real de concordancia consigna-entrega
- Validación IA con Gemini (si está configurada)
- Extracción real de contenido (PDF, Docx, etc)
- Devoluciones empáticas personalizadas
- Todo con la misma profundidad que opción [0] pero para TODAS las materias
"""

import os
import sys
import json
import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from docx import Document
import PyPDF2


class CorrectorMasivoPedagogico:
    """Aplica evaluación pedagógica PROFUNDA a todas las entregas"""
    
    def __init__(self):
        self.evaluaciones = []
    
    def ejecutar_correccion_masiva_pedagogica(self, ruta_base="Correcciones_Classroom"):
        """
        FASE 2: Lee archivos descargados y genera evaluaciones PROFUNDAS.
        Usa la misma lógica que opción [0]: concordancia + Gemini + contexto.
        
        Args:
            ruta_base (str): Carpeta raíz con estructura Materia/TP/Alumno
            
        Returns:
            dict: {total_alumnos, evaluaciones_generadas}
        """
        print("[FASE 2/2] 📊 Evaluando entregas (ANÁLISIS PROFUNDO - Concordancia + Gemini)...\n")
        
        if not os.path.exists(ruta_base):
            print(f"❌ Carpeta {ruta_base} no existe")
            return {"total_alumnos": 0, "evaluaciones_generadas": 0}
        
        self.evaluaciones = []
        total_alumnos = 0
        
        # Iterar: Materia → TP → Alumno
        for materia_dir in sorted(os.listdir(ruta_base)):
            materia_path = os.path.join(ruta_base, materia_dir)
            if not os.path.isdir(materia_path):
                continue
            
            print(f"📚 Materia: {materia_dir}")
            
            for tp_dir in sorted(os.listdir(materia_path)):
                tp_path = os.path.join(materia_path, tp_dir)
                if not os.path.isdir(tp_path):
                    continue
                
                print(f"   📝 TP: {tp_dir}")
                
                # Leer consigna completa
                consigna = ""
                ruta_consigna = os.path.join(tp_path, "consigna_referencia.txt")
                if os.path.exists(ruta_consigna):
                    try:
                        with open(ruta_consigna, 'r', encoding='utf-8') as f:
                            consigna = f.read()
                    except:
                        pass
                
                # Iterar alumnos
                for alumno_dir in sorted(os.listdir(tp_path)):
                    alumno_path = os.path.join(tp_path, alumno_dir)
                    if not os.path.isdir(alumno_path):
                        continue
                    
                    total_alumnos += 1
                    
                    # EVALUAR: Lógica PROFUNDA (concordancia + Gemini)
                    evaluacion = self._evaluar_alumno_profundo(
                        materia=materia_dir,
                        tp=tp_dir,
                        alumno=alumno_dir,
                        ruta_entrega=alumno_path,
                        consigna=consigna
                    )
                    
                    self.evaluaciones.append(evaluacion)
                    
                    # Mostrar feedback de evaluación
                    estado_icon = "✅" if evaluacion["nota"] >= 7 else "⚠️" if evaluacion["nota"] >= 4 else "❌"
                    print(f"      {estado_icon} {alumno_dir}: {evaluacion['nota']}/10 ({evaluacion['estado_interno']})")
        
        # Generar Excel
        print("\n💾 Generando Excel con análisis profundo...")
        self._generar_excel(ruta_base)
        
        return {
            "total_alumnos": total_alumnos,
            "evaluaciones_generadas": len(self.evaluaciones)
        }
    
    def _evaluar_alumno_profundo(self, materia, tp, alumno, ruta_entrega, consigna):
        """
        Evalúa alumno usando la MISMA lógica que opción [0]:
        1. Extrae contenido REAL de archivos (PDF, Docx, etc)
        2. Valida con Gemini si corresponde a consigna
        3. Analiza concordancia real con consigna
        4. Genera nota según cobertura
        5. Crea devolución empática
        """
        
        # Buscar y extraer archivos de entrega
        contenido_texto = ""
        archivos_encontrados = []
        
        try:
            for archivo in os.listdir(ruta_entrega):
                if archivo in ["consigna_referencia.txt", "estado_descarga.txt", "debug_estructura.json"]:
                    continue
                
                ruta_archivo = os.path.join(ruta_entrega, archivo)
                
                # Extraer texto según tipo (mismo que opción [0])
                if archivo.endswith(".txt"):
                    try:
                        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                            contenido_texto += f.read() + "\n"
                        archivos_encontrados.append(archivo)
                    except:
                        pass
                
                elif archivo.endswith(".docx"):
                    try:
                        doc = Document(ruta_archivo)
                        contenido_texto += "\n".join([p.text for p in doc.paragraphs]) + "\n"
                        archivos_encontrados.append(archivo)
                    except:
                        pass
                
                elif archivo.endswith(".pdf"):
                    try:
                        with open(ruta_archivo, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                contenido_texto += page.extract_text() + "\n"
                        archivos_encontrados.append(archivo)
                    except:
                        pass
        
        except Exception as e:
            pass
        
        # VALIDACIÓN INICIAL: ¿Está vacía?
        contenido_limpio = contenido_texto.strip()
        
        if not archivos_encontrados or len(contenido_limpio) < 20:
            # Entrega vacía
            return {
                "materia": materia,
                "tp": tp,
                "alumno": alumno,
                "estado_interno": "Adeuda Entrega",
                "nota": 1,
                "motivo_correccion": "No entregó material adjunto.",
                "devolucion_alumno": f"No se ha recibido entrega para esta actividad. Por favor, sube tu trabajo en Classroom.",
                "fecha_correccion": datetime.datetime.now().strftime("%Y-%m-%d")
            }
        
        # ANÁLISIS PROFUNDO: Concordancia real
        print(f"         ⏳ Analizando contenido de {alumno}...", end=" ", flush=True)
        
        # Análisis de concordancia (IGUAL que opción [0])
        try:
            from main import (
                analizar_concordancia_consigna_entrega,
                generar_nota_desde_concordancia,
                _generar_feedback_personalizado,
                verificar_pertinencia_ia_rapida,
                detectar_no_pertinencia_entrega
            )
            
            # 1. Validar pertinencia con IA si disponible
            validacion_ia = verificar_pertinencia_ia_rapida(consigna, contenido_limpio, tp)
            if not validacion_ia.get("corresponde_a_la_consigna", True):
                justificacion_ia = validacion_ia.get("justificacion_breve", "No corresponde a la consigna.")
                print("❌ [No corresponde]")
                return {
                    "materia": materia,
                    "tp": tp,
                    "alumno": alumno,
                    "estado_interno": "Rehacer",
                    "nota": 1,
                    "motivo_correccion": f"Entrega no pertinente (validación IA). {justificacion_ia}",
                    "devolucion_alumno": "La entrega no corresponde de forma directa a la consigna del TP. Por favor, rehaz y vuelve a subir una resolución específica de la actividad solicitada.",
                    "fecha_correccion": datetime.datetime.now().strftime("%Y-%m-%d")
                }
            
            # 2. Detectar no pertinencia
            no_pertinente, justificacion = detectar_no_pertinencia_entrega(consigna, contenido_limpio, tp)
            if no_pertinente:
                print("⚠️ [No pertinente]")
                return {
                    "materia": materia,
                    "tp": tp,
                    "alumno": alumno,
                    "estado_interno": "Rehacer",
                    "nota": 1,
                    "motivo_correccion": f"Entrega no pertinente a la consigna. {justificacion}",
                    "devolucion_alumno": "La entrega adjunta no corresponde a la actividad solicitada o no desarrolla los temas de la consigna. Por favor, rehaz la entrega y vuelve a subir un archivo alineado al TP indicado.",
                    "fecha_correccion": datetime.datetime.now().strftime("%Y-%m-%d")
                }
            
            # 3. Análisis de concordancia PROFUNDO
            concordancia_score, temas_cubiertos, temas_faltantes, obs_concordancia = \
                analizar_concordancia_consigna_entrega(consigna, contenido_limpio, tp)
            
            # 4. Generar nota
            largo_entrega = len(contenido_limpio.split())
            nota = generar_nota_desde_concordancia(concordancia_score, largo_entrega, temas_cubiertos, temas_faltantes)
            
            # 5. Generar devolución empática personalizada
            feedback = _generar_feedback_personalizado(
                tp, nota, concordancia_score, temas_cubiertos, temas_faltantes, 
                consigna, obs_concordancia
            )
            
            # 6. Determinar estado
            if nota < 4:
                estado = "No Aprobado"
            elif nota < 7:
                estado = "Aprobado con Deficiencias"
            else:
                estado = "Aprobado"
            
            print("✅ [Analizado]")
            
            return {
                "materia": materia,
                "tp": tp,
                "alumno": alumno,
                "estado_interno": estado,
                "nota": nota,
                "motivo_correccion": f"Análisis de concordancia: {concordancia_score*100:.0f}% cobertura. {obs_concordancia}",
                "devolucion_alumno": feedback,
                "fecha_correccion": datetime.datetime.now().strftime("%Y-%m-%d")
            }
        
        except ImportError as e:
            # Fallback si no se pueden importar funciones
            print("⚠️ [Fallback simple]")
            
            # Análisis simple como fallback
            consigna_lower = consigna.lower()
            contenido_lower = contenido_limpio.lower()
            palabras_clave = [p for p in consigna_lower.split() if len(p) > 4 and p.isalnum()]
            coincidencias = sum(1 for p in palabras_clave if p in contenido_lower)
            cobertura = (coincidencias / len(palabras_clave)) * 100 if palabras_clave else 0
            palabras_entrega = len(contenido_limpio.split())
            
            if palabras_entrega < 50:
                nota = 3
                estado = "Incompleto"
            elif cobertura >= 80:
                nota = 9
                estado = "Excelente"
            elif cobertura >= 60:
                nota = 8
                estado = "Bueno"
            elif cobertura >= 40:
                nota = 6
                estado = "Aceptable"
            else:
                nota = 3
                estado = "Deficiente"
            
            return {
                "materia": materia,
                "tp": tp,
                "alumno": alumno,
                "estado_interno": estado,
                "nota": nota,
                "motivo_correccion": f"Análisis básico: {cobertura:.0f}% cobertura ({palabras_entrega} palabras)",
                "devolucion_alumno": f"Tu entrega ha sido evaluada. Por favor revisa los comentarios en Classroom para más detalles.",
                "fecha_correccion": datetime.datetime.now().strftime("%Y-%m-%d")
            }
    
    def _generar_excel(self, ruta_base="Correcciones_Classroom"):
        """
        Genera Excel profesional con evaluaciones pedagógicas profundas.
        Columnas: Materia | TP | Alumno | Estado | Nota | Motivo | Devolución
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluaciones Profundas"
        
        # ENCABEZADOS
        encabezados = [
            "Materia",
            "TP",
            "Alumno",
            "Estado",
            "Nota",
            "Motivo Corrección",
            "Devolución Pedagógica"
        ]
        ws.append(encabezados)
        
        # Estilos encabezado (profesional)
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        for celda in ws[1]:
            celda.fill = header_fill
            celda.font = header_font
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Agregar datos
        for eval_data in self.evaluaciones:
            ws.append([
                eval_data["materia"],
                eval_data["tp"],
                eval_data["alumno"],
                eval_data["estado_interno"],
                eval_data["nota"],
                eval_data["motivo_correccion"],
                eval_data["devolucion_alumno"]
            ])
        
        # Estilos celdas de datos
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=2):
            nota = row[4].value
            
            # Color según nota (escala profesional)
            if nota >= 9:
                fill_color = "92D050"  # Verde claro excelente
            elif nota >= 8:
                fill_color = "C6EFCE"  # Verde bueno
            elif nota >= 7:
                fill_color = "FFEB9C"  # Amarillo claro aceptable
            elif nota >= 6:
                fill_color = "FFD966"  # Amarillo deficiente
            elif nota >= 5:
                fill_color = "FFC7CE"  # Rojo claro grave
            else:
                fill_color = "FF6B6B"  # Rojo crítico
            
            for celda in row:
                celda.border = thin_border
                celda.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                celda.alignment = Alignment(wrap_text=True, vertical="top")
        
        # Ajustar ancho columnas
        ws.column_dimensions['A'].width = 22
        ws.column_dimensions['B'].width = 32
        ws.column_dimensions['C'].width = 28
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 8
        ws.column_dimensions['F'].width = 45
        ws.column_dimensions['G'].width = 60
        
        # Altura fila
        ws.row_dimensions[1].height = 30
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            ws.row_dimensions[row[0].row].height = 85
        
        # Guardar
        ruta_excel = os.path.join(ruta_base, "evaluaciones_pedagogicas.xlsx")
        wb.save(ruta_excel)
        print(f"✅ Excel guardado: {ruta_excel}")
        
        return ruta_excel


# ─────────────────────────────────────────
# ENTRY POINT: Función para usar en main.py
# ─────────────────────────────────────────

def iniciar_correccion_masiva_pedagogica(materias_info):
    """
    Ejecuta descarga + evaluación pedagógica PROFUNDA.
    Usa la MISMA lógica que opción [0]: concordancia + Gemini + contexto.
    
    Args:
        materias_info (list): Lista de dicts con datos de materias de API
    """
    print("\n" + "="*70)
    print("🚀 CORRECCIÓN MASIVA - LÓGICA PEDAGÓGICA PROFUNDA (Opción [0] en Masivo)")
    print("="*70 + "\n")
    print("⏱️ ADVERTENCIA: Este análisis es profundo y puede tardar varios minutos.")
    print("Se ejecutarán:")
    print("  • Extracción real de contenido (PDF, Docx, Txt)")
    print("  • Validación con Gemini (si GEMINI_API_KEY está configurada)")
    print("  • Análisis de concordancia consigna-entrega")
    print("  • Devoluciones empáticas personalizadas\n")
    
    # FASE 1: Descargar
    print("[FASE 1/2] 📥 Descargando entregas...\n")
    try:
        from descargar_entregas_classroom import descargar_todas_las_entregas
        
        total_alumnos, total_archivos = descargar_todas_las_entregas(
            materias_info,
            ruta_base="Correcciones_Classroom",
            debug=False
        )
        
        print(f"\n✅ Descarga completada:")
        print(f"   - Alumnos: {total_alumnos}")
        print(f"   - Archivos: {total_archivos}")
    
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # FASE 2: Evaluar con lógica pedagógica profunda
    print("\n" + "="*70)
    corrector = CorrectorMasivoPedagogico()
    resultado = corrector.ejecutar_correccion_masiva_pedagogica("Correcciones_Classroom")
    
    print(f"\n✅ Evaluación completada:")
    print(f"   - Alumnos evaluados: {resultado['evaluaciones_generadas']}")
    
    # Mostrar resumen
    print("\n" + "="*70)
    print("📊 RESUMEN EVALUACIONES (ANÁLISIS PROFUNDO)")
    print("="*70)
    
    # Estadísticas
    notas = [e["nota"] for e in corrector.evaluaciones]
    if notas:
        promedio = sum(notas) / len(notas)
        aprobados = sum(1 for n in notas if n >= 6)
        desaprobados = len(notas) - aprobados
        excelentes = sum(1 for n in notas if n >= 9)
        
        print(f"\nPromedio general: {promedio:.2f}/10")
        print(f"Excelentes (≥9): {excelentes}")
        print(f"Aprobados (≥6): {aprobados}")
        print(f"Desaprobados (<6): {desaprobados}")
    
    # Mostrar primeros 5 alumnos
    print("\nMuestras de evaluaciones:")
    for eval_data in corrector.evaluaciones[:5]:
        print(f"\n{eval_data['alumno']} ({eval_data['tp']}):")
        print(f"  Nota: {eval_data['nota']}/10 | Estado: {eval_data['estado_interno']}")
        print(f"  Motivo: {eval_data['motivo_correccion'][:70]}...")
        print(f"  Devolución: {eval_data['devolucion_alumno'][:90]}...")
    
    if len(corrector.evaluaciones) > 5:
        print(f"\n... y {len(corrector.evaluaciones) - 5} alumnos más")
    
    print("\n" + "="*70)
    print("✅ Corrección masiva profunda completada")
    print("="*70 + "\n")
