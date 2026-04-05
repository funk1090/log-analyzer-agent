import requests
from datetime import datetime

# ── TOOLS ──
def buscar_por_numero(numero, log_path='sample.log'):
    resultados = []
    errores = []
    with open(log_path, 'r') as f:
        for linea in f:
            if numero in linea:
                resultados.append(linea.strip())
                if 'ERROR' in linea:
                    errores.append(linea.strip())
    return {"numero": numero, "total_interacciones": len(resultados), "total_errores": len(errores), "lineas": resultados, "errores": errores}

def buscar_por_error(tipo_error, log_path='sample.log'):
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

def buscar_por_tiempo(minutos=60, log_path='sample.log'):
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
