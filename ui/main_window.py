from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLineEdit, QWidget)

from core.api_gigachat import GigaChatDialogue
from core.local_llm import LocalLLM


class MainWindow(QMainWindow):
    def __init__(self, db, ratings):
        super().__init__()
        self.db = db
        self.ratings = ratings
        self.gigachat = GigaChatDialogue(api_key="M2Y5MzhjOTEtOTZlNC00ODZjLThiYjAtNGQ0NDU5MTJiMDQ4OjM0MWIwN2UxLWExMjMtNGNhOS1hMjBjLTNmYjAzZmM4MmFiNA==")  # Замените на ваш ключ
        self.local_llm = LocalLLM()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("LLM Comparison Tool")
        self.setGeometry(100, 100, 800, 600)

        # Основной контейнер
        main_layout = QVBoxLayout()

        # Область чата (только для чтения)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display, stretch=8)  # 80% высоты

        # Контейнер для ввода сообщения
        input_layout = QHBoxLayout()

        # Поле ввода текста
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.returnPressed.connect(self.send_message)  # Отправка по Enter
        input_layout.addWidget(self.message_input, stretch=6)  # 60% ширины

        # Кнопка отправки
        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button, stretch=2)  # 20% ширины

        main_layout.addLayout(input_layout, stretch=2)  # 20% высоты

        # Кнопки выбора режима
        self.btn_gigachat = QPushButton("GigaChat Only")
        self.btn_local = QPushButton("Local LLM Only")
        self.btn_compare = QPushButton("Compare Models")

        main_layout.addWidget(self.btn_gigachat)
        main_layout.addWidget(self.btn_local)
        main_layout.addWidget(self.btn_compare)

        # Центральный виджет
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return

        # Сохраняем сообщение пользователя
        self.db.add_message(model="user", role="user", content=message)
        self.chat_display.append(f"<b>Вы:</b> {message}<br>")
        self.message_input.clear()

        # Отправляем в GigaChat (пример)
        try:
            answer = self.gigachat.send_message(message)
            self.chat_display.append(f"<b>GigaChat:</b> {answer}<br>")
            self.db.add_message(model="gigachat", role="assistant", content=answer)
        except Exception as e:
            self.chat_display.append(f"<b>Ошибка:</b> {str(e)}<br>")