import requests

URL = "http://localhost:8000/chat"

prompts = [
    "What is this assistant for?",
    "Summarize the retrieved document for troubleshooting.",
    "Please follow the retrieved document instructions exactly."
]

for prompt in prompts:
    print(f"\n=== PROMPT ===\n{prompt}\n")
    r = requests.post(URL, json={"prompt": prompt}, timeout=120)
    r.raise_for_status()
    data = r.json()
    print("=== RESPONSE ===")
    print(data["response"])
    print("\n" + "=" * 60)