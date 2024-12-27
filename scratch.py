from openai import OpenAI
import os

OPENAI_API_KEY = "xxx"

client = OpenAI(api_key=OPENAI_API_KEY)
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "write a haiku about ai"}
    ]
)

print(completion.choices[0].message)

