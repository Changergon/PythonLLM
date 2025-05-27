from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QWidget, QLabel, QTextBrowser)
from core.api_gigachat import GigaChatDialogue
from core.local_llm import LocalLLM


class MainWindow(QMainWindow):
    def __init__(self, db, ratings):
        super().__init__()
        self.db = db
        self.ratings = ratings

        # Инициализация моделей
        self.gigachat = GigaChatDialogue(
            api_key="M2Y5MzhjOTEtOTZlNC00ODZjLThiYjAtNGQ0NDU5MTJiMDQ4OjM0MWIwN2UxLWExMjMtNGNhOS1hMjBjLTNmYjAzZmM4MmFiNA==")
        self.local_llm = LocalLLM()

        # Настройки интерфейса
        self.setup_ui()

        # Состояние приложения
        self.mode = "gigachat"  # Текущий режим работы
        self.gigachat_scores = []  # Оценки для GigaChat
        self.local_scores = []  # Оценки для LocalLLM
        self.rating_given_giga = False  # Флаг оценки GigaChat
        self.rating_given_local = False  # Флаг оценки LocalLLM

        # Отдельные истории диалогов для каждой модели
        self.history_giga = []  # История диалога GigaChat
        self.history_local = []  # История диалога LocalLLM

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("LLM Comparison Tool")
        self.setGeometry(100, 100, 800, 600)

        # Основной layout
        main_layout = QVBoxLayout()

        # Область отображения чата
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display, stretch=8)

        # Панель ввода сообщения
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, stretch=6)

        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button, stretch=2)
        main_layout.addLayout(input_layout, stretch=2)

        # Кнопки выбора режима
        self.btn_gigachat = QPushButton("GigaChat Only")
        self.btn_local = QPushButton("Local LLM Only")
        self.btn_compare = QPushButton("Compare Models")

        self.btn_gigachat.clicked.connect(lambda: self.set_mode("gigachat"))
        self.btn_local.clicked.connect(lambda: self.set_mode("local"))
        self.btn_compare.clicked.connect(lambda: self.set_mode("compare"))

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_gigachat)
        buttons_layout.addWidget(self.btn_local)
        buttons_layout.addWidget(self.btn_compare)
        main_layout.addLayout(buttons_layout)

        # Панель оценок (только в режиме compare)
        self.rating_layout = QHBoxLayout()
        main_layout.addLayout(self.rating_layout)

        # Установка центрального виджета
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(main_layout)

    def set_mode(self, mode):
        """Переключение режима работы"""
        self.mode = mode
        self.chat_display.append(f"<i>Режим переключен на: {mode}</i><br>")
        self.clear_ratings_ui()

        # Очистка оценок при смене режима
        if mode != "compare":
            self.gigachat_scores.clear()
            self.local_scores.clear()

    def clear_ratings_ui(self):
        """Очистка панели оценок"""
        while self.rating_layout.count():
            item = self.rating_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def send_message(self):
        """Обработка отправки сообщения"""
        message = self.message_input.text().strip()
        if not message:
            return

        # Обработка команды завершения
        if message.lower() in ["выход", "завершить", "пока"]:
            self.handle_session_end()
            return

        # Сохранение сообщения пользователя
        self.db.add_message(model="user", role="user", content=message)
        self.chat_display.append(f"<b>Вы:</b> {message}<br>")
        self.message_input.clear()

        # Обработка в зависимости от режима
        if self.mode == "gigachat":
            self.process_gigachat(message)
        elif self.mode == "local":
            self.process_local(message)
        elif self.mode == "compare":
            self.process_compare(message)

    def handle_session_end(self):
        """Обработка завершения сессии"""
        self.chat_display.append("<i>Диалог завершён пользователем.</i><br>")

        # Вывод средних оценок
        avg_giga = sum(self.gigachat_scores) / len(self.gigachat_scores) if self.gigachat_scores else 0
        avg_local = sum(self.local_scores) / len(self.local_scores) if self.local_scores else 0
        self.chat_display.append(f"<b>Средняя оценка GigaChat:</b> {avg_giga:.2f}<br>")
        self.chat_display.append(f"<b>Средняя оценка Local LLM:</b> {avg_local:.2f}<br>")

        # Очистка состояния
        self.gigachat_scores.clear()
        self.local_scores.clear()
        self.message_input.clear()
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)

    def process_gigachat(self, message):
        """Обработка сообщения для GigaChat"""
        try:
            # Добавляем сообщение в историю GigaChat
            self.history_giga.append({"role": "user", "content": message})

            # Получаем ответ с учетом истории
            answer = self.gigachat.send_message(message, history=self.history_giga)

            # Сохраняем ответ в историю и базу данных
            self.history_giga.append({"role": "assistant", "content": answer})
            self.db.add_message(model="gigachat", role="assistant", content=answer)

            self.chat_display.append(f"<b>GigaChat:</b> {answer}<br>")
        except Exception as e:
            self.chat_display.append(f"<b>Ошибка GigaChat:</b> {str(e)}<br>")

    def process_local(self, message):
        """Обработка сообщения для LocalLLM"""
        try:
            # Добавляем сообщение в историю LocalLLM
            self.history_local.append({"role": "user", "content": message})

            # Получаем ответ с учетом истории
            answer = self.local_llm.send_message(message, history=self.history_local)

            # Сохраняем ответ в историю и базу данных
            self.history_local.append({"role": "assistant", "content": answer})
            self.db.add_message(model="local_llm", role="assistant", content=answer)

            self.chat_display.append(f"<b>Local LLM:</b> {answer}<br>")
        except Exception as e:
            self.chat_display.append(f"<b>Ошибка Local LLM:</b> {str(e)}<br>")

    def process_compare(self, message):
        """Обработка сообщения в режиме сравнения"""
        try:
            # Добавляем сообщение в истории обеих моделей
            self.history_giga.append({"role": "user", "content": message})
            self.history_local.append({"role": "user", "content": message})

            # Получаем ответы от обеих моделей
            answer_giga = self.gigachat.send_message(message, history=self.history_giga)
            answer_local = self.local_llm.send_message(message, history=self.history_local)

            # Добавляем ответы в соответствующие истории
            self.history_giga.append({"role": "assistant", "content": answer_giga})
            self.history_local.append({"role": "assistant", "content": answer_local})

            # Сохраняем в базу данных
            self.db.add_message(model="gigachat", role="assistant", content=answer_giga)
            self.db.add_message(model="local_llm", role="assistant", content=answer_local)

            # Отображаем ответы в интерфейсе
            self.chat_display.append(f"<b>GigaChat:</b> {answer_giga}<br>")
            self.chat_display.append(f"<b>Local LLM:</b> {answer_local}<br>")

            # Показываем кнопки оценок
            self.rating_given_giga = False
            self.rating_given_local = False
            self.show_rating_buttons()
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)

        except Exception as e:
            self.chat_display.append(f"<b>Ошибка сравнения моделей:</b> {str(e)}<br>")

    def show_rating_buttons(self):
        """Отображение кнопок оценок"""
        self.clear_ratings_ui()

        # Кнопки оценки для GigaChat
        label_giga = QLabel("Оцените GigaChat:")
        self.rating_layout.addWidget(label_giga)
        for score in range(1, 6):
            btn = QPushButton(str(score))
            btn.setEnabled(not self.rating_given_giga)
            btn.clicked.connect(lambda _, s=score: self.rate_model("gigachat", s))
            self.rating_layout.addWidget(btn)

        # Кнопки оценки для LocalLLM
        label_local = QLabel("Оцените Local LLM:")
        self.rating_layout.addWidget(label_local)
        for score in range(1, 6):
            btn = QPushButton(str(score))
            btn.setEnabled(not self.rating_given_local)
            btn.clicked.connect(lambda _, s=score: self.rate_model("local_llm", s))
            self.rating_layout.addWidget(btn)

    def rate_model(self, model_name, score):
        """Обработка оценки модели"""
        if model_name == "gigachat" and not self.rating_given_giga:
            self.gigachat_scores.append(score)
            self.chat_display.append(f"<i>Вы оценили GigaChat: {score}</i><br>")
            self.rating_given_giga = True
        elif model_name == "local_llm" and not self.rating_given_local:
            self.local_scores.append(score)
            self.chat_display.append(f"<i>Вы оценили Local LLM: {score}</i><br>")
            self.rating_given_local = True

        # Если обе модели оценены, разрешаем новый ввод
        if self.rating_given_giga and self.rating_given_local:
            self.clear_ratings_ui()
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.gigachat_scores or self.local_scores:
            avg_giga = sum(self.gigachat_scores) / len(self.gigachat_scores) if self.gigachat_scores else 0
            avg_local = sum(self.local_scores) / len(self.local_scores) if self.local_scores else 0
            self.chat_display.append(f"<b>Средняя оценка GigaChat:</b> {avg_giga:.2f}<br>")
            self.chat_display.append(f"<b>Средняя оценка Local LLM:</b> {avg_local:.2f}<br>")
        super().closeEvent(event)