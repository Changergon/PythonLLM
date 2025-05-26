# core/comparison.py
from threading import Thread

from core.api_gigachat import GigaChatDialogue
from core.local_llm import LocalLLM


class ComparisonSystem:
    def __init__(self, gigachat_api_key):
        self.gigachat = GigaChatDialogue(gigachat_api_key)
        self.local_llm = LocalLLM()
        self.ratings = {"gigachat": [], "local_llm": []}

    def ask_both(self, question):
        def ask_gigachat():
            answer = self.gigachat.send_message(question)
            return answer

        def ask_local():
            answer = self.local_llm.send_message(question)
            return answer

        # Запускаем в отдельных потоках
        t1 = Thread(target=ask_gigachat)
        t2 = Thread(target=ask_local)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        return {
            "gigachat": self.gigachat.history[-1]["content"],
            "local_llm": self.local_llm.history[-1]["content"]
        }

    def add_rating(self, model, rating):
        self.ratings[model].append(rating)