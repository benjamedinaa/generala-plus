# Stack recomendado

## Recomendacion corta

Usar un stack hibrido:

- **Python** para reglas, motor y servidor.
- **FastAPI + WebSockets** para partidas online en tiempo real.
- **Pygame** como cliente desktop actual.
- **TypeScript + Vite + PixiJS** como futuro cliente web, si se decide ir a navegador.
- **PostgreSQL** solo cuando haya cuentas, historial o ranking.
- **Redis** solo si hay muchas salas simultaneas o se necesita escalar servidores.

Este camino permite jugar a distancia sin reescribir todo el juego desde cero.

## Stack por capas

### Motor de juego

Tecnologia:

- Python 3.13.
- Modulos puros en `generala_plus/core`.
- Tests con `unittest` o `pytest` si se migra despues.

Responsabilidad:

- Reglas de Generala.
- Reglas de Generala Plus.
- Cartas, personajes, eventos, monedas.
- Validacion de acciones.
- Transiciones de turno.
- Estado serializable.

Motivo:

El motor ya existe en Python. Cambiarlo ahora aumentaria el riesgo y retrasaria el online real.

### Servidor online

Tecnologia recomendada:

- FastAPI.
- WebSockets nativos.
- Uvicorn.
- Pydantic para mensajes tipados.

Responsabilidad:

- Crear salas privadas.
- Permitir unirse por codigo.
- Mantener el estado autoritativo.
- Recibir acciones de jugadores.
- Validar acciones en el motor.
- Emitir snapshots a todos los clientes.
- Manejar desconexion/reconexion.

Motivo:

WebSockets encajan bien porque Generala Plus no necesita latencia tipo shooter. Necesita sincronizacion clara, turnos, eventos y feedback en tiempo real.

### Cliente desktop

Tecnologia:

- Pygame.

Responsabilidad:

- Mantener el juego actual.
- Conectarse al servidor WebSocket.
- Dibujar la mesa.
- Mandar acciones.
- Recibir snapshots.

Motivo:

Ya esta avanzado visualmente. No conviene descartarlo.

### Cliente web futuro

Tecnologia recomendada:

- TypeScript.
- Vite.
- PixiJS.
- Zustand o estado simple propio.
- WebSocket client nativo.

Alternativa:

- Phaser si se quiere un framework mas orientado a juegos.

Decision:

Para Generala Plus recomiendo **PixiJS**, no Phaser. El juego es mas UI premium, cartas, dados y animaciones 2D que juego con fisicas. PixiJS da mas control visual y menos estructura innecesaria.

### Persistencia

Fase inicial:

- Sin base de datos.
- Salas en memoria.
- Partidas privadas temporales.

Fase intermedia:

- SQLite para logs locales o partidas guardadas.

Fase publica:

- PostgreSQL para usuarios, rankings, historial y estadisticas.

### Hosting

Para jugar con amigos:

- Backend WebSocket en Render, Railway o Fly.io.
- Cliente desktop descargable desde GitHub Releases.
- Cliente web futuro en Vercel, Netlify o GitHub Pages.

Recomendacion:

- **Fly.io** si se prioriza WebSockets estables.
- **Railway** si se prioriza facilidad.
- **Render** si se prioriza configuracion simple, aceptando posibles sleeps en plan gratis.

## Stack final recomendado

```text
Cliente desktop actual
Python + Pygame
        |
        | WebSocket
        v
Servidor autoritativo
Python + FastAPI + Uvicorn
        |
        v
Motor puro
generala_plus/core

Futuro cliente web
TypeScript + Vite + PixiJS
        |
        | WebSocket
        v
Mismo servidor
```

## Lo que no recomiendo ahora

### Rehacer todo en Unity

No aporta suficiente beneficio para este tipo de juego. Aumenta complejidad y obliga a rehacer UI, reglas y online.

### Rehacer todo en Godot

Godot podria funcionar, pero tambien obliga a reescribir mucho. Tiene sentido si el objetivo cambia a juego comercial multiplataforma con UI rehecha desde cero.

### Poner sockets directos P2P entre jugadores

Funciona en LAN, pero falla para amigos a distancia por NAT, routers, firewalls y puertos. Para un juego normal, conviene servidor intermedio.

### Meter la logica online dentro de Pygame

Hace que el proyecto sea dificil de mantener. El servidor debe ser la fuente de verdad.

