# Decisiones tecnicas

Formato ADR simplificado: decision, motivo, consecuencias.

## ADR 001 - Mantener Python como motor principal

Decision:

Mantener las reglas y el motor en Python.

Motivo:

El proyecto ya tiene reglas, tests y cliente Pygame en Python. Reescribir ahora aumentaria el riesgo.

Consecuencias:

- El servidor puede reutilizar el motor.
- El cliente web futuro necesitara consumir snapshots, no ejecutar reglas completas.
- Si se quiere logica compartida web/servidor en el futuro, se evaluara portar el motor despues, no ahora.

## ADR 002 - Servidor autoritativo

Decision:

El servidor decide el estado real de la partida.

Motivo:

Evita desincronizacion, trampas simples, resultados distintos entre clientes y bugs por doble implementacion.

Consecuencias:

- El cliente debe ser mas pasivo.
- Las animaciones deben partir del snapshot o de eventos emitidos.
- El servidor necesita tests fuertes.

## ADR 003 - WebSockets para tiempo real

Decision:

Usar WebSockets para online a distancia.

Motivo:

Generala Plus es por turnos. WebSocket es suficiente, simple de depurar y compatible con web.

Consecuencias:

- No hace falta UDP.
- No hace falta rollback netcode.
- Se puede compartir servidor con cliente desktop y cliente web.

## ADR 004 - Cliente web futuro con PixiJS

Decision:

Si se hace cliente web, usar TypeScript + Vite + PixiJS.

Motivo:

El juego depende de UI visual, cartas, dados, animaciones y layout 2D. PixiJS da control de render sin imponer estructura pesada.

Consecuencias:

- Hay que recrear componentes visuales en web.
- El protocolo y servidor ya sirven.
- Se puede publicar el cliente web facilmente.

## ADR 005 - Sin base de datos al principio

Decision:

No usar base de datos para la primera version online con amigos.

Motivo:

Las salas privadas temporales pueden vivir en memoria. Agregar base de datos ahora no mejora la partida.

Consecuencias:

- Si el servidor reinicia, se pierden salas activas.
- Para ranking/historial se agregara PostgreSQL despues.

## ADR 006 - Codigos de sala en vez de IP

Decision:

La experiencia final online debe usar codigos de sala.

Motivo:

Pedir IP del host es tecnico y falla fuera de LAN. Un juego compartible debe permitir: crear sala, copiar codigo, unirse.

Consecuencias:

- Necesitamos servidor publico.
- El lobby debe cambiar.
- La experiencia para amigos mejora mucho.

