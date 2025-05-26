# core/local_llm.py
import requests

class LocalLLM:
    def __init__(self, model_name="mistral"):
        self.model = model_name
        self.history = []

    def send_message(self, message):
        self.history.append({"role": "user", "content": message})
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": self.model, "messages": self.history}
        )
        answer = response.json()["message"]["content"]
        self.history.append({"role": "assistant", "content": answer})
        return answer