# Generala Plus

Juego de Generala en Pygame con modo clasico y modo Generala Plus.

Generala Plus conserva la base del juego tradicional: 5 dados, hasta 3 tiradas, retener dados y completar la planilla. El modo Plus suma cartas, monedas, personajes, eventos de ronda, mercado visible y animaciones premium sin convertir la partida en un juego de cartas.

## Ejecutar

Forma recomendada en Windows:

```powershell
.\Jugar Generala Plus.bat
```

Ese launcher intenta usar Python 3 y, si falta `pygame`, lo instala desde `requirements.txt`.

Forma manual:

```powershell
python ejercicio-9.py
```

Tambien se puede ejecutar como paquete:

```powershell
python -m generala_plus
```

## Estructura

- `ejercicio-9.py`: launcher compatible con el nombre original.
- `Jugar Generala Plus.bat`: launcher portable para abrir el juego en Windows.
- `crear_paquete_para_amigos.ps1`: wrapper visible para armar una carpeta limpia en `dist/Generala Plus`.
- `scripts/`: herramientas internas de mantenimiento y empaquetado.
- `generala_plus/rules.py`: categorias, cartas, personajes, eventos, mazo y calculo de puntajes.
- `generala_plus/core/`: estado serializable y motor base sin Pygame, preparado para online.
- `generala_plus/net/`: cliente/servidor TCP basico para modo online y protocolo JSON.
- `generala_plus/info_content.py`: contenido del manual, textos largos y explicaciones testeables.
- `generala_plus/settings.py`: tamanos, layout y colores actuales.
- `generala_plus/theme.py`: mapa de tema preparado para el cambio visual.
- `generala_plus/audio.py`: generacion y carga de sonidos premium del juego.
- `generala_plus/pygame_app.py`: loop de Pygame, input, turnos y render.
- `assets/`: imagenes, fuentes y sonidos generados para compartir el juego.
- `docs/arquitectura_y_online.md`: notas para mantener abierta la puerta a un modo online futuro.
- `docs/estructura_del_proyecto.md`: mapa de carpetas y responsabilidades.
- `tests/`: pruebas de reglas que protegen el balance.

## Compartir con amigos

Si tus amigos tienen Python instalado, puedes generar una carpeta limpia ejecutando:

```powershell
.\crear_paquete_para_amigos.ps1
```

Luego comparte la carpeta `dist/Generala Plus`. Dentro esta el archivo `Jugar Generala Plus.bat`.

Tambien puedes generar un ZIP listo para mandar:

```powershell
.\scripts\build_release_zip.ps1
```

El archivo queda en `release/Generala-Plus-windows.zip`.

Por ahora el paquete usa Python instalado en la maquina de cada amigo. Si quieres compartirlo con gente que no tiene Python, el siguiente paso natural seria empaquetarlo como `.exe` con PyInstaller.

## Online basico

El proyecto ya incluye una primera version online real, pensada como base estable para seguir creciendo. Funciona por TCP en LAN, Hamachi, Radmin VPN, ZeroTier o una red similar.

Para hostear:

```powershell
.\Host Online Generala Plus.bat
```

Para unirse:

```powershell
.\Unirse Online Generala Plus.bat
```

El host escucha en el puerto `8765`. Si juegan fuera de la misma red, el host tiene que abrir ese puerto o usar una VPN.

Esta primera version online es intencionalmente basica y corre por consola. Ya permite acciones principales: tirar dados, retener/liberar, anotar categorias, comprar cartas y pasar la compra. La UI Pygame online, lobby visual, reconexion, cartas avanzadas, habilidades y eventos completos quedan preparados como siguiente etapa.

Comandos del cliente online:

```text
tirar
hold 1
soltar
anotar full
comprar 2
pasar
estado
ayuda
salir
```

## Controles rapidos

- Click izquierdo en un dado: retener o liberar.
- Click derecho en cualquier dado: soltar todos los dados retenidos.
- Espacio: tirar dados.
- Teclas 1-5: alternar dados.
- L: soltar todos.
- H: abrir ayuda.
- ESC: pausa.
- F11: pantalla completa.
- R: reiniciar desde la pantalla final.

## Modo Plus

- Cada jugador tiene monedas, cartas y un personaje.
- El mercado muestra 3 cartas visibles.
- Una carta no se repite dentro del mismo mercado.
- Cada jugador ve cada carta del mercado una sola vez durante la partida.
- Maximo 1 carta y 1 habilidad por turno.
- Cada 4 rondas aparece una ronda clasica sin poderes.
- Las jugadas asistidas valen menos que las naturales.

## Pruebas

```powershell
python -m unittest discover -s tests
```
