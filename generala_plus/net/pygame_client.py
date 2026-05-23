import socket
import threading

from .protocol import ERROR, HELLO, INFO, STATE, WELCOME, action_message, Message
from .wire import read_message, send_message


class PygameOnlineClient:
    def __init__(self, host, port, name, character_key="matematico"):
        self.host = host
        self.port = port
        self.name = name
        self.character_key = character_key
        self.player_index = None
        self.state = None
        self.info = ""
        self.error = ""
        self.connected = False
        self.running = False
        self.sock = None
        self.file = None
        self.lock = threading.RLock()
        self.thread = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.file = self.sock.makefile("rw", encoding="utf-8", newline="\n")
        send_message(self.file, Message(HELLO, {"name": self.name, "character_key": self.character_key}))
        self.running = True
        self.connected = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _listen(self):
        while self.running:
            try:
                message = read_message(self.file)
            except Exception as exc:
                with self.lock:
                    self.error = f"Conexion cerrada: {exc}"
                    self.connected = False
                break
            if message is None:
                with self.lock:
                    self.error = "Conexion cerrada."
                    self.connected = False
                break
            with self.lock:
                if message.type == WELCOME:
                    self.player_index = int(message.payload["player_index"])
                    self.info = f"Conectado como jugador {self.player_index + 1}."
                elif message.type == STATE:
                    self.state = message.payload
                elif message.type == ERROR:
                    self.error = str(message.payload.get("text", "Error online."))
                elif message.type == INFO:
                    self.info = str(message.payload.get("text", ""))

    def send_action(self, action):
        if not self.connected or self.file is None:
            return False
        try:
            send_message(self.file, action_message(action))
            return True
        except OSError as exc:
            with self.lock:
                self.error = f"No se pudo enviar accion: {exc}"
                self.connected = False
            return False

    def snapshot(self):
        with self.lock:
            return {
                "player_index": self.player_index,
                "state": self.state,
                "info": self.info,
                "error": self.error,
                "connected": self.connected,
            }

    def close(self):
        self.running = False
        self.connected = False
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
