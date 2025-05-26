import time
import uuid
import re
import requests


def format_answer_with_code(text):
    # Преобразуем блоки кода вида ```...``` в HTML <pre><code>
    code_blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
    for block in code_blocks:
        html_block = f"<pre><code>{block.strip()}</code></pre>"
        text = text.replace(f"```{block}```", html_block)

    # Экранируем переносы строк
    text = text.replace("\n", "<br>")
    return text


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

        # Ключ уже base64, не кодируем заново
        basic_auth_str = self.api_key

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {basic_auth_str}"
        }

        response = requests.post(url, headers=headers, data=payload, verify=False)
        if response.status_code != 200:
            raise Exception(f"Ошибка авторизации: {response.status_code} | {response.text}")

        data = response.json()
        self.token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    def send_message(self, message, history=None):
        # Проверка и обновление токена
        if time.time() >= self.token_expires_at:
            self._get_token()

        # Если история не передана, используем внутреннюю
        if history is None:
            self.history.append({"role": "user", "content": message})
            messages_to_send = self.history
        else:
            history.append({"role": "user", "content": message})
            messages_to_send = history

        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        payload = {
            "model": "GigaChat",
            "messages": messages_to_send
        }

        response = requests.post(chat_url, headers=headers, json=payload, verify=False)

        if response.status_code == 403:
            self._get_token()
            headers["Authorization"] = f"Bearer {self.token}"
            response = requests.post(chat_url, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            raise Exception(f"Ошибка запроса: {response.status_code} | {response.text}")

        answer = response.json()["choices"][0]["message"]["content"]

        if history is None:
            self.history.append({"role": "assistant", "content": answer})
        else:
            history.append({"role": "assistant", "content": answer})

        return format_answer_with_code(answer)
