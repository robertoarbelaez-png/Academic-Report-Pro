from flask import Flask, render_template, request, jsonify, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from werkzeug.utils import secure_filename
import os, uuid, requests, re, html
from datetime import datetime

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -------- CONFIG NORMAS --------
NORMAS = {
    "apa7": {"font": "Times-Roman", "size": 12},
    "icontec": {"font": "Helvetica", "size": 12},
    "ieee": {"font": "Times-Roman", "size": 10}
}

# -------- UTIL --------
def limpiar(texto):
    if not texto:
        return ""
    texto = html.escape(texto)
    texto = texto.replace("\n", "<br/>")
    texto = texto.replace("CONCLUSIONS", "CONCLUSIONES")
    texto = texto.replace("INFORMÉ", "INFORME")
    return texto

# -------- FALLBACK LOCAL --------
def contenido_local(tema):
    return {
        "introduccion": f"Este informe analiza {tema}.",
        "objetivos": "Analizar el tema.",
        "marco_teorico": "Bases teóricas del tema.",
        "metodologia": "Investigación descriptiva.",
        "desarrollo": f"Resultados sobre {tema}.",
        "conclusiones": "Se concluye que es importante.",
        "recomendaciones": "Se recomienda seguir investigando."
    }

# -------- IA --------
def generar_ia(tema):
    if not GROQ_API_KEY:
        return None

    try:
        prompt = f"""
Genera un informe académico completo sobre: {tema}

SECCIONES:
INTRODUCCIÓN
OBJETIVOS
MARCO TEÓRICO
METODOLOGÍA
DESARROLLO
CONCLUSIONES
RECOMENDACIONES

Todo en español y bien estructurado.
"""
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }

        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)

        if res.status_code != 200:
            return None

        texto = res.json()['choices'][0]['message']['content']

        secciones = {}
        for sec in ["INTRODUCCIÓN","OBJETIVOS","MARCO TEÓRICO","METODOLOGÍA","DESARROLLO","CONCLUSIONES","RECOMENDACIONES"]:
            match = re.search(rf"{sec}:(.*?)(?=\n[A-Z]|$)", texto, re.DOTALL)
            secciones[sec.lower()] = match.group(1).strip() if match else ""

        return secciones

    except:
        return None

# -------- PDF --------
def generar_pdf(datos, secciones):
    filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
    path = os.path.join('informes_generados', filename)

    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Tema: {datos['tema']}", styles['Normal']))
    story.append(Paragraph(f"Autor: {datos['nombre']}", styles['Normal']))
    story.append(PageBreak())

    for titulo, contenido in secciones.items():
        story.append(Paragraph(titulo.upper(), styles['Heading2']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(limpiar(contenido), styles['Normal']))
        story.append(PageBreak())

    doc.build(story)
    return filename, path

# -------- RUTAS --------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    datos = request.json
    tema = datos.get('tema', '').strip()

    if len(tema) < 3:
        return jsonify({'success': False, 'error': 'Tema inválido'})

    modo = datos.get('modo', 'auto')

    # 🔥 MODO MANUAL
    if modo == "manual":
        secciones = {
            "introduccion": datos.get('introduccion', ''),
            "objetivos": datos.get('objetivos', ''),
            "marco_teorico": "",
            "metodologia": "",
            "desarrollo": "",
            "conclusiones": datos.get('conclusiones', ''),
            "recomendaciones": ""
        }

    else:
        secciones = generar_ia(tema)
        if not secciones:
            secciones = contenido_local(tema)

    filename, path = generar_pdf(datos, secciones)

    return jsonify({
        "success": True,
        "download_url": f"/descargar/{filename}"
    })

@app.route('/descargar/<filename>')
def descargar(filename):
    safe = secure_filename(filename)
    path = os.path.join('informes_generados', safe)

    if not os.path.exists(path):
        return "No encontrado", 404

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
