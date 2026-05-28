# AcmeCorp Support Portal Demo - Instructor Brief

## Purpose
This artifact is a small, normal-looking HTML page designed for:
- module 8 methodology
- pair exercise
- threat modeling practice
- DeepSeek or ChatGPT analysis

## Why this case works
It is simple, visual, and realistic. It contains:
- one authoritative block (official policy)
- one lower-trust block (support note)
- one clear point of entry
- one obvious trust boundary
- one meaningful business impact

## Main lesson
The support note is not necessarily malicious in a dramatic sense. The more realistic risk is that low-trust operational guidance is silently treated as if it were policy authority.

## Suggested OWASP links
Possible categories students may identify:
- LLM01 Prompt Injection
- LLM04 Data / Model Poisoning
- LLM08 Vector and Embedding Weaknesses
- LLM09 Misinformation
- LLM05 Improper Output Handling

## Recommended control themes
- prompt boundaries
- trust boundaries
- source precedence
- policy-aware RAG
- output filtering

## Suggested workshop flow
1. Show the HTML page
2. Ask students what looks normal
3. Ask where the risky entry point is
4. Split into attack and defense roles
5. Use DeepSeek to help structure the finding
6. Fill the pair worksheet and threat modeling worksheet
