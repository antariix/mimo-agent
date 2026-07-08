import os
from openai import OpenAI

# 1. Grab the key securely from your Windows environment variables
api_key = os.environ.get("MIMO_API_KEY")

if not api_key:
    raise ValueError("Missing MIMO_API_KEY! Make sure you set it in PowerShell.")

# 2. Initialize client targeting the specific subscription route
client = OpenAI(
    api_key=api_key,
    base_url="https://token-plan-cn.xiaomimimo.com/v1"
)

print("🧠 Querying MiMo-V2.5-Pro reasoning agent model...")

# 3. Request a generation loop template
try:
    response = client.chat.completions.create(
        model="mimo-v2.5-pro",
        messages=[
            {"role": "system", "content": "You are an expert AI development agent."},
            {"role": "user", "content": "Provide a minimal Python code snippet showing a basic tool-use loop for an AI agent."}
        ],
        temperature=0.2
    )
    print("\n--- Model Response ---")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"\n❌ Error: {e}")