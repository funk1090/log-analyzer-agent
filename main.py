from datetime import datetime
from agent import agente_log

# ── MAIN ──
if __name__ == "__main__":
    LOG_PATH = "telecom_demo.log"  # <-- cambia aquí cuando necesites otro archivo
    print("🤖 Log Analyzer Agent — escribe 'salir' para terminar\n")
    while True:
        consulta = input("❓ Tu consulta: ")
        if consulta.lower() in ['salir', 'exit', 'quit', 'q']:
            break
        respuesta = agente_log(consulta, LOG_PATH)
        print(f"\n🤖 {respuesta}\n")