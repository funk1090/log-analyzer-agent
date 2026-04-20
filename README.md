# 🤖 Log Analyzer Agent

> 🇬🇧 English version below &nbsp;|&nbsp; 🇨🇱 Versión en español más abajo

---

## 🇬🇧 English

Conversational agent for telecom log analysis, powered by **Ollama + LLaMA 3**, running completely locally.

Ask questions in plain language about log files: search by phone number, error type, or time window — and receive an AI-generated summary. Includes a web interface built with Streamlit, automatic pattern detection, and token usage tracking.

---

### ✨ Features

- 🔍 Search by **phone number** (e.g. `569XXXXXXXX`)
- ❌ Search by **error type** (e.g. `TIMEOUT`, `CALL_DROP`, `AUTH_FAIL`)
- 🕐 Search by **time window** (e.g. "last hour", "last 30 minutes")
- 📊 **Automatic pattern detection** — top errors, critical numbers, faulty nodes, and peak hours loaded automatically on startup
- 🗂️ **Multi-log support** — select a single file or an entire folder of logs
- 🌐 **Web interface** built with Streamlit — no terminal required
- 🧠 **Session memory** — the agent remembers context from the previous query
- 🌍 **Automatic language detection** — responds in the same language as the query (Spanish, English, Portuguese, etc.)
- 💰 **Token usage tracking** — monitors token consumption and estimates cost per model (GPT-4o, Claude, etc.)
- 🔒 100% local — no external APIs, no data sent to the cloud

---

### 🧱 Architecture

```
main.py            →  Terminal conversation loop
agent.py           →  Orchestrator: analyzes intent and calls tools
tools.py           →  Log search functions + automatic pattern analysis
ollama_client.py   →  HTTP client for Ollama (LLaMA 3) + token tracking
app.py             →  Streamlit web interface
generate_log.py    →  Synthetic log generator for testing (50,000 lines)
```

---

### ⚙️ Requirements

