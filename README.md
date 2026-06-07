# 🤖 Log Analyzer Agent

> 🇬🇧 English version below &nbsp;|&nbsp; 🇨🇱 Versión en español más abajo

---

## 🇬🇧 English

Conversational AIOps agent for telecom log analysis, powered by **Ollama + LLaMA 3**, running completely locally.

Ask questions in plain language about log files: search by phone number, error type, or time window — and receive an AI-generated diagnosis. The agent automatically correlates error patterns against known failure playbooks and actively queries live network elements via SSH to confirm hypotheses.

---

### ✨ Features

- 🔍 Search by **phone number** (e.g. `569XXXXXXXX`)
- ❌ Search by **error type** (e.g. `TIMEOUT`, `CALL_DROP`, `AUTH_FAIL`)
- 🕐 Search by **time window** (e.g. "last hour", "last 30 minutes")
- 📊 **Automatic pattern detection** — top errors, critical numbers, faulty nodes, and peak hours
- 🧠 **Passive correlation** — 6 LTE failure playbooks automatically matched against log data
- 🔌 **Active investigation** — SSH connector queries live network elements when a pattern is detected
- 🗂️ **Multi-log support** — single file or entire folder of logs
- 🌐 **Web interface** built with Streamlit
- 🧠 **Session memory** — remembers context from the previous query
- 🌍 **Automatic language detection** — responds in Spanish, English, Portuguese, and more
- 💰 **Token usage tracking** — estimates cost per model (GPT-4o, Claude, etc.)
- 🔒 **100% local** — no external APIs, no data sent to the cloud

---

### 🧱 Architecture

```
main.py              →  Terminal conversation loop
agent.py             →  Orchestrator: intent analysis + correlation + SSH investigation
tools.py             →  Log search functions + automatic pattern analysis
correlator.py        →  Playbook correlation engine (passive diagnosis)
connector_ssh.py     →  Universal SSH connector (active investigation)
ollama_client.py     →  HTTP client for Ollama (LLaMA 3) + token tracking
app.py               →  Streamlit web interface
generate_log.py      →  Synthetic log generator for testing (50,000 lines)
playbooks.json       →  LTE failure pattern rules (editable, no code required)
ne_inventory.json    →  Network element inventory with SSH credentials and commands
```

### How a query flows

```
User query (natural language)
        ↓
analizar_intencion() — LLaMA 3 classifies intent as JSON
        ↓
Execute search tool (buscar_por_numero / buscar_por_error / buscar_por_tiempo / analisis_general)
        ↓
correlacionar() — match results against playbooks
        ↓
If pattern detected → investigar() — SSH to suspected NE, run command, get real-time output
        ↓
LLM generates response: findings + diagnosis + recommended actions + live NE data
        ↓
Response to user
```

---

### ⚙️ Requirements

