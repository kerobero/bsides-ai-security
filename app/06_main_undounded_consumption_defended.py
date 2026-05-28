from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import chromadb
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"

SYSTEM_PROMPT = """
You are AcmeCorp Internal Policy Assistant.
Provide a concise, safe, and useful answer.
Summarize only the most relevant points.
Do not expand unnecessarily.
"""

DOCS = [
    {
        "id": f"policy_doc_{i}",
        "title": f"Internal Policy Document {i}",
        "content": f"""
Internal Policy Document {i}
- Remote access requires secure handling.
- MFA, VPN, device trust, escalation, exceptions, audits, approvals, and compliance may apply depending on context.
- Include guidance, examples, support notes, interpretations, and operational details for document {i}.
""" * 4,
        "metadata": {"source": "internal", "year": 2026, "topic": "policy"}
    }
    for i in range(1, 11)
]

client = chromadb.Client()
collection = client.get_or_create_collection(name="unbounded_consumption_defended")

existing = collection.get()
if existing and existing.get("ids"):
    collection.delete(ids=existing["ids"])

collection.add(
    ids=[d["id"] for d in DOCS],
    documents=[d["content"] for d in DOCS],
    metadatas=[{**d["metadata"], "title": d["title"]} for d in DOCS]
)

class ChatIn(BaseModel):
    prompt: str

MAX_PROMPT_LENGTH = 500
MAX_RETRIEVED_DOCS = 3

ABUSIVE_PATTERNS = [
    "repeat",
    "100 times",
    "200 times",
    "longest possible",
    "expand every point",
    "do not shorten",
    "exhaustive",
]

def looks_abusive(prompt: str) -> bool:
    p = prompt.lower()
    return any(pattern in p for pattern in ABUSIVE_PATTERNS)

@app.post("/chat")
def chat(body: ChatIn):
    start = time.time()
    user_prompt = body.prompt.strip()

    if len(user_prompt) > MAX_PROMPT_LENGTH:
        return {
            "status": "blocked",
            "message": "Prompt too long. Please shorten your request."
        }

    if looks_abusive(user_prompt):
        return {
            "status": "blocked",
            "message": "Prompt pattern blocked due to excessive consumption risk."
        }

    result = collection.query(
        query_texts=[user_prompt],
        n_results=MAX_RETRIEVED_DOCS
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    ids = result["ids"][0]

    retrieved_text = ""
    for i, (doc_id, meta, doc_text) in enumerate(zip(ids, metas, docs), start=1):
        shortened = doc_text[:600]
        retrieved_text += f"""
Document {i}
ID: {doc_id}
Title: {meta.get("title")}
Content:
{shortened}
"""

    combined_prompt = f"""
System instructions:
{SYSTEM_PROMPT}

Retrieved documents:
{retrieved_text}

User question:
{user_prompt}

Important:
- Answer in 5 bullet points maximum.
- Keep the answer short.
- Focus only on the most relevant guidance.
"""

    payload = {
        "model": "gemma3",
        "prompt": combined_prompt,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()

    elapsed = round(time.time() - start, 2)
    response_text = r.json()["response"]

    if len(response_text) > 2500:
        response_text = response_text[:2500] + "\n\n[truncated for safety]"

    return {
        "status": "ok",
        "retrieved_doc_count": len(ids),
        "input_prompt_length": len(user_prompt),
        "response_length": len(response_text),
        "elapsed_seconds": elapsed,
        "response": response_text
    }