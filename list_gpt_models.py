import os
import openai

# Make sure your API key is set (e.g. via environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Call the new v1 endpoint
models = openai.models.list()

print("Available model IDs:")
for m in models.data:
    print(" •", m.id)
