"""
TokenMesh: AWS Bedrock (Meta Llama) integration example.

Install: pip install boto3
Credentials: configure via AWS CLI (`aws configure`) or env vars
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
"""
import json
import time
import boto3
from tokenmesh import tracker

client = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "meta.llama4-maverick-17b-instruct-v1:0"

prompt = "Explain token counting in large language models."
body = json.dumps({
    "prompt": prompt,
    "max_gen_len": 512,
    "temperature": 0.7,
})

start = time.time()

response = client.invoke_model(
    modelId=MODEL_ID,
    body=body,
    contentType="application/json",
    accept="application/json",
)

latency_ms = int((time.time() - start) * 1000)

result = json.loads(response["body"].read())

# Bedrock returns token counts in the response metadata
input_tokens  = result.get("prompt_token_count", 0)
output_tokens = result.get("generation_token_count", 0)

tracker.track(
    provider="aws_bedrock",
    model="llama-4-maverick",
    tenant_id="my_company",
    project_id="my_project",
    agent_id="llama_agent",
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    latency_ms=latency_ms,
)

print(result.get("generation", ""))
