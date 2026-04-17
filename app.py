def generar_con_ia(tema, tipo_contenido, info_usuario=""):
    """Genera contenido REAL usando IA (OpenRouter + Gemini)"""
    
    if not OPENROUTER_API_KEY:
        print("❌ No hay API key configurada")
        return None
    
    print(f"🤖 Intentando generar {tipo_contenido} con IA para: {tema[:50]}...")
    
    prompts = {
        'introduccion': f"""Genera una INTRODUCCIÓN académica profesional sobre: "{tema}".

Información adicional: {info_usuario if info_usuario else 'No hay información adicional'}

Debe incluir:
1. Contextualización del tema (por qué es importante hoy)
2. Planteamiento del problema
3. Justificación del estudio
4. Estructura del informe

Escribe en español, tono académico pero claro. EXTENSIÓN: 300-400 palabras.""",

        'objetivos': f"""Genera los OBJETIVOS para un informe académico sobre "{tema}".

Debe incluir:
- 1 Objetivo General
- 4 Objetivos Específicos

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
        
        # Modelo gratuito Gemini (corregido)
        data = {
            "model": "google/gemini-2.0-flash-lite:free",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente académico profesional. Generas contenido de alta calidad para informes universitarios en español. Usas un lenguaje formal pero claro."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
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
            
            # Si falla con Gemini, intentar con modelo alternativo
            if response.status_code == 400:
                print("🔄 Intentando con modelo alternativo...")
                data["model"] = "meta-llama/llama-3.2-3b-instruct:free"
                response2 = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=60)
                if response2.status_code == 200:
                    resultado = response2.json()
                    contenido = resultado['choices'][0]['message']['content']
                    print(f"✅ IA generó {len(contenido)} caracteres (modelo alternativo)")
                    return contenido.replace('\n', '<br/>')
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La IA tardó demasiado en responder")
        return None
    except Exception as e:
        print(f"❌ Error conectando con IA: {str(e)}")
        return None
