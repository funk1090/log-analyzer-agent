import re
import json
from datetime import datetime
from tools import buscar_por_error, buscar_por_numero, buscar_por_tiempo, analisis_general
from ollama_client import llamar_ollama

MAX_LINEAS_LLM = 20

memoria = {
    "ultima_intencion": None,
    "ultimo_valor":     None,
    "ultimo_contexto":  None
}

def dict_a_linea(d):
    return f"{d['timestamp']} | {d['msisdn']} | {d['service']} | {d['code']}: {d['description']}"

def tasa_error(errores, total):
    return round(errores / total * 100, 1) if total > 0 else 0

def resumen_lineas(lineas, total_real, label="errores"):
    muestra = lineas[:MAX_LINEAS_LLM]
    texto   = chr(10).join(muestra)
    if total_real > MAX_LINEAS_LLM:
        texto += f"\n... y {total_real - MAX_LINEAS_LLM} {label} más no mostrados."
    return texto, len(muestra)

def analizar_intencion(consulta):
    PALABRAS_CONTINUIDAD = [
        "ahora", "solo", "continua", "continuar", "mismos", "otra vez",
        "now", "only", "continue", "same", "también", "y los", "and the",
        "del mismo", "for the same"
    ]
    if any(p in consulta.lower() for p in PALABRAS_CONTINUIDAD):
        if memoria["ultima_intencion"]:
            print("🧠 Usando memoria previa")
            return {"intencion": memoria["ultima_intencion"], "valor": memoria["ultimo_valor"]}

    prompt = f"""You are a classifier. Read the query and return ONLY a JSON object. No explanation, no markdown, no extra text.

Query: "{consulta}"

Return this exact JSON format:
{{"intencion": "...", "valor": "...", "idioma": "..."}}

Classification rules (apply the first match):

1. "resumen" — user wants a general overview/summary with no specific number or error code
   valor = "general"
   Matches: "summary", "resumen", "overview", "analiza el log", "general status", "dame un resumen"

2. "numero_error" — user mentions a phone number starting with 569 (11 digits) AND a specific error code
   valor = "<number>|<error_code>"
   Example: "did 56912345678 have TIMEOUT?" → {{"intencion":"numero_error","valor":"56912345678|TIMEOUT"}}
   NEVER invent an error code. If no code is explicitly stated, use "numero" instead.

3. "numero" — user mentions a phone number starting with 569 (11 digits), no specific error code
   valor = the phone number
    Examples:
   - "show me errors for 56912345678" → {{"intencion":"numero","valor":"56912345678"}}
   - "muestrame el error para el siguiente numero 56912345678" → {{"intencion":"numero","valor":"56912345678"}}
   - "muestrame la informacion para el numero 56912345678" → {{"intencion":"numero","valor":"56912345678"}}
   - "que paso con el 56912345678" → {{"intencion":"numero","valor":"56912345678"}}
   - "errores del 56912345678" → {{"intencion":"numero","valor":"56912345678"}}

4. "error" — user mentions a specific error code or keyword, no phone number
   Error codes: TIMEOUT, CALL_DROP, CALL_FAIL, AUTH_FAIL, AUTH_TIMEOUT, SMS_FAIL, SMS_TIMEOUT, DATA_DROP, DATA_FAIL, ROAM_FAIL, NET_DROP, NET_TIMEOUT
   Also match informal variations: "timeout errors", "errores de timeout", "call drops", "auth failures", "caídas de llamada"
   valor = the normalized error code in uppercase
   Example: "show me AUTH_FAIL errors" → {{"intencion":"error","valor":"AUTH_FAIL"}}
   Example: "muestrame los timeout" → {{"intencion":"error","valor":"TIMEOUT"}}
   Example: "errores de caída de llamada" → {{"intencion":"error","valor":"CALL_DROP"}}

5. "tiempo" — user mentions a time window. TIMEOUT is an error code, NOT a time window.
   valor = minutes as a number string
   Example: "last hour" → {{"intencion":"tiempo","valor":"60"}}
   Example: "últimos 30 minutos" → {{"intencion":"tiempo","valor":"30"}}
   Example: "last 2 hours" → {{"intencion":"tiempo","valor":"120"}}

LANGUAGE DETECTION:
- Detect the language of the query and add it to the JSON
- "idioma" must be the full language name (e.g. "Spanish", "English", "Portuguese", "French")
- Example: "muestrame los errores" → "idioma": "Spanish"
- Example: "show me errors" → "idioma": "English"
- Example: "mostra os erros" → "idioma": "Portuguese"

STRICT RULES:
- Return ONLY the JSON object, nothing else
- NEVER use "AUTH_FAIL" or any error code as the value of "intencion"
- NEVER invent phone numbers
- TIMEOUT in "intencion" field is always wrong — use "error" with valor "TIMEOUT"
- If nothing matches, return {{"intencion":"resumen","valor":"general"}}"""

    respuesta = llamar_ollama(prompt).strip()

    # Limpiar backticks
    if "```" in respuesta:
        partes = respuesta.split("```")
        respuesta = partes[1] if len(partes) > 1 else partes[0]
        if respuesta.startswith("json"):
            respuesta = respuesta[4:]

    respuesta = respuesta.strip()

    # Reintento si la respuesta está vacía o no es JSON
    if not respuesta or not respuesta.startswith("{"):
        print("⚠️  Respuesta inválida, reintentando...")
        respuesta = llamar_ollama(prompt).strip()
        if "```" in respuesta:
            respuesta = respuesta.split("```")[1]
            if respuesta.startswith("json"):
                respuesta = respuesta[4:]
        respuesta = respuesta.strip()

    return json.loads(respuesta)


