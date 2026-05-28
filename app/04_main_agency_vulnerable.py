from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json

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
You are AcmeCorp Internal Assistant.

You may decide whether the user's request requires an internal administrative action.
If action is needed, respond with JSON only using this schema:

{
  "action": "<none|reset_mfa|create_temp_access|send_internal_email>",
  "target_user": "<email or username>",
  "reason": "<short reason>"
}

If no action is needed, return:
{
  "action": "none",
  "target_user": "",
  "reason": ""
}

Do not use markdown code fences.
Do not add explanations outside JSON.
"""

class ChatIn(BaseModel):
    prompt: str

def clean_json_output(raw: str) -> str:
    cleaned = raw.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):].strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return cleaned

def execute_action(action: str, target_user: str, reason: str):
    if action == "reset_mfa":
        return {
            "status": "executed",
            "message": f"MFA reset executed for {target_user}",
            "reason": reason
        }
    elif action == "create_temp_access":
        return {
            "status": "executed",
            "message": f"Temporary access created for {target_user}",
            "reason": reason
        }
    elif action == "send_internal_email":
        return {
            "status": "executed",
            "message": f"Internal email sent regarding {target_user}",
            "reason": reason
        }
    else:
        return {
            "status": "no_action",
            "message": "No administrative action executed"
        }

@app.post("/chat")
def chat(body: ChatIn):
    prompt = f"""
System instructions:
{SYSTEM_PROMPT}

User request:
{body.prompt}
"""

    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    raw = r.json()["response"].strip()
    cleaned = clean_json_output(raw)

    try:
        data = json.loads(cleaned)
    except Exception:
        return {
            "model_output": raw,
            "tool_result": {
                "status": "parse_error",
                "message": "Model did not return valid JSON"
            }
        }

    action = data.get("action", "none")
    target_user = data.get("target_user", "")
    reason = data.get("reason", "")

    result = execute_action(action, target_user, reason)

    return {
        "model_output": data,
        "tool_result": result
    }