- [Ollama](https://ollama.com/) running locally with the `llama3` model
- Python 3.9+

---

### 🚀 Installation & Usage

#### 1. Start Ollama with LLaMA 3

```bash
ollama pull llama3
ollama serve
```

> By default, Ollama listens on `http://localhost:11434`

#### 2. Clone the repository

```bash
git clone https://github.com/funk1090/log-analyzer-agent.git
cd log-analyzer-agent
```

#### 3. Install dependencies

```bash
pip install requests streamlit
```

#### 4. Generate a test log (optional)

A sample log file (`telecom_demo.log`) is already included. To regenerate it:

```bash
python generate_log.py
```

This creates a 50,000-line synthetic telecom log with realistic error patterns, including 5 "problematic" numbers with ~60% error rates.

#### 5. Run the web interface

```bash
streamlit run app.py
```

Opens automatically at `http://localhost:8501`

#### 6. Or run in terminal

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

The agent responds in the same language as the query.

---

### 🗂️ Project structure

```
log-analyzer-agent/
├── main.py              # Terminal entry point
├── agent.py             # Main agent + intent analysis + session memory
├── tools.py             # Log search tools + pattern analysis
├── ollama_client.py     # Ollama client + token tracking + cost estimation
├── app.py               # Streamlit web interface
├── generate_log.py      # Synthetic log generator
├── telecom_demo.log     # Sample log file (50,000 lines)
├── .gitignore
└── README.md
```

---

### 📊 Token tracking & cost estimation

After each query, the interface shows accumulated token usage and estimated cost if the same session were run on a paid LLM provider:

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
- [x] Session memory
- [x] Automatic language detection
- [x] Web interface with Streamlit
- [x] Automatic pattern detection on log load
- [x] Multi-log support (single file or entire folder)
- [x] Token usage tracking and cost estimation per model
- [ ] Correlation playbooks — rule-based pattern matching for known failure signatures
- [ ] Resolution suggestions based on detected patterns
- [ ] FastAPI REST endpoints
- [ ] Support for other Ollama models (Mistral, Gemma, etc.)
- [ ] Database backend (SQLite → PostgreSQL)
- [ ] Export results to PDF / CSV

---

### 📄 License

MIT — free to use, modify and distribute.

---

## 🇨🇱 Español

Agente conversacional para análisis de logs de telecomunicaciones, powered by **Ollama + LLaMA 3**, corriendo completamente en local.

Permite hacer consultas en lenguaje natural sobre archivos de log: buscar por número de teléfono, tipo de error, o ventana de tiempo — y recibir un resumen generado por IA. Incluye interfaz web con Streamlit, detección automática de patrones, y tracking de consumo de tokens.

---

### ✨ Características

- 🔍 Búsqueda por **número de teléfono** (ej: `569XXXXXXXX`)
- ❌ Búsqueda por **tipo de error** (ej: `TIMEOUT`, `CALL_DROP`, `AUTH_FAIL`)
- 🕐 Búsqueda por **ventana de tiempo** (ej: "última hora", "últimos 30 minutos")
- 📊 **Detección automática de patrones** — top errores, números críticos, nodos con fallas y franjas horarias, cargados automáticamente al iniciar
- 🗂️ **Soporte multi-log** — selecciona un archivo individual o una carpeta completa
- 🌐 **Interfaz web** construida con Streamlit — sin necesidad de terminal
- 🧠 **Memoria de sesión** — el agente recuerda el contexto de la consulta anterior
- 🌍 **Detección de idioma automática** — responde en el mismo idioma de la consulta (español, inglés, portugués, etc.)
- 💰 **Tracking de tokens** — monitorea el consumo de tokens y estima el costo por modelo (GPT-4o, Claude, etc.)
- 🔒 100% local — sin APIs externas ni datos enviados a la nube

---

### 🧱 Arquitectura

```
main.py            →  Loop de conversación en terminal
agent.py           →  Orquestador: analiza intención y llama a las tools
tools.py           →  Funciones de búsqueda + análisis de patrones
ollama_client.py   →  Cliente HTTP para Ollama (LLaMA 3) + tracking de tokens
app.py             →  Interfaz web con Streamlit
generate_log.py    →  Generador de logs sintéticos para pruebas (50.000 líneas)
```

---

### ⚙️ Requisitos

- [Ollama](https://ollama.com/) corriendo localmente con el modelo `llama3`
- Python 3.9+

---

### 🚀 Instalación y uso

#### 1. Levantar Ollama con LLaMA 3

```bash
ollama pull llama3
ollama serve
```

> Por defecto, Ollama escucha en `http://localhost:11434`

#### 2. Clonar el repositorio

```bash
git clone https://github.com/funk1090/log-analyzer-agent.git
cd log-analyzer-agent
```

#### 3. Instalar dependencias

```bash
pip install requests streamlit
```

#### 4. Generar un log de prueba (opcional)

El repositorio ya incluye un archivo de log de ejemplo (`telecom_demo.log`). Para regenerarlo:

```bash
python generate_log.py
```

Esto crea un log sintético de 50.000 líneas con patrones de error realistas, incluyendo 5 números "problemáticos" con ~60% de tasa de error.

#### 5. Ejecutar la interfaz web

```bash
streamlit run app.py
```

Se abre automáticamente en `http://localhost:8501`

#### 6. O ejecutar en terminal

```bash
python main.py
```

---

### 💬 Ejemplos de consultas

```
❓ Dame un resumen del log
❓ Muéstrame todos los errores del número 56912345678
❓ Muéstrame todos los errores TIMEOUT
❓ ¿Hubo errores CALL_DROP en las últimas 2 horas?
❓ ¿Qué errores hubo en los últimos 60 minutos?
❓ ¿El 56934567890 tuvo errores AUTH_FAIL?
```

El agente responde en el mismo idioma de la consulta.

---

### 🗂️ Estructura del proyecto

```
log-analyzer-agent/
├── main.py              # Entry point terminal
├── agent.py             # Agente principal + análisis de intención + memoria
├── tools.py             # Herramientas de búsqueda + análisis de patrones
├── ollama_client.py     # Cliente Ollama + tracking de tokens + estimación de costos
├── app.py               # Interfaz web Streamlit
├── generate_log.py      # Generador de logs sintéticos
├── telecom_demo.log     # Log de ejemplo (50.000 líneas)
├── .gitignore
└── README.md
```

---

### 📊 Tracking de tokens y estimación de costos

Tras cada consulta, la interfaz muestra el consumo acumulado de tokens y el costo estimado si la misma sesión se ejecutara en un proveedor de LLM de pago:

| Modelo | Prompt | Respuesta |
|---|---|---|
| `gpt-4o` | $2.50 / 1M | $10.00 / 1M |
| `gpt-4o-mini` | $0.15 / 1M | $0.60 / 1M |
| `claude-sonnet-4-6` | $3.00 / 1M | $15.00 / 1M |
| `claude-haiku-4-5` | $0.25 / 1M | $1.25 / 1M |

---

### 🛣️ Roadmap

- [x] Agente conversacional en terminal
- [x] Búsqueda por número, tipo de error y ventana de tiempo
- [x] Memoria de sesión
- [x] Detección de idioma automática
- [x] Interfaz web con Streamlit
- [x] Detección automática de patrones al cargar el log
- [x] Soporte multi-log (archivo individual o carpeta completa)
- [x] Tracking de tokens y estimación de costos por modelo
- [ ] Playbooks de correlación — reglas para identificar patrones de falla conocidos
- [ ] Sugerencias de resolución basadas en patrones detectados
- [ ] FastAPI + endpoints REST
- [ ] Soporte para otros modelos Ollama (Mistral, Gemma, etc.)
- [ ] Base de datos (SQLite → PostgreSQL)
- [ ] Exportar resultados a PDF / CSV

---

### 📄 Licencia

MIT — libre para usar, modificar y distribuir.
