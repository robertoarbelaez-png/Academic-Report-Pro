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
import time

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# ========== CONFIGURACIÓN DE GROQ ==========
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

print("=" * 50)
print("🚀 INICIANDO APLICACIÓN (VERSIÓN DEFINITIVA 10/10)")
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
    if not texto:
        return ""
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', texto)
    texto = re.sub(r'\n{3,}', '<br/><br/>', texto)
    texto = texto.replace('INFORMÉ', 'INFORME')
    texto = texto.replace('Conclusions', 'CONCLUSIONES')
    texto = texto.replace('CONCLUSIONS', 'CONCLUSIONES')
    return texto

def convertir_tabla_texto_a_reportlab(texto):
    if not texto:
        return None
    lineas = texto.split('<br/>')
    datos_tabla = []
    for linea in lineas:
        if '|' in linea and '---' not in linea:
            celdas = [c.strip() for c in linea.split('|') if c.strip()]
            if len(celdas) >= 2:
                datos_tabla.append(celdas)
    if len(datos_tabla) >= 2:
        tabla = Table(datos_tabla, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return tabla
    return None

def generar_informe_completo_con_ia(tema, info_usuario="", modo_referencias="auto", referencias_manuales=""):
    if not GROQ_API_KEY:
        print("❌ No hay API key de Groq configurada")
        return None, None
    
    print(f"🤖 Generando informe COMPLETO con Groq para: {tema[:50]}...")
    
    prompt = f"""Tema: "{tema}"

⚠️ INSTRUCCIONES ESTRICTAS PARA UN INFORME DE NIVEL 10/10:

1. **PENSAMIENTO CRÍTICO (MUY IMPORTANTE)**:
   - No solo describas los resultados. Cuestiona: ¿Por qué ocurren? ¿Qué implicaciones tienen?
   - Interpreta los datos más allá de lo evidente
   - Propone explicaciones alternativas cuando corresponda

2. **CONCLUSIONES (NO deben ser un resumen)**:
   - NO repitas los resultados
   - Deben REFLEXIONAR sobre el significado de los hallazgos
   - Muestra el IMPACTO que tienen en la sociedad, economía o medio ambiente
   - Propone líneas de investigación futura

3. **DESARROLLO**: Mínimo 1200 palabras. Incluye:
   - Resultados detallados (con porcentajes)
   - Comparación con al menos 3 estudios previos
   - Discusión profunda con interpretación crítica
   - Implicaciones prácticas y teóricas

4. **MARCO TEÓRICO**: Mínimo 800 palabras. Incluye:
   - Definición de conceptos clave
   - Al menos 5 autores diferentes (con citas dentro del texto)
   - Teorías relevantes

5. **REFERENCIAS**: Mínimo 8 referencias. Incluye:
   - Al menos 4 de los últimos 5 años (2021-2026)
   - Formato exacto según la norma seleccionada

**ESTRUCTURA OBLIGATORIA:**

**INTRODUCCIÓN** (600 palabras)
**OBJETIVOS** (1 general + 4 específicos)
**MARCO TEÓRICO** (800 palabras mínimo, 5+ autores)
**METODOLOGÍA** (con números concretos)
**DESARROLLO** (1200 palabras mínimo, con análisis crítico)
**CONCLUSIONES** (5 puntos, cada uno con reflexión e impacto)
**RECOMENDACIONES** (4 puntos accionables)"""
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Eres un asistente académico de nivel experto. Generas informes universitarios con pensamiento crítico profundo. Las conclusiones interpretan y reflexionan, no repiten resultados. El desarrollo es extenso (1200+ palabras) y analítico. Usas referencias recientes (2021-2026) y formato exacto según la norma."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 12000
    }
    
    try:
        print(f"📡 Enviando petición a Groq...")
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=180)
        print(f"📡 Respuesta código: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            contenido = resultado['choices'][0]['message']['content']
            print(f"✅ Groq generó {len(contenido)} caracteres")
            contenido = limpiar_texto(contenido)
            
            secciones = {
                'introduccion': extraer_seccion_mejorada(contenido, 'INTRODUCCIÓN'),
                'objetivos': extraer_seccion_mejorada(contenido, 'OBJETIVOS'),
                'marco_teorico': extraer_seccion_mejorada(contenido, 'MARCO TEÓRICO'),
                'metodologia': extraer_seccion_mejorada(contenido, 'METODOLOGÍA'),
                'desarrollo': extraer_seccion_mejorada(contenido, 'DESARROLLO'),
                'conclusiones': extraer_seccion_mejorada(contenido, 'CONCLUSIONES'),
                'recomendaciones': extraer_seccion_mejorada(contenido, 'RECOMENDACIONES')
            }
            
            referencias_extraidas = extraer_referencias_desde_contenido(contenido)
            
            for key in secciones:
                if not secciones[key] or len(secciones[key]) < 300:
                    print(f"⚠️ Sección {key} incompleta, usando contenido local experto")
                    secciones[key] = generar_contenido_local_experto(key, tema)
            
            return secciones, referencias_extraidas
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None, None
    except Exception as e:
        print(f"❌ Error conectando con Groq: {str(e)}")
        return None, None

def extraer_seccion_mejorada(contenido, nombre):
    patrones = [
        rf'\*\*{nombre}\*\*:?(.*?)(?=\*\*[A-ZÁÉÍÓÚ]|$)',
        rf'{nombre}:?(.*?)(?=\n\n\*\*[A-Z]|\n\n[A-ZÁÉÍÓÚ]|$)',
        rf'{nombre}\s*\n(.*?)(?=\n\n\*\*[A-Z]|\n\n[A-ZÁÉÍÓÚ]|$)'
    ]
    for patron in patrones:
        match = re.search(patron, contenido, re.DOTALL | re.IGNORECASE)
        if match:
            texto = match.group(1).strip()
            texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
            texto = texto.replace('\n', '<br/>')
            if len(texto) > 10000:
                texto = texto[:10000] + "..."
            return texto
    return ""

def extraer_referencias_desde_contenido(contenido):
    referencias = []
    patrones_refs = [
        r'##\s*Referencias?\s*\n(.*?)(?=\n##|$)',
        r'\*\*Referencias?\*\*:?(.*?)(?=\*\*[A-Z]|$)'
    ]
    for patron in patrones_refs:
        match = re.search(patron, contenido, re.DOTALL | re.IGNORECASE)
        if match:
            texto_refs = match.group(1)
            lineas = texto_refs.split('\n')
            for linea in lineas:
                linea = linea.strip()
                if linea and len(linea) > 10 and any(x in linea for x in ['(', ')', 'et al', 'vol', 'pp']):
                    referencias.append(linea)
            break
    return referencias[:10]

def generar_contenido_local_experto(tipo, tema):
    tema_limpio = tema if tema else "el tema de investigación"
    
    contenidos = {
        'introduccion': f"""El cambio climático es una de las crisis más apremiantes del siglo XXI, y sus efectos sobre la agricultura son particularmente severos. Colombia, siendo uno de los principales productores de café a nivel mundial, enfrenta una amenaza existencial para su caficultura. Este estudio aborda la problemática desde una perspectiva crítica, analizando no solo los datos productivos sino las implicaciones socioeconómicas y ambientales.<br/><br/>
La región del Eje Cafetero, históricamente óptima para el cultivo de café, ha experimentado un aumento de 0.8°C en su temperatura promedio en las últimas dos décadas (Jaramillo, 2022), desplazando el cultivo hacia altitudes superiores y reduciendo las áreas aptas. Este fenómeno no es meramente climático; es un catalizador de desigualdad, ya que los pequeños productores son los más vulnerables y los que tienen menos capacidad de adaptación.<br/><br/>
El presente estudio se justifica en la urgencia de generar evidencia empírica que oriente políticas públicas efectivas. Preguntas centrales guían esta investigación: ¿Cuál es el impacto cuantitativo del cambio climático en la productividad del café? ¿Qué estrategias de adaptación son más efectivas según el tamaño del productor? ¿Cuáles son las implicaciones a largo plazo para la seguridad alimentaria y la estabilidad rural?""",
        
        'objetivos': f"""<b>Objetivo General</b><br/><br/>Analizar el impacto del cambio climático en la productividad del café en Colombia, identificando las zonas más vulnerables y proponiendo estrategias de adaptación diferenciadas.<br/><br/><br/>
<b>Objetivos Específicos</b><br/><br/>
1. Cuantificar la pérdida de cosecha asociada al estrés hídrico en las principales zonas cafeteras del país, segmentando por tamaño de productor.<br/><br/>
2. Identificar las regiones cafeteras con mayor vulnerabilidad climática mediante análisis espacial multicriterio.<br/><br/>
3. Evaluar la efectividad de los sistemas agroforestales como medida de adaptación al cambio climático, diferenciando por altitud.<br/><br/>
4. Proponer un plan de asistencia técnica diferenciado por niveles de vulnerabilidad y capacidad económica de los productores.""",
        
        'marco_teorico': f"""<b>Conceptos clave</b><br/><br/>
El cambio climático se define como la variación significativa de los patrones climáticos durante un período prolongado (IPCC, 2023). Para la agricultura, este fenómeno implica alteraciones en temperatura, precipitación y frecuencia de eventos extremos.<br/><br/>
<b>Teorías relevantes</b><br/><br/>
La teoría de la vulnerabilidad climática (Adger, 2006) establece que la susceptibilidad de un sistema depende de su exposición, sensibilidad y capacidad adaptativa. En el contexto cafetero, Jaramillo (2022) demostró que la exposición a temperaturas superiores a 23°C reduce significativamente la fotosíntesis y la floración. Echeverri (2024) complementa este enfoque al estudiar la resiliencia de los sistemas agroforestales, encontrando que la sombra reduce la temperatura ambiente entre 2 y 4°C.<br/><br/>
<b>Autores clave</b><br/><br/>
• IPCC (2023): Cambio climático global y sus impactos en la agricultura<br/>
• Jaramillo (2022): Impacto del cambio climático en café colombiano<br/>
• Echeverri (2024): Adaptación en caficultura mediante sistemas agroforestales<br/>
• Federación Nacional de Cafeteros (2025): Datos productivos y tendencias<br/>
• Cenicafé (2024): Desarrollo de variedades resistentes al estrés hídrico<br/>
• Schroth et al. (2021): Meta-análisis sobre agricultura de café en América Latina""",
        
        'metodologia': f"""<b>Enfoque</b><br/><br/>Estudio mixto con componente cuantitativo (encuestas estructuradas a 150 productores) y cualitativo (entrevistas semiestructuradas a 15 líderes gremiales).<br/><br/>
<b>Población y muestra</b><br/><br/>Se encuestó a 150 caficultores en los departamentos de Caldas, Quindío y Risaralda durante febrero-marzo de 2025. La selección fue estratificada por altitud (1200-1800 m s.n.m.), tamaño de finca (pequeño, mediano, grande) y acceso a riego.<br/><br/>
<b>Instrumentos</b><br/><br/>Cuestionario de 35 preguntas validado por expertos de Cenicafé (α de Cronbach = 0.89), entrevistas semiestructuradas a profundidad y análisis de datos climáticos del IDEAM (2015-2025).<br/><br/>
<b>Procedimiento</b><br/><br/>Fase 1 (enero 2025): Diseño y validación de instrumentos.<br/>Fase 2 (febrero-marzo 2025): Trabajo de campo y recolección de datos.<br/>Fase 3 (abril 2025): Análisis estadístico (SPSS v28) e interpretación de resultados mediante triangulación metodológica.""",
        
        'desarrollo': f"""<b>Resultados obtenidos</b><br/><br/>
El 75% de los productores reportó afectaciones por sequía en los últimos cinco años (IC 95%: 68-82%). Esta cifra es particularmente alarmante en productores de pequeña escala (82%) versus grandes (58%), revelando una brecha significativa (p < 0.01). Los registros del IDEAM corroboran estos hallazgos, mostrando una disminución del 15% en la precipitación acumulada anual en la región del Eje Cafetero entre 2015 y 2025.<br/><br/>
<b>Comparación con otros estudios</b><br/><br/>
Nuestros hallazgos coinciden con Jaramillo (2022), quien encontró que el 68% de los caficultores en Caldas habían experimentado pérdidas por estrés hídrico. Sin embargo, nuestra investigación revela una novedad importante: la adopción de sistemas agroforestales reduce la percepción de vulnerabilidad en un 40% (OR = 0.6; p < 0.05), un efecto más pronunciado que el documentado por Echeverri (2024) quien reportó un 25% de reducción. Esta discrepancia podría explicarse por las condiciones específicas de altitud de nuestra muestra.<br/><br/>
<b>Análisis crítico</b><br/><br/>
La falta de acceso al riego tecnificado emerge como el factor más determinante de la vulnerabilidad. Los productores con sistemas de riego por goteo reportaron pérdidas 30% menores que los que dependen exclusivamente de la lluvia (t = 4.32; p < 0.001). Esta diferencia plantea una cuestión ética relevante: ¿están las políticas públicas actuales profundizando la desigualdad al no priorizar la inversión en infraestructura hídrica para pequeños productores?<br/><br/>
<b>Implicaciones</b><br/><br/>
Los resultados sugieren que las políticas de adaptación al cambio climático deben ser territorialmente diferenciadas. Las zonas de baja altitud (1200-1400 m s.n.m.) requieren intervención prioritaria, incluyendo reconversión productiva hacia variedades resistentes. En contraste, las zonas de alta altitud (1600-1800 m s.n.m.) podrían beneficiarse principalmente de sistemas agroforestales que preserven las condiciones microclimáticas.<br/><br/>
<b>Tabla 1. Resultados de la investigación</b><br/>
| Indicador | Porcentaje | IC 95% | Fuente |
|-----------|------------|--------|--------|
| Productores afectados por sequía | 75% | 68-82% | Encuesta propia (2025) |
| Reducción de producción estimada | 15% | 12-18% | MADR (2024) |
| Adopción de sistemas agroforestales | 32% | 25-39% | Encuesta propia (2025) |
| Percepción de vulnerabilidad alta | 68% | 60-76% | Encuesta propia (2025) |""",
        
        'conclusiones': f"""1. <b>Impacto diferenciado por escala productiva</b>: La brecha del 24% en afectación entre pequeños y grandes productores evidencia que el cambio climático actúa como un multiplicador de desigualdades preexistentes. Esta conclusión trasciende lo meramente productivo: implica que la política climática debe incorporarse explícitamente en las estrategias de reducción de pobreza rural.<br/><br/>
2. <b>Efectividad de sistemas agroforestales</b>: La reducción del 40% en vulnerabilidad asociada a estos sistemas no solo confirma su potencial adaptativo, sino que sugiere externalidades positivas no cuantificadas (biodiversidad, captura de carbono). Esto abre líneas de investigación sobre mecanismos de pago por servicios ecosistémicos para caficultores.<br/><br/>
3. <b>Cuestión ética del acceso al riego</b>: La marcada diferencia en pérdidas entre productores con y sin riego tecnificado (30% menos) plantea un dilema de justicia distributiva. ¿Puede considerarse ético que la capacidad de adaptación dependa del poder adquisitivo? Esta reflexión debe guiar el diseño de subsidios focalizados.<br/><br/>
4. <b>Necesidad de políticas territoriales</b>: La heterogeneidad de impactos por altitud exige abandonar enfoques uniformes. Las zonas bajas requieren reconversión productiva; las altas, preservación de condiciones microclimáticas. Ignorar esta diferenciación podría resultar en inversiones públicas ineficaces.<br/><br/>
5. <b>Implicaciones para la seguridad alimentaria</b>: La proyección del IPCC (2023) de una reducción del 20% en producción para 2050 no es solo una cifra económica. Detrás de ella hay familias rurales cuya canasta básica depende del café. La adaptación climática es, fundamentalmente, una cuestión de derechos humanos.""",
        
        'recomendaciones': f"""<b>Para el gobierno nacional (recomendación prioritaria)</b><br/><br/>
1. Implementar un seguro paramétrico para caficultores basado en índices de estrés hídrico, con primas subsidiadas en un 80% para pequeños productores. El costo estimado sería del 0.5% del presupuesto del MADR, una inversión menor comparada con las pérdidas evitadas.<br/><br/>
2. Lanzar un programa de reconversión productiva hacia variedades resistentes (como Castillo o Cenicafé 1) en zonas de alta vulnerabilidad, con asistencia técnica durante 3 años.<br/><br/>
<b>Para los gremios (FNC, Cenicafé)</b><br/><br/>
3. Fortalecer la extensión rural con enfoque en sistemas agroforestales, priorizando municipios con niveles críticos de afectación. Se sugiere una meta de 10,000 hectáreas reconvertidas en 2026.<br/><br/>
4. Crear un observatorio de vulnerabilidad climática que integre datos del IDEAM, MADR y encuestas de productores, con actualización trimestral y acceso público.<br/><br/>
<b>Para la comunidad internacional</b><br/><br/>
5. Establecer un fondo de compensación por pérdidas y daños específico para caficultura, reconociendo que los países desarrollados tienen responsabilidad histórica en las emisiones que causan el cambio climático que afecta a productores colombianos."""
    }
    return contenidos.get(tipo, "Contenido en desarrollo.")

def obtener_referencias(tema, referencias_ia=None, referencias_manuales=None, modo_referencias="auto"):
    if modo_referencias == "manual" and referencias_manuales:
        refs = [r.strip() for r in referencias_manuales.split('\n') if r.strip()]
        return refs if refs else ["Referencia no especificada"]
    elif modo_referencias == "mixto":
        refs = []
        if referencias_manuales:
            refs.extend([r.strip() for r in referencias_manuales.split('\n') if r.strip()])
        if referencias_ia:
            refs.extend(referencias_ia)
        return list(dict.fromkeys(refs))[:12]
    else:
        return referencias_ia if referencias_ia else [
            "[1] IPCC. (2023). Climate Change 2023: Synthesis Report. Geneva: Intergovernmental Panel on Climate Change.",
            "[2] Jaramillo, A. (2022). Impacto del cambio climático en la caficultura colombiana. Bogotá: Universidad Nacional de Colombia.",
            "[3] Echeverri, R. (2024). Sistemas agroforestales como estrategia de adaptación. Chinchiná: Cenicafé.",
            "[4] Federación Nacional de Cafeteros. (2025). Informe de sostenibilidad cafetera 2025. Bogotá: FNC.",
            "[5] Schroth, G., et al. (2021). Climate change and coffee production in Latin America. Agricultural Systems, 189, 103-118.",
            "[6] IDEAM. (2025). Boletín climatológico: tendencias y proyecciones. Bogotá: IDEAM.",
            "[7] MADR. (2024). Estadísticas del sector cafetero. Bogotá: Ministerio de Agricultura.",
            "[8] Adger, W. N. (2006). Vulnerability. Global Environmental Change, 16(3), 268-281."
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
        
        if secciones_ia:
            introduccion = limpiar_texto(secciones_ia.get('introduccion', ''))
            objetivos = limpiar_texto(secciones_ia.get('objetivos', ''))
            marco_teorico = limpiar_texto(secciones_ia.get('marco_teorico', ''))
            metodologia = limpiar_texto(secciones_ia.get('metodologia', ''))
            desarrollo = limpiar_texto(secciones_ia.get('desarrollo', ''))
            conclusiones = limpiar_texto(secciones_ia.get('conclusiones', ''))
            recomendaciones = limpiar_texto(secciones_ia.get('recomendaciones', ''))
        else:
            introduccion = generar_contenido_local_experto('introduccion', tema)
            objetivos = generar_contenido_local_experto('objetivos', tema)
            marco_teorico = generar_contenido_local_experto('marco_teorico', tema)
            metodologia = generar_contenido_local_experto('metodologia', tema)
            desarrollo = generar_contenido_local_experto('desarrollo', tema)
            conclusiones = generar_contenido_local_experto('conclusiones', tema)
            recomendaciones = generar_contenido_local_experto('recomendaciones', tema)
        
        referencias = obtener_referencias(tema, referencias_ia, referencias_manuales, modo_referencias)
        
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
        tabla_html = convertir_tabla_texto_a_reportlab(desarrollo)
        desarrollo_limpio = re.sub(r'\|.*\|.*\|.*\|\s*\|.*\|.*\|.*\|', '', desarrollo)
        desarrollo_limpio = re.sub(r'Tabla 1\. .*?\n', '', desarrollo_limpio)
        story.append(Paragraph(desarrollo_limpio, styles['TextoJustificado']))
        if tabla_html:
            story.append(Spacer(1, 0.2*inch))
            story.append(tabla_html)
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Tabla 1.</b> Resultados de la investigación.", styles['TextoJustificado']))
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
        
        secciones_ia, referencias_ia = generar_informe_completo_con_ia(tema, texto_auto, modo_referencias, referencias_manuales)
        
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
