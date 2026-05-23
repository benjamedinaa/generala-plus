# 🎲 GENERALA — DESIGN PROMPT COMPLETO
### Estilo: Luxury Monochrome / Dark Elegance / Modern Casino
**Motor:** Python + Pygame | **Paleta:** Blanco puro, Negro profundo, Gris platino, Toques dorados opcionales

---

## 1. FILOSOFÍA DE DISEÑO

> *"Menos es más, pero lo que hay, es perfecto."*

El juego debe sentirse como una **mesa de casino de alto lujo**, modernizada con estética de diseño gráfico contemporáneo. Inspiración: Apple Store meets Casino Royale meets Bauhaus. Cada pixel tiene propósito. El jugador debe sentir que está usando algo **caro**.

---

## 2. PALETA DE COLORES EXACTA

```
FONDO PRINCIPAL:       #0A0A0A  (negro casi puro, no absoluto — evitar fatiga visual)
FONDO SECUNDARIO:      #111111  (paneles, cards)
FONDO ELEVADO:         #1A1A1A  (modales, tooltips)
BORDE SUTIL:           #2A2A2A  (separadores, líneas finas)
BORDE ACTIVO:          #444444  (hover, selección)
GRIS PLATINO OSCURO:   #555555  (texto deshabilitado)
GRIS PLATINO MEDIO:    #888888  (texto secundario, subtítulos)
GRIS PLATINO CLARO:    #CCCCCC  (texto principal)
BLANCO SUAVE:          #F0F0F0  (énfasis, headers)
BLANCO PURO:           #FFFFFF  (acentos máximos, dados activos)
GLOW BLANCO:           rgba(255,255,255,0.08) (resplandores sutiles)

ACENTO DORADO:         #C9A84C  (SOLO para: generala servida, puntaje récord)
ACENTO DORADO GLOW:    rgba(201,168,76,0.3)
ROJO ERROR:            #CC3333  (combinaciones inválidas, solo cuando necesario)
VERDE ÉXITO:           #2ECC71  (solo para confirmación rápida, transitorio)
```

---

## 3. TIPOGRAFÍA

```
FUENTE PRINCIPAL:  "Inter" o "Space Grotesk" — sans-serif geométrica moderna
FUENTE DISPLAY:    "Bebas Neue" o "Oswald" — para el título y puntajes grandes
FUENTE MONO:       "JetBrains Mono" — para contadores, turnos, dados en debug

JERARQUÍA:
  - Título "GENERALA":        72px, Bebas Neue, tracking +8px, blanco puro
  - Puntajes en planilla:     28px, Inter Bold, blanco suave
  - Labels de categorías:     14px, Inter Regular, gris platino medio (#888)
  - Texto de ayuda:           11px, Inter Light, gris oscuro (#555)
  - Contador de turnos:       48px, Bebas Neue, centrado, tracking +4px
```

---

## 4. DADOS — EL CORAZÓN DEL DISEÑO

