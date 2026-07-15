# Generala Plus - Vault del proyecto

Este directorio esta pensado para abrirse en Obsidian como base de trabajo del proyecto.

## Notas principales

- [[01_Stack_Recomendado]]
- [[02_Roadmap_Online_Web]]
- [[03_Arquitectura_Tiempo_Real]]
- [[04_Decisiones_Tecnicas_ADR]]
- [[05_Tareas_Proximas]]
- [[06_Como_usar_Obsidian]]

## Objetivo actual

Llevar Generala Plus de juego local/online basico a un juego compartible con amigos, con partidas privadas en tiempo real a distancia, arquitectura mantenible y camino posible hacia version web.

## Estado base del proyecto

- Cliente actual: Python + Pygame.
- Core de reglas: Python, parcialmente separado en `generala_plus/core`.
- Online actual: sockets/servidor Python con flujo basico.
- Distribucion actual: paquetes ZIP/EXE para Windows.
- Direccion visual: casino premium minimalista, verde oscuro, negro, grafito y champagne.

## Criterio principal

No rehacer todo sin necesidad. Primero consolidar el motor y el online. Despues decidir si conviene construir cliente web completo.

