# Estructura del proyecto

Esta es la organizacion pensada para mantener listo el modo local y abrir camino al modo online.

## Raiz

- `Jugar Generala Plus.bat`: acceso directo principal para jugar en Windows.
- `ejercicio-9.py`: launcher Python compatible con el nombre original.
- `README.md`: guia corta para ejecutar, compartir y probar.
- `requirements.txt`: dependencias minimas.
- `crear_paquete_para_amigos.ps1`: wrapper visible que llama al script real de empaquetado.

## Carpetas principales

- `generala_plus/`: paquete del juego.
- `assets/`: sonidos, imagenes y recursos compartibles.
- `docs/`: notas tecnicas y de arquitectura.
- `scripts/`: herramientas de mantenimiento y empaquetado.
- `tests/`: pruebas automaticas.
- `artifacts/`: capturas y salidas de QA, ignoradas para distribuir.
- `dist/`: paquete final para compartir, generado por script.

## Paquete `generala_plus`

- `pygame_app.py`: aplicacion local Pygame, render, input, animaciones y flujo visual.
- `rules.py`: reglas puras, puntajes, cartas, personajes, eventos y mazo.
- `visual.py`: componentes visuales, dados, cartas e iconografia.
- `audio.py`: sonidos y mezcla.
- `info_content.py`: textos largos del manual y tooltips.
- `settings.py`: layout, colores y constantes de pantalla.
- `core/`: estado serializable y motor de acciones sin Pygame.
- `net/`: formato de mensajes para el futuro modo online.

## Regla de mantenimiento

El modo local debe seguir funcionando desde Pygame. El modo online debe crecer desde `core/` y `net/`, no desde sockets metidos directamente en `pygame_app.py`.
