#C:\PyProject\PythonLLM\main.py
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.database import DialogueDB
from core.ratings import RatingSystem

def main():
    app = QApplication([])

    # Инициализация базы данных и системы оценок
    db = DialogueDB()
    ratings = RatingSystem()

    # Передаём db и ratings в MainWindow
    window = MainWindow(db, ratings)
    window.show()

    app.exec_()

if __name__ == "__main__":
    main()