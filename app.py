from flask import Flask, render_template, request, jsonify, send_file, make_response
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
import json
import io
import random

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== PLANTILLAS VARIADAS (EVITAN REPETICIÓN) ==========

PLANTILLAS_INTRO = [
    """El presente informe académico aborda el estudio de {tema}, una temática de creciente relevancia en el contexto {contexto}. En los últimos años, este campo ha experimentado una evolución significativa, transformando radicalmente los procesos de enseñanza y aprendizaje.<br/><br/>

<b>Contextualización del problema</b><br/>
En {institucion}, se ha observado que los estudiantes presentan dificultades significativas en la comprensión de los conceptos fundamentales relacionados con {tema}. Esta situación se manifiesta en diversos indicadores académicos, tales como el rendimiento por debajo de lo esperado y la desmotivación manifestada durante las clases.<br/><br/>

<b>Planteamiento del problema</b><br/>
A partir de las observaciones preliminares y del análisis documental, se formula la siguiente pregunta de investigación: ¿Cuál es el nivel de comprensión y aplicación de los conceptos fundamentales de {tema} en los estudiantes de {institucion}, y qué estrategias didácticas podrían implementarse para mejorar su aprendizaje?<br/><br/>

<b>Justificación del estudio</b><br/>
Este trabajo se justifica desde tres perspectivas fundamentales. Desde el punto de vista teórico, contribuye al cuerpo de conocimiento existente sobre {tema}. Desde la perspectiva práctica, los hallazgos permitirán diseñar intervenciones pedagógicas más efectivas. Desde el ámbito institucional, los resultados servirán como insumo para la toma de decisiones curriculares.<br/><br/>

<b>Estructura del informe</b><br/>
El documento se organiza en las siguientes secciones: introducción, objetivos, marco teórico, metodología, desarrollo, conclusiones y referencias bibliográficas.""",

    """{tema} se ha convertido en un elemento fundamental en la formación profesional del siglo XXI. Comprender sus fundamentos y aplicaciones resulta esencial para el desarrollo de competencias profesionales en los estudiantes de educación superior.<br/><br/>

<b>Antecedentes del problema</b><br/>
Diversos estudios han documentado las dificultades que enfrentan los estudiantes al abordar {tema}. Según investigaciones recientes, existe una brecha significativa entre el conocimiento teórico y la aplicación práctica, lo que afecta directamente el rendimiento académico.<br/><br/>

<b>Preguntas de investigación</b><br/>
Para orientar este estudio, se formulan las siguientes preguntas: ¿Qué factores influyen en el aprendizaje de {tema}? ¿Qué estrategias metodológicas resultan más efectivas? ¿Cómo se relaciona el dominio de {tema} con el éxito académico general?<br/><br/>

<b>Objetivos del estudio</b><br/>
Este trabajo busca analizar la comprensión de {tema} en estudiantes de {institucion}, identificando fortalezas, debilidades y oportunidades de mejora en el proceso de enseñanza-aprendizaje."""
]

PLANTILLAS_OBJETIVOS = [
    """<b>Objetivo General</b><br/><br/>
Analizar la comprensión y aplicación de los conceptos fundamentales de {tema} en estudiantes de educación superior, identificando las principales fortalezas y áreas de oportunidad en el proceso de enseñanza-aprendizaje.<br/><br/><br/>

<b>Objetivos Específicos</b><br/><br/>
1. Identificar los conceptos teóricos básicos relacionados con {tema} que los estudiantes dominan con mayor facilidad, así como aquellos que representan mayores dificultades.<br/><br/>
2. Describir las dificultades más comunes que enfrentan los estudiantes al aplicar los conocimientos de {tema} en situaciones prácticas y contextualizadas.<br/><br/>
3. Analizar la relación entre el dominio de {tema} y el rendimiento académico general de los estudiantes en otras asignaturas afines.<br/><br/>
4. Proponer estrategias didácticas específicas, basadas en evidencia empírica, para mejorar la enseñanza y el aprendizaje de {tema}.<br/><br/>
5. Evaluar la efectividad de diferentes metodologías de enseñanza (clases magistrales, aprendizaje basado en proyectos, gamificación) en la comprensión de {tema}.""",

    """<b>Propósito general de la investigación</b><br/><br/>
Determinar el nivel de competencia en {tema} que poseen los estudiantes de {institucion}, así como los factores que inciden en su proceso de aprendizaje.<br/><br/><br/>

<b>Metas específicas</b><br/><br/>
• Diagnosticar el estado actual del conocimiento sobre {tema} en la población estudiantil.<br/><br/>
• Identificar las principales barreras y obstáculos que enfrentan los estudiantes.<br/><br/>
• Establecer correlaciones entre el dominio de {tema} y variables como edad, género y nivel académico.<br/><br/>
• Diseñar una propuesta de intervención pedagógica fundamentada en los hallazgos obtenidos.<br/><br/>
• Validar la efectividad de la propuesta mediante un estudio piloto."""
]

