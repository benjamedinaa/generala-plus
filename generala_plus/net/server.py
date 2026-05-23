import argparse
import socket
import threading

from ..core import GeneralaEngine
from ..core.actions import Action
from ..core.engine import InvalidAction
from .protocol import ACTION, ERROR, HELLO, INFO, STATE, WELCOME, Message
from .wire import read_message, send_message


class ClientSlot:
    def __init__(self, conn, address, file, index, name):
        self.conn = conn
        self.address = address
        self.file = file
        self.index = index
        self.name = name
        self.alive = True


class OnlineServer:
    def __init__(self, host="0.0.0.0", port=8765, seed=None):
        self.host = host
        self.port = port
        self.seed = seed
        self.clients = []
        self.engine = None
        self.lock = threading.RLock()
        self.running = True

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(2)
            print(f"Generala Plus Online escuchando en {self.host}:{self.port}")
            print("Esperando 2 jugadores...")
            while self.running and len(self.clients) < 2:
                conn, address = server.accept()
                file = conn.makefile("rw", encoding="utf-8", newline="\n")
                hello = read_message(file)
                if not hello or hello.type != HELLO:
                    conn.close()
                    continue
                name = hello.payload.get("name") or f"Jugador {len(self.clients) + 1}"
                slot = ClientSlot(conn, address, file, len(self.clients), name)
                self.clients.append(slot)
                send_message(file, Message(WELCOME, {"player_index": slot.index, "name": slot.name}))
                self.broadcast(Message(INFO, {"text": f"{slot.name} se unio a la mesa."}))
                print(f"{slot.name} conectado desde {address}")
            self.start_game()
            threads = [threading.Thread(target=self.client_loop, args=(client,), daemon=True) for client in self.clients]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

    def start_game(self):
        names = [client.name for client in self.clients]
        self.engine = GeneralaEngine.new_game(names, seed=self.seed)
        self.broadcast_state()

    def client_loop(self, client):
        try:
            while self.running and client.alive:
                message = read_message(client.file)
                if message is None:
                    break
                if message.type == ACTION:
                    self.handle_action(client, message.payload.get("action", {}))
        except Exception as exc:
            self.send_error(client, f"Conexion cerrada: {exc}")
        finally:
            client.alive = False
            self.broadcast(Message(INFO, {"text": f"{client.name} salio de la mesa."}))

    def handle_action(self, client, data):
        try:
            action = Action.from_dict(data)
            if action.player_index != client.index:
                raise InvalidAction("El cliente intento actuar como otro jugador.")
            with self.lock:
                self.engine.apply(action)
                self.broadcast_state()
        except Exception as exc:
            self.send_error(client, str(exc))

    def broadcast_state(self):
        for client in self.clients:
            if client.alive:
                payload = self.engine.state.to_dict(viewer_index=client.index)
                send_message(client.file, Message(STATE, payload))

    def broadcast(self, message):
        for client in self.clients:
            if client.alive:
                try:
                    send_message(client.file, message)
                except OSError:
                    client.alive = False

    def send_error(self, client, text):
        if client.alive:
            try:
                send_message(client.file, Message(ERROR, {"text": text}))
            except OSError:
                client.alive = False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Servidor online basico de Generala Plus.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)
    OnlineServer(args.host, args.port, seed=args.seed).serve_forever()


if __name__ == "__main__":
    main()
