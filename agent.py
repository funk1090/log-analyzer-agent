import re
import json
from datetime import datetime
from tools import buscar_por_error, buscar_por_numero, buscar_por_tiempo
from ollama_client import llamar_ollama

# ── CONFIGURACIÓN ──
MAX_LINEAS_LLM = 20  # Máximo de líneas que se mandan al LLM

# ── MEMORIA ──
memoria = {
    "ultima_intencion": None,
    "ultimo_valor": None,
    "ultimo_contexto": None
}

# ── HELPERS ──
def dict_a_linea(d):
    return f"{d['timestamp']} | {d['msisdn']} | {d['service']} | {d['code']}: {d['description']}"

def tasa_error(errores, total):
    if total == 0:
        return 0
    return round(errores / total * 100, 1)

def resumen_lineas(lineas, total_real, label="errores"):
    """Genera texto de muestra con indicador del total real."""
    muestra = lineas[:MAX_LINEAS_LLM]
    texto = chr(10).join(muestra)
    if total_real > MAX_LINEAS_LLM:
        texto += f"\n... y {total_real - MAX_LINEAS_LLM} {label} más no mostrados."
    return texto, len(muestra)

# ── ANALIZADOR DE INTENCIÓN ──
def analizar_intencion(consulta):

    if any(p in consulta.lower() for p in ["ahora", "solo", "continua", "continuar", "mismos", "otra vez"]):
        if memoria["ultima_intencion"]:
            return {
                "intencion": memoria["ultima_intencion"],
                "valor": memoria["ultimo_valor"]
            }

    prompt = f"""You are a log analysis assistant. Analyze the query and respond ONLY with valid JSON, regardless of the language of the query.
Consulta / Query: "{consulta}"

Responde con este formato exacto:
{{"intencion": "numero" | "error" | "tiempo" | "numero_error", "valor": "el valor correspondiente"}}

Reglas — aplica la primera que coincida:

1. **numero_error**: SOLO si hay un número (569XXXXXXXXX) Y el usuario menciona EXPLÍCITAMENTE un código de error (TIMEOUT, FAIL, DROP, etc.).
   Si el usuario solo dice "errores", "errors", "problemas" sin un código específico → usa "numero" en vez de "numero_error".
   Ejemplo correcto: "el 56912345678 tuvo TIMEOUT?" → {{"intencion": "numero_error", "valor": "56912345678|TIMEOUT"}}
   Ejemplo correcto: "show me the errors for 56912345678" → {{"intencion": "numero", "valor": "56912345678"}}
   Ejemplo INCORRECTO: "show me the errors for 56912345678" → {{"intencion": "numero_error", "valor": "56912345678|TIMEOUT"}} ← NUNCA inventes el código de error

2. **numero**: Si hay un número 569XXXXXXXXX y NO menciona código de error.
   Ejemplo: "qué pasó con el 56923456789?" → {{"intencion": "numero", "valor": "56923456789"}}

3. **error**: Si menciona un código de error técnico como TIMEOUT, CALL_DROP, AUTH_FAIL, SMS_FAIL,
   DATA_DROP, DATA_FAIL, ROAM_FAIL, NET_DROP, NET_TIMEOUT, SMS_TIMEOUT, CALL_FAIL.
   NO importa cómo está redactado — "muéstrame los TIMEOUT", "hay CALL_DROP?", "errores de AUTH_FAIL" → todos son intención "error".
   Ejemplo: "muéstrame todos los TIMEOUT" → {{"intencion": "error", "valor": "TIMEOUT"}}
   Ejemplo: "hay errores de CALL_DROP?" → {{"intencion": "error", "valor": "CALL_DROP"}}

4. **tiempo**: SOLO si menciona una duración explícita como "última hora", "últimos 30 minutos", "últimas 2 horas".
   NUNCA uses "tiempo" solo porque aparece la palabra TIMEOUT — TIMEOUT es un código de error, no tiempo.
   Ejemplos:
   - "qué errores hubo en la última hora?" → {{"intencion": "tiempo", "valor": "60"}}
   - "qué pasó en los últimos 30 minutos?" → {{"intencion": "tiempo", "valor": "30"}}
   - "muéstrame errores de las últimas 2 horas" → {{"intencion": "tiempo", "valor": "120"}}

CRÍTICO:
- Si NO hay un número real (569XXXXXXXXX con 11 dígitos reales), NUNCA uses "numero" ni "numero_error".
- NUNCA inventes ni completes números de teléfono. Si no hay número explícito en la consulta, no es "numero" ni "numero_error".
- Una pregunta sobre tiempo NO tiene número de teléfono.

IMPORTANTE:
- TIMEOUT es un código de error, NO una ventana de tiempo. Siempre es intención "error".
- NO inventes números ni errores.
- Responde SOLO el JSON."""

    respuesta = llamar_ollama(prompt).strip()

    if "```" in respuesta:
        respuesta = respuesta.split("```")[1]
        if respuesta.startswith("json"):
            respuesta = respuesta[4:]

    return json.loads(respuesta)


