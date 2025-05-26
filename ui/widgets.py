from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget

class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.layout.addWidget(self.chat_display)

    def add_message(self, sender, message):
        self.chat_display.append(f"<b>{sender}:</b> {message}<br>")


from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

class RatingWidget(QWidget):
    def __init__(self, on_rating_selected):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.buttons = []
        for score in [1, 2, 3, 4, 5]:
            btn = QPushButton(str(score))
            btn.clicked.connect(lambda _, s=score: on_rating_selected(s))
            self.layout.addWidget(btn)
            self.buttons.append(btn)