### 4.1 Geometría Base
- **Forma:** Cuadrado con `border-radius = 18%` del tamaño total
- **Tamaño base:** 90×90 px en reposo, escalan a 100×100 px al seleccionarse
- **Sombra en reposo:** `box-shadow: 0 8px 32px rgba(0,0,0,0.8)`
- **Material:** Apariencia de resina negra pulida (gradiente sutil de #1C1C1C a #0D0D0D)

### 4.2 Cara del Dado
```
DADO EN REPOSO:
  - Fondo: gradiente radial, esquinas #0D0D0D → centro #1E1E1E
  - Borde: 1.5px solid #333333
  - Puntos (pips): color #FFFFFF, tamaño 10px, forma circular perfecta
  - Brillo superior: gradiente lineal de arriba, rgba(255,255,255,0.06) a transparent

DADO SELECCIONADO (retenido):
  - Fondo: gradiente de #FFFFFF a #E8E8E8
  - Borde: 2px solid #FFFFFF + glow: 0 0 20px rgba(255,255,255,0.4)
  - Puntos: color #0A0A0A
  - Animación de selección: escala de 1.0 a 1.11 en 180ms, ease-out-back
  - Pequeño ícono de candado (🔒) o check debajo del dado, tamaño 12px

DADO AL TIRAR (animación):
  - Rotación 3D simulada con series de sprites o rotación 2D rápida
  - Duración: 600–900ms con velocidad decreciente (ease-in-quad)
  - Frames de rotación: alterna 6 caras visibles (2D representation)
  - Blur de movimiento: leve gaussian blur (radio 3-4px) durante vuelo
  - Rebote final: overshoot de escala 1.15 → 1.0 en los últimos 120ms
  - Sonido sugerido: clack seco, graves, corto (< 200ms)

DADO HOVER:
  - Border color: #555555
  - Leve brillo superior: rgba(255,255,255,0.10)
  - Cursor: pointer con ícono personalizado de candado/cadena
```

### 4.3 Layout de los 5 Dados
```
Posición: centrados horizontalmente, con gap de 20px entre sí
Alineación vertical: zona media-superior de la pantalla (35-45% del alto)
Animación de entrada inicial: caen desde arriba con bounce, delay escalonado
  - Dado 1: delay 0ms
  - Dado 2: delay 60ms
  - Dado 3: delay 120ms
  - Dado 4: delay 180ms
  - Dado 5: delay 240ms
```

---

## 5. SISTEMA DE PARTÍCULAS

### 5.1 Partículas al Tirar los Dados
```python
# Al hacer clic en "TIRAR":
- Emitir 30-50 partículas desde cada dado que se mueve
- Forma: cuadraditos pequeños (3×3 px) rotando, simulando esquirlas
- Color: mayormente #333333 y #444444, algunos #FFFFFF con opacidad 40%
- Velocidad inicial: random(200, 600) px/s en dirección radial
- Vida útil: 400-700ms
- Física: gravedad simulada de 800 px/s², fricción 0.92 por frame
- Fade out: alpha de 255 → 0 en los últimos 30% de vida
- Rotación propia: cada partícula rota entre 2-8 grados por frame
```

### 5.2 Partículas de Éxito — Generala / Escalera / Full
```python
# Al anotar una combinación alta:
GENERALA SERVIDA (máxima):
  - 200 partículas doradas (#C9A84C) + blancas
  - Explosión radial desde el centro del área de dados
  - Formas: mezcla de círculos (r=2-5px) y rombos pequeños
  - Velocidad: random(400, 1200) px/s
  - Grav: 600 px/s², rebote en el suelo (y_max = bottom_screen)
  - Trail: cada partícula deja rastro de 4-6 puntos, opacidad decreciente
  - Duración total: 2.5 segundos
  - Glow: cada partícula tiene halo de radio 3px, misma color con alpha 60

GENERALA NORMAL / PÓKER:
  - 80 partículas blancas
  - Explosión más pequeña, sin trail
  - Duración: 1.2 segundos

FULL / ESCALERA:
  - 40 partículas grises #AAAAAA
  - Dispersión moderada
  - Duración: 0.8 segundos
```

### 5.3 Partículas Ambientales (Background)
```python
# Siempre activas, muy sutiles:
- 15-20 partículas flotantes en el fondo
- Forma: puntos de 1-2px de diámetro
- Color: #FFFFFF con alpha 15-40 (random)
- Movimiento: deriva lenta (< 30px/s), dirección random que cambia suavemente
- Comportamiento: rebotan suavemente en los bordes de la pantalla
- Algunas parpadean (alpha oscila con seno, frecuencia 0.5-2 Hz)
- Efecto "polvo de casino bajo la luz"
```

### 5.4 Partículas de Hover sobre Categorías
```python
# Al pasar el mouse sobre una fila de la planilla con puntos disponibles:
- 5-8 partículas pequeñas emergen de la fila
- Flotan hacia arriba lentamente (drift up, 40px/s)
- Color: #FFFFFF con alpha inicial 120, fade out
- Vida: 600-900ms
- Indica que la celda está disponible
```

---

## 6. PANTALLA PRINCIPAL — LAYOUT GENERAL

```
┌─────────────────────────────────────────────────────────┐
│  [LOGO/TÍTULO]              [TURNO X/3]   [●MENÚ]       │  Header — 70px
├─────────────────────────────────────────────────────────┤
│                                                         │
│           ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐           │
│           │ ⚀ │  │ ⚃ │  │ ⚄ │  │ ⚁ │  │ ⚅ │           │  Zona Dados
│           └───┘  └───┘  └───┘  └───┘  └───┘           │  ~30% del alto
│                                                         │
│                  [ TIRAR DADOS ]                        │  Botón central
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   CATEGORÍA          JUGADOR 1        JUGADOR 2         │
│   ─────────────────────────────────────────────────    │
│   Unos               5                —                 │
│   Doses              —                8                 │
│   Treses             9                —                 │
│   Cuatros            —                12                │
│   Cincos             —                —                 │
│   Seises             18               —                 │
│   ─────────────────────────────────────────────────    │
│   BONUS              —                —                 │
│   ─────────────────────────────────────────────────    │
│   Escalera           —                —                 │
│   Full               —                —                 │
│   Poker              —                —                 │
│   Generala           —                —                 │
│   G. Servida         —                —                 │
│   ─────────────────────────────────────────────────    │
│   TOTAL              32               20                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. BOTÓN "TIRAR DADOS"

```
ESTADO NORMAL:
  - Dimensiones: 220×54px, border-radius: 8px
  - Fondo: #FFFFFF
  - Texto: "TIRAR DADOS", color #0A0A0A, Bebas Neue 22px, tracking +3px
  - Borde: ninguno
  - Sombra: 0 4px 24px rgba(255,255,255,0.15)

HOVER:
  - Fondo: #E8E8E8
  - Sombra: 0 6px 32px rgba(255,255,255,0.25)
  - Cursor: pointer
  - Transición: 150ms ease

CLICK / PRESSED:
  - Escala: 0.96
  - Fondo: #CCCCCC
  - Transición: 80ms

DESHABILITADO (sin tiros restantes / jugador debe anotar):
  - Fondo: #1A1A1A
  - Texto: color #444444
  - Borde: 1px solid #2A2A2A
  - Sin sombra
  - Cursor: not-allowed

ÚLTIMO TIRO (tercero):
  - Pulsa suavemente (glow pulsante en rojo muy sutil)
  - Texto: "ÚLTIMO TIRO" (cambiar label)
```

---

## 8. PLANILLA DE PUNTAJE

### 8.1 Estilo de Filas
```
FILA NORMAL VACÍA:
  - Fondo: #111111
  - Borde inferior: 1px solid #1E1E1E
  - Texto categoría: #888888, 14px
  - Celda puntaje: #555555 (placeholder "—"), centrado

FILA HOVER (disponible para anotar):
  - Fondo: animación de barrido horizontal: gradiente de izq a der
    rgba(255,255,255,0.04) → rgba(255,255,255,0.08) → rgba(255,255,255,0.04)
  - Border left: 2px solid #FFFFFF
  - Texto categoría: #FFFFFF
  - Preview del puntaje: aparece en la celda del jugador activo
    con animación fade-in, color #AAAAAA italic (el puntaje que obtendría)
  - Cursor: pointer

FILA ANOTADA (con valor):
  - Texto puntaje: #FFFFFF, bold
  - Fondo celda: #1A1A1A
  - Pequeño checkmark (✓) al lado del número, color #444

FILA ANOTADA — CERO (forzada):
  - Número "0" en color #CC4444
  - Fondo: ligeramente rojizo rgba(204,68,68,0.05)

FILA GENERALA SERVIDA:
  - Fondo especial: gradiente sutil dorado rgba(201,168,76,0.08)
  - Texto: #C9A84C
  - Borde: 1px solid rgba(201,168,76,0.3)
  - Glow: text-shadow dorado sutil
  - Número "50" en dorado brillante con leve parpadeo de orgullo

FILA BONUS:
  - Separador visual más grueso (2px) arriba y abajo
  - Fondo: #0D0D0D
  - Texto "BONUS" en mayúsculas, tracking wide
  - Barra de progreso debajo: muestra 0-63 puntos acumulados
    Vacía: #1A1A1A, Rellena: gradiente #FFFFFF → #AAAAAA
    Tamaño: ancho de la celda × progreso/63, altura 3px
```

### 8.2 Animaciones de la Planilla
```python
AL ANOTAR UN PUNTAJE:
  - El número "entra" con animación de conteo rápido (0 → N en 400ms)
  - La fila hace un flash breve (fondo va a rgba(255,255,255,0.12) y vuelve)
  - Si actualiza el TOTAL: el total también anima el conteo

AL PASAR EL TURNO:
  - Columna del nuevo jugador activo: borde izquierdo aparece con fade-in
  - Columna anterior: borde izquierdo desaparece con fade-out
  - Header de columna activa: texto blanco puro, background rgba(255,255,255,0.05)
```

---

## 9. EFECTOS DE PANTALLA GLOBALES

### 9.1 Vignette
```python
# Overlay oscuro en los bordes de la pantalla, siempre activo
# Implementar con superficie pygame de gradiente radial:
# Centro: alpha=0, Bordes: alpha=80-120 (color negro)
# Añade profundidad y enfoca al centro
```

### 9.2 Scanlines (Opcional, Sutil)
```python
# Líneas horizontales muy tenues (alpha 8-15)
# Separación: cada 4px
# Color negro puro
# Velocidad de movimiento: 0 (estáticas) o muy lenta (10px/s hacia abajo)
# Efecto "pantalla CRT de casino"
```

### 9.3 Noise / Grain
```python
# Capa de ruido estático sobre toda la pantalla
# Superficie pygame con píxeles random en alpha muy bajo (5-12)
# Se regenera cada 2-4 frames para simular grano de película
# Color: blanco #FFFFFF
# Da textura y calidez a los negros planos
```

### 9.4 Bloom / Glow en Elementos Blancos
```python
# Simular bloom dibujando el elemento primero con blur grande + alpha bajo,
# luego encima el elemento nítido
# Ejemplo para un dado blanco seleccionado:
#   1. Dibujar rectángulo blanco con blur radius=20, alpha=60
#   2. Dibujar rectángulo blanco con blur radius=8, alpha=100
#   3. Dibujar dado normal encima
# En pygame: usar pygame.transform.smoothscale + blit con BLEND_ADD
```

---

## 10. TRANSICIONES Y ANIMACIONES GLOBALES

```
INICIO DEL JUEGO:
  - Fade in desde negro puro, duración 800ms
  - Logo "GENERALA" aparece letra por letra desde el centro
    con efecto de glitch breve (desplazamiento horizontal ±4px)
  - Los dados caen desde fuera de pantalla con bounce
  - La planilla hace slide-in desde abajo

FIN DE TURNO:
  - Pequeña animación de "flash" horizontal (línea blanca cruza la pantalla)
  - Duración 200ms

FIN DE JUEGO:
  - Pantalla de resultados con fade-in
  - Confetti/partículas doradas para el ganador
  - Texto del ganador con efecto de "stamp" (aparece grande y se encoge)
  - Partículas doradas continuas durante 3 segundos

MENÚ PAUSE:
  - Blur de la pantalla detrás (simular con superficie oscurecida alpha=160)
  - Panel modal entra desde arriba con bounce
  - Todo lo demás: pointer-events none (no interactivo)
```

---

## 11. CURSOR PERSONALIZADO

```python
# Cursor normal: punto blanco pequeño (8px) con halo sutil
# Cursor sobre dado: ícono de candado + cadena (32×32px, blanco/negro)
# Cursor sobre celda de planilla: ícono de pluma/lápiz minimalista
# Cursor sobre botón: flecha normal pero con punto ligeramente más grande
# Implementar con pygame.mouse.set_cursor() y superficies custom
```

---

## 12. SONIDO (Referencias para Diseño Sincronizado)

```
dado_lanzar.wav     → impacto seco, graves, reverb corto (sala de madera)
dado_seleccionar.wav → click suave, agudo, tipo "switch toggle"
dado_deseleccionar.wav → click reverso (pitch ligeramente bajo)
puntaje_anotar.wav  → chime suave, 2 notas ascendentes
generala.wav        → fanfare breve, 1.5 segundos
bonus.wav           → ding corto y satisfactorio
turno_cambio.wav    → whoosh sutil lateral
boton_hover.wav     → tick muy suave, casi inaudible
```

---

## 13. RESPONSIVE / RESOLUCIONES

```
TARGET PRINCIPAL:  1280×720 (HD)
SOPORTE:           1920×1080 (Full HD) → escalar UI ×1.5
                   1024×600 (pequeño) → compactar planilla

ESCALA BASE: Todos los valores en este documento están en 1280×720.
Usar pygame.transform.scale o factor de escala global:
  SCALE = min(screen_w / 1280, screen_h / 720)
  Todos los tamaños multiplicados por SCALE.
```

---

## 14. CÓDIGO BASE — CONSTANTES DE DISEÑO (Python)

```python
# ============================================================
# GENERALA — DESIGN CONSTANTS
# ============================================================

# Colores
C_BG_DEEP       = (10,  10,  10)
C_BG_PANEL      = (17,  17,  17)
C_BG_ELEVATED   = (26,  26,  26)
C_BORDER_SUBTLE = (42,  42,  42)
C_BORDER_ACTIVE = (68,  68,  68)
C_GRAY_DARK     = (85,  85,  85)
C_GRAY_MID      = (136, 136, 136)
C_GRAY_LIGHT    = (204, 204, 204)
C_WHITE_SOFT    = (240, 240, 240)
C_WHITE         = (255, 255, 255)
C_GOLD          = (201, 168, 76)
C_RED_ERROR     = (204, 51,  51)
C_GREEN_SUCCESS = (46,  204, 113)

# Dimensiones (base 1280×720)
SCREEN_W, SCREEN_H  = 1280, 720
HEADER_H            = 70
DIE_SIZE            = 90
DIE_RADIUS          = 16          # border-radius en px
DIE_GAP             = 20
DICE_Y              = 200         # Y centro de los dados
BUTTON_W, BUTTON_H  = 220, 54
BUTTON_RADIUS       = 8
SCORECARD_Y         = 380         # Y inicio de la planilla
ROW_HEIGHT          = 30
COL_W_CAT           = 200         # ancho columna categoría
COL_W_PLAYER        = 130         # ancho columna por jugador

# Animación
FPS                 = 60
DIE_ROLL_DURATION   = 0.75        # segundos
DIE_SELECT_SCALE    = 1.11        # factor escala al seleccionar
DIE_SELECT_DURATION = 0.18        # segundos
PARTICLE_COUNT_ROLL = 35          # partículas por dado al tirar
PARTICLE_COUNT_WIN  = 200         # partículas en generala
PARTICLE_AMBIENT    = 18          # partículas de fondo
BLOOM_LAYERS        = [(20, 60), (8, 100), (0, 255)]  # (blur, alpha)

# Tipografía (nombres de archivo o pygame.font)
FONT_DISPLAY        = "BebasNeue-Regular.ttf"
FONT_BODY           = "Inter-Regular.ttf"
FONT_BODY_BOLD      = "Inter-Bold.ttf"
FONT_MONO           = "JetBrainsMono-Regular.ttf"

# Tamaños de fuente
FS_TITLE            = 72
FS_SCORE_BIG        = 48
FS_SCORE_MED        = 28
FS_LABEL            = 14
FS_HINT             = 11
```

---

## 15. CHECKLIST FINAL DE CALIDAD VISUAL

```
□ El fondo nunca es negro puro (#000) — siempre #0A0A0A mínimo
□ Los textos secundarios siempre en gris (#888), nunca blanco puro
□ Toda animación tiene curva ease (no linear)
□ Los dados seleccionados tienen glow visible pero no exagerado
□ Las partículas nunca superan alpha=255 en su nacimiento (fade-in brief)
□ La vignette está siempre activa, alpha entre 80-120 en bordes
□ El grain/noise se regenera cada 3 frames exactos
□ Nunca hay dos fuentes diferentes en el mismo contexto
□ El dorado (#C9A84C) se usa SOLO en generala servida y récords
□ Los bordes son de 1px o 1.5px — nunca 2px en elementos comunes
□ El botón "TIRAR" cambia de texto en el tercer tiro
□ La barra de progreso del bonus se anima con cada punto acumulado
□ Las transiciones de pantalla duran entre 150ms y 800ms máximo
□ El cursor cambia según el contexto (dado / planilla / botón)
□ Los puntajes en planilla aparecen con animación de conteo
□ Las partículas de fondo son siempre visibles (no se detienen)
□ Resolución base 1280×720 con sistema de escala global implementado
□ FPS mínimo 60 — el sistema de partículas no debe bajar de 55 FPS
```

---

*Generado para uso en Python + Pygame. Cada especificación es implementable directamente.*
*Versión: 1.0 | Estilo: Luxury Monochrome Modern Casino*
