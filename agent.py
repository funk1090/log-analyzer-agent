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
    if any(p in consulta.lower() for p in ["ahora", "solo", "continua", "continuar", "mismos", "otra vez", "now", "only", "continue", "same"]):
        if memoria["ultima_intencion"]:
            return {"intencion": memoria["ultima_intencion"], "valor": memoria["ultimo_valor"]}

    prompt = f"""You are a log analysis assistant. Analyze the query and respond ONLY with valid JSON, regardless of the language of the query.
Query: "{consulta}"

Respond with this exact format:
{{"intencion": "numero" | "error" | "tiempo" | "numero_error" | "resumen", "valor": "the corresponding value"}}

Rules — apply the first one that matches:

1. **resumen**: General summary or overview request with no specific number or error.
   Examples:
   - "give me a summary" → {{"intencion": "resumen", "valor": "general"}}
   - "analiza el log" → {{"intencion": "resumen", "valor": "general"}}

2. **numero_error**: ONLY if there is a real phone number (569XXXXXXXXX) AND a specific error code explicitly mentioned.
   Correct: "did 56912345678 have TIMEOUT?" → {{"intencion": "numero_error", "valor": "56912345678|TIMEOUT"}}
   WRONG: never invent an error code if user didn't say one.

3. **numero**: Phone number 569XXXXXXXXX present, no specific error code.
   Example: "show me errors for 56912345678" → {{"intencion": "numero", "valor": "56912345678"}}

4. **error**: Specific error code mentioned, no phone number.
   Examples:
   - "show me all TIMEOUT" → {{"intencion": "error", "valor": "TIMEOUT"}}
   - "hay CALL_DROP?" → {{"intencion": "error", "valor": "CALL_DROP"}}

5. **tiempo**: Explicit time window only. TIMEOUT is an error code, NOT a time window.
   Examples:
   - "last hour" → {{"intencion": "tiempo", "valor": "60"}}
   - "últimos 30 minutos" → {{"intencion": "tiempo", "valor": "30"}}
   - "last 2 hours" → {{"intencion": "tiempo", "valor": "120"}}

CRITICAL:
- NEVER invent phone numbers or error codes.
- TIMEOUT is an error code, not a time window.
- Respond ONLY with the JSON."""

    respuesta = llamar_ollama(prompt).strip()
    if "```" in respuesta:
        respuesta = respuesta.split("```")[1]
        if respuesta.startswith("json"):
            respuesta = respuesta[4:]
    return json.loads(respuesta)


def agente_log(consulta, log_path='telecom_demo.log'):
    print(f"\n🔍 Procesando: {consulta}")
    try:
        intencion = analizar_intencion(consulta)
        tipo  = intencion.get('intencion')
        valor = str(intencion.get('valor', ''))
        print(f"📋 Intención detectada: {tipo} | Valor: {valor}")
    except Exception as e:
        return f"No pude entender la consulta: {e}"

    if tipo in [None, "", "desconocida"]:
        if memoria["ultima_intencion"]:
            print("🧠 Usando memoria previa")
            tipo  = memoria["ultima_intencion"]
            valor = memoria["ultimo_valor"]
        else:
            return "No pude determinar qué buscar."

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

    prompt_resumen = f"""You are an expert telecom log analysis assistant.
CRITICAL: Detect the language of the user's question and respond ENTIRELY in that same language.
If the question is in English, respond in English. Si la pregunta es en español, responde en español.

User question: "{consulta}"

Data found:
{contexto}

Generate a clear technical summary using ONLY the exact numbers from the context, do not invent data:
1. What you found (real totals)
2. Error types and when they occurred
3. Conclusion about the number or service status
4. Show the log lines included in the context"""

    return llamar_ollama(prompt_resumen)