PLANTILLAS_MARCO = [
    """<b>Antecedentes de la investigación</b><br/><br/>
El estudio de {tema} ha sido abordado por numerosos autores en las últimas décadas. Según Hernández Sampieri (2021), la investigación educativa requiere un enfoque riguroso que combine elementos cualitativos y cuantitativos para obtener una visión integral del fenómeno estudiado.<br/><br/>

En el contexto específico de {tema}, Tanenbaum (2017) establece que los fundamentos de esta disciplina se basan en principios que han evolucionado significativamente con el avance tecnológico. El autor identifica tres componentes esenciales: los conceptos teóricos fundamentales, las habilidades prácticas necesarias para su aplicación, y las actitudes hacia el aprendizaje continuo.<br/><br/>

<b>Bases teóricas fundamentales</b><br/><br/>
La teoría constructivista del aprendizaje, propuesta por Piaget y posteriormente desarrollada por Vygotsky, proporciona el marco pedagógico para entender cómo los estudiantes construyen conocimiento sobre {tema}. Según esta perspectiva, el aprendizaje es un proceso activo en el que el estudiante integra nueva información con sus estructuras cognitivas preexistentes.<br/><br/>

Coll (2018) complementa esta visión al analizar el impacto de las tecnologías en los procesos cognitivos, señalando que el aprendizaje mediado por tecnología requiere estrategias didácticas específicas que consideren las características del entorno digital.<br/><br/>

<b>Conceptos clave</b><br/><br/>
• <b>Aprendizaje significativo:</b> Término acuñado por Ausubel que hace referencia a la integración de nuevos conocimientos con estructuras cognitivas preexistentes. En el contexto de {tema}, esto implica conectar los nuevos conceptos con experiencias previas de los estudiantes.<br/><br/>

• <b>Competencia digital:</b> Conjunto de habilidades necesarias para utilizar efectivamente las tecnologías de la información, incluyendo aspectos técnicos, cognitivos y actitudinales.<br/><br/>

• <b>Metacognición:</b> Proceso mediante el cual los estudiantes toman conciencia de sus propios procesos de aprendizaje, identificando sus fortalezas y debilidades.<br/><br/>

<b>Estado del arte</b><br/><br/>
Investigaciones recientes (Area Moreira, 2021; Pérez Gómez, 2021) demuestran que existe una correlación positiva entre el dominio de {tema} y el éxito académico en disciplinas relacionadas. Sin embargo, todavía hay vacíos en la comprensión de cómo se transfieren estos conocimientos a contextos prácticos.""",

    """<b>Marco referencial</b><br/><br/>
Para comprender adecuadamente {tema}, es necesario revisar las contribuciones teóricas más relevantes en este campo. Autores como Stallings (2016) y Laudon (2021) han establecido las bases conceptuales que sustentan la investigación actual.<br/><br/>

<b>Fundamentos teóricos</b><br/><br/>
El paradigma socioconstructivista, representado por Vygotsky y sus seguidores, ofrece un marco explicativo para entender cómo los estudiantes aprenden {tema} en interacción con otros y con herramientas culturales. La zona de desarrollo próximo y el andamiaje son conceptos particularmente útiles para diseñar intervenciones pedagógicas.<br/><br/>

<b>Dimensiones de análisis</b><br/><br/>
Para este estudio, se han identificado tres dimensiones fundamentales: la dimensión cognitiva (conocimientos declarativos y procedimentales), la dimensión actitudinal (motivación, autoeficacia, interés) y la dimensión social (interacción, colaboración, comunicación)."""
]

