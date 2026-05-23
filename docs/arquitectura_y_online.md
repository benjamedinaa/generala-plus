# Arquitectura y modo online

El modo local esta terminado y sigue funcionando con Pygame. Para sumar online sin volver fragil el proyecto, se agrego una capa nueva independiente de la interfaz:

```text
generala_plus/core/
  actions.py   -> acciones serializables de jugador
  state.py     -> estado serializable de partida
  engine.py    -> controlador puro, sin Pygame

generala_plus/net/
  protocol.py  -> mensajes JSON para cliente/servidor
  wire.py      -> lectura/escritura JSON por linea
  commands.py  -> comandos de consola para el cliente online
  server.py    -> servidor autoritativo TCP basico
  client.py    -> cliente TCP basico por terminal
```

## Principio principal

Pygame dibuja y captura input. El servidor online aplica acciones sobre `GeneralaEngine` y envia snapshots de `GameState`.

Esto evita tres problemas:

- que cada cliente tire dados por su cuenta,
- que el estado visual sea la fuente de verdad,
- que una regla se implemente dos veces de formas distintas.

## Flujo online actual

```text
Cliente terminal -> Action JSON -> Servidor autoritativo -> GameState publico -> Clientes
```

Ejemplos de acciones ya definidas:

- `roll_dice`
- `toggle_hold`
- `release_all`
- `score_category`
- `buy_market_card`
- `pass_buy`
- `use_card`
- `use_ability`

## Estado publico y estado privado

`GameState.to_dict(viewer_index=...)` ya permite ocultar la mano del rival:

- el jugador propio ve su mano completa,
- el rival ve solo la cantidad de cartas,
- el mercado se mantiene publico,
- mazo y descarte se exponen como cantidad.

Este es el modelo correcto para online: el servidor conoce todo, cada cliente recibe solo lo que debe ver.

## Como probarlo

En la maquina host:

```powershell
python -m generala_plus.net.server --host 0.0.0.0 --port 8765
```

En cada cliente:

```powershell
python -m generala_plus.net.client --host <ip-del-host> --port 8765 --name Ana
```

Tambien existen launchers:

- `Host Online Generala Plus.bat`
- `Unirse Online Generala Plus.bat`

## Que falta para online completo con UI

1. Completar en `GeneralaEngine` todas las cartas, habilidades, ataques y eventos del modo Plus.
2. Conectar `pygame_app.py` a un cliente de red.
3. Crear pantalla Host / Join dentro del juego.
4. Manejar lobby, listo, desconexion y reconexion.
5. Agregar guardado/replay de partidas online.

## Orden recomendado

1. Mantener el juego local como referencia.
2. Mover progresivamente logica de `pygame_app.py` hacia `core/engine.py`.
3. Mantener el servidor autoritativo como unica fuente de verdad.
4. Empezar con LAN o host por IP.
5. Luego pensar en servidor central o codigos de sala.
