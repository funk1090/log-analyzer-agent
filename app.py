import streamlit as st
import os
import glob
from agent import agente_log
from tools import obtener_logs_de_folder, analisis_general

st.set_page_config(page_title="Log Analyzer Agent", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
    .stApp { background-color: #0a0e1a; color: #e2e8f0; }
    [data-testid="stSidebar"] { background-color: #0f1629; border-right: 1px solid #1e2d4a; }
    .metric-card { background: #0f1629; border: 1px solid #1e2d4a; border-radius: 8px; padding: 0.75rem 1rem; text-align: center; margin-bottom: 0.5rem; }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #38bdf8; }
    .metric-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-error { color: #f87171; }
    .metric-ok    { color: #34d399; }
    .chat-user  { background: #1e2d4a; border-left: 3px solid #38bdf8; border-radius: 0 8px 8px 0; padding: 0.75rem 1rem; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #bae6fd; }
    .chat-agent { background: #0f1629; border: 1px solid #1e2d4a; border-radius: 8px; padding: 1rem 1.25rem; margin: 0.5rem 0; font-size: 0.9rem; line-height: 1.6; }
    .chat-label { font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }
    .intent-tag { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; margin-left: 0.5rem; background: #1e2d4a; color: #38bdf8; border: 1px solid #2a3f5f; }
    .section-title { font-size: 0.72rem; color: #64748b; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.5px; margin: 0.75rem 0 0.4rem 0; }
    .pattern-card { background: #0f1629; border: 1px solid #1e2d4a; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.4rem; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
    .pattern-num  { color: #f87171; font-weight: 700; }
    .pattern-label { color: #64748b; }
    .stTextInput > div > div > input { background-color: #0f1629 !important; border: 1px solid #1e2d4a !important; color: #e2e8f0 !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.9rem !important; border-radius: 8px !important; }
    .stTextInput > div > div > input:focus { border-color: #38bdf8 !important; box-shadow: 0 0 0 2px rgba(56,189,248,0.1) !important; }
    .stButton > button { background: #38bdf8 !important; color: #0a0e1a !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important; }
    .stButton > button:hover { background: #7dd3fc !important; }
    .stSelectbox > div > div { background-color: #0f1629 !important; border: 1px solid #1e2d4a !important; color: #e2e8f0 !important; border-radius: 8px !important; }
    hr { border-color: #1e2d4a !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
for key, val in [("historial", []), ("log_path", None), ("log_mode", "single"), ("patron_data", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🔍 Log Analyzer")
    st.markdown("---")

    # Modo: carpeta o archivo
    st.markdown('<div class="section-title">Fuente de logs</div>', unsafe_allow_html=True)
    modo = st.radio("Modo", ["Archivo único", "Carpeta completa"], label_visibility="collapsed", horizontal=True)

    if modo == "Archivo único":
        st.session_state.log_mode = "single"
        # Input manual de path
        path_manual = st.text_input("Path del archivo", value=st.session_state.log_path or "", placeholder="/ruta/al/archivo.log")
        logs_locales = glob.glob("*.log")
        if logs_locales:
            st.markdown('<div class="section-title">O selecciona uno</div>', unsafe_allow_html=True)
            seleccionado = st.selectbox("Log local", [""] + logs_locales, label_visibility="collapsed")
            if seleccionado:
                path_manual = seleccionado
        if path_manual and os.path.isfile(path_manual):
            st.session_state.log_path = path_manual
        elif path_manual:
            st.warning("Archivo no encontrado")

    else:
        st.session_state.log_mode = "folder"
        folder_manual = st.text_input("Path de la carpeta", placeholder="/ruta/a/la/carpeta/logs")
        if folder_manual and os.path.isdir(folder_manual):
            logs_en_folder = obtener_logs_de_folder(folder_manual)
            if logs_en_folder:
                st.session_state.log_path = logs_en_folder  # lista de paths
                st.success(f"{len(logs_en_folder)} archivos encontrados")
                with st.expander("Ver archivos"):
                    for l in logs_en_folder:
                        st.markdown(f"<span style='font-family:monospace;font-size:0.75rem;color:#64748b'>{os.path.basename(l)}</span>", unsafe_allow_html=True)
            else:
                st.warning("No se encontraron archivos .log en esa carpeta")
        elif folder_manual:
            st.warning("Carpeta no encontrada")

    # Métricas del log actual
    if st.session_state.log_path:
        st.markdown("---")
        st.markdown('<div class="section-title">Estadísticas</div>', unsafe_allow_html=True)
        try:
            datos = analisis_general(st.session_state.log_path)
            st.markdown(f"""
            <div class="metric-card"><div class="metric-value">{datos['total_lineas']:,}</div><div class="metric-label">Total líneas</div></div>
            <div class="metric-card"><div class="metric-value metric-error">{datos['total_errores']:,}</div><div class="metric-label">Errores · {datos['tasa_error']}%</div></div>
            <div class="metric-card"><div class="metric-value metric-ok">{datos['total_ok']:,}</div><div class="metric-label">OK</div></div>
            """, unsafe_allow_html=True)

            # Patrones automáticos
            st.markdown("---")
            st.markdown('<div class="section-title">🔥 Top errores</div>', unsafe_allow_html=True)
            for e in datos['top_errores']:
                st.markdown(f'<div class="pattern-card"><span class="pattern-num">{e["total"]}</span> <span class="pattern-label">{e["codigo"]}</span></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">📱 Números críticos</div>', unsafe_allow_html=True)
            for n in datos['top_numeros']:
                st.markdown(f'<div class="pattern-card"><span class="pattern-num">{n["errores"]}</span> <span class="pattern-label">{n["numero"]}</span></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">🗼 Nodos con más fallas</div>', unsafe_allow_html=True)
            for n in datos['top_nodos']:
                st.markdown(f'<div class="pattern-card"><span class="pattern-num">{n["errores"]}</span> <span class="pattern-label">{n["nodo"]}</span></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">🕐 Franja horaria crítica</div>', unsafe_allow_html=True)
            for h in datos['franja_horaria']:
                st.markdown(f'<div class="pattern-card"><span class="pattern-num">{h["errores"]}</span> <span class="pattern-label">{h["hora"]}</span></div>', unsafe_allow_html=True)

        except Exception as ex:
            st.error(f"Error al leer el log: {ex}")

    # Quick queries
    st.markdown("---")
    st.markdown('<div class="section-title">Consultas rápidas</div>', unsafe_allow_html=True)
    quick_queries = [
        "give me a summary of the log",
        "show me errors in the last 60 minutes",
        "show me all TIMEOUT errors",
        "show me all CALL_DROP errors",
        "show me AUTH_FAIL errors",
    ]
    for q in quick_queries:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.session_state["quick_query"] = q

    st.markdown("---")
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.historial = []
        st.rerun()

    st.markdown('<div style="font-size:0.7rem;color:#334155;margin-top:1rem;font-family:monospace">ollama · llama3 · local</div>', unsafe_allow_html=True)

# ── MAIN ──
st.markdown("""
<div style="padding:1.5rem 0 1rem;border-bottom:1px solid #1e2d4a;margin-bottom:1.5rem">
    <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.8rem;color:#38bdf8">🔍 Log Analyzer Agent</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#64748b;margin-top:0.25rem">natural language · telecom logs · 100% local</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.log_path:
    st.info("👈 Selecciona un archivo o carpeta de logs en el panel lateral para comenzar.")
else:
    # Historial
    if not st.session_state.historial:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#334155">
            <div style="font-size:2rem;margin-bottom:1rem">🤖</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem">Escribe una consulta o selecciona una del menú lateral</div>
        </div>""", unsafe_allow_html=True)

    for entrada in st.session_state.historial:
        st.markdown(f'<div class="chat-label">usuario</div><div class="chat-user">❓ {entrada["consulta"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-label">agente <span class="intent-tag">{entrada.get("tipo","")}</span></div><div class="chat-agent">{entrada["respuesta"]}</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)

    # Input
    st.markdown("---")
    col1, col2 = st.columns([5, 1])
    with col1:
        consulta = st.text_input("Consulta", placeholder="Ej: give me a summary / errores del número 56912345678...", label_visibility="collapsed")
    with col2:
        enviar = st.button("Enviar →", use_container_width=True)

    consulta_a_procesar = st.session_state.pop("quick_query", None) or (consulta if enviar else None)

    if consulta_a_procesar and consulta_a_procesar.strip():
        if not st.session_state.historial or st.session_state.historial[-1]["consulta"] != consulta_a_procesar:
            with st.spinner("🔍 Analizando logs..."):
                try:
                    respuesta = agente_log(consulta_a_procesar, st.session_state.log_path)
                    st.session_state.historial.append({"consulta": consulta_a_procesar, "respuesta": respuesta, "tipo": ""})
                except Exception as e:
                    st.error(f"Error: {e}")
            st.rerun()