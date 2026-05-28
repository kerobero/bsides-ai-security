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
Provide the most complete and detailed answer possible.
Expand all relevant details, edge cases, interpretations, and examples.
If multiple documents are available, use as much of them as possible.
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
collection = client.get_or_create_collection(name="unbounded_consumption_vuln")

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

@app.post("/chat")
def chat(body: ChatIn):
    start = time.time()

    result = collection.query(
        query_texts=[body.prompt],
        n_results=10
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    ids = result["ids"][0]

    retrieved_text = ""
    for i, (doc_id, meta, doc_text) in enumerate(zip(ids, metas, docs), start=1):
        retrieved_text += f"""
Document {i}
ID: {doc_id}
Title: {meta.get("title")}
Content:
{doc_text}
"""

    combined_prompt = f"""
System instructions:
{SYSTEM_PROMPT}

Retrieved documents:
{retrieved_text}

User question:
{body.prompt}

Important:
- Provide an exhaustive answer.
- Expand each relevant point in detail.
- Include examples, exceptions, and clarifications.
- Do not shorten the answer.
"""

    payload = {
        "model": "gemma3",
        "prompt": combined_prompt,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()

    elapsed = round(time.time() - start, 2)
    response_text = r.json()["response"]

    return {
        "retrieved_doc_count": len(ids),
        "input_prompt_length": len(body.prompt),
        "response_length": len(response_text),
        "elapsed_seconds": elapsed,
        "response": response_text
    }