from groq import Groq

# ⚠️ HARDCODED API KEY (REMOVE BEFORE PUSHING TO GITHUB)
GROQ_API_KEY = "YOUR_GROQ_API"

client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt):
    resp = client.chat.completions.create(
        # ✅ CURRENT WORKING MODEL ON GROQ
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a precise JSON extraction engine. Always output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    return resp.choices[0].message.content
