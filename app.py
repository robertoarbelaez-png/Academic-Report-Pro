from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os, uuid, re, requests
from datetime import datetime

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ================= LIMPIEZA =================
def limpiar_texto(texto):
    if not texto:
        return ""
    
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
    texto = texto.replace("**", "")
    texto = texto.replace("\n", "<br/><br/>")
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

# ================= EXTRACCIÓN PERFECTA =================
def dividir_secciones(texto):
    secciones = {
        "INTRODUCCIÓN": "",
        "OBJETIVOS": "",
        "MARCO TEÓRICO": "",
        "METODOLOGÍA": "",
        "DESARROLLO": "",
        "CONCLUSIONES": "",
        "RECOMENDACIONES": ""
    }

    actual = None

    for linea in texto.split("\n"):
        linea = linea.strip()

        if "INTRODUCCIÓN" in linea.upper():
            actual = "INTRODUCCIÓN"
            continue
        elif "OBJETIVOS" in linea.upper():
            actual = "OBJETIVOS"
            continue
        elif "MARCO TEÓRICO" in linea.upper():
            actual = "MARCO TEÓRICO"
            continue
        elif "METODOLOGÍA" in linea.upper():
            actual = "METODOLOGÍA"
            continue
        elif "DESARROLLO" in linea.upper():
            actual = "DESARROLLO"
            continue
        elif "CONCLUSIONES" in linea.upper():
            actual = "CONCLUSIONES"
            continue
        elif "RECOMENDACIONES" in linea.upper():
            actual = "RECOMENDACIONES"
            continue

        if actual:
            secciones[actual] += linea + " "

    return secciones

# ================= CONTENIDO FALLBACK =================
def contenido_local(tema):
    return {
        "INTRODUCCIÓN": f"Este informe analiza {tema} desde una perspectiva académica.",
        "OBJETIVOS": f"Analizar {tema} y comprender su impacto.",
        "MARCO TEÓRICO": f"Se fundamenta en teorías relacionadas con {tema}.",
        "METODOLOGÍA": "Enfoque descriptivo del estudio.",
        "DESARROLLO": f"Se desarrolla el tema {tema} con análisis detallado.",
        "CONCLUSIONES": f"{tema} es relevante en el contexto actual.",
        "RECOMENDACIONES": "Se recomienda profundizar en el estudio."
    }

# ================= RUTA PRINCIPAL =================
@app.route('/')
def index():
    return render_template('index.html')

# ================= GENERAR =================
@app.route('/generar', methods=['POST'])
def generar():
    try:
        datos = request.json
        tema = datos.get('tema', '')

        if not tema:
            return jsonify({'success': False, 'error': 'Tema requerido'}), 400

        contenido = None

        # ===== IA =====
        if GROQ_API_KEY:
            try:
                prompt = f"""
Genera un INFORME ACADÉMICO con esta estructura EXACTA:

INTRODUCCIÓN
OBJETIVOS
MARCO TEÓRICO
METODOLOGÍA
DESARROLLO
CONCLUSIONES
RECOMENDACIONES

Tema: {tema}

NO uses símbolos como ** ni markdown.
"""

                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 3000
                    },
                    timeout=40
                )

                if response.status_code == 200:
                    contenido = response.json()['choices'][0]['message']['content']

            except:
                pass

        if not contenido:
            secciones = contenido_local(tema)
        else:
            secciones = dividir_secciones(contenido)

            # fallback si alguna sección viene vacía
            fallback = contenido_local(tema)
            for key in secciones:
                if len(secciones[key]) < 20:
                    secciones[key] = fallback[key]

        # ===== PDF =====
        filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
        path = os.path.join('informes_generados', filename)

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='Titulo',
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12
        ))

        story = []

        # PORTADA
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(tema.upper(), styles['Normal']))
        story.append(PageBreak())

        # ÍNDICE
        story.append(Paragraph("ÍNDICE", styles['Titulo']))
        for i, t in enumerate(secciones.keys(), 1):
            story.append(Paragraph(f"{i}. {t}", styles['Normal']))
        story.append(PageBreak())

        # CONTENIDO
        for i, (titulo, texto) in enumerate(secciones.items(), 1):
            story.append(Paragraph(f"{i}. {titulo}", styles['Titulo']))
            story.append(Paragraph(limpiar_texto(texto), styles['Normal']))
            story.append(PageBreak())

        doc.build(story)

        return jsonify({
            'success': True,
            'download_url': f'/descargar/{filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ================= DESCARGAR =================
@app.route('/descargar/<filename>')
def descargar(filename):
    return send_file(os.path.join('informes_generados', filename), as_attachment=True)

if __name__ == '__main__':
    app.run()