# ── AGENTE PRINCIPAL ──
def agente_log(consulta, log_path='telecom_demo.log'):
    print(f"\n🔍 Procesando: {consulta}")

    try:
        intencion = analizar_intencion(consulta)
        tipo = intencion.get('intencion')
        valor = str(intencion.get('valor', ''))
        print(f"📋 Intención detectada: {tipo} | Valor: {valor}")
    except Exception as e:
        return f"No pude entender la consulta: {e}"

    if tipo in [None, "", "desconocida"]:
        if memoria["ultima_intencion"]:
            print("🧠 Usando memoria previa")
            tipo = memoria["ultima_intencion"]
            valor = memoria["ultimo_valor"]
        else:
            return "No pude determinar qué buscar."

    # ── EJECUCIÓN SEGÚN INTENCIÓN ──
    if tipo == 'numero':
        datos = buscar_por_numero(valor, log_path)
        total = datos['total_interacciones']
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
        datos = buscar_por_error(valor, log_path)
        total_err = datos['total_ocurrencias']
        numeros = datos['numeros_afectados']

        muestra, n_muestra = resumen_lineas(datos['lineas'], total_err)

        contexto = f"""Tipo de error: {datos['tipo_error']}
Total ocurrencias: {total_err}
Números afectados: {len(numeros)} números distintos
Lista de números: {', '.join(numeros[:20])}{'...' if len(numeros) > 20 else ''}
Muestra de líneas ({n_muestra} de {total_err} totales):
{muestra}"""

    elif tipo == 'tiempo':
        datos = buscar_por_tiempo(int(valor), log_path)
        total_err = datos['total_errores']
        numeros = datos['numeros_afectados']
        tipos = datos['tipos_error']

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
            print("⚠️  Error genérico o sin tipo — mostrando todos los errores del número")
            datos = buscar_por_numero(valor.strip(), log_path)
            total = datos['total_interacciones']
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
            numero = partes[0].strip()
            error = partes[1].strip()
            datos_numero = buscar_por_numero(numero, log_path)
            lineas_filtradas = [dict_a_linea(d) for d in (datos_numero['interacciones'] or []) if error.upper() in d['code'].upper()]
            total_err = len(lineas_filtradas)
            muestra, n_muestra = resumen_lineas(lineas_filtradas, total_err)
            contexto = f"""Número: {numero}
Error buscado: {error}
Total ocurrencias: {total_err}
Muestra de líneas ({n_muestra} de {total_err} totales):
{muestra}"""

    else:
        return "No pude determinar qué buscar."

    # ── GUARDAR MEMORIA ──
    memoria["ultima_intencion"] = tipo
    memoria["ultimo_valor"] = valor
    memoria["ultimo_contexto"] = contexto

    # ── RESUMEN VIA LLM ──
    prompt_resumen = f"""You are an expert telecom log analysis assistant.
CRITICAL: Detect the language of the user's question and respond ENTIRELY in that same language.
If the question is in English, respond in English. Si la pregunta es en español, responde en español.

User question: "{consulta}"

Datos encontrados:
{contexto}

Generate a clear technical summary using ONLY the exact numbers from the context:
1. What you found (real totals)
2. Error types and when they occurred
3. Conclusion about the number or service status
4. Show the log lines included in the context"""

    return llamar_ollama(prompt_resumen)