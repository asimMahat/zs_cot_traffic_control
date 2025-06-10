# llm_interface.py (updated for openai>=1.0.0)
import os
import openai

class LLMInterface:
    def __init__(self, model):
        self.model = "gpt-3.5-turbo"

    def query(self, system_msg: str, user_msg: str) -> str:
        # In openai>=1.0.0, ChatCompletion.create → chat.completions.create
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=100
        )
        # The structure of response.choices is the same
        return response.choices[0].message.content
