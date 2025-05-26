import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import List, Dict, Optional
import re


class LocalLLM:
    """Локальная языковая модель с поддержкой истории диалога"""

    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer, self.model = self._load_model(model_name)
        self.default_history: List[Dict[str, str]] = []

        # Установим специальные токены для TinyLlama
        if "TinyLlama" in model_name:
            self.tokenizer.chat_template = """{% for message in messages %}
                {% if message['role'] == 'user' %}
                    {{ '<|user|>\n' + message['content'] + '<|end|>\n<|assistant|>\n' }}
                {% else %}
                    {{ message['content'] + '<|end|>\n' }}
                {% endif %}
            {% endfor %}"""

    def _load_model(self, model_name: str):
        """Загрузка модели с автоматическим выбором режима"""
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.float16
            )
        except Exception as e:
            print(f"Ошибка загрузки с квантованием: {e}, загружаем без квантования")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16
            )
        return tokenizer, model

    def _prepare_prompt(self, message: str, history: List[Dict[str, str]]) -> str:
        """Подготавливает промт для модели"""
        # Формируем сообщения в формате, ожидаемом моделью
        messages = []

        # Добавляем системное сообщение
        messages.append({
            "role": "system",
            "content": "Ты - опытный Python-разработчик. Отвечай только кодом в формате:\n```python\n# код\n```"
        })

        # Добавляем историю диалога
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Добавляем текущее сообщение пользователя
        messages.append({
            "role": "user",
            "content": message
        })

        # Применяем шаблон чата
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

    def send_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Отправляет сообщение модели

        Args:
            message: Текст сообщения
            history: Опциональная история диалога

        Returns:
            Ответ модели
        """
        try:
            target_history = history if history is not None else self.default_history
            target_history.append({"role": "user", "content": message})

            prompt = self._prepare_prompt(message, target_history)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Генерация ответа с более строгими параметрами
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.2,  # Уменьшаем случайность
                top_p=0.9,
                repetition_penalty=1.5,  # Уменьшаем повторения
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

            # Декодируем ответ, пропуская промт
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )

            # Извлекаем код из ответа
            code_match = re.search(r"```python\n(.*?)\n```", response, re.DOTALL)
            if code_match:
                clean_response = code_match.group(1).strip()
            else:
                clean_response = response.strip()

            # Сохраняем ответ в историю
            target_history.append({"role": "assistant", "content": clean_response})

            return f"<pre><code>{clean_response}</code></pre>"

        except Exception as e:
            error_msg = f"Ошибка генерации: {str(e)}"
            if history is not None:
                history.append({"role": "assistant", "content": error_msg})
            return error_msg