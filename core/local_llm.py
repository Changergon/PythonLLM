#C:\PyProject\PythonLLM\core\local_llm.py
import html
import re
from typing import List, Dict, Optional
import copy
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MAX_HISTORY_LEN = 10

def wrap_code(text: str) -> str:
    return f"<pre><code>{html.escape(text.strip())}</code></pre>"

def format_answer_with_code(text: str) -> str:
    code_blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
    for block in code_blocks:
        text = text.replace(f"```{block}```", wrap_code(block))
    text = text.replace("\n\n", "<br><br>")
    text = text.replace("\n", " ")
    return text

def _load_model(model_name: str):
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

class LocalLLM:
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer, self.model = _load_model(model_name)
        self.default_history: List[Dict[str, str]] = []

        if "TinyLlama" in model_name:
            self.tokenizer.chat_template = """{% for message in messages %}
            {{ message['role'] + ': ' + message['content'] + '\\n' }}
            {% endfor %}assistant: """

    def _prepare_prompt(self, history: List[Dict[str, str]]) -> str:
        messages = [
            {"role": "system", "content": (
                "Ты помощник-программист. Отвечай коротко, понятно и по теме."
            )}
            ,
            *history
        ]
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def send_message(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        try:
            if history is not None:
                target_history = copy.deepcopy(history)
            else:
                target_history = copy.deepcopy(self.default_history)

            target_history.append({"role": "user", "content": message})
            target_history = target_history[-MAX_HISTORY_LEN:]

            prompt = self._prepare_prompt(target_history)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

            response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

            target_history.append({"role": "assistant", "content": response})

            if history is None:
                self.default_history = target_history

            return format_answer_with_code(response)

        except Exception as e:
            error_msg = f"Ошибка генерации: {str(e)}"
            if history is not None:
                history.append({"role": "assistant", "content": error_msg})
            return error_msg
