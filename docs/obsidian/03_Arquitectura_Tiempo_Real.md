# Arquitectura de tiempo real

## Principio

El servidor manda la verdad. El cliente manda intenciones.

El cliente no debe decidir:

- resultado de dados,
- puntajes finales,
- compra valida,
- efecto de cartas,
- cooldown de habilidades,
- evento activo,
- ganador.

El cliente solo debe mandar acciones:

```json
{
  "type": "action",
  "room": "ABCD",
  "player": "token",
  "action": {
    "kind": "roll_dice"
  }
}
```

El servidor responde con snapshot:

```json
{
  "type": "snapshot",
  "state": {
    "phase": "turn",
    "active_player": 0,
    "dice": [1, 2, 3, 4, 5],
    "held": [false, true, false, false, false]
  }
}
```

## Modelo de sala

Cada sala debe tener:

- codigo corto visible,
- modo: clasico o plus,
- jugadores,
- estado de lobby,
- motor de partida,
- historial corto de acciones,
- timestamp de ultima actividad.

## Estados de lobby

```text
created
waiting_for_players
ready_check
in_game
finished
closed
```

## Estados de partida

```text
turn
selecting_card_target
selecting_score_category
buy
round_transition
finished
```

## Mensajes WebSocket

### Cliente a servidor

- `create_room`
- `join_room`
- `leave_room`
- `set_name`
- `select_mode`
- `select_character`
- `ready`
- `action`
- `ping`

### Servidor a cliente

- `room_created`
- `joined`
- `snapshot`
- `error`
- `player_joined`
- `player_left`
- `reconnected`
- `pong`

## Reconexion

Modelo recomendado:

- Al unirse, el servidor entrega un `player_token`.
- El cliente guarda el token en memoria y, si se puede, en archivo local.
- Si se corta la conexion, el jugador puede reconectar con:

```json
{
  "type": "reconnect",
  "room": "ABCD",
  "player_token": "..."
}
```

## Privacidad del estado

Cada jugador debe recibir una vista distinta.

Jugador propio:

- ve su mano completa,
- ve monedas,
- ve cartas disponibles,
- ve mercado.

Rival:

- no ve mano completa,
- solo ve cantidad de cartas,
- ve monedas si el juego lo permite,
- ve estado publico.

## Sincronizacion visual

El snapshot debe incluir datos suficientes para que el cliente anime, pero no debe depender de la animacion.

Ejemplo:

```json
{
  "last_event": {
    "kind": "card_bought",
    "player": 0,
    "card": "ajuste_fino",
    "market_index": 1
  }
}
```

El cliente usa `last_event` para animar carta viajando, moneda, banner o sonido.

## Version de protocolo

Agregar siempre:

```json
{
  "protocol_version": "1"
}
```

Si cliente y servidor no coinciden, mostrar:

```text
Version incompatible. Actualiza el juego.
```

## Testing necesario

- Crear sala.
- Unirse a sala.
- Sala llena.
- Desconexion durante turno.
- Reconexion.
- Accion invalida fuera de turno.
- Compra sin monedas.
- Carta que requiere objetivo.
- Fin de partida.
- Modo clasico.
- Modo plus.

