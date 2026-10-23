
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)


class LoginWindow(QWidget):
    def __init__(self, api):
        super().__init__()

        self.api = api
        self.main_window = None

        self.setWindowTitle("Connexion - HomeLab")
        self.setFixedSize(420, 480)
        self.setObjectName("loginWindow")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(16)

        layout.addStretch()

        title = QLabel("HomeLab")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("loginTitle")
        layout.addWidget(title)

        subtitle = QLabel("Connecte-toi à ton serveur personnel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("loginSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.username_input.setClearButtonEnabled(True)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("loginError")
        layout.addWidget(self.error_label)

        self.login_button = QPushButton("Se connecter")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        layout.addStretch()

        self.api.login_result.connect(self.on_login_result)
        self.password_input.returnPressed.connect(self.attempt_login)
        self.username_input.returnPressed.connect(
            lambda: self.password_input.setFocus()
        )

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText(
                "Entre ton nom d'utilisateur et ton mot de passe."
            )
            return

        self.error_label.clear()
        self.login_button.setEnabled(False)
        self.login_button.setText("Connexion en cours…")

        self.api.login(username, password)

    def on_login_result(self, success, message):
        self.login_button.setEnabled(True)
        self.login_button.setText("Se connecter")

        if not success:
            self.error_label.setText(message)
            return

        from ui.main_window import MainWindow

        self.main_window = MainWindow(self.api)
        self.main_window.show()
        self.close()
