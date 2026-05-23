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

ONLINE_CARD_POOL = set(build_deck())


class ClientSlot:
    def __init__(self, conn, address, file, index, name, character_key="matematico"):
        self.conn = conn
        self.address = address
        self.file = file
        self.index = index
        self.name = name
        self.character_key = character_key
        self.alive = True
        self.connection_id = 0


class OnlineServer:
    def __init__(self, host="0.0.0.0", port=8765, seed=None, plus_mode=True):
        self.host = host
        self.port = port
        self.seed = seed
        self.plus_mode = plus_mode
        self.clients = []
        self.threads = []
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
            self.logger.info("Servidor escuchando en %s:%s modo=%s", self.host, self.port, "plus" if self.plus_mode else "clasico")
            while self.running:
                try:
                    conn, address = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                self.accept_client(conn, address)
        self.server_socket = None
        self.logger.info("Servidor finalizado.")

    def accept_client(self, conn, address):
        try:
            file = conn.makefile("rw", encoding="utf-8", newline="\n")
            hello = read_message(file)
            if not hello or hello.type != HELLO:
                conn.close()
                return
            name = hello.payload.get("name") or f"Jugador {len(self.clients) + 1}"
            character_key = hello.payload.get("character_key") or "matematico"
            with self.lock:
                slot = self.find_reconnect_slot(name)
                if slot:
                    try:
                        if slot.conn:
                            slot.conn.close()
                    except OSError:
                        pass
                    slot.conn = conn
                    slot.address = address
                    slot.file = file
                    slot.alive = True
                    slot.connection_id += 1
                    send_message(file, Message(WELCOME, {"player_index": slot.index, "name": slot.name, "reconnected": True}))
                    self.logger.info("Cliente reconectado: %s desde %s", slot.name, address)
                    if self.engine:
                        self.engine.log_event(f"{slot.name} reconecto a la mesa.")
                    self.broadcast(Message(INFO, {"text": f"{slot.name} volvio a la mesa."}))
                    self.start_client_thread(slot)
                    self.broadcast_state()
                    return
                if self.engine is not None or len(self.clients) >= 2:
                    send_message(file, Message(ERROR, {"text": "Mesa llena o partida ya iniciada. Para reconectar usa el mismo nombre."}))
                    conn.close()
                    return
                slot = ClientSlot(conn, address, file, len(self.clients), name, character_key)
                self.clients.append(slot)
                send_message(file, Message(WELCOME, {"player_index": slot.index, "name": slot.name}))
                self.broadcast(Message(INFO, {"text": f"{slot.name} se unio a la mesa."}))
                print(f"{slot.name} conectado desde {address}")
                self.logger.info("Cliente conectado: %s desde %s con personaje %s", slot.name, address, slot.character_key)
                self.start_client_thread(slot)
                if len(self.clients) == 2 and self.engine is None:
                    self.start_game()
        except Exception as exc:
            self.logger.warning("No se pudo aceptar cliente %s: %s", address, exc)
            try:
                conn.close()
            except OSError:
                pass

    def find_reconnect_slot(self, name):
        normalized = str(name).strip().lower()
        for client in self.clients:
            if client.name.strip().lower() == normalized:
                return client
        return None

    def start_client_thread(self, client):
        connection_id = client.connection_id
        thread = threading.Thread(target=self.client_loop, args=(client, connection_id), daemon=True)
        self.threads.append(thread)
        thread.start()

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
        self.engine = GeneralaEngine.new_game(names, plus_mode=self.plus_mode, character_keys=characters, seed=self.seed)
        if self.plus_mode:
            self.engine.state.deck = [card for card in build_deck() if card in ONLINE_CARD_POOL]
            self.engine.random.shuffle(self.engine.state.deck)
            self.engine.state.market = []
            self.engine.state.discard = []
            for player in self.engine.state.players:
                player.offered_market_cards.clear()
            self.engine.fill_market_for_active_player(record_offer=True)
        self.broadcast_state()

    def client_loop(self, client, connection_id):
        try:
            while self.running and client.alive:
                if connection_id != client.connection_id:
                    return
                message = read_message(client.file)
                if message is None:
                    break
                if message.type == ACTION:
                    self.handle_action(client, message.payload.get("action", {}))
        except Exception as exc:
            self.send_error(client, f"Conexion cerrada: {exc}")
        finally:
            if connection_id != client.connection_id:
                return
            client.alive = False
            self.broadcast(Message(INFO, {"text": f"{client.name} salio de la mesa. Esperando reconexion."}))
            if self.engine:
                self.engine.log_event(f"{client.name} se desconecto. Puede reconectar con el mismo nombre.")
                self.broadcast_state()

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
        if not self.engine:
            return
        for client in self.clients:
            if client.alive:
                try:
                    payload = self.engine.state.to_dict(viewer_index=client.index)
                    send_message(client.file, Message(STATE, payload))
                except OSError:
                    client.alive = False

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
    parser.add_argument("--classic", action="store_true", help="Hostea una mesa online de Generala clasica.")
    args = parser.parse_args(argv)
    OnlineServer(args.host, args.port, seed=args.seed, plus_mode=not args.classic).serve_forever()


if __name__ == "__main__":
    main()