# ========== FUNCIONES DE GENERACIÓN ==========

def generar_contenido_variado(tipo, tema, institucion, info_usuario=""):
    """Genera contenido variado usando plantillas aleatorias"""
    
    tema_limpio = tema if tema else "el tema de investigación"
    institucion_limpia = institucion if institucion else "la institución educativa"
    contexto = random.choice(["educativo actual", "académico contemporáneo", "formativo profesional"])
    
    if tipo == 'introduccion':
        plantilla = random.choice(PLANTILLAS_INTRO)
        contenido = plantilla.format(tema=tema_limpio, institucion=institucion_limpia, contexto=contexto)
        
        if info_usuario and len(info_usuario) > 100:
            contenido += f"<br/><br/><b>Información complementaria del estudiante:</b><br/>{info_usuario[:500]}..."
        
        return contenido
    
    elif tipo == 'objetivos':
        plantilla = random.choice(PLANTILLAS_OBJETIVOS)
        return plantilla.format(tema=tema_limpio, institucion=institucion_limpia)
    
    elif tipo == 'marco_teorico':
        plantilla = random.choice(PLANTILLAS_MARCO)
        return plantilla.format(tema=tema_limpio)
    
    elif tipo == 'metodologia':
        enfoques = ["mixto (cualitativo-cuantitativo)", "cuantitativo de tipo descriptivo", "cualitativo de tipo fenomenológico"]
        disenos = ["no experimental de tipo transversal", "descriptivo correlacional", "exploratorio secuencial"]
        muestras = [f"60 estudiantes de {institucion_limpia}", f"una muestra representativa de 120 participantes", f"45 estudiantes seleccionados mediante muestreo estratificado"]
        
        return f"""<b>Enfoque y tipo de investigación</b><br/><br/>
El presente estudio adopta un enfoque {random.choice(enfoques)}, con un diseño {random.choice(disenos)}.<br/><br/>

<b>Población y muestra</b><br/><br/>
La población objetivo estuvo conformada por estudiantes de {institucion_limpia}. Se seleccionó {random.choice(muestras)}.<br/><br/>

<b>Criterios de selección</b><br/><br/>
• <b>Criterios de inclusión:</b> Estudiantes matriculados en programas de pregrado, haber cursado al menos una asignatura relacionada con {tema_limpio}, disponibilidad para participar voluntariamente.<br/>
• <b>Criterios de exclusión:</b> Estudiantes con más del 30% de inasistencia a clases durante el período de recolección.<br/><br/>

<b>Instrumentos de recolección de datos</b><br/><br/>
1. <b>Cuestionario estructurado:</b> Diseñado específicamente para este estudio, consta de 25 ítems distribuidos en cuatro dimensiones. Utiliza escala Likert de 5 puntos. El instrumento fue validado mediante juicio de 3 expertos, obteniendo un coeficiente de validez de contenido de 0.89.<br/><br/>

2. <b>Prueba de conocimientos:</b> 15 preguntas de opción múltiple con cuatro opciones de respuesta cada una, diseñadas para evaluar el nivel de comprensión de {tema_limpio}. La confiabilidad del instrumento se estableció mediante el coeficiente KR-20, obteniendo un valor de 0.85.<br/><br/>

3. <b>Entrevistas semiestructuradas:</b> Aplicadas a 10 estudiantes seleccionados aleatoriamente de la muestra, con el objetivo de profundizar en aspectos cualitativos no capturados por los instrumentos cuantitativos.<br/><br/>

<b>Procedimiento</b><br/><br/>
• <b>Fase 1 (Semana 1-2):</b> Diseño, construcción y validación de instrumentos mediante juicio de expertos.<br/>
• <b>Fase 2 (Semana 3):</b> Prueba piloto con 15 estudiantes para ajustar instrumentos.<br/>
• <b>Fase 3 (Semana 4-6):</b> Recolección de datos en condiciones controladas, previo consentimiento informado.<br/>
• <b>Fase 4 (Semana 7-8):</b> Procesamiento y análisis de datos, tanto cuantitativos como cualitativos.<br/><br/>

<b>Análisis de datos</b><br/><br/>
Los datos cuantitativos se analizaron mediante estadística descriptiva (medias, desviaciones estándar, frecuencias, porcentajes) e inferencial (prueba t de Student, ANOVA de un factor, correlación de Pearson). Se utilizó el software SPSS versión 28.0. Los datos cualitativos se procesaron mediante análisis de contenido temático con el apoyo del software Atlas.ti versión 23."""
    
    elif tipo == 'desarrollo':
        return f"""<b>Presentación y análisis de resultados</b><br/><br/>
Los resultados obtenidos muestran que el dominio de {tema_limpio} presenta variaciones significativas entre los estudiantes evaluados.<br/><br/>

<b>Análisis por dimensiones</b><br/><br/>
• <b>Dimensión teórica:</b> Los estudiantes demuestran un dominio básico de los conceptos fundamentales, con un promedio de 72.4 puntos sobre 100. Las mayores dificultades se presentan en conceptos abstractos y relaciones complejas.<br/><br/>

• <b>Dimensión práctica:</b> El rendimiento práctico fue de 68.7 puntos, con una correlación positiva con la teoría (r = 0.62, p < 0.01). Se observa que la práctica supervisada mejora significativamente el desempeño.<br/><br/>

• <b>Dimensión actitudinal:</b> El 72% de los estudiantes considera {tema_limpio} relevante para su formación profesional, y el 68% prefiere metodologías prácticas sobre clases teóricas tradicionales.<br/><br/>

<b>Análisis cualitativo</b><br/><br/>
Las entrevistas realizadas permitieron identificar cuatro categorías principales:<br/>
1. <b>Dificultades conceptuales:</b> Los estudiantes reportan problemas para abstraer conceptos complejos cuando no cuentan con ejemplos concretos.<br/>
2. <b>Necesidad de práctica:</b> Señalan que la práctica supervisada mejora significativamente su comprensión y retención.<br/>
3. <b>Valoración del feedback:</b> Consideran esencial la retroalimentación inmediata durante el proceso de aprendizaje.<br/>
4. <b>Aplicaciones reales:</b> Demandan más ejemplos contextualizados en situaciones profesionales reales."""
    
    elif tipo == 'conclusiones':
        return f"""<b>Conclusiones del estudio</b><br/><br/>

<b>1. Cumplimiento de los objetivos</b><br/>
El objetivo general de analizar la comprensión de {tema_limpio} se ha cumplido satisfactoriamente. Los resultados evidencian que existe un dominio moderado de los conceptos fundamentales, con un 65% de estudiantes alcanzando niveles satisfactorios en las evaluaciones teóricas.<br/><br/>

<b>2. Hallazgos principales</b><br/>
• La metodología práctica demostró ser significativamente más efectiva que la instrucción exclusivamente teórica.<br/>
• La experiencia previa es un factor determinante, explicando aproximadamente el 50% de la varianza en el rendimiento.<br/>
• No existen diferencias significativas por género, lo que indica igualdad de oportunidades en el aprendizaje.<br/>
• Se identificó una correlación fuerte entre horas de estudio y rendimiento (r = 0.71, p < 0.001).<br/><br/>

<b>3. Limitaciones del estudio</b><br/>
• El tamaño de muestra (n=60) limita la generalización de los resultados a otras poblaciones.<br/>
• El diseño transversal no permite establecer relaciones causales definitivas entre variables.<br/>
• Los instrumentos de medición presentan limitaciones propias de cualquier investigación educativa.<br/>
• El contexto específico puede limitar la aplicabilidad a otras instituciones.<br/><br/>

<b>4. Aportaciones del estudio</b><br/>
• Evidencia empírica sobre la efectividad de metodologías prácticas en el aprendizaje de {tema_limpio}.<br/>
• Instrumentos validados para el contexto local que pueden ser utilizados en futuras investigaciones.<br/>
• Identificación de barreras específicas de aprendizaje desde la perspectiva estudiantil.<br/>
• Recomendaciones concretas para la mejora de la enseñanza."""
    
    elif tipo == 'recomendaciones':
        return f"""<b>Recomendaciones basadas en los hallazgos</b><br/><br/>

<b>Para la institución educativa</b><br/><br/>
1. <b>Rediseño curricular basado en evidencia:</b> Incorporar al menos un 40% de horas prácticas en las asignaturas relacionadas con {tema_limpio}, considerando la evidencia de mayor efectividad de estas metodologías.<br/><br/>

2. <b>Programas de nivelación obligatorios:</b> Implementar cursos introductorios para estudiantes sin experiencia previa, dada la brecha significativa identificada.<br/><br/>

3. <b>Inversión en infraestructura tecnológica:</b> Ampliar los laboratorios especializados y los horarios de acceso, ya que el 78% de los estudiantes señaló limitaciones de recursos como barrera para el aprendizaje práctico.<br/><br/>

4. <b>Sistema de tutorías estructurado:</b> Establecer un programa formal de tutorías entre pares, aprovechando la correlación positiva encontrada entre asistencia a tutorías y rendimiento académico.<br/><br/>

<b>Para los docentes</b><br/><br/>
5. <b>Adopción de metodologías activas:</b> Priorizar el aprendizaje basado en proyectos, estudios de caso y gamificación sobre las clases magistrales tradicionales.<br/><br/>

6. <b>Evaluación formativa continua:</b> Implementar evaluaciones frecuentes con retroalimentación inmediata y personalizada.<br/><br/>

7. <b>Desarrollo de materiales contextualizados:</b> Crear ejemplos, ejercicios y proyectos específicos para cada programa académico.<br/><br/>

<b>Para futuras investigaciones</b><br/><br/>
8. <b>Estudio longitudinal:</b> Realizar seguimiento a una cohorte de estudiantes durante toda su formación para evaluar la evolución del aprendizaje.<br/><br/>

9. <b>Investigación experimental:</b> Comparar diferentes metodologías de enseñanza en un diseño experimental controlado.<br/><br/>

10. <b>Factores motivacionales y emocionales:</b> Profundizar en la relación entre motivación, autoeficacia y rendimiento."""
    
    return ""

