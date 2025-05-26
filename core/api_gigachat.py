import requests
import uuid

class GigaChatDialogue:
    def __init__(self, api_key):
        self.api_key = api_key
        self.token = self._get_token()
        self.history = []

    def _get_token(self):
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        rq_uid = str(uuid.uuid4())
        payload = {
            "scope": "GIGACHAT_API_PERS"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self.api_key}"
        }

        response = requests.post(url, headers=headers, data=payload, verify=False)
        if response.status_code != 200:
            raise Exception(f"Ошибка авторизации: {response.status_code} | {response.text}")
        return response.json()["access_token"]

    def send_message(self, message):
        self.history.append({"role": "user", "content": message})
        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        payload = {
            "model": "GigaChat",
            "messages": self.history
        }

        response = requests.post(chat_url, headers=headers, json=payload, verify=False)
        if response.status_code != 200:
            raise Exception(f"Ошибка запроса: {response.status_code} | {response.text}")
        answer = response.json()["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": answer})
        return answer
