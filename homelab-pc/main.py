import sys

from PySide6.QtWidgets import QApplication, QLabel
from ui.login_window import LoginWindow
from services.api_client import ApiClient

app = QApplication(sys.argv) # Crée l'app Qt et initialiser sont environement graphique. "sys.argv" transmet les éventuels arguments reçus au lancement du programme.

app.setStyleSheet("""
    QMainWindow {
        background-color: #151922;
    }

    #sidebar {
        background-color: #1D2330;
    }

    #navButton {
        color: #E6EAF2;
        background-color: transparent;
        border: none;
        padding: 12px;
        text-align: left;
        border-radius: 6px;
    }

    #navButton:hover {
        background-color: #30394B;
    }

    #pageTitle {
        color: #FFFFFF;
        font-size: 26px;
        font-weight: bold;
    }

    #pageDescription {
        color: #AAB4C5;
        font-size: 14px;
    }

    #navButton[active="true"] {
    background-color: #35445F;
    color: #FFFFFF;
    border-left: 3px solid #6C9EFF;
    font-weight: bold;
    }

    #statCard {
        background-color: #1D2330;
        border: 1px solid #30394B;
        border-radius: 10px;
        padding: 8px;
    }

    #statTitle {
        color: #AAB4C5;
        font-size: 14px;
    }

    #statValue {
        color: #FFFFFF;
        font-size: 25px;
        font-weight: bold;
    }

    #statDetail {
        color: #AAB4C5;
        font-size: 12px;
    }

    #loginWindow {
        background-color: #151922;
    }

    #loginTitle {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: bold;
    }

    #loginSubtitle {
        color: #AAB4C5;
        font-size: 14px;
    }

    #loginWindow QLineEdit {
        background-color: #1D2330;
        color: #FFFFFF;
        border: 1px solid #30394B;
        border-radius: 7px;
        padding: 12px;
        font-size: 14px;
    }

    #loginWindow QLineEdit:focus {
        border: 1px solid #6C9EFF;
    }

    #loginError {
        color: #FF7777;
        font-size: 12px;
    }

    #loginButton {
        background-color: #527DCC;
        color: #FFFFFF;
        border: none;
        border-radius: 7px;
        padding: 12px;
        font-weight: bold;
    }

    #loginButton:hover {
        background-color: #638FE0;
    }

    #loginButton:disabled {
        background-color: #35445F;
    }

""")

# Un seul client API pour conserver la session et ses cookies.
api = ApiClient("http://192.168.1.62:8765")
api.connection_test_result.connect(
    lambda success, message: print(
        "Connexion locale :", "OK" if success else "ÉCHEC", message
    )
)

api.test_connection("http://192.168.1.62:8765")

window = LoginWindow(api)
window.show()

sys.exit(app.exec())