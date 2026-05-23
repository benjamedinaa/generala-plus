import argparse
import socket
import threading

from ..core import GeneralaEngine
from ..core.actions import Action
from ..core.engine import InvalidAction
from ..rules import build_deck
from .logging_utils import get_online_logger
from .protocol import ACTION, ERROR, HELLO, INFO, STATE, WELCOME, Message
from .wire import read_message, send_message

ONLINE_CARD_POOL = {
    "ajuste_fino",
    "reintento",
    "espejo",
    "seguro",
    "tirada_extra",
    "copia",
    "comodin",
    "escalera_rota",
    "ultima_oportunidad",
    "dado_dorado",
    "dado_maestro",
    "duplicador",
    "generala_falsa",
    "milagro_controlado",
    "foco_numerico",
    "ancla",
    "apertura",
    "pulso_controlado",
    "dado_duplicador",
}


class ClientSlot:
    def __init__(self, conn, address, file, index, name, character_key="matematico"):
        self.conn = conn
        self.address = address
        self.file = file
        self.index = index
        self.name = name
        self.character_key = character_key
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
        self.server_socket = None
        self.logger = get_online_logger("server")

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            self.server_socket = server
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(2)
            server.settimeout(0.5)
            print(f"Generala Plus Online escuchando en {self.host}:{self.port}")
            print("Esperando 2 jugadores...")
            self.logger.info("Servidor escuchando en %s:%s", self.host, self.port)
            while self.running and len(self.clients) < 2:
                try:
                    conn, address = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                file = conn.makefile("rw", encoding="utf-8", newline="\n")
                hello = read_message(file)
                if not hello or hello.type != HELLO:
                    conn.close()
                    continue
                name = hello.payload.get("name") or f"Jugador {len(self.clients) + 1}"
                character_key = hello.payload.get("character_key") or "matematico"
                slot = ClientSlot(conn, address, file, len(self.clients), name, character_key)
                self.clients.append(slot)
                send_message(file, Message(WELCOME, {"player_index": slot.index, "name": slot.name}))
                self.broadcast(Message(INFO, {"text": f"{slot.name} se unio a la mesa."}))
                print(f"{slot.name} conectado desde {address}")
                self.logger.info("Cliente conectado: %s desde %s con personaje %s", slot.name, address, slot.character_key)
            if not self.running or len(self.clients) < 2:
                self.close_clients()
                self.logger.info("Servidor cerrado antes de iniciar partida.")
                return
            self.start_game()
            threads = [threading.Thread(target=self.client_loop, args=(client,), daemon=True) for client in self.clients]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.server_socket = None
        self.logger.info("Servidor finalizado.")

    def stop(self):
        self.running = False
        try:
            if self.server_socket:
                self.server_socket.close()
        except OSError:
            pass
        self.close_clients()

    def close_clients(self):
        for client in self.clients:
            client.alive = False
            try:
                client.conn.close()
            except OSError:
                pass

    def start_game(self):
        names = [client.name for client in self.clients]
        characters = [client.character_key for client in self.clients]
        self.logger.info("Iniciando partida online: %s", ", ".join(names))
        self.engine = GeneralaEngine.new_game(names, character_keys=characters, seed=self.seed)
        self.engine.state.deck = [card for card in build_deck() if card in ONLINE_CARD_POOL]
        self.engine.random.shuffle(self.engine.state.deck)
        self.engine.state.market = []
        self.engine.state.discard = []
        for player in self.engine.state.players:
            player.offered_market_cards.clear()
        self.engine.fill_market_for_active_player(record_offer=True)
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
                self.logger.info("Accion %s de jugador %s aplicada.", action.kind, client.index)
                self.broadcast_state()
        except Exception as exc:
            self.logger.warning("Accion rechazada para %s: %s", client.name, exc)
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
