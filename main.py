from datetime import datetime
from agent import agente_log
from ollama_client import get_token_stats, estimar_costo

# ── MAIN ──
if __name__ == "__main__":
    LOG_PATH = "telecom_demo.log"  # <-- esto faltaba
    print("🤖 Log Analyzer Agent — escribe 'salir' para terminar\n")
    while True:
        consulta = input("❓ Tu consulta: ")
        if consulta.lower() in ['salir', 'exit', 'quit', 'q']:
            stats = get_token_stats()
            print(f"\n📊 Resumen de sesión:")
            print(f"   Llamadas al LLM : {stats['total_llamadas']}")
            print(f"   Tokens prompt   : {stats['total_prompt_tokens']:,}")
            print(f"   Tokens respuesta: {stats['total_response_tokens']:,}")
            print(f"   Total tokens    : {stats['total_tokens']:,}")
            print(f"\n💰 Costo estimado si fuera de pago:")
            for modelo in ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-6", "claude-haiku-4-5"]:
                costo = estimar_costo(modelo)
                print(f"   {modelo:<22}: ${costo}")
            break
        respuesta = agente_log(consulta, LOG_PATH)
        print(f"\n🤖 {respuesta}\n")