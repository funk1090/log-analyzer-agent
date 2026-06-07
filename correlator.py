import json
from collections import defaultdict
from tools import buscar_por_tiempo, buscar_por_numero

PLAYBOOKS_PATH       = "playbooks.json"
UMBRAL_CONCENTRACION = 0.50   # nodo dominante si concentra > 50% de los errores del tipo


# ── CARGA ─────────────────────────────────────────────────────────────────────

def cargar_playbooks(path=PLAYBOOKS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["playbooks"]


# ── HELPERS DE PARSING ────────────────────────────────────────────────────────

def _extraer_nodo(linea):
    """Extrae el nodo de una línea de log: ... ERROR [NodeB_01] ..."""
    try:
        return linea[linea.index("[") + 1 : linea.index("]")]
    except ValueError:
        return None

def _extraer_numero(linea):
    """Extrae el MSISDN de una línea: ... | 56912345678 | ..."""
    try:
        partes = linea.split("|")
        return partes[1].strip() if len(partes) >= 2 else None
    except Exception:
        return None

def _extraer_codigo(linea):
    """Extrae el código de error: ... | SERVICE | CODE: desc"""
    try:
        partes = linea.split("|")
        return partes[3].split(":")[0].strip() if len(partes) >= 4 else None
    except Exception:
        return None


# ── EVALUACIÓN DE CONCENTRACIÓN EN NODO ──────────────────────────────────────

def _evaluar_concentracion(lineas):
    """
    Calcula si los errores están concentrados en un nodo.
    Retorna (bool_concentrado, nodo_dominante, porcentaje).
    """
    conteo = defaultdict(int)
    for linea in lineas:
        nodo = _extraer_nodo(linea)
        if nodo:
            conteo[nodo] += 1

    if not conteo:
        return False, None, 0.0

    total      = sum(conteo.values())
    nodo_top   = max(conteo, key=conteo.get)
    porcentaje = conteo[nodo_top] / total

    return porcentaje >= UMBRAL_CONCENTRACION, nodo_top, round(porcentaje * 100, 1)


# ── EVALUADORES POR TIPO ──────────────────────────────────────────────────────

def _evaluar_general(pb, log_path):
    """
    Evalúa un playbook masivo: usa buscar_por_tiempo() y filtra por
    los códigos de error definidos en el playbook.
    """
    conds        = pb["condiciones"]
    codigos      = {c.upper() for c in conds["codigos_error"]}
    ventana      = conds["ventana_minutos"]
    min_ocurr    = conds["min_ocurrencias"]
    min_numeros  = conds.get("min_numeros_afectados", 1)
    req_concentr = conds.get("concentrado_en_nodo", False)

    datos = buscar_por_tiempo(ventana, log_path)

    # Filtrar líneas que contengan alguno de los códigos del playbook
    lineas_match = [
        l for l in datos["lineas"]
        if any(cod in l.upper() for cod in codigos)
    ]

    if len(lineas_match) < min_ocurr:
        return None

    # Números afectados dentro de las líneas filtradas
    numeros = {_extraer_numero(l) for l in lineas_match} - {None}
    if len(numeros) < min_numeros:
        return None

    # Verificar concentración en nodo
    concentrado, nodo_top, pct = _evaluar_concentracion(lineas_match)
    if req_concentr and not concentrado:
        return None

    codigos_detectados = {_extraer_codigo(l) for l in lineas_match} - {None}

    return {
        "playbook_id"         : pb["id"],
        "nombre"              : pb["nombre"],
        "severidad"           : pb["severidad"],
        "causa_probable"      : pb["causa_probable"],
        "elemento_sospechoso" : pb["elemento_sospechoso"],
        "acciones"            : pb["acciones"],
        "investigar_en"       : pb.get("investigar_en"),
        "evidencia": {
            "ocurrencias"        : len(lineas_match),
            "ventana_minutos"    : ventana,
            "numeros_afectados"  : len(numeros),
            "concentrado"        : concentrado,
            "nodo_dominante"     : nodo_top if concentrado else None,
            "pct_nodo"           : pct if concentrado else None,
            "codigos_detectados" : sorted(codigos_detectados),
        }
    }


def _evaluar_numero_individual(pb, datos_numero):
    """
    Evalúa PB006 (aplica_a: numero_individual) sobre los datos
    ya obtenidos de buscar_por_numero().
    """
    conds     = pb["condiciones"]
    codigos   = {c.upper() for c in conds["codigos_error"]}
    min_ocurr = conds["min_ocurrencias"]
    min_tipos = conds.get("min_tipos_error_distintos", 2)

    interacciones = datos_numero.get("interacciones") or []
    errores_match = [
        d for d in interacciones
        if d["level"] == "ERROR" and d["code"].upper() in codigos
    ]

    if len(errores_match) < min_ocurr:
        return None

    tipos_distintos = {e["code"] for e in errores_match}
    if len(tipos_distintos) < min_tipos:
        return None

    return {
        "playbook_id"         : pb["id"],
        "nombre"              : pb["nombre"],
        "severidad"           : pb["severidad"],
        "causa_probable"      : pb["causa_probable"],
        "elemento_sospechoso" : pb["elemento_sospechoso"],
        "acciones"            : pb["acciones"],
        "investigar_en"       : pb.get("investigar_en"),
        "evidencia": {
            "numero"              : datos_numero["numero"],
            "ocurrencias"         : len(errores_match),
            "tipos_distintos"     : sorted(tipos_distintos),
            "total_errores_numero": datos_numero["total_errores"],
        }
    }


# ── PUNTO DE ENTRADA PRINCIPAL ────────────────────────────────────────────────

_ORDEN_SEVERIDAD = {"critica": 0, "alta": 1, "media": 2, "baja": 3}

def correlacionar(log_path, datos_numero=None, playbooks_path=PLAYBOOKS_PATH):
    """
    Evalúa todos los playbooks y retorna los que disparan.

    Parámetros:
      log_path       — ruta al log (string, lista o directorio)
      datos_numero   — dict de buscar_por_numero() — opcional, activa PB006
      playbooks_path — ruta al JSON de playbooks

    Retorna:
      Lista de dicts de playbooks disparados, ordenada por severidad.
    """
    playbooks  = cargar_playbooks(playbooks_path)
    disparados = []

    for pb in playbooks:
        conds = pb["condiciones"]
        try:
            if conds.get("aplica_a") == "numero_individual":
                if datos_numero is not None:
                    resultado = _evaluar_numero_individual(pb, datos_numero)
                    if resultado:
                        disparados.append(resultado)
            else:
                resultado = _evaluar_general(pb, log_path)
                if resultado:
                    disparados.append(resultado)
        except Exception as e:
            print(f"⚠️  Error evaluando {pb['id']}: {e}")

    disparados.sort(key=lambda x: _ORDEN_SEVERIDAD.get(x["severidad"], 99))
    return disparados


# ── FORMATEADOR PARA EL LLM ───────────────────────────────────────────────────

def formatear_para_contexto(disparados):
    """
    Convierte los playbooks disparados en un bloque de texto
    listo para incluir en el prompt del LLM.
    """
    if not disparados:
        return "Sin patrones de falla conocidos detectados en los datos analizados."

    lineas = ["=== DIAGNÓSTICO AUTOMÁTICO ===\n"]

    for r in disparados:
        ev  = r["evidencia"]
        sev = r["severidad"].upper()

        lineas.append(f"[{sev}] {r['playbook_id']} — {r['nombre']}")
        lineas.append(f"  Causa probable    : {r['causa_probable']}")
        lineas.append(f"  NE sospechoso     : {r['elemento_sospechoso']}")

        if "numero" in ev:
            lineas.append(f"  Número afectado   : {ev['numero']}")
            lineas.append(f"  Tipos de error    : {', '.join(ev['tipos_distintos'])}")
            lineas.append(f"  Ocurrencias       : {ev['ocurrencias']}")
        else:
            lineas.append(f"  Ocurrencias       : {ev['ocurrencias']} en últimos {ev['ventana_minutos']} min")
            lineas.append(f"  Números afectados : {ev['numeros_afectados']}")
            lineas.append(f"  Códigos detectados: {', '.join(ev['codigos_detectados'])}")
            if ev.get("nodo_dominante"):
                lineas.append(f"  Nodo concentrado  : {ev['nodo_dominante']} ({ev['pct_nodo']}% de los errores)")

        lineas.append("  Acciones recomendadas:")
        for i, accion in enumerate(r["acciones"], 1):
            lineas.append(f"    {i}. {accion}")
        lineas.append("")

    return "\n".join(lineas)