- [Ollama](https://ollama.com/) running locally with the `llama3` model
- Python 3.9+
- `paramiko` (SSH connector)

---

### 🚀 Installation & Usage

#### 1. Start Ollama with LLaMA 3

```bash
ollama pull llama3
ollama serve
```

#### 2. Clone the repository

```bash
git clone https://github.com/funk1090/log-analyzer-agent.git
cd log-analyzer-agent
```

#### 3. Install dependencies

```bash
pip install requests streamlit paramiko
```

#### 4. Configure the NE inventory

Edit `ne_inventory.json` with your network elements (IPs, SSH credentials, commands per intent). A simulated MME and HSS pointing to a local Docker container are included for testing.

#### 5. Generate a test log (optional)

```bash
python generate_log.py
```

#### 6. Run the web interface

```bash
streamlit run app.py
```

#### 7. Or run in terminal

```bash
python main.py
```

---

### 💬 Example queries

```
❓ Give me a summary of the log
❓ Show me all errors for number 56912345678
❓ Show me all TIMEOUT errors
❓ Were there any CALL_DROP errors in the last 2 hours?
❓ What errors occurred in the last 60 minutes?
❓ Did 56934567890 have AUTH_FAIL errors?
```

The agent responds in the same language as the query and automatically includes diagnosis and live NE data when patterns are detected.

---

### 🧩 Playbooks (LTE failure patterns)

| ID | Pattern | Severity | Suspected NE |
|---|---|---|---|
| PB001 | Authentication storm | High | HSS |
| PB002 | Radio node degradation | High | eNodeB |
| PB003 | Data plane failure | High | SGW |
| PB004 | Roaming failure | Medium | HSS |
| PB005 | Transport/core degradation | Critical | Transport |
| PB006 | Multi-service failure (isolated client) | Low | HSS |

Playbooks are defined in `playbooks.json` and can be edited without touching code. Thresholds, error codes, and recommended actions are all configurable.

---

### 🗂️ Project structure

```
log-analyzer-agent/
├── main.py              # Terminal entry point
├── agent.py             # Main agent + intent + correlation + SSH integration
├── tools.py             # Log search tools + pattern analysis
├── correlator.py        # Playbook correlation engine
├── connector_ssh.py     # Universal SSH connector (paramiko)
├── ollama_client.py     # Ollama client + token tracking + cost estimation
├── app.py               # Streamlit web interface
├── generate_log.py      # Synthetic log generator
├── playbooks.json       # LTE failure playbooks (editable)
├── ne_inventory.json    # Network element inventory (editable)
├── telecom_demo.log     # Sample log file (50,000 lines)
└── README.md
```

---

### 📊 Token tracking & cost estimation

| Model | Prompt | Response |
|---|---|---|
| `gpt-4o` | $2.50 / 1M | $10.00 / 1M |
| `gpt-4o-mini` | $0.15 / 1M | $0.60 / 1M |
| `claude-sonnet-4-6` | $3.00 / 1M | $15.00 / 1M |
| `claude-haiku-4-5` | $0.25 / 1M | $1.25 / 1M |

---

### 🛣️ Roadmap

- [x] Conversational agent in terminal
- [x] Search by number, error type, and time window
- [x] Session memory + automatic language detection
- [x] Streamlit web interface
- [x] Automatic pattern detection on log load
- [x] Multi-log support
- [x] Token usage tracking and cost estimation
- [x] Passive correlation — LTE playbooks + correlation engine
- [x] Active investigation — universal SSH connector to network elements
- [ ] Calibrate playbooks with real network data
- [ ] FastAPI REST endpoints
- [ ] Support for other Ollama models (Mistral, Gemma, etc.)
- [ ] Database backend (SQLite → PostgreSQL)
- [ ] Export results to PDF / CSV

---

### 📄 License

MIT — free to use, modify and distribute.

---

## 🇨🇱 Español

Agente AIOps conversacional para análisis de logs de telecomunicaciones, powered by **Ollama + LLaMA 3**, corriendo completamente en local.

Permite hacer consultas en lenguaje natural sobre archivos de log y recibir un diagnóstico generado por IA. El agente correlaciona automáticamente los patrones de error contra playbooks de falla conocidos y consulta activamente elementos de red vía SSH para confirmar hipótesis.

---

### ✨ Características

- 🔍 Búsqueda por **número de teléfono** (ej: `569XXXXXXXX`)
- ❌ Búsqueda por **tipo de error** (ej: `TIMEOUT`, `CALL_DROP`, `AUTH_FAIL`)
- 🕐 Búsqueda por **ventana de tiempo** (ej: "última hora", "últimos 30 minutos")
- 📊 **Detección automática de patrones** — top errores, números críticos, nodos y franjas horarias
- 🧠 **Correlación pasiva** — 6 playbooks de falla LTE evaluados automáticamente
- 🔌 **Investigación activa** — conector SSH consulta elementos de red cuando detecta un patrón
- 🗂️ **Soporte multi-log** — archivo individual o carpeta completa
- 🌐 **Interfaz web** con Streamlit
- 🧠 **Memoria de sesión** — recuerda el contexto de la consulta anterior
- 🌍 **Detección de idioma automática** — responde en español, inglés, portugués y más
- 💰 **Tracking de tokens** — estima el costo por modelo
- 🔒 **100% local** — sin APIs externas

---

### 🧱 Arquitectura

```
main.py              →  Loop de conversación en terminal
agent.py             →  Orquestador: intención + correlación + investigación SSH
tools.py             →  Funciones de búsqueda + análisis de patrones
correlator.py        →  Motor de correlación de playbooks (diagnóstico pasivo)
connector_ssh.py     →  Conector SSH universal (investigación activa)
ollama_client.py     →  Cliente HTTP para Ollama + tracking de tokens
app.py               →  Interfaz web con Streamlit
generate_log.py      →  Generador de logs sintéticos (50.000 líneas)
playbooks.json       →  Reglas de patrones de falla LTE (editable, sin código)
ne_inventory.json    →  Inventario de NEs con credenciales SSH y comandos
```

---

### ⚙️ Requisitos

- [Ollama](https://ollama.com/) con el modelo `llama3`
- Python 3.9+
- `paramiko`

---

### 🚀 Instalación y uso

```bash
# 1. Levantar Ollama
ollama pull llama3 && ollama serve

# 2. Clonar repo
git clone https://github.com/funk1090/log-analyzer-agent.git
cd log-analyzer-agent

# 3. Instalar dependencias
pip install requests streamlit paramiko

# 4. Ejecutar interfaz web
streamlit run app.py

# 5. O ejecutar en terminal
python main.py
```

---

### 🧩 Playbooks LTE

| ID | Patrón | Severidad | NE sospechoso |
|---|---|---|---|
| PB001 | Tormenta de autenticación | Alta | HSS |
| PB002 | Degradación de nodo de radio | Alta | eNodeB |
| PB003 | Falla del plano de datos | Alta | SGW |
| PB004 | Falla de roaming | Media | HSS |
| PB005 | Degradación de transporte o core | Crítica | Transporte |
| PB006 | Falla multi-servicio en cliente aislado | Baja | HSS |

---

### 🛣️ Roadmap

- [x] Agente conversacional en terminal
- [x] Búsqueda por número, tipo de error y ventana de tiempo
- [x] Memoria de sesión + detección de idioma automática
- [x] Interfaz web con Streamlit
- [x] Detección automática de patrones al cargar el log
- [x] Soporte multi-log
- [x] Tracking de tokens y estimación de costos
- [x] Correlación pasiva — playbooks LTE + motor de correlación
- [x] Investigación activa — conector SSH universal a elementos de red
- [ ] Calibrar playbooks con datos reales de red
- [ ] FastAPI + endpoints REST
- [ ] Soporte multi-modelo Ollama (Mistral, Gemma, etc.)
- [ ] Base de datos (SQLite → PostgreSQL)
- [ ] Exportar resultados a PDF / CSV

---

### 📄 Licencia

MIT — libre para usar, modificar y distribuir.
