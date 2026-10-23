
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.setObjectName("statCard")

        layout = QVBoxLayout(self)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")

        self.value_label = QLabel("--")
        self.value_label.setObjectName("statValue")

        self.detail_label = QLabel("En attente de données")
        self.detail_label.setObjectName("statDetail")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)

    def set_values(self, value: str, detail: str):
        self.value_label.setText(value)
        self.detail_label.setText(detail)
