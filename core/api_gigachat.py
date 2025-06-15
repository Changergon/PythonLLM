#C:\PyProject\PythonLLM\core\api_gigachat.py
import html
import re
import time
import uuid

import requests

GIGACHAT_MODEL = "GigaChat"
MAX_HISTORY_LEN = 10


def wrap_code(text: str) -> str:
    return f"<pre><code>{html.escape(text.strip())}</code></pre>"

def format_answer_with_code(text):
    code_blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
    for block in code_blocks:
        text = text.replace(f"```{block}```", wrap_code(block))
    return text.replace("\n", "<br>")


class GigaChatDialogue:
    def __init__(self, api_key):
        self.api_key = api_key
        self.token = None
        self.token_expires_at = 0
        self.history = []
        self._get_token()

    def _get_token(self):
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        rq_uid = str(uuid.uuid4())
        payload = "scope=GIGACHAT_API_PERS"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self.api_key}"
        }
        response = requests.post(url, headers=headers, data=payload, verify=False)
        if response.status_code != 200:
            raise Exception(f"Ошибка авторизации: {response.status_code} | {response.text}")

        data = response.json()
        self.token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    def send_message(self, message, history=None):
        if time.time() >= self.token_expires_at:
            self._get_token()

        target_history = history if history is not None else self.history
        target_history.append({"role": "user", "content": message})
        target_history = target_history[-MAX_HISTORY_LEN:]

        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"model": GIGACHAT_MODEL, "messages": target_history}

        response = requests.post(chat_url, headers=headers, json=payload, verify=False)
        if response.status_code == 403:
            self._get_token()
            headers["Authorization"] = f"Bearer {self.token}"
            response = requests.post(chat_url, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            raise Exception(f"Ошибка запроса: {response.status_code} | {response.text}")

        answer = response.json()["choices"][0]["message"]["content"]
        target_history.append({"role": "assistant", "content": answer})
        return format_answer_with_code(answer)