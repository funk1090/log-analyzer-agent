import requests
from datetime import datetime

# ── TOOLS ──
def parse_line(linea):
    """
    Parsea una línea del log y devuelve un diccionario con los campos.
    Si la línea no cumple el formato esperado, devuelve None.
    """
    try:
        # Ejemplo de línea:
        # 2026-03-26 08:00:01,123 INFO [NodeB_01] MSG0000123 | 56912345678 | SMS | MO_SUBMIT: Message submitted successfully

        timestamp = linea[0:23]  # "2026-03-26 08:00:01,123"

        # El resto de la línea después del timestamp
        resto = linea[24:].strip().split(" ", 3)

        level = resto[0]               # INFO / ERROR / WARN
        node = resto[1].strip("[]")    # NodeB_01
        msg_id = resto[2]              # MSG0000123

        # Ahora viene la parte separada por " | "
        campos = resto[3].split(" | ")

        msisdn = campos[0].strip("| ").strip()             # 56912345678
        service = campos[1]            # SMS
        code, desc = campos[2].split(": ", 1)

        return {
            "timestamp": timestamp,
            "level": level,
            "node": node,
            "msg_id": msg_id,
            "msisdn": msisdn,
            "service": service,
            "code": code,
            "description": desc
        }

    except Exception:
        return None



def buscar_por_numero(numero, log_path='telecom_demo.log', guardar_lineas=True):
    """
    Busca todas las interacciones asociadas a un MSISDN dentro del log.
    - numero: string del MSISDN (ej: "56912345678")
    - log_path: ruta del archivo .log
    - guardar_lineas: si False, solo cuenta (ideal para logs gigantes)
    """

    total = 0
    total_err = 0

    resultados = []
    errores = []

    # Patrón exacto para evitar falsos positivos
    patron = f"| {numero} |"

    with open(log_path, 'r') as f:
        for linea in f:
            if patron in linea:
                total += 1

                data = parse_line(linea)
                if not data:
                    continue

                if data["level"] == "ERROR":
                    total_err += 1

                if guardar_lineas:
                    resultados.append(data)
                    if data["level"] == "ERROR":
                        errores.append(data)

    return {
        "numero": numero,
        "total_interacciones": total,
        "total_errores": total_err,
        "interacciones": resultados if guardar_lineas else None,
        "errores": errores if guardar_lineas else None
    }


def buscar_por_error(tipo_error, log_path='telecom_demo.log'):
    resultados = []
    numeros_afectados = set()
    with open(log_path, 'r') as f:
        for linea in f:
            if 'ERROR' in linea and tipo_error.upper() in linea.upper():
                resultados.append(linea.strip())
                partes = linea.split('|')
                if len(partes) >= 2:
                    numeros_afectados.add(partes[1].strip())
    return {"tipo_error": tipo_error, "total_ocurrencias": len(resultados), "numeros_afectados": list(numeros_afectados), "lineas": resultados}

def buscar_por_tiempo(minutos=60, log_path='telecom_demo.log'):
    resultados = []
    numeros_afectados = set()
    tipos_error = set()
    ultima_linea = None
    with open(log_path, 'r') as f:
        for linea in f:
            if linea.strip():
                ultima_linea = linea.strip()
    timestamp_ref = datetime.strptime(ultima_linea[:23], '%Y-%m-%d %H:%M:%S,%f')
    with open(log_path, 'r') as f:
        for linea in f:
            if 'ERROR' not in linea:
                continue
            try:
                timestamp_linea = datetime.strptime(linea[:23], '%Y-%m-%d %H:%M:%S,%f')
                diferencia = (timestamp_ref - timestamp_linea).total_seconds() / 60
                if diferencia <= minutos:
                    resultados.append(linea.strip())
                    partes = linea.split('|')
                    if len(partes) >= 2:
                        numeros_afectados.add(partes[1].strip())
                    if len(partes) >= 4:
                        tipos_error.add(partes[3].strip().split(':')[0])
            except:
                continue
    return {"ventana_minutos": minutos, "total_errores": len(resultados), "numeros_afectados": list(numeros_afectados), "tipos_error": list(tipos_error), "lineas": resultados}
