# Jugar online con un amigo

El modo online actual funciona por consola y usa un servidor autoritativo. Es ideal para jugar con un amigo por la misma red Wi-Fi o por una VPN tipo Radmin VPN, Hamachi o ZeroTier.

## Opcion recomendada: misma Wi-Fi

### En tu PC

1. Abri `Host y Jugar Online Generala Plus.bat`.
2. El launcher muestra tus IPv4.
3. Pasale a tu amigo la IPv4 que corresponda a tu red local. Normalmente se ve parecida a `192.168.0.15` o `192.168.1.20`.
4. Tu ventana ya queda conectada como jugador local.

### En la PC de tu amigo

1. Tu amigo abre `Unirse Online Generala Plus.bat`.
2. Cuando pida IP del host, escribe la IPv4 que le pasaste.
3. Escribe su nombre.
4. Cuando entren los dos jugadores, empieza la mesa.

Puerto usado: `8765`.

## Si no estan en la misma Wi-Fi

La forma mas simple es usar una VPN de LAN virtual:

- Radmin VPN
- Hamachi
- ZeroTier

Pasos:

1. Ambos entran a la misma red virtual.
2. Vos abris `Host y Jugar Online Generala Plus.bat`.
3. Le pasas a tu amigo tu IP de la VPN.
4. Tu amigo abre `Unirse Online Generala Plus.bat` y usa esa IP.

Abrir puertos en el router tambien sirve, pero suele ser mas molesto y depende de cada proveedor de internet.

## Comandos de partida

```text
tirar                  tira los dados
hold 1                 retiene o libera el dado 1
soltar                 libera todos los dados
usar 1 3 +             usa carta 1, dado 3, subir
usar 1 3 -             usa carta 1, dado 3, bajar
usar 1 2 6             Dado maestro: dado 2 pasa a 6
usar 2 1 4             Copia: copia dado 1 sobre dado 4
anotar full            anota Full
comprar 2              compra la segunda carta del mercado
pasar                  termina compra sin comprar
estado                 muestra el estado actual
ayuda                  muestra ayuda
salir                  cierra el cliente
```

## Flujo de turno

1. En tu turno, escribi `tirar`.
2. Usa `hold 1`, `hold 2`, etc. para retener dados.
3. Podes tirar hasta 3 veces.
4. Si tenes una carta util, usa `usar`.
5. Anota con `anotar <categoria>`.
6. En fase compra, compra con `comprar 1`, `comprar 2`, `comprar 3` o termina con `pasar`.

## Notas

- El servidor es la fuente de verdad: los clientes no deciden los dados.
- El rival no ve tu mano completa, solo cuantas cartas tenes.
- El mercado online evita cartas que todavia requieren UI compleja.
- Si Windows Firewall pregunta, permiti Python en redes privadas.
