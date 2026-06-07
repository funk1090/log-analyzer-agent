import json
import paramiko

INVENTORY_PATH = "ne_inventory.json"


# ── CARGA ─────────────────────────────────────────────────────────────────────

def cargar_inventario(path=INVENTORY_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {ne["id"]: ne for ne in data["elementos"] if ne.get("activo", True)}


def buscar_ne_por_tipo(tipo_ne, inventario):
    """Retorna el primer NE activo que coincide con el tipo buscado."""
    tipo_ne = tipo_ne.upper()
    for ne in inventario.values():
        if ne["tipo"].upper() == tipo_ne:
            return ne
    return None


# ── CONEXIÓN SSH ──────────────────────────────────────────────────────────────

def ejecutar_comando(ne, intencion):
    """
    Conecta al NE via SSH, ejecuta el comando asociado a la intención,
    y retorna el output como string.

    Parámetros:
      ne        — dict del ne_inventory.json
      intencion — clave del dict 'comandos' (ej: "estado_nodo")

    Retorna:
      dict con keys: ne_id, tipo, comando, output, error
    """
    resultado = {
        "ne_id"   : ne["id"],
        "tipo"    : ne["tipo"],
        "intencion": intencion,
        "comando" : None,
        "output"  : None,
        "error"   : None,
    }

    # Buscar comando para la intención pedida
    comando = ne.get("comandos", {}).get(intencion)
    if not comando:
        resultado["error"] = f"Intención '{intencion}' no definida para {ne['id']}"
        return resultado

    resultado["comando"] = comando

    # Conectar y ejecutar
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        auth = ne.get("auth", {})

        if auth.get("metodo") == "password":
            client.connect(
                hostname = ne["host"],
                port     = ne["puerto"],
                username = ne["usuario"],
                password = auth["password"],
                timeout  = ne.get("timeout_segundos", 10),
            )
        elif auth.get("metodo") == "clave":
            client.connect(
                hostname  = ne["host"],
                port      = ne["puerto"],
                username  = ne["usuario"],
                key_filename = auth["ruta_clave"],
                timeout   = ne.get("timeout_segundos", 10),
            )
        else:
            resultado["error"] = f"Método de auth desconocido: {auth.get('metodo')}"
            return resultado

        _, stdout, stderr = client.exec_command(comando)
        output = stdout.read().decode("utf-8", errors="replace").strip()
        error  = stderr.read().decode("utf-8", errors="replace").strip()

        resultado["output"] = output if output else None
        if error:
            resultado["error"] = error

    except paramiko.AuthenticationException:
        resultado["error"] = "Error de autenticación SSH — verificar usuario/contraseña"
    except paramiko.SSHException as e:
        resultado["error"] = f"Error SSH: {e}"
    except OSError as e:
        resultado["error"] = f"No se pudo conectar a {ne['host']}:{ne['puerto']} — {e}"
    finally:
        client.close()

    return resultado


# ── PUNTO DE ENTRADA PRINCIPAL ────────────────────────────────────────────────

def investigar(tipo_ne, intencion, inventory_path=INVENTORY_PATH):
    """
    Busca el NE del tipo indicado en el inventario, se conecta,
    ejecuta el comando de la intención y retorna el resultado.

    Parámetros:
      tipo_ne        — tipo de NE a buscar (ej: "HSS", "MME", "eNodeB")
      intencion      — qué consultar (ej: "estado_nodo", "alarmas_activas")
      inventory_path — ruta al ne_inventory.json

    Retorna:
      dict con output del comando o mensaje de error
    """
    inventario = cargar_inventario(inventory_path)
    ne = buscar_ne_por_tipo(tipo_ne, inventario)

    if not ne:
        return {
            "ne_id"    : None,
            "tipo"     : tipo_ne,
            "intencion": intencion,
            "comando"  : None,
            "output"   : None,
            "error"    : f"No se encontró NE de tipo '{tipo_ne}' en el inventario",
        }

    print(f"🔌 Conectando a {ne['id']} ({ne['host']}:{ne['puerto']}) — intención: {intencion}")
    return ejecutar_comando(ne, intencion)


# ── FORMATEADOR PARA EL LLM ───────────────────────────────────────────────────

def formatear_resultado(resultado):
    """
    Convierte el resultado de la investigación SSH en texto
    para incluir en el prompt del LLM.
    """
    if resultado.get("error") and not resultado.get("output"):
        return (
            f"=== INVESTIGACIÓN ACTIVA: {resultado['tipo']} ===\n"
            f"Estado: No disponible\n"
            f"Razón : {resultado['error']}\n"
        )

    lineas = [
        f"=== INVESTIGACIÓN ACTIVA: {resultado['tipo']} ({resultado['ne_id']}) ===",
        f"Intención : {resultado['intencion']}",
        f"Comando   : {resultado['comando']}",
        "",
        resultado["output"] or "(sin output)",
    ]
    if resultado.get("error"):
        lineas.append(f"\nAdvertencia: {resultado['error']}")

    return "\n".join(lineas)
