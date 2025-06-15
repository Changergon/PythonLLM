#C:\PyProject\PythonLLM\core\ratings.py
import json
from pathlib import Path


def _calculate_stats(scores):
    if not scores:
        return {"average": 0, "count": 0}
    return {
        "average": sum(scores) / len(scores),
        "count": len(scores)
    }


class RatingSystem:
    def __init__(self, file_path="data/ratings.json"):
        self.file = Path(file_path)
        self.file.parent.mkdir(exist_ok=True)
        if not self.file.exists():
            self.file.write_text('{"gigachat": [], "local_llm": []}')

    def add_rating(self, model, score):
        data = json.loads(self.file.read_text())
        data[model].append(score)
        self.file.write_text(json.dumps(data, indent=2))

    def get_stats(self):
        data = json.loads(self.file.read_text())
        return {
            "gigachat": _calculate_stats(data["gigachat"]),
            "local_llm": _calculate_stats(data["local_llm"])
        }

