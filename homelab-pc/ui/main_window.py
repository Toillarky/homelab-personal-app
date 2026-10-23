from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
)
from PySide6.QtCore import QTimer
from services.api_client import ApiClient
from PySide6.QtGui import QIcon

from ui.pages import create_page
from ui.stat_card import StatCard
from ui.file_browser import FileBrowser
from ui.login_window import LoginWindow


class MainWindow(QMainWindow):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.api.setParent(self)
        self.api.health_result.connect(self.update_connection_status)
        self.api.stats_result.connect(self.update_stats)

        self.api.files_result.connect(self.on_files_result)
        self.api.upload_result.connect(self.on_upload_result)
        self.api.download_result.connect(self.on_download_result)

        self.api.directory_result.connect(self.on_directory_result)
        self.api.file_delete_result.connect(self.on_file_delete_result)
        self.api.move_result.connect(self.on_move_result)

        self.api.logout_result.connect(self.on_logout_result)

        self.setWindowIcon(QIcon("assets/icon.ico"))

        self.setWindowTitle("Server Manager")
        self.resize(1100, 700)

        # Conteneur principal
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre latérale
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)

        # Zone de navigation
        self.pages = QStackedWidget()

        # tableau de bord
        self.pages.addWidget(
            create_page("Tableau de bord", "Vue générale du HomeLab.")
        )

        # explorateur de fichiers
        self.files_page = create_page("Fichiers", "Cloud Personnel")
        self.file_browser = FileBrowser(self.api)
        self.files_page.layout().addWidget(self.file_browser)
        self.pages.addWidget(self.files_page)

        # serveur minecraft
        self.pages.addWidget(
            create_page("En Création...", "Cette fonctions n'a pas encore été ajouté.")
        )

        self.connection_status = QLabel("Connexion au HomeLab…")
        self.connection_status.setObjectName("pageDescription")
        self.server_address = QLabel("Serveur : 192.168.1.62:8765")
        self.server_address.setObjectName("pageDescription")

        dashboard = self.pages.widget(0)
        dashboard.layout().addWidget(self.connection_status)
        dashboard.layout().addWidget(self.server_address)
        
        self.cpu_card = StatCard("Processeur CPU")
        self.ram_card = StatCard("RAM Mémoire vive")
        self.disk_card = StatCard("Disque système stockage")

        self.stats_layout = QHBoxLayout()
        self.stats_layout.addWidget(self.cpu_card)
        self.stats_layout.addWidget(self.ram_card)
        self.stats_layout.addWidget(self.disk_card)

        dashboard = self.pages.widget(0)
        dashboard.layout().addLayout(self.stats_layout)

        # Boutons
        navigation = [
            ("Tableau de bord", 0),
            ("Fichiers Partagé", 1),
            ("IA Local", 2),
            #("Serveur Minecraft", 3),
        ]

        self.nav_buttons = []

        for text, index in navigation:
            button = QPushButton(text)
            button.setObjectName("navButton")

            button.clicked.connect(
                lambda checked=False, i=index: self.change_page(i)
            )

            self.nav_buttons.append(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        self.logout_button = QPushButton("Se déconnecter")
        self.logout_button.setObjectName("navButton")
        self.logout_button.clicked.connect(self.request_logout)
        sidebar_layout.addWidget(self.logout_button)

        # Assemblage
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages, 1)

        self.change_page(0)
        self.check_connection()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.check_connection)
        self.refresh_timer.start(5000)



    def change_page(self, index: int):
        self.pages.setCurrentIndex(index)

        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
    
    def request_logout(self):
        self.logout_button.setEnabled(False)
        self.logout_button.setText("Déconnexion…")
        self.api.logout()
    
    def update_connection_status(self, success: bool, message: str):
        if success:
            self.connection_status.setText("● Server en ligne")
        else:
            self.connection_status.setText(f"x Server hors ligne — {message}")
    
    def update_stats(self, success: bool, data):
        if not success:
            self.cpu_card.set_values("--", "Statistiques indisponibles")
            self.ram_card.set_values("--", "Statistiques indisponibles")
            self.disk_card.set_values("--", "Statistiques indisponibles")
            return

        stats = data
        gib = 1024 ** 3

        self.cpu_card.set_values(
            f"{stats['cpu_percent']:.1f} %",
            "Utilisation du processeur"
        )

        ram = stats["ram"]
        self.ram_card.set_values(
            f"{ram['percent']:.1f} %",
            f"{ram['used'] / gib:.1f} / {ram['total'] / gib:.1f} Gio utilisés"
        )

        disk = stats["disk"]
        self.disk_card.set_values(
            f"{disk['percent']:.1f} %",
            f"{disk['used'] / gib:.1f} / {disk['total'] / gib:.1f} Gio utilisés"
        )

    def on_files_result(self, success: bool, data):
        if success:
            self.file_browser.display_files(data)
        else:
            self.file_browser.show_error(str(data))

    def check_connection(self):
        self.connection_status.setText("Vérification de la connexion…")
        self.api.check_health()
        self.api.get_stats()

    def on_upload_result(self, success: bool, message: str):
        self.file_browser.upload_button.setEnabled(True)

        if success:
            self.file_browser.status_label.setText(
                "Fichier envoyé avec succès !"
            )
            self.file_browser.load_files()
        else:
            self.file_browser.show_error(
                f"Envoi impossible : {message}"
            )
    
    def on_directory_result(self, success: bool, message: str):
        self.file_browser.new_folder_button.setEnabled(True)
        #self.file_browser.delete_folder_button.setEnabled(True)

        if success:
            self.file_browser.status_label.setText("Opération réussie.")
            self.file_browser.load_files()
        else:
            self.file_browser.show_error(
                f"Opération impossible : {message}"
            )
        
    def on_download_result(self, success: bool, message: str):
        self.file_browser.download_button.setEnabled(True)

        if success:
            self.file_browser.status_label.setText(
                f"Téléchargement terminé : {message}"
            )
        else:
            self.file_browser.show_error(
                f"Téléchargement impossible : {message}"
            )
        
    def on_file_delete_result(self, success: bool, message: str):
        #self.file_browser.delete_file_button.setEnabled(True)

        if success:
            self.file_browser.status_label.setText("Fichier supprimé.")
            self.file_browser.load_files()
        else:
            self.file_browser.show_error(
                f"Suppression impossible : {message}"
            )

    def on_move_result(self, success: bool, message: str):
        if success:
            self.file_browser.status_label.setText("Élément déplacé.")
            self.file_browser.load_files()
        else:
            self.file_browser.show_error(
                f"Déplacement impossible : {message}"
            )
    
    def on_logout_result(self, success: bool, message: str):
        self.logout_button.setEnabled(True)
        self.logout_button.setText("Se déconnecter")

        if not success:
            self.file_browser.show_error(
                f"Déconnexion impossible : {message}"
            )
            return

        self.login_window = LoginWindow(self.api)
        self.login_window.show()
        self.close()
