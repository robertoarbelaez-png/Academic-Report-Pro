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
    texto = texto.replace('INFORMÉ', 'INFORME')
    texto = texto.replace('CONCLUSIONS', 'CONCLUSIONES')
    texto = re.sub(r'<br/?>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

# ================= CONTENIDO LOCAL =================
def contenido_local(tema):
    return {
        "introduccion": f"Este informe analiza {tema} desde una perspectiva académica.",
        "objetivos": f"Analizar {tema} y comprender su impacto.",
        "marco_teorico": f"Se fundamenta en teorías relacionadas con {tema}.",
        "metodologia": "Enfoque descriptivo del estudio.",
        "desarrollo": f"Se desarrolla el tema {tema} con análisis crítico.",
        "conclusiones": f"{tema} es relevante en el contexto actual.",
        "recomendaciones": "Se recomienda profundizar en el tema."
    }

# ================= RUTAS =================
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generar', methods=['POST'])
def generar():
    try:
        data = request.json
        tema = data.get('tema', '')

        if not tema or len(tema) < 3:
            return jsonify({"success": False, "error": "Tema inválido"}), 400

        secciones = None

        # ===== IA (rápida) =====
        if GROQ_API_KEY:
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": f"Genera un informe académico sobre {tema}"}],
                        "max_tokens": 1500
                    },
                    timeout=25
                )
                if res.status_code == 200:
                    texto = limpiar_texto(res.json()['choices'][0]['message']['content'])
                    secciones = contenido_local(tema)
                    secciones["desarrollo"] = texto
            except:
                pass

        # fallback seguro
        if not secciones:
            secciones = contenido_local(tema)

        # ===== PDF =====
        filename = f"informe_{uuid.uuid4().hex[:6]}.pdf"
        filepath = os.path.join('informes_generados', filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='Titulo',
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=10
        ))

        story = []

        # ===== PORTADA =====
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("INFORME ACADÉMICO", styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(tema.upper(), styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(PageBreak())

        # ===== ÍNDICE =====
        story.append(Paragraph("ÍNDICE", styles['Titulo']))
        indices = [
            "1. INTRODUCCIÓN ........................................ 2",
            "2. OBJETIVOS ........................................... 3",
            "3. MARCO TEÓRICO ....................................... 4",
            "4. METODOLOGÍA ......................................... 5",
            "5. DESARROLLO .......................................... 6",
            "6. CONCLUSIONES ........................................ 7",
            "7. RECOMENDACIONES ..................................... 8"
        ]
        for item in indices:
            story.append(Paragraph(item, styles['Normal']))
        story.append(PageBreak())

        # ===== CONTENIDO =====
        for titulo, contenido in [
            ("1. INTRODUCCIÓN", secciones["introduccion"]),
            ("2. OBJETIVOS", secciones["objetivos"]),
            ("3. MARCO TEÓRICO", secciones["marco_teorico"]),
            ("4. METODOLOGÍA", secciones["metodologia"]),
            ("5. DESARROLLO", secciones["desarrollo"]),
            ("6. CONCLUSIONES", secciones["conclusiones"]),
            ("7. RECOMENDACIONES", secciones["recomendaciones"])
        ]:
            story.append(Paragraph(titulo, styles['Titulo']))
            story.append(Paragraph(contenido, styles['Normal']))
            story.append(PageBreak())

        doc.build(story)

        return jsonify({
            "success": True,
            "download_url": f"/descargar/{filename}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/descargar/<file>')
def descargar(file):
    return send_file(os.path.join('informes_generados', file), as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
