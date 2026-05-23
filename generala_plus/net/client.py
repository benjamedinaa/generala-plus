import argparse
import socket
import threading

from .commands import HELP_TEXT, format_state, parse_command
from .protocol import ERROR, HELLO, INFO, STATE, WELCOME, action_message, Message
from .wire import read_message, send_message


class OnlineClient:
    def __init__(self, host="127.0.0.1", port=8765, name="Jugador"):
        self.host = host
        self.port = port
        self.name = name
        self.player_index = None
        self.file = None
        self.running = True
        self.last_state = None

    def run(self):
        with socket.create_connection((self.host, self.port), timeout=20) as sock:
            self.file = sock.makefile("rw", encoding="utf-8", newline="\n")
            send_message(self.file, Message(HELLO, {"name": self.name}))
            listener = threading.Thread(target=self.listen_loop, daemon=True)
            listener.start()
            print(HELP_TEXT)
            while self.running:
                try:
                    raw = input("> ")
                except EOFError:
                    break
                command = raw.strip().lower()
                if command in {"salir", "quit", "exit"}:
                    break
                if command in {"ayuda", "help", "h"}:
                    print(HELP_TEXT)
                    continue
                if command in {"estado", "state"}:
                    if self.last_state is not None and self.player_index is not None:
                        print(format_state(self.last_state, self.player_index))
                    continue
                try:
                    if self.player_index is None:
                        print("Todavia no recibiste indice de jugador.")
                        continue
                    action = parse_command(raw, self.player_index)
                    if action is None:
                        print("Comando desconocido. Escribi 'ayuda'.")
                        continue
                    send_message(self.file, action_message(action))
                except Exception as exc:
                    print(f"No pude interpretar el comando: {exc}")
            self.running = False

    def listen_loop(self):
        while self.running:
            try:
                message = read_message(self.file)
            except Exception as exc:
                print(f"Conexion cerrada: {exc}")
                self.running = False
                return
            if message is None:
                self.running = False
                return
            if message.type == WELCOME:
                self.player_index = int(message.payload["player_index"])
                print(f"Conectado como jugador {self.player_index + 1}: {message.payload.get('name')}")
            elif message.type == STATE:
                self.last_state = message.payload
                if self.player_index is not None:
                    print(format_state(self.last_state, self.player_index))
            elif message.type == ERROR:
                print(f"ERROR: {message.payload.get('text')}")
            elif message.type == INFO:
                print(f"INFO: {message.payload.get('text')}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cliente online basico de Generala Plus.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--name", default="Jugador")
    args = parser.parse_args(argv)
    OnlineClient(args.host, args.port, args.name).run()


if __name__ == "__main__":
    main()
