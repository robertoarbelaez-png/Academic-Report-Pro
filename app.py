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
import sys

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== CONFIGURACIÓN DE IA ==========
# La variable se lee desde el entorno (Render)
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# LOGS PARA DEPURACIÓN (aparecerán en Render)
print("=" * 50)
print("🚀 INICIANDO APLICACIÓN")
print(f"🔑 API Key cargada: {'SÍ ✅' if OPENROUTER_API_KEY else 'NO ❌'}")
print(f"📝 Longitud de la API Key: {len(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else 0} caracteres")
print(f"🌐 Puerto: {os.environ.get('PORT', '5000')}")
print("=" * 50)

def generar_con_ia(tema, tipo_contenido, info_usuario=""):
    """Genera contenido REAL usando IA (OpenRouter + Gemini)"""
    
    # Si no hay API key, no intentar
    if not OPENROUTER_API_KEY:
        print("❌ No hay API key configurada")
        return None
    
    print(f"🤖 Intentando generar {tipo_contenido} con IA para: {tema[:50]}...")
    
    prompts = {
        'introduccion': f"""Genera una INTRODUCCIÓN académica profesional sobre: "{tema}".

Información adicional del usuario: {info_usuario if info_usuario else 'No hay información adicional'}

La introducción debe incluir:
1. Contextualización del tema (por qué es importante hoy)
2. Planteamiento del problema
3. Justificación del estudio
4. Estructura del informe

Escribe en español, tono académico pero claro. EXTENSIÓN: 300-400 palabras.""",

        'objetivos': f"""Genera los OBJETIVOS para un informe académico sobre "{tema}".

Debe incluir:
- 1 Objetivo General (que abarque todo el estudio)
- 4 Objetivos Específicos (pasos concretos)

Formato: Usa <b>Objetivo General</b> y luego <b>Objetivos Específicos</b> con numeración (1., 2., 3., 4.).""",

        'marco_teorico': f"""Genera el MARCO TEÓRICO para un informe académico sobre "{tema}".

Incluye:
1. Antecedentes (qué se ha investigado antes)
2. Bases teóricas (conceptos clave, autores relevantes)
3. Estado del arte (investigaciones recientes)

EXTENSIÓN: 400-500 palabras. Usa <b>subtítulos</b> para organizar.""",

        'metodologia': f"""Genera la METODOLOGÍA para una investigación sobre "{tema}".

Incluye:
- Enfoque y tipo de investigación
- Población y muestra
- Instrumentos de recolección de datos
- Procedimiento seguido

EXTENSIÓN: 250-350 palabras.""",

        'desarrollo': f"""Genera la sección de DESARROLLO/ANÁLISIS para un informe sobre "{tema}".

Información base del usuario: {info_usuario if info_usuario else 'Sin información específica'}

Incluye:
1. Presentación de resultados
2. Análisis de los hallazgos
3. Discusión relacionando con el marco teórico

EXTENSIÓN: 400-500 palabras.""",

        'conclusiones': f"""Genera las CONCLUSIONES para un informe sobre "{tema}".

Incluye:
- Hallazgos principales (3-5 puntos concretos)
- Limitaciones del estudio
- Aportaciones del trabajo

EXTENSIÓN: 250-300 palabras.""",

        'recomendaciones': f"""Genera RECOMENDACIONES para un informe sobre "{tema}".

Incluye:
- Recomendaciones para la institución
- Recomendaciones para docentes/investigadores
- Recomendaciones para futuros estudios

EXTENSIÓN: 200-250 palabras."""
    }
    
    prompt = prompts.get(tipo_contenido, "")
    if not prompt:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Agregar identificador de la app
        headers["HTTP-Referer"] = "https://academic-report-pro.onrender.com"
        headers["X-Title"] = "Academic Report Pro"
        
        data = {
            "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente académico profesional. Generas contenido de alta calidad para informes universitarios. Usas español formal pero claro. NUNCA inventas datos falsos."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1200,
            "temperature": 0.8
        }
        
        print(f"📡 Enviando petición a OpenRouter...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=60)
        
        print(f"📡 Respuesta código: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            contenido = resultado['choices'][0]['message']['content']
            print(f"✅ IA generó {len(contenido)} caracteres")
            return contenido.replace('\n', '<br/>')
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La IA tardó demasiado en responder")
        return None
    except Exception as e:
        print(f"❌ Error conectando con IA: {str(e)}")
        return None

def generar_contenido_local(tipo, tema, info_usuario=""):
    """Contenido de respaldo (cuando no hay IA o falla)"""
    print(f"📝 Usando contenido local para {tipo}")
    tema_limpio = tema if tema else "el tema de investigación"
    
    contenidos = {
        'introduccion': f"""El presente informe académico aborda el estudio de {tema_limpio}, una temática de creciente relevancia en el contexto educativo actual.<br/><br/>

<b>Contextualización</b><br/>
En las instituciones educativas, se ha observado que los estudiantes presentan dificultades significativas en la comprensión de los conceptos fundamentales relacionados con {tema_limpio}.<br/><br/>

<b>Planteamiento del problema</b><br/>
¿Cuál es el nivel de comprensión y aplicación de los conceptos fundamentales de {tema_limpio} en los estudiantes?<br/><br/>

<b>Justificación</b><br/>
Este trabajo se justifica desde el punto de vista teórico, práctico e institucional, aportando al conocimiento existente y ofreciendo estrategias de mejora.<br/><br/>

<b>Estructura del informe</b><br/>
El documento se organiza en introducción, objetivos, marco teórico, metodología, desarrollo, conclusiones y recomendaciones.""",
        
        'objetivos': f"""<b>Objetivo General</b><br/><br/>
Analizar la comprensión y aplicación de los conceptos fundamentales de {tema_limpio} en estudiantes de educación superior.<br/><br/><br/>

<b>Objetivos Específicos</b><br/><br/>
1. Identificar los conceptos teóricos básicos relacionados con {tema_limpio}.<br/><br/>
2. Describir las dificultades más comunes que enfrentan los estudiantes.<br/><br/>
3. Analizar la relación entre el dominio de {tema_limpio} y el rendimiento académico.<br/><br/>
4. Proponer estrategias didácticas específicas para mejorar el aprendizaje.""",
        
        'marco_teorico': f"""<b>Antecedentes</b><br/><br/>
El estudio de {tema_limpio} ha sido abordado por diversos autores en las últimas décadas.<br/><br/>

<b>Bases teóricas</b><br/><br/>
La teoría constructivista del aprendizaje proporciona el marco pedagógico fundamental.<br/><br/>

<b>Conceptos clave</b><br/><br/>
• Aprendizaje significativo<br/>
• Competencia digital<br/>
• Metacognición<br/><br/>

<b>Estado del arte</b><br/><br/>
Investigaciones recientes demuestran que existe una correlación positiva entre el dominio de {tema_limpio} y el éxito académico.""",
        
        'metodologia': f"""<b>Enfoque y tipo de investigación</b><br/><br/>
Enfoque mixto (cualitativo-cuantitativo), diseño no experimental transversal.<br/><br/>

<b>Población y muestra</b><br/><br/>
Estudiantes de educación superior, muestra representativa.<br/><br/>

<b>Instrumentos</b><br/><br/>
• Cuestionario estructurado<br/>
• Prueba de conocimientos<br/>
• Entrevistas semiestructuradas<br/><br/>

<b>Procedimiento</b><br/><br/>
Fase 1: Diseño y validación de instrumentos<br/>
Fase 2: Recolección de datos<br/>
Fase 3: Análisis e interpretación""",
        
        'desarrollo': f"""<b>Análisis de resultados</b><br/><br/>
Los hallazgos indican que el dominio de {tema_limpio} presenta variaciones significativas entre los estudiantes evaluados.<br/><br/>

<b>Dimensiones analizadas</b><br/><br/>
• <b>Conocimientos teóricos:</b> Los estudiantes demuestran un dominio básico de los conceptos fundamentales.<br/><br/>
• <b>Habilidades prácticas:</b> El rendimiento práctico muestra una correlación positiva con la teoría.<br/><br/>
• <b>Actitudes:</b> La mayoría de los estudiantes considera {tema_limpio} relevante para su formación profesional.<br/><br/>

<b>Discusión</b><br/><br/>
Los resultados coinciden con lo reportado en la literatura especializada, confirmando la importancia de metodologías activas en el aprendizaje.""",
        
        'conclusiones': f"""1. Se ha logrado cumplir con los objetivos planteados en la investigación.<br/><br/>
2. Las metodologías prácticas demostraron ser más efectivas que la instrucción exclusivamente teórica.<br/><br/>
3. La experiencia previa es un factor determinante en el rendimiento académico.<br/><br/>
4. No existen diferencias significativas por género en el aprendizaje.<br/><br/>
5. Se requiere investigación adicional para generalizar los hallazgos a otras poblaciones.""",
        
        'recomendaciones': f"""<b>Para la institución educativa</b><br/><br/>
1. Fortalecer los programas de formación en {tema_limpio}.<br/><br/>
2. Invertir en infraestructura tecnológica y recursos didácticos.<br/><br/>

<b>Para los docentes</b><br/><br/>
3. Implementar metodologías activas como el aprendizaje basado en proyectos.<br/><br/>
4. Diseñar materiales contextualizados según las necesidades de los estudiantes.<br/><br/>

<b>Para futuras investigaciones</b><br/><br/>
5. Realizar estudios longitudinales para evaluar el impacto a largo plazo.<br/><br/>
6. Ampliar la muestra a diferentes contextos educativos."""
    }
    
    return contenidos.get(tipo, "Contenido en desarrollo.")

def generar_contenido(tipo, tema, info_usuario=""):
    """Intenta usar IA primero, si falla usa contenido local"""
    # Intentar con IA
    contenido_ia = generar_con_ia(tema, tipo, info_usuario)
    if contenido_ia:
        print(f"✅ Usando IA para {tipo}")
        return contenido_ia
    
    # Fallback a contenido local
    print(f"⚠️ Usando contenido LOCAL para {tipo}")
    return generar_contenido_local(tipo, tema, info_usuario)

# ========== REFERENCIAS ACADÉMICAS REALES ==========
REFERENCIAS = {
    'default': [
        "Hernández Sampieri, R., Fernández Collado, C., & Baptista Lucio, P. (2021). Metodología de la Investigación (7ª ed.). McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa (6ª ed.). La Muralla.",
        "Sabino, C. A. (2014). El proceso de investigación (4ª ed.). Episteme.",
        "Flick, U. (2015). El diseño de la investigación cualitativa. Morata.",
        "Taylor, S. J., & Bogdan, R. (2016). Introducción a los métodos cualitativos de investigación. Paidós."
    ]
}

def obtener_referencias(tema):
    return REFERENCIAS['default']

# ========== GENERADOR DE PDF ==========
class GeneradorPDF:
    def __init__(self):
        self.estilos = self._crear_estilos()
    
    def _crear_estilos(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TextoJustificado', parent=styles['Normal'],
            alignment=TA_JUSTIFY, fontSize=11, fontName='Times-Roman', spaceAfter=12, leading=16))
        styles.add(ParagraphStyle(name='Titulo1', parent=styles['Heading1'],
            fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'), spaceBefore=24, spaceAfter=16))
        styles.add(ParagraphStyle(name='TituloPortada', parent=styles['Title'],
            fontSize=24, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a365d')))
        return styles
    
    def generar_pdf(self, datos_usuario, opciones, texto_auto=""):
        nombre = datos_usuario.get('nombre', 'Estudiante') or "Estudiante"
        tema = datos_usuario.get('tema', 'Tema de Investigación') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', 'Asignatura') or "Asignatura"
        profesor = datos_usuario.get('profesor', 'Docente') or "Docente"
        institucion = datos_usuario.get('institucion', 'Institución Educativa') or "Institución Educativa"
        fecha_entrega = datos_usuario.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        
        print(f"\n📄 Generando informe para tema: {tema}")
        
        # Generar o usar contenido del usuario
        introduccion = datos_usuario.get('introduccion', '')
        if not introduccion or len(introduccion) < 50:
            introduccion = generar_contenido('introduccion', tema, texto_auto)
        
        objetivos = datos_usuario.get('objetivos', '')
        if not objetivos or len(objetivos) < 50:
            objetivos = generar_contenido('objetivos', tema)
        
        marco_teorico = datos_usuario.get('marco_teorico', '')
        if not marco_teorico or len(marco_teorico) < 50:
            marco_teorico = generar_contenido('marco_teorico', tema)
        
        metodologia = datos_usuario.get('metodologia', '')
        if not metodologia or len(metodologia) < 50:
            metodologia = generar_contenido('metodologia', tema)
        
        desarrollo = datos_usuario.get('desarrollo', '')
        if not desarrollo or len(desarrollo) < 50:
            desarrollo = generar_contenido('desarrollo', tema, texto_auto)
        
        conclusiones = datos_usuario.get('conclusiones', '')
        if not conclusiones or len(conclusiones) < 50:
            conclusiones = generar_contenido('conclusiones', tema)
        
        recomendaciones = datos_usuario.get('recomendaciones', '')
        if opciones.get('incluir_recomendaciones', True) and (not recomendaciones or len(recomendaciones) < 50):
            recomendaciones = generar_contenido('recomendaciones', tema)
        
        referencias = obtener_referencias(tema)
        
        filename = f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.pdf"
        filepath = os.path.join('informes_generados', filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        story = []
        
        # PORTADA
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("INFORME ACADÉMICO", self.estilos['TituloPortada']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(tema.upper(), self.estilos['TextoJustificado']))
        story.append(Spacer(1, 1.2*inch))
        story.append(Paragraph(f"<b>Presentado por:</b> {nombre}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Asignatura:</b> {asignatura}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Docente:</b> {profesor}", self.estilos['TextoJustificado']))
        story.append(Paragraph(f"<b>Institución:</b> {institucion}", self.estilos['TextoJustificado']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {fecha_entrega}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # ÍNDICE
        story.append(Paragraph("ÍNDICE", self.estilos['Titulo1']))
        indices = ["1. INTRODUCCIÓN", "2. OBJETIVOS", "3. MARCO TEÓRICO", "4. METODOLOGÍA",
                   "5. DESARROLLO", "6. CONCLUSIONES", "7. REFERENCIAS"]
        if opciones.get('incluir_recomendaciones', True):
            indices.insert(-1, "RECOMENDACIONES")
        
        for idx in indices:
            story.append(Paragraph(f"• {idx}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # SECCIONES
        contador = 1
        
        story.append(Paragraph(f"{contador}. INTRODUCCIÓN", self.estilos['Titulo1']))
        story.append(Paragraph(introduccion.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. OBJETIVOS", self.estilos['Titulo1']))
        story.append(Paragraph(objetivos.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. MARCO TEÓRICO", self.estilos['Titulo1']))
        story.append(Paragraph(marco_teorico.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. METODOLOGÍA", self.estilos['Titulo1']))
        story.append(Paragraph(metodologia.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. DESARROLLO", self.estilos['Titulo1']))
        story.append(Paragraph(desarrollo.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        story.append(Paragraph(f"{contador}. CONCLUSIONES", self.estilos['Titulo1']))
        story.append(Paragraph(conclusiones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
        story.append(PageBreak())
        contador += 1
        
        if opciones.get('incluir_recomendaciones', True):
            story.append(Paragraph(f"{contador}. RECOMENDACIONES", self.estilos['Titulo1']))
            story.append(Paragraph(recomendaciones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        story.append(Paragraph(f"{contador}. REFERENCIAS", self.estilos['Titulo1']))
        for i, ref in enumerate(referencias, 1):
            story.append(Paragraph(f"{i}. {ref}", self.estilos['TextoJustificado']))
            story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        print(f"✅ PDF generado: {filename}")
        return filename, filepath

generador = GeneradorPDF()

# ========== RUTAS ==========
@app.route('/')
def index():
    print("📄 Página principal solicitada")
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        modo = datos.get('modo', 'auto')
        texto_auto = datos.get('texto_completo', '') if modo in ['auto', 'rapido'] else ''
        
        print(f"\n📨 Solicitud de generación recibida")
        print(f"   Modo: {modo}")
        print(f"   Tema: {datos.get('tema', 'No especificado')}")
        
        opciones = {
            'incluir_resumen': datos.get('incluir_resumen', False),
            'incluir_resultados': datos.get('incluir_resultados', True),
            'incluir_recomendaciones': datos.get('incluir_recomendaciones', True)
        }
        
        datos_usuario = {
            'nombre': datos.get('nombre', ''),
            'tema': datos.get('tema', ''),
            'asignatura': datos.get('asignatura', ''),
            'profesor': datos.get('profesor', ''),
            'institucion': datos.get('institucion', ''),
            'fecha_entrega': datos.get('fecha_entrega', ''),
            'introduccion': datos.get('introduccion', ''),
            'objetivos': datos.get('objetivos', ''),
            'marco_teorico': datos.get('marco_teorico', ''),
            'metodologia': datos.get('metodologia', ''),
            'desarrollo': datos.get('desarrollo', ''),
            'conclusiones': datos.get('conclusiones', ''),
            'recomendaciones': datos.get('recomendaciones', '')
        }
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, texto_auto)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/descargar/{filename}'
        })
    
    except Exception as e:
        print(f"❌ Error en generación: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar/<filename>')
def descargar(filename):
    print(f"📥 Descargando: {filename}")
    return send_file(
        os.path.join('informes_generados', filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado en puerto {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
