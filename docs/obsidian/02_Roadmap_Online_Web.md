# Roadmap online y web

## Objetivo

Que dos amigos puedan jugar Generala Plus en tiempo real desde distintas PCs, sin configurar puertos ni depender de estar en la misma red.

## Fase 1 - Consolidar motor compartido

Objetivo:

Que local y online usen exactamente el mismo motor de reglas.

Tareas:

- Revisar que `generala_plus/core/engine.py` cubra todas las acciones reales del modo local.
- Mover cualquier regla restante desde `pygame_app.py` hacia `core`.
- Mantener `pygame_app.py` como capa visual e input.
- Aumentar tests de cartas, eventos, habilidades, mercado y final de partida.

Criterio de terminado:

- Una accion aplicada localmente y online produce el mismo resultado.
- El servidor no necesita llamar funciones visuales.
- El cliente no decide resultados: solo pide acciones.

## Fase 2 - Servidor WebSocket

Objetivo:

Reemplazar la conexion online actual por una capa mas apta para jugar a distancia y para futuro cliente web.

Tareas:

- Crear `generala_plus/server/app.py` con FastAPI.
- Crear endpoints WebSocket:
  - `/ws/lobby/{room_code}`
  - `/ws/game/{room_code}`
- Crear salas por codigo corto.
- Soportar:
  - crear sala,
  - unirse a sala,
  - elegir modo,
  - elegir personaje,
  - listo/no listo,
  - empezar partida,
  - reconectar por nombre o token simple.

Criterio de terminado:

- Dos clientes desktop pueden jugar conectandose a un servidor publico.
- No hace falta saber la IP del host.
- El estado se mantiene autoritativo en el servidor.

## Fase 3 - Cliente Pygame conectado al nuevo servidor

Objetivo:

El juego actual se conecta al servidor WebSocket sin perder la UI premium.

Tareas:

- Cambiar pantalla online:
  - crear sala,
  - ingresar codigo,
  - copiar codigo,
  - estado de conexion,
  - reconexion.
- Reemplazar acciones TCP actuales por mensajes WebSocket.
- Mantener fallback local.
- Mostrar errores claros:
  - sala no existe,
  - sala llena,
  - desconectado,
  - version incompatible.

Criterio de terminado:

- El usuario puede abrir el juego, crear sala, pasar codigo a un amigo y jugar.

## Fase 4 - Deploy privado

Objetivo:

Tener servidor real online para amigos.

Tareas:

- Crear Dockerfile.
- Crear configuracion para Fly.io/Railway/Render.
- Agregar variables:
  - `PORT`
  - `ROOM_TTL_MINUTES`
  - `LOG_LEVEL`
- Subir release nueva.
- Documentar instrucciones para jugadores.

Criterio de terminado:

- El servidor esta disponible por URL publica.
- Dos PCs de redes distintas pueden jugar.

## Fase 5 - Cliente web opcional

Objetivo:

Permitir jugar desde navegador sin descargar EXE.

Tareas:

- Crear carpeta `web/`.
- Usar Vite + TypeScript + PixiJS.
- Implementar:
  - pantalla inicial,
  - lobby,
  - mesa,
  - cartas,
  - dados,
  - planilla,
  - pausa/informacion.
- Reusar protocolo WebSocket.

Criterio de terminado:

- Un jugador puede jugar desde web contra otro en desktop o web.

## Fase 6 - Producto compartible

Objetivo:

Que el proyecto se pueda compartir como juego privado serio.

Tareas:

- Pagina simple de descarga.
- Release notes.
- Versionado semantico.
- Logs de errores.
- Crash report local simple.
- Guia para amigos.

## Prioridad recomendada

1. Motor compartido.
2. WebSocket server.
3. UI online por codigo de sala.
4. Deploy publico privado.
5. Web client.

No conviene empezar por web antes de cerrar el motor y el protocolo.

