# Log Analyzer Agent — Resumen Técnico del Proyecto

## 1. Objetivo del Proyecto

Construir un agente AIOps conversacional para análisis de logs de telecomunicaciones. Permite a operadores de soporte hacer consultas en lenguaje natural, recibir diagnósticos automáticos basados en playbooks, y obtener datos en tiempo real de elementos de red vía SSH. Corre 100% local sin APIs externas.

---

## 2. Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| LLM local | Ollama + LLaMA 3 |
| Interfaz web | Streamlit |
| SSH | paramiko |
| Containerización | Docker Desktop |
| Control de versiones | Git + GitHub |
| Repositorio | https://github.com/funk1090/log-analyzer-agent |

---

## 3. Arquitectura del Sistema

```
app.py              →  Interfaz web Streamlit
main.py             →  Loop de conversación en terminal
agent.py            →  Orquestador principal
tools.py            →  Búsquedas en log + análisis de patrones
correlator.py       →  Motor de correlación de playbooks
connector_ssh.py    →  Conector SSH universal a NEs externos
ollama_client.py    →  Cliente HTTP para Ollama + tracking de tokens
generate_log.py     →  Generador de logs sintéticos
playbooks.json      →  Playbooks de falla LTE (editable)
ne_inventory.json   →  Inventario de NEs con SSH (editable)
```

### Flujo completo de una consulta

```
Usuario escribe consulta
        ↓
analizar_intencion() — LLaMA 3 clasifica como JSON
        ↓
Fallback automático si JSON viene None o inválido
        ↓
Tool correspondiente (buscar_por_numero / buscar_por_error / buscar_por_tiempo / analisis_general)
        ↓
correlacionar() — evalúa playbooks contra los datos
        ↓
Si hay playbook disparado → investigar() vía SSH al NE sospechoso
        ↓
prompt_resumen — LLaMA 3 genera respuesta con: hallazgos + diagnóstico + datos live del NE
        ↓
Respuesta al usuario
```

---

## 4. Archivos y Responsabilidades

### `agent.py`
- Función principal: `agente_log(consulta, log_path)`
- Detecta intención: `resumen | numero | error | tiempo | numero_error`
- Fallback automático cuando el LLM retorna None
- Memoria de sesión con palabras clave explícitas
- Detección de idioma en el clasificador
- Limite de 20 líneas al LLM para evitar saturación
- Integra correlator y conector SSH en el flujo

**Orden de fallback (importante — número va antes que tiempo):**
```python
if valor.startswith("569") and len(valor) == 11 and valor.isdigit() → numero
elif valor.isdigit() → tiempo
elif códigos de error → error
elif valor == "general" → resumen
```

### `tools.py`
- `parse_line(linea)` — parsea cada línea al formato dict
- `buscar_por_numero(numero, log_path)` — busca interacciones de un MSISDN
- `buscar_por_error(tipo_error, log_path)` — busca por código de error
- `buscar_por_tiempo(minutos, log_path)` — busca errores en ventana de tiempo
- `analisis_general(log_path)` — top 5 errores, números, nodos, franjas horarias
- `_resolver_paths(log_path)` — acepta string, lista o directorio

### `correlator.py`
- `correlacionar(log_path, datos_numero, playbooks_path)` — punto de entrada principal
- `_evaluar_general(pb, log_path)` — evalúa playbooks masivos via buscar_por_tiempo()
- `_evaluar_numero_individual(pb, datos_numero)` — evalúa PB006 sobre un MSISDN
- `_evaluar_concentracion(lineas)` — detecta si >50% de errores están en un nodo
- `formatear_para_contexto(disparados)` — formatea para el prompt del LLM
- Retorna lista ordenada por severidad: critica → alta → media → baja

### `connector_ssh.py`
- `investigar(tipo_ne, intencion, inventory_path)` — punto de entrada principal
- `cargar_inventario(path)` — carga ne_inventory.json como dict indexado por id
- `buscar_ne_por_tipo(tipo_ne, inventario)` — busca primer NE activo del tipo pedido
- `ejecutar_comando(ne, intencion)` — conecta SSH y ejecuta el comando del NE
- `formatear_resultado(resultado)` — formatea output para el prompt del LLM
- Soporta autenticación por password y por clave privada

### `playbooks.json`
6 playbooks para red 4G LTE:

| ID | Patrón | Severidad | Condición clave | NE sospechoso |
|---|---|---|---|---|
| PB001 | Tormenta de autenticación | alta | concentrado_en_nodo: true | HSS |
| PB002 | Degradación de nodo de radio | alta | concentrado_en_nodo: true | eNodeB |
| PB003 | Falla del plano de datos | alta | concentrado_en_nodo: false | SGW |
| PB004 | Falla de roaming | media | concentrado_en_nodo: false | HSS |
| PB005 | Degradación de transporte | critica | concentrado_en_nodo: false | TRANSPORTE |
| PB006 | Falla multi-servicio cliente | baja | aplica_a: numero_individual | HSS |

