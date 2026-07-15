# Tareas proximas

## Sprint 1 - Base online seria

Objetivo:

Preparar el proyecto para partidas online reales a distancia.

Tareas:

- [ ] Auditar diferencias entre modo local y `generala_plus/core/engine.py`.
- [ ] Mover reglas restantes desde `pygame_app.py` hacia `core`.
- [ ] Definir mensajes WebSocket en un documento de protocolo.
- [ ] Crear servidor FastAPI minimo.
- [ ] Crear salas por codigo.
- [ ] Crear snapshot publico/privado por jugador.
- [ ] Probar dos clientes locales contra el servidor.

## Sprint 2 - Lobby moderno

Objetivo:

Reemplazar IP/host por experiencia de juego normal.

Tareas:

- [ ] Pantalla "Crear sala".
- [ ] Pantalla "Unirse con codigo".
- [ ] Boton copiar codigo.
- [ ] Estado de jugadores conectados.
- [ ] Seleccion de modo antes de crear sala.
- [ ] Seleccion de personaje en lobby Plus.
- [ ] Boton listo.
- [ ] Manejo visual de desconexion.

## Sprint 3 - Deploy privado

Objetivo:

Que se pueda jugar desde dos redes distintas.

Tareas:

- [ ] Crear Dockerfile.
- [ ] Elegir hosting.
- [ ] Deploy de servidor.
- [ ] Configurar URL del servidor en cliente.
- [ ] Crear build v0.11.0.
- [ ] Probar con dos PCs reales.

## Sprint 4 - Pulido online

Objetivo:

Que online se sienta igual de confiable que local.

Tareas:

- [ ] Reconectar con token.
- [ ] Mensajes de error claros.
- [ ] Indicador de latencia.
- [ ] Timeout de sala inactiva.
- [ ] Logs por sala.
- [ ] Tests de acciones invalidas.

## Sprint 5 - Cliente web opcional

Objetivo:

Probar si conviene version web.

Tareas:

- [ ] Crear `web/` con Vite + TypeScript.
- [ ] Conectar WebSocket.
- [ ] Renderizar lobby.
- [ ] Renderizar mesa basica.
- [ ] Renderizar dados y planilla.
- [ ] Renderizar cartas.
- [ ] Probar desktop vs web.

## Definicion de listo para online con amigos

- [ ] Crear sala desde el juego.
- [ ] Compartir codigo.
- [ ] Unirse desde otra red.
- [ ] Jugar modo Clasico.
- [ ] Jugar modo Plus.
- [ ] Terminar partida.
- [ ] Reconectar si se corta internet.
- [ ] Descargar release sin pasos tecnicos.

