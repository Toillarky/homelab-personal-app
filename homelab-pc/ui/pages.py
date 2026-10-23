from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

def create_page(title: str, description: str) -> QWidget: # create_page(): une fonction réutilisable pour créer plusieurs pages avec la même structure.
    page = QWidget()

    layout = QVBoxLayout(page) # organise les éléments verticalement sans avoir à calculer leurs coordonnées manuellement.
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    title_label = QLabel(title)
    title_label.setObjectName("pageTitle") # donne un identifiant au widget, que nous pourrons cibler avec le système de styles Qt (QSS).

    description_label = QLabel(description)
    description_label.setObjectName("pageDescription")

    layout.addWidget(title_label)
    layout.addWidget(description_label)

    return page
