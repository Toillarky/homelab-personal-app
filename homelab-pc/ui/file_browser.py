# file_browser.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QInputDialog, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QIcon, QDrag
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

def get_icon(name: str) -> QIcon:
    return QIcon(str(ICONS_DIR / name))


class UpDropButton(QPushButton):
    move_requested = Signal(str)

    def dragEnterEvent(self, event):
        if event.mimeData().text().startswith("homelab-internal-move:"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().text().startswith("homelab-internal-move:"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        text = event.mimeData().text()
        prefix = "homelab-internal-move:"

        if not text.startswith(prefix):
            event.ignore()
            return

        source_name = text[len(prefix):]
        if source_name:
            self.move_requested.emit(source_name)
            event.acceptProposedAction()
        else:
            event.ignore()

class FileBrowser(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)

        self.api = api
        self.current_path = ""

        layout = QVBoxLayout(self)

        # Barre de navigation
        top_bar = QHBoxLayout()

        
        
        self.path_label = QLabel("Dossier : /")

        
        self.up_button = UpDropButton("")                                                # up in directory and up files out folder
        self.up_button.setIcon(get_icon("up-out-svgrepo-com-blanc.svg"))
        self.up_button.setAcceptDrops(True)
        self.up_button.clicked.connect(self.go_up)
        self.up_button.move_requested.connect(self.move_item_to_parent)
        top_bar.addWidget(self.up_button)

        
        self.new_folder_button = QPushButton("Nouveau dossier")
        self.new_folder_button.setIcon(get_icon("folder-plus.svg"))

        self.new_folder_button.clicked.connect(self.create_folder)                        # create folder
        top_bar.addWidget(self.new_folder_button)
        top_bar.addWidget(self.path_label)
        
        self.upload_button = QPushButton("Envoyer un fichier")                            # Upload
        self.upload_button.setIcon(get_icon("upload.svg"))
        self.upload_button.clicked.connect(self.choose_file)
        top_bar.addWidget(self.upload_button)

        #self.delete_folder_button = QPushButton("Supprimer le dossier")                   # delete folder
        #self.delete_folder_button.clicked.connect(self.delete_selected_folder)
        #top_bar.addWidget(self.delete_folder_button)
        
        #self.delete_file_button = QPushButton("Supprimer le fichier")                     # delete file
        #self.delete_file_button.clicked.connect(self.delete_selected_file)
        #top_bar.addWidget(self.delete_file_button)
        
        #self.download_button = QPushButton("Télécharger")                                 # Download
        #self.download_button.setIcon(get_icon("download.svg"))
        #self.download_button.clicked.connect(self.download_selected_file)
        #top_bar.addWidget(self.download_button)


        layout.addLayout(top_bar)

        # Liste des fichiers et dossiers
        self.file_list = FileListWidget()
        self.file_list.move_requested.connect(self.move_item_to_folder)
        self.file_list.itemDoubleClicked.connect(self.open_item)

        layout.addWidget(self.file_list)

        self.status_label = QLabel("Chargement...")
        layout.addWidget(self.status_label)

        self.load_files()

    def load_files(self):
        self.status_label.setText("Chargement...")
        self.file_list.clear()
        self.api.get_files(self.current_path)


    def display_files(self, data):
        self.current_path = data.get("path", self.current_path)
        self.path_label.setText(
            f"Dossier : /{self.current_path}" if self.current_path else "Dossier : /"
        )

        self.file_list.clear()

        for item in data.get("items", []):
            name = item["name"]
            is_directory = item["type"] == "directory"

            if is_directory:
                label = f"📁  {name}"
            else:
                size = item.get("size")
                label = f"📄  {name}"
                if size is not None:
                    label += f"  ({size / 1024:.1f} Ko)"

            entry = QListWidgetItem()
            entry.setData(Qt.ItemDataRole.UserRole, item)
            self.file_list.addItem(entry)

            # Ligne personnalisée
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 2, 8, 2)
            row_layout.setSpacing(6)

            name_label = QLabel(label)
            row_layout.addWidget(name_label, 1)

            # Bouton télécharger : uniquement pour les fichiers
            if not is_directory:
                download_button = QPushButton()
                download_button.setIcon(get_icon("download.svg"))
                download_button.setToolTip("Télécharger")
                download_button.setFixedSize(32, 32)
                download_button.clicked.connect(
                    lambda checked=False, e=entry:
                        self.download_item(e)
                )
                row_layout.addWidget(download_button)

            # Bouton renommer
            rename_button = QPushButton()
            rename_button.setIcon(get_icon("rename.svg"))
            rename_button.setToolTip("Renommer")
            rename_button.setFixedSize(32, 32)
            rename_button.clicked.connect(
                lambda checked=False, e=entry:
                    self.rename_item(e)
            )
            row_layout.addWidget(rename_button)

            # Bouton supprimer
            delete_button = QPushButton()
            delete_button.setIcon(get_icon("trash.svg"))
            delete_button.setToolTip("Supprimer")
            delete_button.setFixedSize(32, 32)
            delete_button.clicked.connect(
                lambda checked=False, e=entry:
                    self.delete_item(e)
            )
            row_layout.addWidget(delete_button)

            row.setLayout(row_layout)
            self.file_list.setItemWidget(entry, row)
            entry.setSizeHint(row.sizeHint())

        self.status_label.setText(
            f"{len(data.get('items', []))} élément(s)"
        )

    def move_item_to_parent(self, source_name: str):
        if not self.current_path:
            self.show_error("Tu es déjà à la racine.")
            return

        parent_path = self.current_path.rpartition("/")[0]
        source_path = f"{self.current_path}/{source_name}"

        self.status_label.setText("Déplacement vers le dossier parent…")
        self.api.move_item(source_path, parent_path)

    def move_item_to_folder(self, source_name: str, destination_name: str):
        source_path = (
            f"{self.current_path}/{source_name}"
            if self.current_path
            else source_name
        )
        destination_path = (
            f"{self.current_path}/{destination_name}"
            if self.current_path
            else destination_name
        )

        self.status_label.setText("Déplacement en cours…")
        self.api.move_item(source_path, destination_path)

    def show_error(self, message):
        self.status_label.setText(f"Erreur : {message}")

    def open_item(self, entry):
        item = entry.data(Qt.ItemDataRole.UserRole)

        if item["type"] != "directory":
            return

        # Utilise le chemin réel si l'API le fournit
        if item.get("path") is not None:
            self.current_path = item["path"]
        else:
            name = item["name"]
            self.current_path = (
                f"{self.current_path}/{name}" if self.current_path else name
            )

        self.load_files()


    def go_up(self):
        if not self.current_path:
            return

        # Depuis la racine du dossier personnel, retourner à la racine générale
        if self.current_path.startswith("utilisateurs/") and self.current_path.count("/") == 1:
            self.current_path = ""

        # Sinon, remonter d'un seul niveau
        else:
            self.current_path = self.current_path.rpartition("/")[0]

        self.load_files()

    
    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier à envoyer"
        )

        if not file_path:
            return

        self.status_label.setText("Envoi du fichier en cours...")
        self.upload_button.setEnabled(False)
        self.api.upload_file(file_path, self.current_path)
    
    def download_selected_file(self):
        entry = self.file_list.currentItem()

        if entry is None:
            self.status_label.setText("Sélectionne d'abord un fichier.")
            return

        item = entry.data(Qt.ItemDataRole.UserRole)

        if item["type"] != "file":
            self.status_label.setText("Sélectionne un fichier, pas un dossier.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier",
            item["name"]
        )

        if not save_path:
            return

        self.status_label.setText("Téléchargement en cours...")
        self.download_button.setEnabled(False)

        remote_path = (
            f"{self.current_path}/{item['name']}"
            if self.current_path
            else item["name"]
        )

        self.api.download_file(remote_path, save_path)
    
    def create_folder(self):
        name, accepted = QInputDialog.getText(
            self,
            "Nouveau dossier",
            "Nom du dossier :"
        )

        if not accepted:
            return

        name = name.strip()

        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            QMessageBox.warning(
                self,
                "Nom invalide",
                "Saisis un nom de dossier valide."
            )
            return

        self.new_folder_button.setEnabled(False)
        self.status_label.setText("Création du dossier en cours...")
        self.api.create_directory(self.current_path, name)

    def delete_selected_folder(self):
        entry = self.file_list.currentItem()

        if entry is None:
            self.status_label.setText("Sélectionne d'abord un dossier.")
            return

        item = entry.data(Qt.ItemDataRole.UserRole)

        if item["type"] != "directory":
            self.status_label.setText("Sélectionne un dossier.")
            return

        name = item["name"]

        confirmation = QMessageBox.question(
            self,
            "Supprimer le dossier",
            f"Supprimer le dossier « {name} » ?\n\n"
            "Le dossier doit être vide.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        remote_path = (
            f"{self.current_path}/{name}"
            if self.current_path
            else name
        )

        #self.delete_folder_button.setEnabled(False)
        self.status_label.setText("Suppression du dossier en cours...")
        self.api.delete_directory(remote_path)
    
    
    def delete_selected_file(self):
        item = self.file_list.currentItem()

        if item is None:
            self.show_error("Sélectionne d'abord un fichier.")
            return

        data = item.data(Qt.ItemDataRole.UserRole)

        if data.get("type") != "file":
            self.show_error("Sélectionne un fichier, pas un dossier.")
            return

        name = data.get("name", item.text())

        confirmation = QMessageBox.question(
            self,
            "Supprimer le fichier",
            f"Veux-tu vraiment supprimer le fichier « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        remote_path = (
            f"{self.current_path.strip('/')}/{name}"
            if self.current_path.strip("/")
            else name
        )

        #self.delete_file_button.setEnabled(False)
        self.status_label.setText("Suppression du fichier en cours…")
        self.api.delete_file(remote_path)


    def download_item(self, entry):
        item = entry.data(Qt.ItemDataRole.UserRole)
        if item.get("type") != "file":
            return

        # Sélectionne cet élément pour réutiliser le téléchargement existant.
        self.file_list.setCurrentItem(entry)
        self.download_selected_file()


    def delete_item(self, entry):
        item = entry.data(Qt.ItemDataRole.UserRole)
        self.file_list.setCurrentItem(entry)

        if item.get("type") == "directory":
            self.delete_selected_folder()
        else:
            self.delete_selected_file()


    def rename_item(self, entry):
        item = entry.data(Qt.ItemDataRole.UserRole)
        old_name = item.get("name", "")

        new_name, ok = QInputDialog.getText(
            self,
            "Renommer",
            "Nouveau nom :",
            text=old_name,
        )

        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()

        if (
            new_name in (".", "..")
            or "/" in new_name
            or "\\" in new_name
        ):
            self.show_error("Nom de fichier ou dossier invalide.")
            return

        if new_name == old_name:
            return

        source_path = (
            f"{self.current_path}/{old_name}"
            if self.current_path
            else old_name
        )

        self.api.move_item(
            source_path,
            self.current_path,
            new_name=new_name,
        )



class FileListWidget(QListWidget):
    move_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DragDrop
        )
        self._drag_source = None

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        self._drag_source = data["name"]

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("homelab-internal-move")
        mime_data.setText(f"homelab-internal-move:{self._drag_source}")
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

        self._drag_source = None

    
    def dragEnterEvent(self, event):
        if event.mimeData().text().startswith("homelab-internal-move:"):
            event.acceptProposedAction()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        item = self.itemAt(event.position().toPoint())

        if (
            event.mimeData().text().startswith("homelab-internal-move:")
            and item is not None
            and item.data(Qt.ItemDataRole.UserRole).get("type") == "directory"
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        item = self.itemAt(event.position().toPoint())

        if (
            self._drag_source is None
            or item is None
            or item.data(Qt.ItemDataRole.UserRole).get("type") != "directory"
        ):
            event.ignore()
            return

        destination_name = item.data(Qt.ItemDataRole.UserRole)["name"]
        self.move_requested.emit(
            self._drag_source,
            destination_name,
        )
        event.acceptProposedAction()
