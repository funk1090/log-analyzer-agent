import re
import json
from datetime import datetime
from tools import buscar_por_error, buscar_por_numero, buscar_por_tiempo
from ollama_client import llamar_ollama

# ── MEMORIA ──
memoria = {
    "ultima_intencion": None,
    "ultimo_valor": None,
    "ultimo_contexto": None
}

# ── ANALIZADOR DE INTENCIÓN ──
def analizar_intencion(consulta):

    # Si la consulta indica continuidad, usar memoria
    if any(p in consulta.lower() for p in ["ahora", "solo", "continua", "continuar", "mismos", "otra vez"]):
        if memoria["ultima_intencion"]:
            return {
                "intencion": memoria["ultima_intencion"],
                "valor": memoria["ultimo_valor"]
            }

    prompt = f"""Analiza esta consulta sobre logs de red y responde SOLO en JSON válido.
Consulta: "{consulta}"

Responde con este formato exacto:
{{"intencion": "numero" | "error" | "tiempo" | "numero_error" | "otro", "valor": "el valor correspondiente"}}

Reglas — aplica la primera que coincida:

1. **numero_error**:
   Se usa SOLO si la consulta contiene:
   - un número de teléfono (11 dígitos, empieza con 569)
   Y
   - un tipo de error (FAIL, ERROR, DROP, TIMEOUT, etc.)

2. **numero**:
   Si contiene un número 569XXXXXXXX y NO menciona error.

3. **error**:
   Si menciona un error especifico pero NO contiene número.

4. **tiempo**:
   Si menciona una ventana temporal:
   - "última hora" → 60
   - "últimas 2 horas" → 120
   - "últimos 10 minutos" → 10

5. **otra**:
   Si ninguna de las previas reglas aplica, responde a la consulta con lo que pide el usuario en base al archivo de log.
IMPORTANTE:
- NO clasifiques como "numero_error" si NO hay número.
- NO inventes números.
- NO inventes errores.
- Responde SOLO el JSON."""

    respuesta = llamar_ollama(prompt).strip()

    # Limpieza de backticks
    if "```" in respuesta:
        respuesta = respuesta.split("```")[1]
        if respuesta.startswith("json"):
            respuesta = respuesta[4:]

    return json.loads(respuesta)


# ── AGENTE PRINCIPAL ──
def agente_log(consulta, log_path='telecom_normal.log'):
    print(f"\n🔍 Procesando: {consulta}")

    try:
        intencion = analizar_intencion(consulta)
        tipo = intencion.get('intencion')
        valor = str(intencion.get('valor', ''))
        print(f"📋 Intención detectada: {tipo} | Valor: {valor}")
    except Exception as e:
        return f"No pude entender la consulta: {e}"

    # Si la intención es inválida, usar memoria
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
        contexto = f"Número: {datos['numero']}\nTotal interacciones: {datos['total_interacciones']}\nTotal errores: {datos['total_errores']}\nLíneas:\n{chr(10).join(datos['lineas'])}"

    elif tipo == 'error':
        datos = buscar_por_error(valor, log_path)
        contexto = f"Tipo de error: {datos['tipo_error']}\nTotal: {datos['total_ocurrencias']}\nNúmeros afectados: {', '.join(datos['numeros_afectados'])}\nLíneas:\n{chr(10).join(datos['lineas'])}"

    elif tipo == 'tiempo':
        datos = buscar_por_tiempo(int(valor), log_path)
        contexto = f"Ventana: {datos['ventana_minutos']} min\nErrores: {datos['total_errores']}\nNúmeros: {', '.join(datos['numeros_afectados'])}\nTipos: {', '.join(datos['tipos_error'])}\nLíneas:\n{chr(10).join(datos['lineas'])}"

    elif tipo == 'numero_error':
        partes = valor.split('|')

        if len(partes) < 2:
            return f"❗ Formato incorrecto para numero_error. Recibí: '{valor}'. Esperado: <numero>|<error>"

        numero = partes[0].strip()
        error = partes[1].strip()

        datos_numero = buscar_por_numero(numero, log_path)
        lineas_filtradas = [l for l in datos_numero['lineas'] if error.upper() in l.upper()]

        contexto = f"""Número: {numero}
Error buscado: {error}
Ocurrencias encontradas: {len(lineas_filtradas)}
Líneas:
{chr(10).join(lineas_filtradas)}"""

    else:
        return "No pude determinar qué buscar."

    # ── GUARDAR MEMORIA ──
    memoria["ultima_intencion"] = tipo
    memoria["ultimo_valor"] = valor
    memoria["ultimo_contexto"] = contexto

    # ── RESUMEN ──
    prompt_resumen = f"""Eres un asistente experto en análisis de logs de telecomunicaciones.

El usuario preguntó: "{consulta}"

Datos encontrados:
{contexto}

Genera un resumen claro y técnico:
1. Qué encontraste
2. Qué errores hay y cuándo ocurrieron
3. Conclusión sobre el estado del número o servicio
4. Imprimi las lineas del log encontradas"""

    return llamar_ollama(prompt_resumen)
