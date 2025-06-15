# core/stats.py
import matplotlib

matplotlib.use('Qt5Agg')  # Устанавливаем Qt-совместимый бэкенд
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy


class RatingPlotWidget(FigureCanvasQTAgg):
    """Виджет для отображения диаграммы оценок в Qt."""

    def __init__(self, ratings_data, model_name, parent=None):
        fig = Figure(figsize=(5, 3), dpi=100)
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.update_figure(ratings_data, model_name)

    def update_figure(self, ratings_data, model_name):
        """Обновляет данные на диаграмме."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ratings = ratings_data.get(model_name, [])
        if not ratings:
            ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
            ax.set_title(f"{model_name} (нет оценок)")
        else:
            ax.hist(ratings, bins=range(1, 7), align='left', rwidth=0.8)
            ax.set_xticks(range(1, 6))
            ax.set_xlabel("Оценка")
            ax.set_ylabel("Количество")
            ax.set_title(f"Оценки: {model_name}")

        self.draw()