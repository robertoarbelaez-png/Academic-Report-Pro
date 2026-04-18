from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import uuid
from datetime import datetime
import re
import requests
import html

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== CONFIGURACIÓN DE GROQ ==========
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

print("=" * 50)
print("🚀 INICIANDO APLICACIÓN (VERSIÓN CORREGIDA)")
print(f"🔑 Groq API Key cargada: {'SÍ ✅' if GROQ_API_KEY else 'NO ❌'}")
print("=" * 50)

# ========== NORMAS ACADÉMICAS ==========
NORMAS_CONFIG = {
    'apa7': {'nombre': 'APA 7ª Edición', 'margen_superior': 72, 'margen_inferior': 72,
             'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman', 
             'tamaño': 12, 'interlineado': 24, 'sangria': 36},
    'apa6': {'nombre': 'APA 6ª Edición', 'margen_superior': 72, 'margen_inferior': 72,
             'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
             'tamaño': 12, 'interlineado': 24, 'sangria': 36},
    'icontec': {'nombre': 'ICONTEC (Colombia)', 'margen_superior': 85, 'margen_inferior': 85,
                'margen_izquierdo': 113, 'margen_derecho': 85, 'fuente': 'Helvetica',
                'tamaño': 12, 'interlineado': 18, 'sangria': 0},
    'vancouver': {'nombre': 'Vancouver', 'margen_superior': 72, 'margen_inferior': 72,
                  'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
                  'tamaño': 11, 'interlineado': 16, 'sangria': 0},
    'chicago': {'nombre': 'Chicago', 'margen_superior': 72, 'margen_inferior': 72,
                'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
                'tamaño': 12, 'interlineado': 18, 'sangria': 36},
    'harvard': {'nombre': 'Harvard', 'margen_superior': 72, 'margen_inferior': 72,
                'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
                'tamaño': 12, 'interlineado': 18, 'sangria': 36},
    'mla': {'nombre': 'MLA 9ª Edición', 'margen_superior': 72, 'margen_inferior': 72,
            'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
            'tamaño': 12, 'interlineado': 24, 'sangria': 36},
    'ieee': {'nombre': 'IEEE', 'margen_superior': 72, 'margen_inferior': 72,
             'margen_izquierdo': 72, 'margen_derecho': 72, 'fuente': 'Times-Roman',
             'tamaño': 10, 'interlineado': 12, 'sangria': 0}
}

def limpiar_texto(texto):
    """Limpia caracteres especiales y prepara texto para ReportLab"""
    if not texto:
        return ""
    
    try:
        if isinstance(texto, bytes):
            texto = texto.decode('utf-8')
        texto = html.escape(texto)
    except:
        pass
    
    # Reemplazar caracteres problemáticos
    reemplazos = {
        '\xa0': ' ', '\xad': '-', '\u2013': '-', '\u2014': '-',
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2026': '...',
        '$<br/>': '', '<br/>2': '',
    }
    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)
    
    texto = re.sub(r'\n{3,}', '<br/><br/>', texto)
    
    # CORRECCIONES CRÍTICAS
    texto = texto.replace('INFORMÉ', 'INFORME')
    texto = texto.replace('Conclusions', 'CONCLUSIONES')
    texto = texto.replace('CONCLUSIONS', 'CONCLUSIONES')
    
    return texto

