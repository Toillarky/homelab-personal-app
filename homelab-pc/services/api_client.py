# api_client.py
from PySide6.QtCore import QObject, Signal, QUrl, QUrlQuery, QFile, QSaveFile
from PySide6.QtNetwork import QHttpMultiPart, QHttpPart
from pathlib import Path
import json
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
)


class ApiClient(QObject):
    login_result = Signal(bool, str)
    logout_result = Signal(bool, str)
    health_result = Signal(bool, str)
    stats_result = Signal(bool, object)
    
    files_result = Signal(bool, object)
    upload_result = Signal(bool, str)
    download_result = Signal(bool, str)
    directory_result = Signal(bool, str)
    file_delete_result = Signal(bool, str)
    move_result = Signal(bool, str)
    
    connection_test_result = Signal(bool, str)

    def __init__(self, base_url: str, parent=None):
        super().__init__(parent)

        self.base_url = base_url.rstrip("/")
        self.manager = QNetworkAccessManager(self)

    def login(self, username: str, password: str):
        url = QUrl(f"{self.base_url}/auth/login")
        request = QNetworkRequest(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json",
        )

        payload = json.dumps({
            "username": username,
            "password": password,
        }).encode("utf-8")

        reply = self.manager.post(request, payload)
        reply.finished.connect(lambda: self._handle_login_reply(reply))

    def _handle_login_reply(self, reply: QNetworkReply):
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")

        if (
            reply.error() == QNetworkReply.NetworkError.NoError
            and status is not None
            and 200 <= int(status) < 300
        ):
            self.login_result.emit(True, "Connexion réussie.")
        else:
            try:
                data = json.loads(body)
                message = data.get("detail", reply.errorString())
            except json.JSONDecodeError:
                message = body or reply.errorString()

            self.login_result.emit(False, str(message))

        reply.deleteLater()
    
    def logout(self):
        url = QUrl(f"{self.base_url}/auth/logout")
        request = QNetworkRequest(url)

        reply = self.manager.post(request, b"")
        reply.finished.connect(
            lambda: self._handle_logout_reply(reply)
        )

    def _handle_logout_reply(self, reply: QNetworkReply):
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")

        success = (
            reply.error() == QNetworkReply.NetworkError.NoError
            and status is not None
            and 200 <= int(status) < 300
        )

        if success:
            message = "Déconnexion réussie."
        else:
            try:
                data = json.loads(body)
                message = data.get("detail", reply.errorString())
            except json.JSONDecodeError:
                message = body or reply.errorString()

        self.logout_result.emit(success, str(message))
        reply.deleteLater()

    def check_health(self):
        url = QUrl(f"{self.base_url}/health")
        request = QNetworkRequest(url)
        reply = self.manager.get(request)
        reply.finished.connect(
            lambda: self._handle_health_reply(reply)
        )

    
    def test_connection(self, address: str):
        url = QUrl(f"{address.rstrip('/')}/health")
        request = QNetworkRequest(url)

        reply = self.manager.get(request)
        reply.setProperty("tested_address", address.rstrip("/"))

        reply.finished.connect(
            lambda: self._handle_connection_test(reply)
        )


    def _handle_connection_test(self, reply: QNetworkReply):
        address = reply.property("tested_address")
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )

        success = (
            reply.error() == QNetworkReply.NetworkError.NoError
            and status is not None
            and 200 <= int(status) < 300
        )

        message = address if success else reply.errorString()
        self.connection_test_result.emit(success, message)

        reply.deleteLater()



    def _handle_health_reply(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.health_result.emit(False, reply.errorString())
        else:
            body = bytes(reply.readAll()).decode("utf-8")
            self.health_result.emit(True, body)

        reply.deleteLater()

    def get_stats(self):
        url = QUrl(f"{self.base_url}/stats")
        request = QNetworkRequest(url)
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._handle_stats_reply(reply))

    def _handle_stats_reply(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.stats_result.emit(False, reply.errorString())
        else:
            try:
                body = bytes(reply.readAll()).decode("utf-8")
                data = json.loads(body)
                self.stats_result.emit(True, data)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                self.stats_result.emit(False, str(error))

        reply.deleteLater()

    def get_files(self, path: str = ""):
        from urllib.parse import quote

        encoded_path = quote(path, safe="/")
        url = QUrl(f"{self.base_url}/files?path={encoded_path}")
        request = QNetworkRequest(url)
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._handle_files_reply(reply))

    def _handle_files_reply(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.files_result.emit(False, reply.errorString())
        else:
            try:
                body = bytes(reply.readAll()).decode("utf-8")
                data = json.loads(body)
                self.files_result.emit(True, data)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                self.files_result.emit(False, str(error))

        reply.deleteLater()
    
    def upload_file(self, file_path: str, remote_path: str = ""):
        file_url = Path(file_path).resolve().as_uri()

        multipart = QHttpMultiPart(
            QHttpMultiPart.ContentType.FormDataType
        )

        file_part = QHttpPart()
        file_part.setHeader(
            QNetworkRequest.KnownHeaders.ContentDispositionHeader,
            f'form-data; name="file"; filename="{Path(file_path).name}"'
        )

        with open(file_path, "rb") as source:
            file_part.setBody(source.read())

        multipart.append(file_part)

        url = QUrl(f"{self.base_url}/files/upload")
        query = QUrlQuery()
        query.addQueryItem("path", remote_path)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.manager.post(request, multipart)
        multipart.setParent(reply)

        reply.finished.connect(
            lambda: self._handle_upload_reply(reply)
        )
    
    def download_file(self, remote_path: str, local_path: str):
        url = QUrl(f"{self.base_url}/files/download")
        query = QUrlQuery()
        query.addQueryItem("path", remote_path)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.manager.get(request)

        reply.setProperty("local_path", local_path)
        reply.finished.connect(lambda: self._handle_download_reply(reply))


    def _handle_download_reply(self, reply: QNetworkReply):
        local_path = reply.property("local_path")

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.download_result.emit(False, reply.errorString())
            reply.deleteLater()
            return

        output = QSaveFile(local_path)

        if not output.open(QFile.OpenModeFlag.WriteOnly):
            self.download_result.emit(False, output.errorString())
            reply.deleteLater()
            return

        data = bytes(reply.readAll())
        written = output.write(data)

        if written != len(data):
            output.cancelWriting()
            self.download_result.emit(False, output.errorString())
            reply.deleteLater()
            return

        if not output.commit():
            self.download_result.emit(False, output.errorString())
            reply.deleteLater()
            return

        self.download_result.emit(True, local_path)
        reply.deleteLater()

    def _handle_upload_reply(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.upload_result.emit(False, reply.errorString())
        else:
            self.upload_result.emit(
                True,
                bytes(reply.readAll()).decode("utf-8")
            )

        reply.deleteLater()
    
    def create_directory(self, parent_path: str, name: str):
        url = QUrl(f"{self.base_url}/files/mkdir")

        query = QUrlQuery()
        query.addQueryItem("path", parent_path or ".")
        query.addQueryItem("name", name)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.manager.post(request, b"")
        reply.finished.connect(
            lambda: self._handle_directory_reply(reply, "create")
        )


    def delete_directory(self, remote_path: str):
        url = QUrl(f"{self.base_url}/files/directory")

        query = QUrlQuery()
        query.addQueryItem("path", remote_path)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.manager.deleteResource(request)
        reply.finished.connect(
            lambda: self._handle_directory_reply(reply, "delete")
        )


    def _handle_directory_reply(self, reply: QNetworkReply, action: str):
        success = reply.error() == QNetworkReply.NetworkError.NoError
        response = bytes(reply.readAll()).decode("utf-8", errors="replace")

        if success:
            message = "Opération réussie"
        else:
            message = response or reply.errorString()

        self.directory_result.emit(success, message)
        reply.deleteLater()

    def delete_file(self, remote_path: str):
        url = QUrl(f"{self.base_url}/files/file")

        query = QUrlQuery()
        query.addQueryItem("path", remote_path)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.manager.deleteResource(request)
        reply.finished.connect(
            lambda: self._handle_file_delete_reply(reply)
        )

    def _handle_file_delete_reply(self, reply: QNetworkReply):
        success = reply.error() == QNetworkReply.NetworkError.NoError
        response = bytes(reply.readAll()).decode("utf-8", errors="replace")

        if success:
            message = "Fichier supprimé"
        else:
            message = response or reply.errorString()

        self.file_delete_result.emit(success, message)
        reply.deleteLater()
    

    def move_item(
        self,
        source_path: str,
        destination_path: str,
        new_name: str | None = None,
    ):
        url = QUrl(f"{self.base_url}/files/move")
        query = QUrlQuery()
        query.addQueryItem("source", source_path)
        query.addQueryItem("destination", destination_path)

        if new_name:
            query.addQueryItem("new_name", new_name)

        url.setQuery(query)

        request = QNetworkRequest(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/x-www-form-urlencoded"
        )
        reply = self.manager.post(request, b"")
        reply.finished.connect(
            lambda: self._handle_move_reply(reply)
        )


    def _handle_move_reply(self, reply: QNetworkReply):
        success = reply.error() == QNetworkReply.NetworkError.NoError
        response = bytes(reply.readAll()).decode("utf-8", errors="replace")

        if success:
            message = "Élément déplacé"
        else:
            message = response or reply.errorString()

        self.move_result.emit(success, message)
        reply.deleteLater()