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

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== CONFIGURACIÓN DE GROQ ==========
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

print("=" * 50)
print("🚀 INICIANDO APLICACIÓN")
print(f"🔑 Groq API Key cargada: {'SÍ ✅' if GROQ_API_KEY else 'NO ❌'}")
print("=" * 50)

# ========== NORMAS ACADÉMICAS ==========
NORMAS_CONFIG = {
    'apa7': {
        'nombre': 'APA 7ª Edición',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 12, 'interlineado': 24,
        'sangria': 36
    },
    'apa6': {
        'nombre': 'APA 6ª Edición',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 12, 'interlineado': 24,
        'sangria': 36
    },
    'icontec': {
        'nombre': 'ICONTEC (Colombia)',
        'margen_superior': 85, 'margen_inferior': 85,
        'margen_izquierdo': 113, 'margen_derecho': 85,
        'fuente': 'Helvetica', 'tamaño': 12, 'interlineado': 18,
        'sangria': 0
    },
    'vancouver': {
        'nombre': 'Vancouver',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 11, 'interlineado': 16,
        'sangria': 0
    },
    'chicago': {
        'nombre': 'Chicago',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 12, 'interlineado': 18,
        'sangria': 36
    },
    'harvard': {
        'nombre': 'Harvard',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 12, 'interlineado': 18,
        'sangria': 36
    },
    'mla': {
        'nombre': 'MLA 9ª Edición',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 12, 'interlineado': 24,
        'sangria': 36
    },
    'ieee': {
        'nombre': 'IEEE',
        'margen_superior': 72, 'margen_inferior': 72,
        'margen_izquierdo': 72, 'margen_derecho': 72,
        'fuente': 'Times-Roman', 'tamaño': 10, 'interlineado': 12,
        'sangria': 0
    }
}

def limpiar_texto(texto):
    """Limpia caracteres extraños del texto"""
    if not texto:
        return ""
    texto = re.sub(r'[^\x20-\x7E\xA0-\xFF\u00C0-\u00FF\u0100-\u017F\n\r]', '', texto)
    texto = re.sub(r'\n{3,}', '<br/><br/>', texto)
    return texto

