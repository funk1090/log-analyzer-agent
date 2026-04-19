# 🤖 Log Analyzer Agent

> 🇬🇧 English version below &nbsp;|&nbsp; 🇨🇱 Versión en español más abajo

---

## 🇬🇧 English

Conversational agent for telecom log analysis, powered by **Ollama + LLaMA 3**, running completely locally.

Ask questions in plain language about log files: search by phone number, error type, or time window — and receive an AI-generated summary.

---

### ✨ Features

- 🔍 Search by **phone number** (e.g. `569XXXXXXXX`)
- ❌ Search by **error type** (e.g. `TIMEOUT`, `DROP`, `FAIL`)
- 🕐 Search by **time window** (e.g. "last hour", "last 30 minutes")
- 🧠 **Session memory** — the agent remembers the context of the previous query
- 💬 LLM-generated summary in natural language
- 🔒 100% local — no external APIs, no data sent to the cloud

---

### 🧱 Architecture

```
main.py          →  Conversation loop with the user
agent.py         →  Orchestrator: analyzes intent and calls tools
tools.py         →  Log file search functions
ollama_client.py →  HTTP client for Ollama (LLaMA 3)
```

---

### ⚙️ Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
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
pip install requests
```

#### 4. Add your log file

Place your `.log` file in the project root. A sample log file (`sample.log`) is included so you can test it immediately.

Expected format per line:

```
YYYY-MM-DD HH:MM:SS,mmm | <number> | <field> | <error_type>: <detail>
```

#### 5. Run the agent

```bash
python main.py
```

---

### 💬 Example queries

```
❓ Your query: What errors did number 56912345678 have?
❓ Your query: Show me all TIMEOUT errors in the last hour
❓ Your query: Were there any DROP errors in the last 2 hours?
❓ Your query: How many times did 56998765432 fail with a FAIL error?
```

---

### 🗂️ Project structure

```
log-analyzer-agent/
├── main.py            # Entry point
├── agent.py           # Main agent + intent analysis
├── tools.py           # Log search tools
├── ollama_client.py   # Ollama client
├── sample.log         # Sample log file for testing
├── .gitignore
└── README.md
```

---

### 🛣️ Roadmap / Future ideas

- [ ] Support for multiple log files simultaneously
- [ ] Web interface (Streamlit or FastAPI)
- [ ] Support for other Ollama models (Mistral, Gemma, etc.)
- [ ] Export results to CSV or JSON
- [ ] Automatic log format detection
- [ ] Unit tests

---

### 📄 License

MIT — free to use, modify and distribute.

---

## 🇨🇱 Español

Agente conversacional para análisis de logs de telecomunicaciones, powered by **Ollama + LLaMA 3**, corriendo completamente en local.

Permite hacer consultas en lenguaje natural sobre archivos de log: buscar por número de teléfono, tipo de error, o ventana de tiempo — y recibir un resumen generado por IA.

---

### ✨ Características

- 🔍 Búsqueda por **número de teléfono** (ej: `569XXXXXXXX`)
- ❌ Búsqueda por **tipo de error** (ej: `TIMEOUT`, `DROP`, `FAIL`)
- 🕐 Búsqueda por **ventana de tiempo** (ej: "última hora", "últimos 30 minutos")
- 🧠 **Memoria de sesión** — el agente recuerda el contexto de la consulta anterior
- 💬 Resumen generado por LLM en lenguaje natural
- 🔒 100% local — sin APIs externas ni datos enviados a la nube

---

### 🧱 Arquitectura

```
main.py          →  Loop de conversación con el usuario
agent.py         →  Orquestador: analiza intención y llama a las tools
tools.py         →  Funciones de búsqueda sobre el archivo de log
ollama_client.py →  Cliente HTTP para Ollama (LLaMA 3)
```

---

### ⚙️ Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
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
pip install requests
```

#### 4. Agregar tu archivo de log

Coloca tu archivo `.log` en la raíz del proyecto. Se incluye un archivo de log de ejemplo (`sample.log`) para que puedas probarlo de inmediato.

El formato esperado por línea es:

```
YYYY-MM-DD HH:MM:SS,mmm | <numero> | <campo> | <tipo_error>: <detalle>
```

#### 5. Ejecutar el agente

```bash
python main.py
```

---

### 💬 Ejemplos de consultas

```
❓ Tu consulta: ¿Qué errores tuvo el número 56912345678?
❓ Tu consulta: Muéstrame todos los TIMEOUT de la última hora
❓ Tu consulta: ¿Hubo errores DROP en las últimas 2 horas?
❓ Tu consulta: ¿Cuántas veces falló el 56998765432 con error FAIL?
```

---

### 🗂️ Estructura del proyecto

```
log-analyzer-agent/
├── main.py            # Entry point
├── agent.py           # Agente principal + análisis de intención
├── tools.py           # Herramientas de búsqueda en logs
├── ollama_client.py   # Cliente Ollama
├── sample.log         # Archivo de log de ejemplo para pruebas
├── .gitignore
└── README.md
```

---

### 🛣️ Roadmap / Ideas futuras

- [ ] Soporte para múltiples archivos de log simultáneos
- [ ] Interfaz web (Streamlit o FastAPI)
- [ ] Soporte para otros modelos Ollama (Mistral, Gemma, etc.)
- [ ] Exportar resultados a CSV o JSON
- [ ] Detección automática del formato de log
- [ ] Tests unitarios

---

### 📄 Licencia

MIT — libre para usar, modificar y distribuir.
