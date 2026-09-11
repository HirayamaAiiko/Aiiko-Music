import sys
import os
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
SOCKET_NAME = "AiikoMusicSingleInstanceSocket"
SOCKET_TIMEOUT_MS = 1000
class SingleInstanceManager(QObject):
    file_received = pyqtSignal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = None
    def try_start(self) -> bool:
        test_socket = QLocalSocket()
        test_socket.connectToServer(SOCKET_NAME)
        if test_socket.waitForConnected(SOCKET_TIMEOUT_MS):
            test_socket.disconnectFromServer()
            logging.info("Single Instance: Otra instancia detectada.")
            return False
        QLocalServer.removeServer(SOCKET_NAME)
        self._server = QLocalServer(self)
        if self._server.listen(SOCKET_NAME):
            self._server.newConnection.connect(self._handle_new_connection)
            logging.info("Single Instance: Instancia principal iniciada (QLocalServer activo).")
            return True
        else:
            logging.warning(f"Single Instance: No se pudo iniciar el server local: {self._server.errorString()}")
            return True                                                                                 
    def send_to_running_instance(self, filepath: str, action: str = "play") -> bool:
        socket = QLocalSocket()
        socket.connectToServer(SOCKET_NAME)
        if socket.waitForConnected(SOCKET_TIMEOUT_MS):
            message = json.dumps({"filepath": filepath, "action": action}).encode('utf-8')
            socket.write(message)
            if socket.waitForBytesWritten(SOCKET_TIMEOUT_MS):
                socket.disconnectFromServer()
                logging.info(f"Single Instance: Comando enviado -> {action}: {filepath}")
                return True
        logging.warning("Single Instance: No se pudo enviar el mensaje a la otra instancia.")
        return False
    def _handle_new_connection(self):
        socket = self._server.nextPendingConnection()
        if socket.waitForReadyRead(SOCKET_TIMEOUT_MS):
            data = socket.readAll().data()
            if data:
                try:
                    msg = json.loads(data.decode('utf-8'))
                    filepath = msg.get('filepath', '')
                    action = msg.get('action', 'play')
                    if filepath and os.path.isfile(filepath):
                        logging.info(f"Single Instance: Recibido -> {action}: {filepath}")
                        self.file_received.emit(filepath, action)
                except Exception as e:
                    logging.warning(f"Single Instance: Error parseando mensaje IPC: {e}")
        socket.disconnectFromServer()
        socket.deleteLater()
    def shutdown(self):
        if self._server:
            self._server.close()
            self._server = None