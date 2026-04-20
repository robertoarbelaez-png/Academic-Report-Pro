from flask import Flask, render_template, request, jsonify, send_file
import os, uuid, requests, json, html
from werkzeug.utils import secure_filename
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
os.makedirs('informes_generados', exist_ok=True)

# API
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -------- CONTENIDO LOCAL --------
def contenido_local(tema):
    return {
        "introduccion": f"Este informe analiza {tema}. Se abordan sus aspectos principales.",
        "objetivos": "Analizar el tema y comprender su impacto en el contexto actual.",
        "marco_teorico": f"El marco teórico de {tema} se fundamenta en investigaciones previas.",
        "metodologia": "Se emplea un enfoque descriptivo basado en revisión documental.",
        "desarrollo": f"Se analizan los principales aspectos relacionados con {tema}.",
        "conclusiones": "Se concluye que el tema es relevante y requiere mayor estudio.",
        "recomendaciones": "Se recomienda profundizar en investigaciones futuras.",
        "referencias": "Fuentes académicas consultadas."
    }

# -------- IA --------
def generar_ia(tema):
    if not GROQ_API_KEY:
        return None

    try:
        prompt = f"""
Genera un informe académico sobre: "{tema}"

Responde SOLO en JSON con esta estructura:

{{
  "introduccion": "",
  "objetivos": "",
  "marco_teorico": "",
  "metodologia": "",
  "desarrollo": "",
  "conclusiones": "",
  "recomendaciones": "",
  "referencias": ""
}}

Todo en español, bien desarrollado.
"""

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)

        if res.status_code != 200:
            return None

        texto = res.json()['choices'][0]['message']['content'].strip()

        if texto.startswith("```"):
            texto = texto.replace("```json", "").replace("```", "").strip()

        return json.loads(texto)

    except Exception as e:
        print("Error IA:", e)
        return None

# -------- SEGURIDAD IA --------
def asegurar_secciones(secciones, tema):
    fallback = contenido_local(tema)

    for key in fallback:
        if key not in secciones or not str(secciones[key]).strip():
            secciones[key] = fallback[key]

    return secciones

# -------- LIMPIAR TEXTO --------
def limpiar(texto):
    texto = html.escape(texto)
    texto = texto.replace("\n", "<br/>")
    return texto

# -------- PDF --------
def generar_pdf(datos, secciones):
    filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
    path = os.path.join('informes_generados', filename)

    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []

    # PORTADA
    story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Tema: {datos['tema']}", styles['Normal']))
    story.append(Paragraph(f"Autor: {datos['nombre']}", styles['Normal']))
    story.append(PageBreak())

    # SECCIONES
    for titulo, contenido in secciones.items():
        story.append(Paragraph(titulo.upper(), styles['Heading2']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(limpiar(contenido), styles['Normal']))
        story.append(PageBreak())

    doc.build(story)
    return filename

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

    nombre = datos.get('nombre', 'Estudiante')

    secciones = generar_ia(tema)

    if not secciones:
        secciones = contenido_local(tema)
    else:
        secciones = asegurar_secciones(secciones, tema)

    filename = generar_pdf({'tema': tema, 'nombre': nombre}, secciones)

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

if __name__ == '__main__':
    app.run(debug=True)