Campos de cada playbook: `id, nombre, descripcion, severidad, condiciones, causa_probable, elemento_sospechoso, acciones, investigar_en`

El campo `investigar_en` define qué consultar en la Etapa 3b: `tipo_ne, intencion, contexto`

### `ne_inventory.json`
Campos por NE: `id, nombre, tipo, vendor, host, puerto, usuario, auth, timeout_segundos, activo, comandos`

El dict `comandos` mapea intenciones a comandos CLI del NE:
```json
"comandos": {
  "estado_nodo":        "comando que ejecutar",
  "alarmas_activas":    "comando que ejecutar",
  "estado_subscriptor": "comando que ejecutar"
}
```

Auth soportada: `{"metodo": "password", "password": "..."}` o `{"metodo": "clave", "ruta_clave": "..."}`

### `ollama_client.py`
- `llamar_ollama(prompt)` — envía a Ollama y retorna respuesta
- `get_token_stats()` — estadísticas acumuladas de la sesión
- `estimar_costo(modelo)` — costo USD estimado para gpt-4o, gpt-4o-mini, claude-sonnet-4-6, claude-haiku-4-5

---

## 5. Formato del Log

```
YYYY-MM-DD HH:MM:SS,mmm LEVEL [NODE] MSGID | MSISDN | SERVICE | CODE: DESCRIPTION
```

**Códigos de error:** `TIMEOUT, CALL_FAIL, CALL_DROP, SMS_FAIL, SMS_TIMEOUT, DATA_DROP, DATA_FAIL, AUTH_FAIL, AUTH_TIMEOUT, ROAM_FAIL, NET_DROP, NET_TIMEOUT`

---

## 6. Decisiones de Diseño

### Separación pasivo/activo
Correlación pasiva (playbooks contra datos del log) y correlación activa (SSH a NEs) son arquitectónicamente independientes. El correlator no sabe de SSH; el conector no sabe de playbooks. El agente los orquesta.

### Conector SSH universal + LLM como parser
Un solo connector_ssh.py funciona para cualquier vendor (Ericsson, Nokia, Cisco, Huawei). El LLM interpreta el output CLI crudo sin necesidad de parsers por vendor — simplificación arquitectural significativa.

### Inventario como configuración externa
`ne_inventory.json` es mantenido por el operador, no por el desarrollador. Agregar un NE nuevo no requiere tocar código.

### Límite de 20 líneas al LLM
LLaMA 3 tiene contexto limitado. Se envían siempre los totales reales y solo 20 líneas representativas para evitar saturación y respuestas inventadas.

### Fallback de intención con orden correcto
El check de número (569 + 11 dígitos) va antes que el check de tiempo (isdigit) porque los números de teléfono satisfacen ambas condiciones.

### Concentración de nodo: umbral 50%
Si un nodo acumula >50% de los errores del tipo evaluado, se considera concentración. Este umbral es configurable en `UMBRAL_CONCENTRACION` en correlator.py.

---

## 7. Entorno de Pruebas

**Contenedor Docker para simular NEs:**
- Imagen: `rastasheep/ubuntu-sshd:latest`
- Nombre: `crazy_pike`
- Puerto: `2222:22`
- Usuario: `root` / Contraseña: `root`
- Scripts instalados: `/root/ne_status.sh`, `/root/auth_stats.sh`

```bash
docker start crazy_pike
ssh root@localhost -p 2222
```

---

## 8. Problemas Conocidos y Soluciones

| Problema | Causa | Solución |
|---|---|---|
| LLM retorna None como intención | LLaMA 3 no completa el JSON | Fallback que infiere desde el valor |
| Número detectado como tiempo | isdigit() true para ambos | Check 569+11 dígitos va antes en el fallback |
| SSH no encontraba NE | ne_inventory.json vacío o tipo no registrado | Verificar inventario y agregar tipo requerido |
| Playbooks masivos no disparan en demo | Log demo distribuye errores en 24h | Esperado — umbrales calibrados para producción |
| LLM mezcla idiomas | Contexto en español + instrucción al final | Instrucción de idioma al inicio del prompt |

---

## 9. Estado Actual del Proyecto

### Completado

| Etapa | Descripción |
|---|---|
| Etapa 1 ✅ | Agente terminal, búsquedas, memoria, fallback |
| Etapa 2 ✅ | Streamlit, patrones, multi-log, tokens, idioma |
| Etapa 3a ✅ | playbooks.json + correlator.py + integración en agent.py |
| Etapa 3b ✅ | ne_inventory.json + connector_ssh.py + 2da integración agent.py |

### Pendiente

| Etapa | Descripción |
|---|---|
| Etapa 4 | Calibrar playbooks con datos reales + equipo de soporte |
| Etapa 5 | FastAPI · multi-modelo · SQLite/PostgreSQL · export PDF/CSV |

---

## 10. Instalación Rápida

```bash
ollama pull llama3 && ollama serve
git clone https://github.com/funk1090/log-analyzer-agent.git
cd log-analyzer-agent
pip install requests streamlit paramiko
streamlit run app.py
```
