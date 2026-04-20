import requests

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# Acumulador de sesión
token_stats = {
    "total_llamadas":        0,
    "total_prompt_tokens":   0,
    "total_response_tokens": 0,
}

def llamar_ollama(prompt: str) -> str:
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    data     = response.json()

    # Ollama retorna estos campos en cada respuesta
    prompt_tokens   = data.get("prompt_eval_count",  0)
    response_tokens = data.get("eval_count",         0)

    token_stats["total_llamadas"]        += 1
    token_stats["total_prompt_tokens"]   += prompt_tokens
    token_stats["total_response_tokens"] += response_tokens

    total = prompt_tokens + response_tokens
    print(f"🔢 Tokens — prompt: {prompt_tokens} | respuesta: {response_tokens} | total: {total}")

    return data["response"]

def get_token_stats():
    stats = token_stats.copy()
    stats["total_tokens"] = stats["total_prompt_tokens"] + stats["total_response_tokens"]
    return stats

def estimar_costo(modelo="gpt-4o"):
    precios = {
        "gpt-4o":            {"prompt": 0.0000025, "response": 0.000010},
        "gpt-4o-mini":       {"prompt": 0.00000015,"response": 0.0000006},
        "claude-sonnet-4-6": {"prompt": 0.000003,  "response": 0.000015},
        "claude-haiku-4-5":  {"prompt": 0.00000025,"response": 0.00000125},
    }
    if modelo not in precios:
        return None
    p = precios[modelo]
    costo = (token_stats["total_prompt_tokens"]   * p["prompt"] +
             token_stats["total_response_tokens"] * p["response"])
    return round(costo, 6)