# ========== REFERENCIAS CONFIABLES ==========

REFERENCIAS_CONFIABLES = {
    'informatica': [
        "Tanenbaum, A. S. (2017). Organización de Computadores: Un Enfoque Estructurado. Pearson Educación.",
        "Stallings, W. (2016). Sistemas Operativos: Aspectos Internos y Principios de Diseño. Pearson.",
        "Laudon, K. C., & Laudon, J. P. (2021). Sistemas de Información Gerencial. Pearson.",
        "Pressman, R. S. (2021). Ingeniería del Software: Un Enfoque Práctico. McGraw-Hill.",
        "Joyanes Aguilar, L. (2017). Fundamentos de Programación. McGraw-Hill.",
        "Silberschatz, A., Korth, H. F., & Sudarshan, S. (2019). Fundamentos de Bases de Datos. McGraw-Hill.",
        "Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). Introduction to Algorithms. MIT Press."
    ],
    'educacion': [
        "Pérez Gómez, Á. I. (2021). La educación en la sociedad digital: desafíos y oportunidades. Morata.",
        "García Aretio, L. (2022). Educación a distancia y virtual: calidad, disrupción y aprendizajes. UNED.",
        "Coll, C. (2018). Psicología de la educación virtual: aprender y enseñar con tecnologías. UOC.",
        "Area Moreira, M. (2021). La integración de las TIC en educación: modelos y prácticas. Octaedro.",
        "Hernández Sampieri, R. (2021). Metodología de la Investigación. McGraw-Hill."
    ],
    'metodologia': [
        "Hernández Sampieri, R., Fernández Collado, C., & Baptista Lucio, P. (2021). Metodología de la Investigación (7ª ed.). McGraw-Hill.",
        "Bisquerra Alzina, R. (2016). Metodología de la investigación educativa. La Muralla.",
        "Sabino, C. A. (2014). El proceso de investigación. Episteme.",
        "Flick, U. (2015). El diseño de la investigación cualitativa. Morata."
    ]
}

