"""
generate_log.py
Genera un archivo de log de telecomunicaciones simulado para pruebas y demos.
Formato compatible con parse_line() en tools.py:
  TIMESTAMP LEVEL [NODE] MSGID | MSISDN | SERVICE | CODE: DESCRIPTION
Uso: python3 generate_log.py
"""

import random
from datetime import datetime, timedelta

# ── CONFIGURACIÓN ──
OUTPUT_FILE  = "telecom_demo.log"
TOTAL_LINEAS = 50_000
FECHA_INICIO = datetime(2025, 4, 1, 0, 0, 0)
FECHA_FIN    = datetime(2025, 4, 1, 23, 59, 59)

# ── NÚMEROS ──
NUMEROS_PROBLEMATICOS = [
    "56912345678", "56923456789", "56934567890",
    "56945678901", "56956789012",
]
NUMEROS_NORMALES = [f"569{random.randint(10000000, 99999999)}" for _ in range(45)]
TODOS_LOS_NUMEROS = NUMEROS_PROBLEMATICOS + NUMEROS_NORMALES

# ── NODOS ──
NODOS = ["NodeB_01", "NodeB_02", "BSC_Norte", "BSC_Sur", "SGSN_01", "GGSN_01", "HLR_01"]

# ── EVENTOS OK → (service, code, description) ──
EVENTOS_OK = [
    ("CALL",    "CONNECT",    "Call established successfully"),
    ("CALL",    "COMPLETE",   "Call completed normally"),
    ("SMS",     "MO_SUBMIT",  "Message submitted successfully"),
    ("SMS",     "MT_DELIVER", "Message delivered to handset"),
    ("DATA",    "SESSION_UP", "Data session started"),
    ("DATA",    "SESSION_OK", "Data session closed normally"),
    ("AUTH",    "AUTH_OK",    "Authentication successful"),
    ("ROAMING", "ATTACH_OK",  "Roaming attach successful"),
]

# ── EVENTOS ERROR → (service, code, description) ──
EVENTOS_ERROR = [
    ("CALL",    "TIMEOUT",      "Call setup timed out"),
    ("CALL",    "CALL_FAIL",    "Call establishment failed"),
    ("CALL",    "CALL_DROP",    "Call dropped unexpectedly"),
    ("SMS",     "SMS_FAIL",     "Message delivery failed"),
    ("SMS",     "SMS_TIMEOUT",  "Message delivery timed out"),
    ("DATA",    "DATA_DROP",    "Data session interrupted"),
    ("DATA",    "DATA_FAIL",    "Data session setup failed"),
    ("AUTH",    "AUTH_FAIL",    "Authentication failed"),
    ("AUTH",    "AUTH_TIMEOUT", "Authentication timed out"),
    ("ROAMING", "ROAM_FAIL",    "Roaming attach failed"),
    ("NETWORK", "NET_DROP",     "Signal lost"),
    ("NETWORK", "NET_TIMEOUT",  "Network not responding"),
]

msg_counter = 0

def next_msg_id():
    global msg_counter
    msg_counter += 1
    return f"MSG{msg_counter:07d}"

def random_timestamp(inicio, fin):
    delta = fin - inicio
    segundos = random.randint(0, int(delta.total_seconds()))
    ms = random.randint(0, 999)
    ts = inicio + timedelta(seconds=segundos)
    return ts.strftime(f"%Y-%m-%d %H:%M:%S,{ms:03d}")

def generar_linea(numero, es_error):
    ts    = random_timestamp(FECHA_INICIO, FECHA_FIN)
    nodo  = random.choice(NODOS)
    msgid = next_msg_id()

    if es_error:
        level = "ERROR"
        service, code, desc = random.choice(EVENTOS_ERROR)
    else:
        level = "INFO"
        service, code, desc = random.choice(EVENTOS_OK)

    # Formato: TIMESTAMP LEVEL [NODE] MSGID | MSISDN | SERVICE | CODE: DESCRIPTION
    return f"{ts} {level} [{nodo}] {msgid} | {numero} | {service} | {code}: {desc}"

def main():
    print(f"⚙️  Generando {TOTAL_LINEAS:,} líneas de log...")

    lineas = []
    for i in range(TOTAL_LINEAS):
        numero = random.choice(TODOS_LOS_NUMEROS)

        if numero in NUMEROS_PROBLEMATICOS:
            es_error = random.random() < 0.60
        else:
            es_error = random.random() < 0.15

        lineas.append(generar_linea(numero, es_error))

        if (i + 1) % 10_000 == 0:
            print(f"   → {i+1:,} líneas generadas...")

    print("📋 Ordenando por timestamp...")
    lineas.sort()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    errores = sum(1 for l in lineas if " ERROR " in l)
    print(f"\n✅ Archivo generado: {OUTPUT_FILE}")
    print(f"   Total líneas  : {len(lineas):,}")
    print(f"   Líneas ERROR  : {errores:,} ({errores/len(lineas)*100:.1f}%)")
    print(f"   Líneas OK     : {len(lineas)-errores:,} ({(len(lineas)-errores)/len(lineas)*100:.1f}%)")
    print(f"\n🔥 Números problemáticos (muchos errores):")
    for n in NUMEROS_PROBLEMATICOS:
        n_err   = sum(1 for l in lineas if f"| {n} |" in l and " ERROR " in l)
        n_total = sum(1 for l in lineas if f"| {n} |" in l)
        print(f"   {n} → {n_err} errores de {n_total} interacciones")

if __name__ == "__main__":
    main()