def generar_contenido_local_generico(tipo, tema):
    """Contenido de respaldo GENÉRICO (se adapta al tema del usuario)"""
    
    tema_limpio = tema if tema else "el tema de investigación"
    
    contenidos = {
        'introduccion': f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia en el contexto actual. Este análisis busca comprender los principales factores que inciden en esta área de estudio.<br/><br/>
La investigación se justifica por la necesidad de generar evidencia empírica que contribuya al conocimiento existente y sirva como base para futuros estudios.<br/><br/>
Las preguntas que guían esta investigación son: ¿Cuáles son los principales aspectos relacionados con {tema_limpio}? ¿Qué implicaciones tienen estos hallazgos? ¿Qué estrategias pueden implementarse para abordar los desafíos identificados?""",
        
        'objetivos': f"""<b>Objetivo General</b><br/><br/>Analizar los principales aspectos relacionados con {tema_limpio} en el contexto actual.<br/><br/><br/>
<b>Objetivos Específicos</b><br/><br/>
1. Identificar los factores clave asociados a {tema_limpio}.<br/><br/>
2. Describir las principales características y tendencias actuales.<br/><br/>
3. Analizar las implicaciones prácticas y teóricas de los hallazgos.<br/><br/>
4. Proponer recomendaciones basadas en el análisis realizado.""",
        
        'marco_teorico': f"""<b>Conceptos clave</b><br/><br/>
Para comprender adecuadamente {tema_limpio}, es necesario definir los conceptos fundamentales que lo sustentan. Diversos autores han contribuido al desarrollo teórico de esta área.<br/><br/>
<b>Bases teóricas</b><br/><br/>
Las teorías existentes proporcionan un marco conceptual sólido para el análisis de {tema_limpio}. La literatura especializada ofrece múltiples perspectivas que enriquecen la comprensión del fenómeno.<br/><br/>
<b>Estado del arte</b><br/><br/>
Investigaciones recientes han profundizado en aspectos específicos de {tema_limpio}, identificando tendencias y áreas de oportunidad para futuros estudios.""",
        
        'metodologia': f"""<b>Enfoque</b><br/><br/>La investigación adopta un enfoque mixto, combinando elementos cualitativos y cuantitativos.<br/><br/>
<b>Población y muestra</b><br/><br/>La población de estudio está conformada por actores relevantes en el área de {tema_limpio}. Se seleccionó una muestra representativa mediante técnicas de muestreo apropiadas.<br/><br/>
<b>Instrumentos</b><br/><br/>Se utilizaron cuestionarios estructurados, entrevistas semiestructuradas y revisión documental como principales instrumentos de recolección de datos.<br/><br/>
<b>Procedimiento</b><br/><br/>El estudio se desarrolló en tres fases: diseño y validación de instrumentos, recolección de datos, y análisis e interpretación de resultados.""",
        
        'desarrollo': f"""<b>Resultados obtenidos</b><br/><br/>
Los resultados del análisis muestran tendencias significativas relacionadas con {tema_limpio}. Los datos recopilados permiten identificar patrones y relaciones relevantes.<br/><br/>
<b>Análisis de resultados</b><br/><br/>
Los hallazgos indican que existen múltiples factores que inciden en {tema_limpio}. Se observan variaciones según el contexto y las condiciones específicas de cada caso.<br/><br/>
<b>Discusión</b><br/><br/>
Los resultados se alinean parcialmente con lo reportado en la literatura especializada, confirmando hallazgos previos y aportando nuevas perspectivas al conocimiento existente.""",
        
        'conclusiones': f"""1. El análisis realizado permite identificar los principales aspectos relacionados con {tema_limpio}.<br/><br/>
2. Los hallazgos confirman la importancia de abordar este tema desde una perspectiva integral.<br/><br/>
3. Se requiere mayor investigación para profundizar en aspectos específicos no cubiertos en este estudio.<br/><br/>
4. Las recomendaciones propuestas constituyen una base para futuras intervenciones.<br/><br/>
5. Este estudio contribuye al conocimiento existente y abre líneas de investigación adicionales.""",
        
        'recomendaciones': f"""<b>Para la institución</b><br/><br/>
1. Fortalecer las líneas de investigación relacionadas con {tema_limpio}.<br/><br/>
<b>Para los profesionales</b><br/><br/>
2. Aplicar los hallazgos en contextos prácticos relevantes.<br/><br/>
<b>Para futuros estudios</b><br/><br/>
3. Ampliar la muestra y el alcance geográfico para generalizar los resultados."""
    }
    return contenidos.get(tipo, "Contenido en desarrollo.")

def obtener_referencias(tema, referencias_ia=None, referencias_manuales=None, modo_referencias="auto", norma="apa7"):
    """Obtiene referencias según el modo seleccionado y el tema del usuario"""
    
    if modo_referencias == "manual" and referencias_manuales:
        refs = [r.strip() for r in referencias_manuales.split('\n') if r.strip()]
        return refs if refs else ["Referencia no especificada"]
    elif modo_referencias == "mixto":
        refs = []
        if referencias_manuales:
            refs.extend([r.strip() for r in referencias_manuales.split('\n') if r.strip()])
        if referencias_ia:
            refs.extend(referencias_ia)
        return list(dict.fromkeys(refs))[:10]
    else:
        if referencias_ia:
            return referencias_ia[:8]
        
        # REFERENCIAS ESPECÍFICAS POR CATEGORÍA DE TEMA
        tema_lower = tema.lower() if tema else ""
        
        # Tecnología / Digital / Agro
        if "tecnología" in tema_lower or "digital" in tema_lower or "agro" in tema_lower or "transformación" in tema_lower:
            return [
                "Bharadwaj, A. (2000). A resource-based perspective on information technology capability and firm performance. MIS Quarterly, 24(1), 169-196.",
                "Kamilaris, A., et al. (2019). A review on the practice of big data analysis in agriculture. Computers and Electronics in Agriculture, 143, 23-37.",
                "Wolfert, S., et al. (2017). Big data in smart farming. Agricultural Systems, 153, 69-80.",
                "Rogers, E. M. (2003). Diffusion of innovations (5th ed.). Free Press.",
                "Castells, M. (2010). The rise of the network society (2nd ed.). Wiley-Blackwell."
            ]
        # Educación
        elif "educación" in tema_lower or "aprendizaje" in tema_lower or "pedagogía" in tema_lower:
            return [
                "Siemens, G. (2005). Connectivism: A learning theory for the digital age. International Journal of Instructional Technology and Distance Learning, 2(1), 3-10.",
                "Coll, C. (2018). Psicología de la educación virtual. UOC.",
                "García Aretio, L. (2022). Educación a distancia y virtual. UNED.",
                "Area Moreira, M. (2021). La integración de las TIC en educación. Octaedro.",
                "Pérez Gómez, Á. I. (2021). La educación en la sociedad digital. Morata."
            ]
        # Salud / Medicina
        elif "salud" in tema_lower or "medicina" in tema_lower or "médico" in tema_lower:
            return [
                "Topol, E. J. (2019). Deep medicine: How artificial intelligence can make healthcare human again. Basic Books.",
                "Mesko, B. (2017). The role of artificial intelligence in precision medicine. Expert Review of Precision Medicine and Drug Development, 2(5), 239-241.",
                "Jiang, F., et al. (2017). Artificial intelligence in healthcare: past, present and future. Stroke and Vascular Neurology, 2(4), 230-243.",
                "Esteva, A., et al. (2019). A guide to deep learning in healthcare. Nature Medicine, 25(1), 24-29."
            ]
        # Referencias genéricas (cuando no se detecta categoría)
        else:
            return [
                "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
                "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla.",
                "Sabino, C. A. (2014). El proceso de investigación. Episteme.",
                "Taylor, S. J., & Bogdan, R. (2016). Introducción a los métodos cualitativos. Paidós."
            ]

# ========== GENERADOR DE PDF ==========
class GeneradorPDF:
    def __init__(self):
        pass
    
    def crear_estilos(self, config_norma):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TextoJustificado', parent=styles['Normal'],
            alignment=TA_JUSTIFY, fontSize=config_norma['tamaño'],
            fontName=config_norma['fuente'], spaceAfter=12, 
            leading=config_norma['interlineado'],
            leftIndent=config_norma['sangria']))
        styles.add(ParagraphStyle(name='Titulo1', parent=styles['Heading1'],
            fontSize=config_norma['tamaño'] + 2, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a365d'), spaceBefore=24, spaceAfter=16))
        styles.add(ParagraphStyle(name='TituloPortada', parent=styles['Title'],
            fontSize=22, alignment=TA_CENTER, spaceAfter=20,
            textColor=colors.HexColor('#1a365d')))
        return styles
    
    def generar_pdf(self, datos_usuario, opciones, secciones_ia=None, referencias_ia=None):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        norma = datos_usuario.get('norma', 'apa7')
        modo_referencias = datos_usuario.get('modo_referencias', 'auto')
        referencias_manuales = datos_usuario.get('referencias_manuales', '')
        
        config_norma = NORMAS_CONFIG.get(norma, NORMAS_CONFIG['apa7'])
        print(f"📏 Aplicando norma: {config_norma['nombre']}")
        
        if secciones_ia and isinstance(secciones_ia, dict):
            introduccion = limpiar_texto(secciones_ia.get('introduccion', ''))
            objetivos = limpiar_texto(secciones_ia.get('objetivos', ''))
            marco_teorico = limpiar_texto(secciones_ia.get('marco_teorico', ''))
            metodologia = limpiar_texto(secciones_ia.get('metodologia', ''))
            desarrollo = limpiar_texto(secciones_ia.get('desarrollo', ''))
            conclusiones = limpiar_texto(secciones_ia.get('conclusiones', ''))
            recomendaciones = limpiar_texto(secciones_ia.get('recomendaciones', ''))
            print("✅ Usando secciones generadas por IA")
        else:
            introduccion = generar_contenido_local_generico('introduccion', tema)
            objetivos = generar_contenido_local_generico('objetivos', tema)
            marco_teorico = generar_contenido_local_generico('marco_teorico', tema)
            metodologia = generar_contenido_local_generico('metodologia', tema)
            desarrollo = generar_contenido_local_generico('desarrollo', tema)
            conclusiones = generar_contenido_local_generico('conclusiones', tema)
            recomendaciones = generar_contenido_local_generico('recomendaciones', tema)
            print("⚠️ Usando contenido local genérico")
        
        referencias = obtener_referencias(tema, referencias_ia, referencias_manuales, modo_referencias, norma)
        
        filename = f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.pdf"
        filepath = os.path.join('informes_generados', filename)
        styles = self.crear_estilos(config_norma)
        
        doc = SimpleDocTemplate(filepath, 
            pagesize=letter,
            rightMargin=config_norma['margen_derecho'],
            leftMargin=config_norma['margen_izquierdo'],
            topMargin=config_norma['margen_superior'],
            bottomMargin=config_norma['margen_inferior'])
        
        story = []
        
        # PORTADA
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("INFORME ACADÉMICO", styles['TituloPortada']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(tema.upper(), styles['TextoJustificado']))
        story.append(Spacer(1, 1.2*inch))
        story.append(Paragraph(f"<b>Presentado por:</b> {nombre}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Asignatura:</b> {asignatura}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Docente:</b> {profesor}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Institución:</b> {institucion}", styles['TextoJustificado']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {fecha_entrega}", styles['TextoJustificado']))
        story.append(Paragraph(f"<b>Norma aplicada:</b> {config_norma['nombre']}", styles['TextoJustificado']))
        story.append(PageBreak())
        
        # ÍNDICE
        story.append(Paragraph("ÍNDICE", styles['Titulo1']))
        indices = ["1. INTRODUCCIÓN", "2. OBJETIVOS", "3. MARCO TEÓRICO", "4. METODOLOGÍA",
                   "5. DESARROLLO", "6. CONCLUSIONES", "7. REFERENCIAS"]
        for idx in indices:
            story.append(Paragraph(f"• {idx}", styles['TextoJustificado']))
        story.append(PageBreak())
        
        # SECCIONES
        story.append(Paragraph("1. INTRODUCCIÓN", styles['Titulo1']))
        story.append(Paragraph(introduccion, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("2. OBJETIVOS", styles['Titulo1']))
        story.append(Paragraph(objetivos, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("3. MARCO TEÓRICO", styles['Titulo1']))
        story.append(Paragraph(marco_teorico, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("4. METODOLOGÍA", styles['Titulo1']))
        story.append(Paragraph(metodologia, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("5. DESARROLLO", styles['Titulo1']))
        story.append(Paragraph(desarrollo, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("6. CONCLUSIONES", styles['Titulo1']))
        story.append(Paragraph(conclusiones, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("7. RECOMENDACIONES", styles['Titulo1']))
        story.append(Paragraph(recomendaciones, styles['TextoJustificado']))
        story.append(PageBreak())
        
        story.append(Paragraph("8. REFERENCIAS", styles['Titulo1']))
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {ref}", styles['TextoJustificado']))
            story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        print(f"✅ PDF generado: {filename}")
        return filename, filepath

generador = GeneradorPDF()

# ========== RUTAS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        modo = datos.get('modo', 'auto')
        tema = datos.get('tema', '')
        texto_auto = datos.get('texto_completo', '') if modo in ['auto', 'rapido'] else ''
        modo_referencias = datos.get('modo_referencias', 'auto')
        referencias_manuales = datos.get('referencias_manuales', '')
        
        if modo == 'rapido' and texto_auto:
            tema = texto_auto
        
        if not tema or len(tema) < 3:
            return jsonify({'success': False, 'error': 'Por favor ingresa un tema válido'}), 400
        
        opciones = {'incluir_recomendaciones': True}
        
        secciones_ia = None
        referencias_ia = None
        
        if GROQ_API_KEY and tema:
            try:
                prompt = f"""Genera un informe académico completo sobre: "{tema}"

Escribe estas secciones:

**INTRODUCCIÓN** (Contexto, problema, justificación)

**OBJETIVOS**
**Objetivo General:** (1)
**Objetivos Específicos:** (4)

**MARCO TEÓRICO** (Conceptos clave, autores, citas)

**METODOLOGÍA** (Enfoque, muestra, instrumentos, procedimiento)

**DESARROLLO** (Resultados, análisis, discusión)

**CONCLUSIONES** (5 puntos)

**RECOMENDACIONES** (3-4 puntos)

Usa español. Usa CONCLUSIONES (nunca Conclusions)."""
                
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                data = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 6000
                }
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    resultado = response.json()
                    contenido = resultado['choices'][0]['message']['content']
                    contenido = limpiar_texto(contenido)
                    
                    secciones_ia = {
                        'introduccion': re.search(r'\*\*INTRODUCCIÓN\*\*:?(.*?)(?=\*\*OBJETIVOS|\*\*MARCO|\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*INTRODUCCIÓN\*\*:?(.*?)(?=\*\*OBJETIVOS|\*\*MARCO|\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'objetivos': re.search(r'\*\*OBJETIVOS\*\*:?(.*?)(?=\*\*MARCO|\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*OBJETIVOS\*\*:?(.*?)(?=\*\*MARCO|\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'marco_teorico': re.search(r'\*\*MARCO TEÓRICO\*\*:?(.*?)(?=\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*MARCO TEÓRICO\*\*:?(.*?)(?=\*\*METODOLOGÍA|\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'metodologia': re.search(r'\*\*METODOLOGÍA\*\*:?(.*?)(?=\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*METODOLOGÍA\*\*:?(.*?)(?=\*\*DESARROLLO|\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'desarrollo': re.search(r'\*\*DESARROLLO\*\*:?(.*?)(?=\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*DESARROLLO\*\*:?(.*?)(?=\*\*CONCLUSIONES|\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'conclusiones': re.search(r'\*\*CONCLUSIONES\*\*:?(.*?)(?=\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*CONCLUSIONES\*\*:?(.*?)(?=\*\*RECOMENDACIONES|$)', contenido, re.DOTALL | re.IGNORECASE) else None,
                        'recomendaciones': re.search(r'\*\*RECOMENDACIONES\*\*:?(.*?)$', contenido, re.DOTALL | re.IGNORECASE).group(1) if re.search(r'\*\*RECOMENDACIONES\*\*:?(.*?)$', contenido, re.DOTALL | re.IGNORECASE) else None
                    }
                    for key in secciones_ia:
                        if secciones_ia[key]:
                            secciones_ia[key] = secciones_ia[key].strip().replace('\n', '<br/>')
                            secciones_ia[key] = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', secciones_ia[key])
                        else:
                            secciones_ia[key] = generar_contenido_local_generico(key, tema)
            except Exception as e:
                print(f"Error con IA: {e}")
                secciones_ia = None
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': tema,
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', ''),
            'norma': datos.get('norma', 'apa7'),
            'modo_referencias': modo_referencias,
            'referencias_manuales': referencias_manuales
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, secciones_ia, referencias_ia)
        
        return jsonify({'success': True, 'filename': filename, 'download_url': f'/descargar/{filename}'})
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join('informes_generados', filename), as_attachment=True, download_name=filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado en puerto {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
