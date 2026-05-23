# Online

El modo online ya esta integrado en la interfaz Pygame y reutiliza la misma mesa visual del modo local. La consola queda como herramienta tecnica secundaria, no como experiencia principal.

## Que permite hacer

- Conectar 2 jugadores a una misma mesa.
- Mantener un servidor autoritativo.
- Tirar dados.
- Retener o liberar dados.
- Soltar todos los dados.
- Anotar categorias.
- Comprar una carta del mercado.
- Usar cartas tacticas principales.
- Pasar la fase de compra.
- Ocultar la mano del rival en el estado publico.

## Que queda para una segunda etapa

- Reconectar si un jugador se cae.
- Ataques, habilidades y cartas avanzadas dentro del motor online.
- Eventos completos con UI online.
- Chat o mensajes rapidos.
- Codigos de sala o servidor central.

## Hostear una partida desde el juego

1. Abrir `Jugar Generala Plus.bat`.
2. Elegir `MODO CLASICO` o `MODO PLUS` en el menu principal.
3. Elegir `JUGAR ONLINE`.
4. Escribir nombre.
5. Si la mesa es Plus, elegir personaje.
6. Presionar `HOSTEAR`.

## Unirse desde el juego

1. Abrir `Jugar Generala Plus.bat`.
2. Elegir `JUGAR ONLINE`.
3. Escribir nombre e IP del host.
4. Si la mesa es Plus, elegir personaje.
5. Presionar `UNIRSE`.

El modo de la partida lo define el host. Si el host eligio Clasico, la mesa online no usa cartas, monedas, mercado ni personajes. Si eligio Plus, la mesa abre con el sistema Plus visual.

## Launchers tecnicos

En la maquina que hace de host:

```powershell
.\Host y Jugar Online Generala Plus.bat
```

Ese archivo abre el servidor en otra ventana y te conecta como jugador usando `127.0.0.1`.

Si queres abrir solo el servidor:

```powershell
.\Host Online Generala Plus.bat
```

O manualmente:

```powershell
python -m generala_plus.net.server --host 0.0.0.0 --port 8765
```

## Unirse

En la maquina cliente:

```powershell
.\Unirse Online Generala Plus.bat
```

O manualmente:

```powershell
python -m generala_plus.net.client --host 192.168.1.50 --port 8765 --name Ana
```

## Comandos

```text
tirar                  tira los dados
hold 1                 retiene o libera el dado 1
soltar                 libera todos los dados
anotar escalera        anota una categoria
comprar 2              compra la segunda carta del mercado
usar 1 3 +             usa la carta 1 de tu mano, dado 3, subir
usar 1 3 -             usa la carta 1 de tu mano, dado 3, bajar
usar 1 2 6             Dado maestro: dado 2 pasa a 6
usar 2 1 4             Copia: copia dado 1 sobre dado 4
pasar                  termina la fase de compra
estado                 vuelve a imprimir el estado
ayuda                  muestra comandos
salir                  cierra el cliente
```

Categorias validas: `unos`, `doses`, `treses`, `cuatros`, `cincos`, `seises`, `escalera`, `full`, `poker`, `generala`, `doble`.

## Cartas disponibles en online basico

Ya funcionan estas cartas tacticas:

- Ajuste fino
- Reintento
- Espejo
- Tirada extra
- Copia
- Comodin
- Dado maestro
- Duplicador
- Seguro
- Escalera rota
- Generala falsa
- Milagro controlado
- Dado dorado
- Dado duplicador
- Foco numerico
- Ancla
- Apertura
- Pulso controlado
- Ultima oportunidad

El mercado online usa solo cartas compatibles con esta version. Las cartas de ataque y algunas interacciones especiales quedan para la version online visual, porque requieren seleccionar rival, bloquear categorias o resolver efectos entre turnos con mas UI.

## Redes recomendadas

Para jugar con amigos fuera de la misma Wi-Fi, lo mas simple es usar una VPN de LAN virtual como Radmin VPN, Hamachi o ZeroTier. Otra opcion es abrir el puerto `8765` en el router del host.

## Nota de diseno

El servidor aplica acciones, no confia en que el cliente modifique el estado. Esto evita trampas accidentales, desincronizaciones y dados distintos entre jugadores. Si Windows muestra un error `WinError` al conectar, normalmente significa que la IP no responde, el host todavia no termino de abrir la mesa o Firewall bloqueo Python en el puerto `8765`.