def agente_log(consulta, log_path='telecom_demo.log'):
    print(f"\n🔍 Procesando: {consulta}")
    try:
        intencion = analizar_intencion(consulta)
        tipo   = intencion.get('intencion')
        valor  = str(intencion.get('valor', ''))
        idioma = intencion.get('idioma', 'Spanish')
        print(f"📋 Intención detectada: {tipo} | Valor: {valor} | Idioma: {idioma}")
    except Exception as e:
        return f"No pude entender la consulta: {e}"

    if tipo in [None, "", "desconocida", None]:
    # Inferir intención desde el valor cuando el LLM falla
        if valor == "general":
            print("🔁 Fallback → resumen")
            tipo = "resumen"
        elif valor.isdigit():
            print("🔁 Fallback → tiempo")
            tipo = "tiempo"
        elif any(e in valor.upper() for e in ["TIMEOUT","DROP","FAIL","AUTH","SMS","NET","ROAM","DATA","CALL"]):
            print("🔁 Fallback → error")
            tipo = "error"
        elif valor.startswith("569") and len(valor) == 11:
            print("🔁 Fallback → numero")
            tipo = "numero"
        else:
            return "No pude interpretar la consulta, ¿puedes reformularla?"

    if tipo == 'resumen':
        datos    = analisis_general(log_path)
        top_err  = "\n".join([f"  - {e['codigo']}: {e['total']}" for e in datos['top_errores']])
        top_num  = "\n".join([f"  - {n['numero']}: {n['errores']}" for n in datos['top_numeros']])
        top_nod  = "\n".join([f"  - {n['nodo']}: {n['errores']}"  for n in datos['top_nodos']])
        top_hora = "\n".join([f"  - {h['hora']}: {h['errores']}"  for h in datos['franja_horaria']])
        contexto = f"""files_analyzed: {datos['archivos_analizados']}
total_lines: {datos['total_lineas']:,}
total_errors: {datos['total_errores']:,}
total_ok: {datos['total_ok']:,}
error_rate: {datos['tasa_error']}%

top_5_error_codes:
{top_err}

top_5_numbers_by_errors:
{top_num}

top_5_nodes_by_errors:
{top_nod}

peak_hours:
{top_hora}"""

    elif tipo == 'numero':
        datos     = buscar_por_numero(valor, log_path)
        total     = datos['total_interacciones']
        total_err = datos['total_errores']
        lineas_error = [dict_a_linea(d) for d in (datos['interacciones'] or []) if d['level'] == 'ERROR']
        muestra, n_muestra = resumen_lineas(lineas_error, total_err)
        contexto = f"""Número: {datos['numero']}
Total interacciones: {total}
Total errores: {total_err}
Tasa de error: {tasa_error(total_err, total)}%
Muestra de errores ({n_muestra} de {total_err} totales):
{muestra}"""

    elif tipo == 'error':
        datos     = buscar_por_error(valor, log_path)
        total_err = datos['total_ocurrencias']
        numeros   = datos['numeros_afectados']
        muestra, n_muestra = resumen_lineas(datos['lineas'], total_err)
        contexto = f"""Tipo de error: {datos['tipo_error']}
Total ocurrencias: {total_err}
Números afectados: {len(numeros)} números distintos
Lista de números: {', '.join(numeros[:20])}{'...' if len(numeros) > 20 else ''}
Muestra de líneas ({n_muestra} de {total_err} totales):
{muestra}"""

    elif tipo == 'tiempo':
        datos     = buscar_por_tiempo(int(valor), log_path)
        total_err = datos['total_errores']
        numeros   = datos['numeros_afectados']
        tipos     = datos['tipos_error']
        muestra, n_muestra = resumen_lineas(datos['lineas'], total_err)
        contexto = f"""Ventana de tiempo: últimos {datos['ventana_minutos']} minutos
Total errores: {total_err}
Números afectados: {len(numeros)} números distintos
Tipos de error: {', '.join(tipos)}
Muestra de líneas ({n_muestra} de {total_err} totales):
{muestra}"""

    elif tipo == 'numero_error':
        partes = valor.split('|')
        ERRORES_GENERICOS = ['ERROR', 'FAIL', 'FALLO', 'ERRORS', 'ERRORES']
        if len(partes) < 2 or partes[1].strip().upper() in ERRORES_GENERICOS:
            print("⚠️  Error genérico — mostrando todos los errores del número")
            datos     = buscar_por_numero(partes[0].strip() if partes else valor.strip(), log_path)
            total     = datos['total_interacciones']
            total_err = datos['total_errores']
            lineas_error = [dict_a_linea(d) for d in (datos['interacciones'] or []) if d['level'] == 'ERROR']
            muestra, n_muestra = resumen_lineas(lineas_error, total_err)
            contexto = f"""Número: {datos['numero']}
Total interacciones: {total}
Total errores: {total_err}
Tasa de error: {tasa_error(total_err, total)}%
Muestra de errores ({n_muestra} de {total_err} totales):
{muestra}"""
        else:
            numero  = partes[0].strip()
            error   = partes[1].strip()
            datos_n = buscar_por_numero(numero, log_path)
            lineas_filtradas = [dict_a_linea(d) for d in (datos_n['interacciones'] or []) if error.upper() in d['code'].upper()]
            total_err = len(lineas_filtradas)
            muestra, n_muestra = resumen_lineas(lineas_filtradas, total_err)
            contexto = f"""Número: {numero}
Error buscado: {error}
Total ocurrencias: {total_err}
Muestra de líneas ({n_muestra} de {total_err} totales):
{muestra}"""
    else:
        return "No pude determinar qué buscar."

    memoria["ultima_intencion"] = tipo
    memoria["ultimo_valor"]     = valor
    memoria["ultimo_contexto"]  = contexto

    prompt_resumen = f"""You MUST respond ONLY in {idioma}. Do not use any other language.

You are a telecom log analysis expert. Using ONLY the data below (do not invent numbers):

User question: "{consulta}"

{contexto}

Provide a technical summary with:
1. Total findings (use exact numbers from data)
2. Error types and timestamps
3. Service status conclusion
4. Sample log lines from context
NOTE: Do NOT invent or fabricate log lines. Only show log lines if they appear in the data above."""

    return llamar_ollama(prompt_resumen)