def generar_informe_completo_con_ia(tema, info_usuario=""):
    """Genera TODO el informe en UNA sola llamada a Groq"""
    
    if not GROQ_API_KEY:
        print("❌ No hay API key de Groq configurada")
        return None
    
    print(f"🤖 Generando informe COMPLETO con Groq para: {tema[:50]}...")
    
    prompt = f"""Genera un INFORME ACADÉMICO COMPLETO sobre el tema: "{tema}".

Información adicional: {info_usuario if info_usuario else 'No hay información adicional'}

⚠️ IMPORTANTE: Cada sección debe tener contenido ESPECÍFICO relacionado directamente con "{tema}". NO uses plantillas genéricas como "aprendizaje significativo" o "teoría constructivista" a menos que estén directamente relacionadas con el tema.

Escribe EXACTAMENTE estas secciones con el siguiente formato:

**INTRODUCCIÓN**
(Escribe aquí 300-400 palabras específicas sobre el tema, explicando contexto, problema y justificación)

**OBJETIVOS**
**Objetivo General:** (1 objetivo específico relacionado con el tema)
**Objetivos Específicos:** (4 objetivos específicos numerados, directamente relacionados con el tema)

**MARCO TEÓRICO**
**Antecedentes:** (investigaciones previas específicas sobre el tema, con autores y años reales)
**Bases Teóricas:** (conceptos clave específicos del tema, no genéricos)
**Estado del Arte:** (investigaciones recientes específicas sobre el tema)

**METODOLOGÍA**
**Enfoque:** (tipo de investigación apropiado para el tema)
**Población y muestra:** (específica al tema, ej: productores de café, estudiantes, etc.)
**Instrumentos:** (encuestas, entrevistas, análisis de datos - específicos al tema)
**Procedimiento:** (pasos concretos para investigar el tema)

**DESARROLLO**
**Análisis de resultados:** (hallazgos específicos sobre el tema)
**Dimensiones analizadas:** (aspectos concretos del tema)
**Discusión:** (relación de hallazgos con la literatura)

**CONCLUSIONES**
(5 puntos específicos sobre el tema)

**RECOMENDACIONES**
(Para institución, para profesionales del área, para futuros estudios)

Escribe TODO en español. Usa CONCLUSIONES (no Conclusions). Usa RECOMENDACIONES (no Recommendations). Cada sección debe ser detallada y específica al tema "{tema}"."""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un asistente académico profesional. Generas informes universitarios completos y detallados. SIEMPRE generas contenido ESPECÍFICO al tema solicitado. NUNCA usas plantillas genéricas como 'aprendizaje significativo' o 'teoría constructivista' a menos que el tema lo requiera. Usas CONCLUSIONES (no Conclusions) y RECOMENDACIONES (no Recommendations)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 5000
    }
    
    try:
        print(f"📡 Enviando petición a Groq...")
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=120)
        print(f"📡 Respuesta código: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            contenido = resultado['choices'][0]['message']['content']
            print(f"✅ Groq generó {len(contenido)} caracteres")
            
            contenido = limpiar_texto(contenido)
            
            secciones = {
                'introduccion': extraer_seccion(contenido, 'INTRODUCCIÓN'),
                'objetivos': extraer_seccion(contenido, 'OBJETIVOS'),
                'marco_teorico': extraer_seccion(contenido, 'MARCO TEÓRICO'),
                'metodologia': extraer_seccion(contenido, 'METODOLOGÍA'),
                'desarrollo': extraer_seccion(contenido, 'DESARROLLO'),
                'conclusiones': extraer_seccion(contenido, 'CONCLUSIONES'),
                'recomendaciones': extraer_seccion(contenido, 'RECOMENDACIONES')
            }
            
            # Verificar que todas las secciones tengan contenido específico
            for key in secciones:
                if not secciones[key] or len(secciones[key]) < 100:
                    print(f"⚠️ Sección {key} incompleta, regenerando...")
                    secciones[key] = generar_seccion_individual(key, tema)
            
            return secciones
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando con Groq: {str(e)}")
        return None

def generar_seccion_individual(seccion, tema):
    """Genera una sección específica si la principal falló"""
    prompts = {
        'objetivos': f"Genera solo los OBJETIVOS para un informe sobre '{tema}'. Incluye 1 Objetivo General y 4 Objetivos Específicos directamente relacionados con el tema. Usa **negritas**.",
        'marco_teorico': f"Genera solo el MARCO TEÓRICO para un informe sobre '{tema}'. Incluye Antecedentes (con autores reales), Bases Teóricas y Estado del Arte. Específico al tema.",
        'metodologia': f"Genera solo la METODOLOGÍA para un informe sobre '{tema}'. Incluye Enfoque, Población y muestra, Instrumentos y Procedimiento. Específico al tema.",
        'desarrollo': f"Genera solo el DESARROLLO para un informe sobre '{tema}'. Incluye Análisis de resultados, Dimensiones analizadas y Discusión."
    }
    
    if seccion not in prompts:
        return generar_contenido_local(seccion, tema)
    
    if not GROQ_API_KEY:
        return generar_contenido_local(seccion, tema)
    
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompts[seccion]}],
            "max_tokens": 1500
        }
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            contenido = response.json()['choices'][0]['message']['content']
            contenido = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', contenido)
            return contenido.replace('\n', '<br/>')
    except Exception as e:
        print(f"Error generando sección {seccion}: {e}")
    
    return generar_contenido_local(seccion, tema)

def extraer_seccion(contenido, nombre):
    """Extrae una sección del contenido generado por IA"""
    patrones = [
        rf'\*\*{nombre}\*\*:?(.*?)(?=\*\*[A-Z]|$)',
        rf'{nombre}:?(.*?)(?=\n\n\*\*[A-Z]|\n\n[A-Z]|$)',
        rf'{nombre}\s*\n(.*?)(?=\n\n\*\*[A-Z]|\n\n[A-Z]|$)'
    ]
    
    for patron in patrones:
        match = re.search(patron, contenido, re.DOTALL | re.IGNORECASE)
        if match:
            texto = match.group(1).strip()
            texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
            texto = texto.replace('\n', '<br/>')
            if len(texto) > 4000:
                texto = texto[:4000] + "..."
            return texto
    
    return ""

