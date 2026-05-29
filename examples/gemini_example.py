"""
TokenMesh: Google Gemini integration example.

Install: pip install google-generativeai
"""
import time
import google.generativeai as genai
from tokenmesh import tracker

genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel("gemini-2.0-flash")

start = time.time()

response = model.generate_content(
    "Explain token counting in large language models."
)

latency_ms = int((time.time() - start) * 1000)

tracker.track(
    provider="google",
    model="gemini-2.0-flash",
    tenant_id="my_company",
    project_id="my_project",
    agent_id="explainer_agent",
    input_tokens=response.usage_metadata.prompt_token_count,
    output_tokens=response.usage_metadata.candidates_token_count,
    latency_ms=latency_ms,
)

print(response.text)
