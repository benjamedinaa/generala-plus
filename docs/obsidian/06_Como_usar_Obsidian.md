# Como usar Obsidian con este proyecto

## Opcion recomendada

Abrir como vault la carpeta:

```text
C:\Users\benja\OneDrive\Desktop\5\docs\obsidian
```

Esto mantiene las notas limpias y separadas del codigo.

## Pasos

1. Abrir Obsidian.
2. Elegir `Open folder as vault`.
3. Seleccionar:

```text
C:\Users\benja\OneDrive\Desktop\5\docs\obsidian
```

4. Abrir `00_Indice.md`.
5. Usar los links internos para navegar.

## Estructura recomendada dentro de Obsidian

Usar estas notas como centro:

- `00_Indice`: entrada principal.
- `01_Stack_Recomendado`: decisiones de tecnologia.
- `02_Roadmap_Online_Web`: fases de trabajo.
- `03_Arquitectura_Tiempo_Real`: modelo tecnico online.
- `04_Decisiones_Tecnicas_ADR`: decisiones importantes.
- `05_Tareas_Proximas`: checklist operativo.

## Plugins utiles

No son obligatorios.

Recomendados:

- Kanban: para convertir tareas en tablero.
- Dataview: para consultar notas y tareas.
- Excalidraw: para diagramas de arquitectura.

## Convencion de notas

Para nuevas decisiones:

```text
ADR 007 - Titulo de decision
```

Para bugs:

```text
BUG - Descripcion corta
```

Para ideas:

```text
IDEA - Descripcion corta
```

## Rutina recomendada

Antes de programar:

- Revisar `05_Tareas_Proximas`.
- Elegir una tarea concreta.
- Anotar decision tecnica si cambia arquitectura.

Despues de programar:

- Marcar tareas hechas.
- Agregar notas de problemas encontrados.
- Actualizar roadmap si cambia prioridad.

## Regla practica

Obsidian no debe reemplazar GitHub ni los tests. Obsidian sirve para pensar, decidir y ordenar. Git guarda cambios reales. Tests validan que el juego siga funcionando.