def generar_contenido_local(tipo, tema):
    """Contenido de respaldo (solo si la IA falla completamente)"""
    tema_limpio = tema if tema else "el tema de investigación"
    
    contenidos = {
        'introduccion': f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia en el contexto actual.<br/><br/>
<b>Contextualización</b><br/>Este tema ha cobrado importancia en los últimos años debido a sus implicaciones en diversos ámbitos.<br/><br/>
<b>Planteamiento del problema</b><br/>Es necesario comprender a fondo los aspectos fundamentales relacionados con {tema_limpio}.<br/><br/>
<b>Justificación</b><br/>Este estudio contribuye al conocimiento existente y ofrece perspectivas valiosas.""",
        
        'objetivos': f"""<b>Objetivo General</b><br/><br/>Analizar los aspectos fundamentales de {tema_limpio}.<br/><br/><br/>
<b>Objetivos Específicos</b><br/><br/>1. Identificar los conceptos clave relacionados con {tema_limpio}.<br/><br/>
2. Describir las principales características y componentes.<br/><br/>
3. Analizar la relación entre variables relevantes.<br/><br/>
4. Proponer recomendaciones basadas en el análisis.""",
        
        'marco_teorico': f"""<b>Antecedentes</b><br/><br/>Diversos autores han estudiado {tema_limpio} en las últimas décadas.<br/><br/>
<b>Bases teóricas</b><br/>Las teorías existentes proporcionan un marco conceptual sólido.<br/><br/>
<b>Conceptos clave</b><br/>• Concepto fundamental 1<br/>• Concepto fundamental 2<br/>• Concepto fundamental 3<br/><br/>
<b>Estado del arte</b><br/>Investigaciones recientes han profundizado en aspectos específicos de {tema_limpio}.""",
        
        'metodologia': f"""<b>Enfoque</b><br/>Enfoque mixto (cualitativo-cuantitativo).<br/><br/>
<b>Población y muestra</b><br/>Población relevante al tema de estudio, muestra representativa.<br/><br/>
<b>Instrumentos</b><br/>Cuestionarios, entrevistas, revisión documental.<br/><br/>
<b>Procedimiento</b><br/>Fase 1: Recolección de datos<br/>Fase 2: Análisis e interpretación<br/>Fase 3: Elaboración de conclusiones""",
        
        'desarrollo': f"""<b>Análisis de resultados</b><br/>Los hallazgos indican aspectos relevantes sobre {tema_limpio}.<br/><br/>
<b>Dimensiones analizadas</b><br/>• Dimensión 1<br/>• Dimensión 2<br/>• Dimensión 3<br/><br/>
<b>Discusión</b><br/>Los resultados coinciden parcialmente con lo reportado en la literatura.""",
        
        'conclusiones': f"""1. Se han identificado los aspectos fundamentales de {tema_limpio}.<br/><br/>
2. El análisis realizado aporta al conocimiento existente.<br/><br/>
3. Se requiere mayor investigación en áreas específicas.<br/><br/>
4. Las recomendaciones propuestas son viables.<br/><br/>
5. Este estudio sienta bases para futuras investigaciones.""",
        
        'recomendaciones': f"""<b>Para la institución</b><br/>1. Fortalecer líneas de investigación relacionadas.<br/><br/>
<b>Para los profesionales</b><br/>2. Aplicar los hallazgos en contextos prácticos.<br/><br/>
<b>Para futuros estudios</b><br/>3. Ampliar la muestra y el alcance geográfico."""
    }
    return contenidos.get(tipo, "Contenido en desarrollo.")

# ========== REFERENCIAS ==========
REFERENCIAS = {
    'default': [
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla.",
        "Sabino, C. A. (2014). El proceso de investigación. Episteme."
    ]
}

def obtener_referencias(tema):
    return REFERENCIAS['default']

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
    
    def generar_pdf(self, datos_usuario, opciones, secciones_ia=None):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        norma = datos_usuario.get('norma', 'apa7')
        
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
            introduccion = generar_contenido_local('introduccion', tema)
            objetivos = generar_contenido_local('objetivos', tema)
            marco_teorico = generar_contenido_local('marco_teorico', tema)
            metodologia = generar_contenido_local('metodologia', tema)
            desarrollo = generar_contenido_local('desarrollo', tema)
            conclusiones = generar_contenido_local('conclusiones', tema)
            recomendaciones = generar_contenido_local('recomendaciones', tema)
            print("⚠️ Usando contenido local")
        
        referencias = obtener_referencias(tema)
        
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
        if opciones.get('incluir_recomendaciones', True):
            indices.insert(-1, "RECOMENDACIONES")
        
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
        
        if opciones.get('incluir_recomendaciones', True):
            story.append(Paragraph("7. RECOMENDACIONES", styles['Titulo1']))
            story.append(Paragraph(recomendaciones, styles['TextoJustificado']))
            story.append(PageBreak())
            story.append(Paragraph("8. REFERENCIAS", styles['Titulo1']))
        else:
            story.append(Paragraph("7. REFERENCIAS", styles['Titulo1']))
        
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {ref}", styles['TextoJustificado']))
            story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        print(f"✅ PDF generado: {filename}")
        return filename, filepath

generador = GeneradorPDF()

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
        
        if modo == 'rapido' and texto_auto:
            tema = texto_auto
        
        print(f"📨 Solicitud recibida - Modo: {modo}, Tema: {tema[:50] if tema else 'VACIO'}")
        
        if not tema or len(tema) < 3:
            return jsonify({'success': False, 'error': 'Por favor ingresa un tema válido'}), 400
        
        opciones = {
            'incluir_recomendaciones': datos.get('incluir_recomendaciones', True)
        }
        
        secciones_ia = generar_informe_completo_con_ia(tema, texto_auto)
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': tema,
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', ''),
            'norma': datos.get('norma', 'apa7')
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, secciones_ia)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/descargar/{filename}'
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(
        os.path.join('informes_generados', filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado en puerto {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
