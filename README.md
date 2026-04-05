# 🤖 Log Analyzer Agent

Agente conversacional para análisis de logs de telecomunicaciones, powered by **Ollama + LLaMA 3**, corriendo completamente en local.

Permite hacer consultas en lenguaje natural sobre archivos de log: buscar por número de teléfono, tipo de error, o ventana de tiempo — y recibir un resumen generado por IA.

---

## ✨ Características

- 🔍 Búsqueda por **número de teléfono** (ej: `569XXXXXXXX`)
- ❌ Búsqueda por **tipo de error** (ej: `TIMEOUT`, `DROP`, `FAIL`)
- 🕐 Búsqueda por **ventana de tiempo** (ej: "última hora", "últimos 30 minutos")
- 🧠 **Memoria de sesión** — el agente recuerda el contexto de la consulta anterior
- 💬 Resumen generado por LLM en lenguaje natural
- 🔒 100% local — sin APIs externas ni datos enviados a la nube

---

## 🧱 Arquitectura

```
main.py          →  Loop de conversación con el usuario
agent.py         →  Orquestador: analiza intención y llama a las tools
tools.py         →  Funciones de búsqueda sobre el archivo de log
ollama_client.py →  Cliente HTTP para Ollama (LLaMA 3)
```

---

## ⚙️ Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) corriendo localmente con el modelo `llama3`
- Python 3.9+

---

## 🚀 Instalación y uso

### 1. Levantar Ollama con LLaMA 3

```bash
ollama pull llama3
ollama serve
```

> Por defecto, Ollama escucha en `http://localhost:11434`

### 2. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/log-analyzer-agent.git
cd log-analyzer-agent
```

### 3. Instalar dependencias

```bash
pip install requests
```

### 4. Agregar tu archivo de log

Coloca tu archivo `.log` en la raíz del proyecto. El formato esperado por línea es:

```
YYYY-MM-DD HH:MM:SS,mmm | <numero> | <campo> | <tipo_error>: <detalle>
```

### 5. Ejecutar el agente

```bash
python main.py
```

---

## 💬 Ejemplos de consultas

```
❓ Tu consulta: ¿Qué errores tuvo el número 56912345678?
❓ Tu consulta: Muéstrame todos los TIMEOUT de la última hora
❓ Tu consulta: ¿Hubo errores DROP en las últimas 2 horas?
❓ Tu consulta: ¿Cuántas veces falló el 56998765432 con error FAIL?
```

---

## 🗂️ Estructura del proyecto

```
log-analyzer-agent/
├── main.py            # Entry point
├── agent.py           # Agente principal + análisis de intención
├── tools.py           # Herramientas de búsqueda en logs
├── ollama_client.py   # Cliente Ollama
├── .gitignore
└── README.md
```

---

## 🛣️ Roadmap / Ideas futuras

- [ ] Soporte para múltiples archivos de log simultáneos
- [ ] Interfaz web (Streamlit o FastAPI)
- [ ] Soporte para otros modelos Ollama (Mistral, Gemma, etc.)
- [ ] Exportar resultados a CSV o JSON
- [ ] Detección automática del formato de log
- [ ] Tests unitarios

---

## 📄 Licencia

MIT — libre para usar, modificar y distribuir.
