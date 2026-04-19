import os
import glob
from datetime import datetime
from collections import defaultdict

def parse_line(linea):
    try:
        timestamp = linea[0:23]
        resto = linea[24:].strip().split(" ", 3)
        level   = resto[0]
        node    = resto[1].strip("[]")
        msg_id  = resto[2]
        campos  = resto[3].split(" | ")
        msisdn  = campos[0].strip("| ").strip()
        service = campos[1]
        code, desc = campos[2].split(": ", 1)
        return {"timestamp": timestamp, "level": level, "node": node,
                "msg_id": msg_id, "msisdn": msisdn, "service": service,
                "code": code, "description": desc}
    except Exception:
        return None

def _resolver_paths(log_path):
    if isinstance(log_path, list):
        return log_path
    if os.path.isdir(log_path):
        return sorted(glob.glob(os.path.join(log_path, "*.log")))
    return [log_path]

def obtener_logs_de_folder(folder_path):
    return sorted(glob.glob(os.path.join(folder_path, "*.log")))

def buscar_por_numero(numero, log_path='telecom_demo.log', guardar_lineas=True):
    total, total_err = 0, 0
    resultados, errores = [], []
    patron = f"| {numero} |"
    for path in _resolver_paths(log_path):
        with open(path, 'r') as f:
            for linea in f:
                if patron not in linea:
                    continue
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
    return {"numero": numero, "total_interacciones": total, "total_errores": total_err,
            "interacciones": resultados if guardar_lineas else None,
            "errores": errores if guardar_lineas else None}

def buscar_por_error(tipo_error, log_path='telecom_demo.log'):
    resultados, numeros_afectados = [], set()
    for path in _resolver_paths(log_path):
        with open(path, 'r') as f:
            for linea in f:
                if 'ERROR' in linea and tipo_error.upper() in linea.upper():
                    resultados.append(linea.strip())
                    partes = linea.split('|')
                    if len(partes) >= 2:
                        numeros_afectados.add(partes[1].strip())
    return {"tipo_error": tipo_error, "total_ocurrencias": len(resultados),
            "numeros_afectados": list(numeros_afectados), "lineas": resultados}

def buscar_por_tiempo(minutos=60, log_path='telecom_demo.log'):
    resultados, numeros_afectados, tipos_error = [], set(), set()
    ultima_linea = None
    archivos = _resolver_paths(log_path)
    for path in archivos:
        with open(path, 'r') as f:
            for linea in f:
                if linea.strip():
                    ultima_linea = linea.strip()
    if not ultima_linea:
        return {"ventana_minutos": minutos, "total_errores": 0,
                "numeros_afectados": [], "tipos_error": [], "lineas": []}
    timestamp_ref = datetime.strptime(ultima_linea[:23], '%Y-%m-%d %H:%M:%S,%f')
    for path in archivos:
        with open(path, 'r') as f:
            for linea in f:
                if 'ERROR' not in linea:
                    continue
                try:
                    ts = datetime.strptime(linea[:23], '%Y-%m-%d %H:%M:%S,%f')
                    if (timestamp_ref - ts).total_seconds() / 60 <= minutos:
                        resultados.append(linea.strip())
                        partes = linea.split('|')
                        if len(partes) >= 2:
                            numeros_afectados.add(partes[1].strip())
                        if len(partes) >= 4:
                            tipos_error.add(partes[3].strip().split(':')[0])
                except Exception:
                    continue
    return {"ventana_minutos": minutos, "total_errores": len(resultados),
            "numeros_afectados": list(numeros_afectados),
            "tipos_error": list(tipos_error), "lineas": resultados}

def analisis_general(log_path='telecom_demo.log'):
    total_lineas = 0
    total_errores = 0
    conteo_errores = defaultdict(int)
    conteo_numeros = defaultdict(int)
    conteo_nodos   = defaultdict(int)
    conteo_horas   = defaultdict(int)

    for path in _resolver_paths(log_path):
        with open(path, 'r') as f:
            for linea in f:
                if not linea.strip():
                    continue
                total_lineas += 1
                if 'ERROR' not in linea:
                    continue
                total_errores += 1
                data = parse_line(linea)
                if not data:
                    continue
                conteo_errores[data["code"]] += 1
                conteo_numeros[data["msisdn"]] += 1
                conteo_nodos[data["node"]] += 1
                try:
                    hora = int(data["timestamp"][11:13])
                    conteo_horas[hora] += 1
                except Exception:
                    pass

    top_errores = sorted(conteo_errores.items(), key=lambda x: x[1], reverse=True)[:5]
    top_numeros = sorted(conteo_numeros.items(), key=lambda x: x[1], reverse=True)[:5]
    top_nodos   = sorted(conteo_nodos.items(),   key=lambda x: x[1], reverse=True)[:5]
    top_horas   = sorted(conteo_horas.items(),   key=lambda x: x[1], reverse=True)[:3]

    archivos = _resolver_paths(log_path)
    tasa = round(total_errores / total_lineas * 100, 1) if total_lineas > 0 else 0

    return {
        "archivos_analizados": len(archivos),
        "total_lineas":        total_lineas,
        "total_errores":       total_errores,
        "total_ok":            total_lineas - total_errores,
        "tasa_error":          tasa,
        "top_errores": [{"codigo": k, "total": v}   for k, v in top_errores],
        "top_numeros": [{"numero": k, "errores": v} for k, v in top_numeros],
        "top_nodos":   [{"nodo": k,   "errores": v} for k, v in top_nodos],
        "franja_horaria": [{"hora": f"{h:02d}:00-{h:02d}:59", "errores": c} for h, c in top_horas]
    }