def obtener_referencias(tema):
    tema_lower = tema.lower()
    if 'informática' in tema_lower or 'computación' in tema_lower or 'tecnología' in tema_lower:
        return REFERENCIAS_CONFIABLES['informatica']
    elif 'educación' in tema_lower or 'aprendizaje' in tema_lower or 'pedagogía' in tema_lower:
        return REFERENCIAS_CONFIABLES['educacion']
    else:
        return REFERENCIAS_CONFIABLES['metodologia']

# ========== GENERADOR DE PDF ==========

class GeneradorPDF:
    def __init__(self):
        self.correcciones = {
            'informatica': 'informática', 'tegnologia': 'tecnología', 'tegnologias': 'tecnologías',
            'desarollo': 'desarrollo', 'roberto': 'Roberto', 'juan': 'Juan', 'maria': 'María',
            'carlos': 'Carlos', 'laura': 'Laura', 'ana': 'Ana', 'pedro': 'Pedro',
            'cun': 'CUN', 'univercidad': 'universidad', 'profecional': 'profesional'
        }
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
    
    def corregir(self, texto):
        if not texto:
            return ""
        for error, correccion in self.correcciones.items():
            texto = texto.replace(error, correccion)
            texto = texto.replace(error.lower(), correccion.lower())
        return texto
    
    def validar_fecha(self, fecha_str):
        if not fecha_str:
            return datetime.now().strftime('%d/%m/%Y')
        patron = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
        match = re.search(patron, fecha_str)
        if match:
            return f"{match.group(1).zfill(2)}/{match.group(2).zfill(2)}/{match.group(3)}"
        return datetime.now().strftime('%d/%m/%Y')
    
    def generar_pdf(self, datos_usuario, opciones, texto_auto=""):
        """Genera PDF solo con las secciones seleccionadas"""
        
        # Limpiar datos
        nombre = self.corregir(datos_usuario.get('nombre', '')) or "Estudiante"
        tema = datos_usuario.get('tema', '') or "Tema de Investigación"
        asignatura = datos_usuario.get('asignatura', '') or "Asignatura"
        profesor = datos_usuario.get('profesor', '') or "Docente"
        institucion = datos_usuario.get('institucion', '') or "Institución Educativa"
        fecha_entrega = self.validar_fecha(datos_usuario.get('fecha_entrega', ''))
        
        # Obtener contenido del usuario o generar
        introduccion = datos_usuario.get('introduccion', '')
        if not introduccion or len(introduccion) < 100:
            introduccion = generar_contenido_variado('introduccion', tema, institucion, texto_auto)
        
        objetivos = datos_usuario.get('objetivos', '')
        if not objetivos or len(objetivos) < 100:
            objetivos = generar_contenido_variado('objetivos', tema, institucion)
        
        marco_teorico = datos_usuario.get('marco_teorico', '')
        if not marco_teorico or len(marco_teorico) < 100:
            marco_teorico = generar_contenido_variado('marco_teorico', tema, institucion)
        
        metodologia = datos_usuario.get('metodologia', '')
        if not metodologia or len(metodologia) < 100:
            metodologia = generar_contenido_variado('metodologia', tema, institucion)
        
        desarrollo = datos_usuario.get('desarrollo', '')
        if not desarrollo or len(desarrollo) < 100:
            desarrollo = generar_contenido_variado('desarrollo', tema, institucion)
        
        conclusiones = datos_usuario.get('conclusiones', '')
        if not conclusiones or len(conclusiones) < 100:
            conclusiones = generar_contenido_variado('conclusiones', tema, institucion)
        
        recomendaciones = datos_usuario.get('recomendaciones', '')
        if not recomendaciones or len(recomendaciones) < 100:
            recomendaciones = generar_contenido_variado('recomendaciones', tema, institucion)
        
        # Opciones de secciones
        incluir_resumen = opciones.get('incluir_resumen', False)
        incluir_resultados = opciones.get('incluir_resultados', True)
        incluir_recomendaciones = opciones.get('incluir_recomendaciones', True)
        
        # Referencias
        referencias = obtener_referencias(tema)
        
        # Generar PDF
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
        if asignatura:
            story.append(Paragraph(f"<b>Asignatura:</b> {asignatura}", self.estilos['TextoJustificado']))
        if profesor:
            story.append(Paragraph(f"<b>Docente:</b> {profesor}", self.estilos['TextoJustificado']))
        if institucion:
            story.append(Paragraph(f"<b>Institución:</b> {institucion}", self.estilos['TextoJustificado']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Fecha de entrega:</b> {fecha_entrega}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # ÍNDICE (solo secciones seleccionadas)
        story.append(Paragraph("ÍNDICE", self.estilos['Titulo1']))
        indices = []
        contador = 1
        
        if introduccion:
            indices.append(f"{contador}. INTRODUCCIÓN")
            contador += 1
        if objetivos:
            indices.append(f"{contador}. OBJETIVOS")
            contador += 1
        if marco_teorico:
            indices.append(f"{contador}. MARCO TEÓRICO")
            contador += 1
        if metodologia:
            indices.append(f"{contador}. METODOLOGÍA")
            contador += 1
        if desarrollo:
            indices.append(f"{contador}. DESARROLLO")
            contador += 1
        if incluir_resultados:
            indices.append(f"{contador}. RESULTADOS")
            contador += 1
        if conclusiones:
            indices.append(f"{contador}. CONCLUSIONES")
            contador += 1
        if incluir_recomendaciones and recomendaciones:
            indices.append(f"{contador}. RECOMENDACIONES")
            contador += 1
        if referencias:
            indices.append(f"{contador}. REFERENCIAS")
        
        for idx in indices:
            story.append(Paragraph(f"• {idx}", self.estilos['TextoJustificado']))
        story.append(PageBreak())
        
        # RESUMEN (opcional)
        if incluir_resumen and introduccion:
            story.append(Paragraph("RESUMEN", self.estilos['Titulo1']))
            resumen = introduccion[:500] + "..." if len(introduccion) > 500 else introduccion
            story.append(Paragraph(resumen, self.estilos['TextoJustificado']))
            story.append(PageBreak())
        
        # SECCIONES (solo las seleccionadas)
        contador = 1
        
        if introduccion:
            story.append(Paragraph(f"{contador}. INTRODUCCIÓN", self.estilos['Titulo1']))
            story.append(Paragraph(introduccion.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if objetivos:
            story.append(Paragraph(f"{contador}. OBJETIVOS", self.estilos['Titulo1']))
            story.append(Paragraph(objetivos.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if marco_teorico:
            story.append(Paragraph(f"{contador}. MARCO TEÓRICO", self.estilos['Titulo1']))
            story.append(Paragraph(marco_teorico.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if metodologia:
            story.append(Paragraph(f"{contador}. METODOLOGÍA", self.estilos['Titulo1']))
            story.append(Paragraph(metodologia.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if desarrollo:
            story.append(Paragraph(f"{contador}. DESARROLLO", self.estilos['Titulo1']))
            story.append(Paragraph(desarrollo.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if incluir_resultados:
            story.append(Paragraph(f"{contador}. RESULTADOS", self.estilos['Titulo1']))
            story.append(Paragraph("A continuación se presentan los resultados obtenidos:", self.estilos['TextoJustificado']))
            
            # Tabla de resultados
            data = [
                ['Indicador', 'Valor obtenido', 'Observación'],
                ['Nivel de conocimiento teórico', '72.4/100', 'Dominio moderado'],
                ['Habilidades prácticas', '68.7/100', 'Requiere refuerzo'],
                ['Actitud hacia el aprendizaje', 'Positiva (72%)', 'Buena disposición'],
                ['Correlación teoría-práctica', 'r = 0.62', 'Relación positiva moderada']
            ]
            
            tabla = Table(data, colWidths=[1.8*inch, 1.5*inch, 2*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
            ]))
            
            story.append(tabla)
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Tabla 1.</b> Resumen de resultados obtenidos en la investigación.", self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if conclusiones:
            story.append(Paragraph(f"{contador}. CONCLUSIONES", self.estilos['Titulo1']))
            story.append(Paragraph(conclusiones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if incluir_recomendaciones and recomendaciones:
            story.append(Paragraph(f"{contador}. RECOMENDACIONES", self.estilos['Titulo1']))
            story.append(Paragraph(recomendaciones.replace('\n', '<br/>'), self.estilos['TextoJustificado']))
            story.append(PageBreak())
            contador += 1
        
        if referencias:
            story.append(Paragraph(f"{contador}. REFERENCIAS", self.estilos['Titulo1']))
            for i, ref in enumerate(referencias, 1):
                story.append(Paragraph(f"{i}. {ref}", self.estilos['TextoJustificado']))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        return filename, filepath

generador = GeneradorPDF()

# ========== EJEMPLOS ==========

EJEMPLOS = {
    'informatica': {
        'tema': 'Impacto de la Informática en la Educación Superior',
        'nombre': 'Ana María Rodríguez',
        'profesor': 'Dr. Carlos Mendoza',
        'asignatura': 'Metodología de la Investigación',
        'institucion': 'Universidad Tecnológica',
        'introduccion': 'La informática ha transformado radicalmente la educación superior en la última década. Este estudio analiza el nivel de competencia digital de los estudiantes y su relación con el rendimiento académico.',
        'objetivos': 'Objetivo General: Analizar el impacto de la informática en el proceso de aprendizaje. Objetivos Específicos: 1. Evaluar el nivel de competencia digital. 2. Identificar brechas en el conocimiento. 3. Proponer estrategias de mejora.',
        'marco_teorico': 'Según diversos autores, la competencia digital es fundamental en el siglo XXI. Tanenbaum (2017) establece los fundamentos de la arquitectura de computadores. Stallings (2016) aborda los sistemas operativos.',
        'metodologia': 'Enfoque mixto con diseño transversal. Muestra: 120 estudiantes. Instrumentos: cuestionario, prueba de conocimientos y entrevistas.',
        'desarrollo': 'Los resultados muestran que el 65% de los estudiantes tiene un dominio básico de informática. Se identificaron correlaciones positivas entre horas de estudio y rendimiento.',
        'conclusiones': 'Se concluye que la informática es fundamental en la educación actual. Se recomienda fortalecer los programas de alfabetización digital.',
        'recomendaciones': '1. Implementar cursos de nivelación. 2. Actualizar infraestructura tecnológica. 3. Capacitar docentes en metodologías activas.'
    }
}

# ========== RUTAS ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        modo = datos.get('modo', 'auto')
        texto_auto = datos.get('texto_completo', '') if modo == 'auto' else ''
        
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
        
        # Si es modo rápido y hay tema pero no texto
        if modo == 'rapido' and datos.get('tema') and not texto_auto:
            texto_auto = f"Análisis sobre {datos.get('tema')}. Este informe explora los conceptos fundamentales y las aplicaciones prácticas."
        
        filename, filepath = generador.generar_pdf(datos_usuario, opciones, texto_auto)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/descargar/{filename}'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"Error: {str(e)}"}), 500

@app.route('/ejemplo', methods=['POST'])
def ejemplo():
    tipo = request.json.get('tipo', 'informatica')
    ejemplo = EJEMPLOS.get(tipo, EJEMPLOS['informatica'])
    return jsonify({
        'success': True,
        'datos': ejemplo
    })

@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(
        os.path.join('informes_generados', filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)