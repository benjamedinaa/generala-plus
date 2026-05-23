# Online basico

Esta es la primera version jugable del modo online. No reemplaza todavia a la interfaz Pygame: funciona por terminal para dejar lista una base estable, testeable y autoritativa.

## Que permite hacer

- Conectar 2 jugadores a una misma mesa.
- Mantener un servidor autoritativo.
- Tirar dados.
- Retener o liberar dados.
- Soltar todos los dados.
- Anotar categorias.
- Comprar una carta del mercado.
- Pasar la fase de compra.
- Ocultar la mano del rival en el estado publico.

## Que queda para una segunda etapa

- Pantalla visual Host / Join dentro de Pygame.
- Lobby con nombres, personajes y listo.
- Reconectar si un jugador se cae.
- Todas las cartas avanzadas y habilidades dentro del motor online.
- Eventos completos con UI online.
- Chat o mensajes rapidos.
- Codigos de sala o servidor central.

## Hostear una partida

En la maquina que hace de host:

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
pasar                  termina la fase de compra
estado                 vuelve a imprimir el estado
ayuda                  muestra comandos
salir                  cierra el cliente
```

Categorias validas: `unos`, `doses`, `treses`, `cuatros`, `cincos`, `seises`, `escalera`, `full`, `poker`, `generala`, `doble`.

## Redes recomendadas

Para jugar con amigos fuera de la misma Wi-Fi, lo mas simple es usar una VPN de LAN virtual como Radmin VPN, Hamachi o ZeroTier. Otra opcion es abrir el puerto `8765` en el router del host.

## Nota de diseno

El servidor aplica acciones, no confia en que el cliente modifique el estado. Esto evita trampas accidentales, desincronizaciones y dados distintos entre jugadores.
