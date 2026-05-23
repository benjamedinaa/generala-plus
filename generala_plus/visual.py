import math
from dataclasses import dataclass

import pygame

from .rules import ATTACK_CARDS, CARD_DEFS, category_name
from .settings import (
    COLORS,
    C_BG_DEEP,
    C_BG_ELEVATED,
    C_BG_PANEL,
    C_BORDER_ACTIVE,
    C_BORDER_SUBTLE,
    C_GOLD,
    C_GRAY_DARK,
    C_GRAY_LIGHT,
    C_GRAY_MID,
    C_RED_ERROR,
    C_SHADOW,
    C_WHITE,
    C_WHITE_SOFT,
    RADIUS,
    SCREEN_H,
    SCREEN_W,
)


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def blend(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def with_alpha(color, alpha):
    return (*color, max(0, min(255, int(alpha))))


def trim_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    result = text
    while result and font.size(result + "...")[0] > max_width:
        result = result[:-1]
    return result + "..."


truncate_text = trim_text


def fit_text(text, fonts, max_width):
    for font in fonts:
        if font.size(text)[0] <= max_width:
            return font, text
    font = fonts[-1]
    return font, trim_text(text, font, max_width)


def draw_soft_shadow(surface, rect, alpha=150, spread=18, radius=20, y_offset=10):
    layer = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(
        layer,
        (0, 0, 0, alpha),
        pygame.Rect(spread, spread + y_offset, rect.w, rect.h),
        border_radius=radius,
    )
    small = pygame.transform.smoothscale(layer, (max(1, layer.get_width() // 4), max(1, layer.get_height() // 4)))
    layer = pygame.transform.smoothscale(small, layer.get_size())
    surface.blit(layer, (rect.x - spread, rect.y - spread))


def draw_glow(surface, rect, color=C_WHITE, alpha=34, spread=18, radius=20):
    if alpha <= 0:
        return
    layer = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), pygame.Rect(spread, spread, rect.w, rect.h), border_radius=radius)
    small = pygame.transform.smoothscale(layer, (max(1, layer.get_width() // 4), max(1, layer.get_height() // 4)))
    layer = pygame.transform.smoothscale(small, layer.get_size())
    surface.blit(layer, (rect.x - spread, rect.y - spread), special_flags=pygame.BLEND_PREMULTIPLIED)


def draw_vertical_gradient(surface, rect, top, bottom, radius=0):
    layer = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for y in range(rect.h):
        t = y / max(1, rect.h - 1)
        pygame.draw.line(layer, blend(top, bottom, t), (0, y), (rect.w, y))
    if radius:
        mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(layer, rect.topleft)


def rounded_mask(size, radius):
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    return mask


def draw_panel(surface, rect, fill=C_BG_PANEL, border=C_BORDER_SUBTLE, radius=None, alpha=235, glow=False):
    rect = pygame.Rect(rect)
    radius = RADIUS["panel"] if radius is None else radius
    draw_soft_shadow(surface, rect, alpha=170, spread=22, radius=radius, y_offset=8)
    if glow:
        draw_glow(surface, rect, C_GOLD, 18, 20, radius)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*fill, alpha), layer.get_rect(), border_radius=radius)
    pygame.draw.rect(layer, (*border, 124), layer.get_rect(), width=1, border_radius=radius)
    pygame.draw.rect(layer, (255, 236, 178, 22), layer.get_rect().inflate(-4, -4), width=1, border_radius=max(1, radius - 3))
    highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
    for y in range(max(1, rect.h // 2)):
        a = int(24 * (1 - y / max(1, rect.h // 2)))
        pygame.draw.line(highlight, (255, 255, 255, a), (0, y), (rect.w, y))
    layer.blit(highlight, (0, 0))
    layer.blit(rounded_mask(rect.size, radius), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(layer, rect.topleft)


def draw_chip(surface, rect, text, font, color=C_GRAY_LIGHT, border=C_BORDER_SUBTLE, fill=None):
    rect = pygame.Rect(rect)
    fill = fill or COLORS["black_casino"]
    pygame.draw.rect(surface, fill, rect, border_radius=rect.h // 2)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=rect.h // 2)
    label = font.render(trim_text(text.upper(), font, rect.w - 16), True, color)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_premium_coin(surface, center, radius, filled=True, alpha=255, accent=C_GOLD):
    center = (int(center[0]), int(center[1]))
    radius = int(radius)
    layer = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    local = (radius * 2, radius * 2)
    base = C_WHITE_SOFT if filled else C_BG_DEEP
    edge = accent if filled else C_BORDER_SUBTLE
    pygame.draw.circle(layer, (0, 0, 0, min(alpha, 85)), (local[0] + 2, local[1] + 3), radius + 1)
    pygame.draw.circle(layer, (*base, alpha if filled else min(alpha, 72)), local, radius)
    pygame.draw.circle(layer, (*edge, min(alpha, 210)), local, radius, 1)
    pygame.draw.circle(layer, (*edge, min(alpha, 92)), local, max(1, radius - 4), 1)
    if filled:
        pygame.draw.arc(layer, (255, 255, 255, min(alpha, 110)), pygame.Rect(local[0] - radius + 4, local[1] - radius + 4, (radius - 4) * 2, (radius - 4) * 2), math.radians(205), math.radians(318), 2)
        pygame.draw.line(layer, (*accent, min(alpha, 150)), (local[0] - radius // 3, local[1] + radius // 3), (local[0] + radius // 3, local[1] + radius // 3), 1)
        if radius >= 7:
            font = pygame.font.SysFont("JetBrains Mono, Consolas, monospace", max(6, radius - 2), bold=True)
            text = font.render("G+", True, C_BG_DEEP)
            text.set_alpha(min(alpha, 190))
            layer.blit(text, text.get_rect(center=(local[0], local[1] - 1)))
    surface.blit(layer, layer.get_rect(center=center))


def draw_geo_icon(surface, rect, key, color=C_WHITE_SOFT, alpha=180, line_width=2):
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    c = (*color, max(0, min(255, int(alpha))))
    muted = (*color, max(0, min(255, int(alpha * 0.45))))
    faint = (*color, max(0, min(255, int(alpha * 0.22))))

    def p(x, y):
        return (int(rect.w * x), int(rect.h * y))

    def line(a, b, width=line_width, col=c):
        pygame.draw.line(layer, col, p(*a), p(*b), width)

    def circle(pos, rad, width=0, col=c):
        pygame.draw.circle(layer, col, p(*pos), max(1, int(min(rect.w, rect.h) * rad)), width)

    def poly(points, width=0, col=c):
        pygame.draw.polygon(layer, col, [p(x, y) for x, y in points], width)

    def rect_line(x, y, w, h, width=line_width, radius=3, col=c):
        pygame.draw.rect(layer, col, pygame.Rect(int(rect.w * x), int(rect.h * y), int(rect.w * w), int(rect.h * h)), width=width, border_radius=radius)

    def die(x, y, s, val=1, col=c, dotted=False, rot=0):
        r = pygame.Rect(int(rect.w * x), int(rect.h * y), int(rect.w * s), int(rect.h * s))
        die_surf = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(die_surf, col, die_surf.get_rect(), width=1, border_radius=max(2, int(r.w * 0.18)))
        pip_sets = {
            1: [(0.5, 0.5)],
            2: [(0.32, 0.32), (0.68, 0.68)],
            3: [(0.32, 0.32), (0.5, 0.5), (0.68, 0.68)],
            4: [(0.32, 0.32), (0.68, 0.32), (0.32, 0.68), (0.68, 0.68)],
            5: [(0.32, 0.32), (0.68, 0.32), (0.5, 0.5), (0.32, 0.68), (0.68, 0.68)],
            6: [(0.32, 0.25), (0.68, 0.25), (0.32, 0.5), (0.68, 0.5), (0.32, 0.75), (0.68, 0.75)],
        }
        for px, py in pip_sets.get(val, pip_sets[1]):
            pygame.draw.circle(die_surf, col, (int(r.w * px), int(r.h * py)), max(1, int(r.w * 0.055)))
        if dotted:
            for dx in range(0, r.w, 4):
                pygame.draw.circle(die_surf, col, (dx, 0), 1)
                pygame.draw.circle(die_surf, col, (dx, r.h - 1), 1)
            for dy in range(0, r.h, 4):
                pygame.draw.circle(die_surf, col, (0, dy), 1)
                pygame.draw.circle(die_surf, col, (r.w - 1, dy), 1)
        if rot:
            die_surf = pygame.transform.rotate(die_surf, rot)
            layer.blit(die_surf, die_surf.get_rect(center=r.center))
        else:
            layer.blit(die_surf, r.topleft)

    def card(x, y, w, h, col=c, rot=0):
        r = pygame.Rect(int(rect.w * x), int(rect.h * y), int(rect.w * w), int(rect.h * h))
        surf = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, col, surf.get_rect(), width=1, border_radius=max(2, int(r.w * 0.12)))
        pygame.draw.line(surf, muted, (int(r.w * 0.25), int(r.h * 0.75)), (int(r.w * 0.75), int(r.h * 0.75)), 1)
        if rot:
            surf = pygame.transform.rotate(surf, rot)
            layer.blit(surf, surf.get_rect(center=r.center))
        else:
            layer.blit(surf, r.topleft)

    def arrow_arc(box, start, end, col=c, arrow_at="end"):
        pygame.draw.arc(layer, col, pygame.Rect(int(rect.w * box[0]), int(rect.h * box[1]), int(rect.w * box[2]), int(rect.h * box[3])), math.radians(start), math.radians(end), line_width)
        angle = math.radians(end if arrow_at == "end" else start)
        cx = box[0] + box[2] / 2 + math.cos(angle) * box[2] * 0.5
        cy = box[1] + box[3] / 2 - math.sin(angle) * box[3] * 0.5
        poly([(cx, cy), (cx - 0.09, cy + 0.03), (cx - 0.03, cy + 0.11)], 0, col)

    def star(cx=0.5, cy=0.5, outer=0.28, inner=0.12, col=c, width=0):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = outer if i % 2 == 0 else inner
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        poly(pts, width, col)

    def text_mark(text, pos=(0.5, 0.5), size=0.22, col=c):
        font = pygame.font.SysFont("JetBrains Mono, Consolas, monospace", max(6, int(min(rect.w, rect.h) * size)), bold=True)
        surf = font.render(text, True, col)
        layer.blit(surf, surf.get_rect(center=p(*pos)))

    def shield(x=0.5, y=0.5, scale=1.0, col=c):
        sx = 0.28 * scale
        sy = 0.36 * scale
        poly([(x, y - sy), (x + sx, y - sy * 0.58), (x + sx * 0.72, y + sy * 0.45), (x, y + sy), (x - sx * 0.72, y + sy * 0.45), (x - sx, y - sy * 0.58)], line_width, col)

    key = (key or "").lower()
    if key == "ajuste_fino":
        circle((0.5, 0.5), 0.28, line_width, c)
        line((0.18, 0.5), (0.36, 0.5), 1, muted)
        line((0.64, 0.5), (0.82, 0.5), 1, muted)
        line((0.5, 0.18), (0.5, 0.36), 1, muted)
        line((0.5, 0.64), (0.5, 0.82), 1, muted)
        line((0.24, 0.74), (0.58, 0.4), line_width, c)
        text_mark("+", (0.78, 0.34), 0.18, c)
        text_mark("-", (0.22, 0.34), 0.2, c)
    elif key == "reintento":
        die(0.34, 0.35, 0.3, 3, c)
        arrow_arc((0.18, 0.16, 0.64, 0.64), 30, 330, c)
    elif key == "espejo":
        line((0.5, 0.14), (0.5, 0.86), 1, muted)
        rect_line(0.18, 0.28, 0.26, 0.44, line_width, 2, c)
        rect_line(0.56, 0.28, 0.26, 0.44, line_width, 2, c)
        circle((0.31, 0.5), 0.045, 0, c)
        for pos in [(0.63, 0.36), (0.75, 0.36), (0.63, 0.5), (0.75, 0.5), (0.63, 0.64), (0.75, 0.64)]:
            circle(pos, 0.025, 0, c)
    elif key == "seguro":
        shield(0.5, 0.45, 0.88, c)
        pygame.draw.arc(layer, muted, pygame.Rect(rect.w * 0.26, rect.h * 0.62, rect.w * 0.48, rect.h * 0.22), math.radians(200), math.radians(340), line_width)
        line((0.34, 0.72), (0.66, 0.72), 1, muted)
    elif key == "reciclaje":
        card(0.25, 0.29, 0.24, 0.34, c, -8)
        card(0.52, 0.37, 0.24, 0.34, muted, 8)
        arrow_arc((0.2, 0.18, 0.62, 0.58), 210, 20, c)
        arrow_arc((0.18, 0.24, 0.62, 0.58), 30, 205, muted)
    elif key == "mano_estable":
        line((0.18, 0.72), (0.82, 0.72), line_width, c)
        line((0.26, 0.58), (0.42, 0.46), line_width, c)
        line((0.42, 0.46), (0.62, 0.58), line_width, c)
        line((0.34, 0.5), (0.34, 0.66), line_width, c)
        die(0.49, 0.34, 0.22, 1, c)
    elif key == "correccion_minima":
        die(0.18, 0.32, 0.3, 2, c)
        for x in (0.55, 0.62, 0.69, 0.76):
            line((x, 0.68), (x, 0.58), 1, muted)
        line((0.52, 0.68), (0.82, 0.68), line_width, c)
        line((0.54, 0.42), (0.72, 0.42), line_width, c)
        poly([(0.72, 0.34), (0.84, 0.42), (0.72, 0.5)], 0, c)
    elif key == "tirada_extra":
        for i, val in enumerate((1, 2, 3)):
            die(0.14 + i * 0.19, 0.46, 0.16, val, c)
        die(0.68, 0.32, 0.22, 4, c)
        text_mark("+", (0.69, 0.68), 0.2, c)
    elif key == "copia":
        die(0.28, 0.36, 0.36, 4, muted)
        die(0.38, 0.26, 0.36, 4, c)
        line((0.24, 0.74), (0.74, 0.74), 1, muted)
    elif key == "comodin":
        die(0.28, 0.26, 0.44, 1, c)
        text_mark("W", (0.5, 0.5), 0.28, c)
        for pos in [(0.25, 0.22), (0.78, 0.3), (0.22, 0.76), (0.78, 0.74)]:
            circle(pos, 0.025, 0, muted)
    elif key == "escudo":
        shield(0.5, 0.5, 0.88, c)
        die(0.39, 0.42, 0.22, 5, muted)
    elif key == "escalera_rota":
        line((0.18, 0.76), (0.36, 0.76), line_width, c)
        line((0.36, 0.76), (0.36, 0.58), line_width, c)
        line((0.36, 0.58), (0.54, 0.58), line_width, c)
        line((0.54, 0.58), (0.54, 0.4), line_width, c)
        line((0.54, 0.4), (0.68, 0.4), line_width, c)
        line((0.72, 0.34), (0.84, 0.22), line_width, muted)
        line((0.78, 0.54), (0.88, 0.44), line_width, muted)
    elif key == "ultima_oportunidad":
        poly([(0.34, 0.18), (0.66, 0.18), (0.56, 0.48), (0.66, 0.82), (0.34, 0.82), (0.44, 0.48)], line_width, c)
        die(0.41, 0.62, 0.18, 1, muted)
        line((0.38, 0.24), (0.62, 0.24), 1, muted)
    elif key == "dado_dorado":
        die(0.28, 0.28, 0.44, 5, c)
        star(0.5, 0.5, 0.18, 0.075, c, 0)
    elif key == "dado_maestro":
        die(0.31, 0.38, 0.38, 6, c)
        poly([(0.28, 0.34), (0.34, 0.16), (0.44, 0.28), (0.5, 0.14), (0.56, 0.28), (0.66, 0.16), (0.72, 0.34)], line_width, c)
        line((0.31, 0.36), (0.69, 0.36), line_width, c)
    elif key == "duplicador":
        die(0.24, 0.38, 0.28, 2, muted)
        die(0.38, 0.28, 0.28, 2, c)
        text_mark("x2", (0.72, 0.66), 0.17, c)
    elif key == "rescate":
        line((0.22, 0.68), (0.7, 0.28), line_width, muted)
        line((0.3, 0.35), (0.74, 0.35), 1, c)
        line((0.3, 0.5), (0.66, 0.5), 1, c)
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.2, rect.h * 0.22, rect.w * 0.58, rect.h * 0.58), math.radians(145), math.radians(340), line_width)
        poly([(0.24, 0.35), (0.14, 0.42), (0.22, 0.52)], 0, c)
    elif key == "generala_falsa":
        for i, pos in enumerate([(0.22, 0.24), (0.46, 0.24), (0.68, 0.24), (0.34, 0.56), (0.58, 0.56)]):
            die(pos[0], pos[1], 0.17, 5, c if i < 4 else muted, dotted=i == 4)
    elif key == "no_cuenta":
        die(0.32, 0.32, 0.36, 3, c)
        circle((0.5, 0.5), 0.35, line_width, c)
        line((0.28, 0.72), (0.72, 0.28), line_width, c)
    elif key == "milagro_controlado":
        circle((0.5, 0.45), 0.34, line_width, c)
        die(0.35, 0.3, 0.3, 6, c)
        pygame.draw.arc(layer, muted, pygame.Rect(rect.w * 0.22, rect.h * 0.62, rect.w * 0.56, rect.h * 0.2), math.radians(200), math.radians(340), line_width)
    elif key == "sabotaje":
        die(0.32, 0.32, 0.36, 4, c)
        line((0.22, 0.78), (0.8, 0.2), line_width + 1, c)
        line((0.42, 0.2), (0.5, 0.36), 1, muted)
        line((0.58, 0.64), (0.66, 0.8), 1, muted)
    elif key == "candado":
        rect_line(0.34, 0.45, 0.42, 0.28, line_width, 4, c)
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.42, rect.h * 0.22, rect.w * 0.26, rect.h * 0.34), math.pi, math.tau, line_width)
        line((0.2, 0.34), (0.48, 0.34), 1, muted)
        line((0.2, 0.47), (0.34, 0.47), 1, muted)
    elif key == "robo":
        card(0.55, 0.24, 0.24, 0.36, c, 8)
        line((0.2, 0.7), (0.44, 0.48), line_width, c)
        line((0.44, 0.48), (0.66, 0.58), line_width, c)
        line((0.36, 0.56), (0.48, 0.66), line_width, muted)
    elif key == "intercambio":
        die(0.18, 0.36, 0.24, 2, c)
        die(0.58, 0.36, 0.24, 5, muted)
        line((0.4, 0.36), (0.64, 0.36), line_width, c)
        poly([(0.64, 0.28), (0.78, 0.36), (0.64, 0.44)], 0, c)
        line((0.6, 0.66), (0.36, 0.66), line_width, muted)
        poly([(0.36, 0.58), (0.22, 0.66), (0.36, 0.74)], 0, muted)
    elif key == "mano_pesada":
        die(0.34, 0.42, 0.32, 3, c)
        poly([(0.38, 0.28), (0.62, 0.28), (0.72, 0.42), (0.28, 0.42)], line_width, muted)
        line((0.5, 0.18), (0.5, 0.28), line_width, muted)
    elif key == "presion":
        poly([(0.5, 0.1), (0.86, 0.76), (0.14, 0.76)], line_width, c)
        die(0.38, 0.56, 0.24, 1, muted)
        line((0.28, 0.5), (0.72, 0.5), line_width, c)
        text_mark("!", (0.5, 0.38), 0.24, c)
    elif key == "foco_numerico":
        for i, val in enumerate((1, 2, 3)):
            die(0.18 + i * 0.2, 0.42, 0.16, val, muted)
        text_mark("+3", (0.62, 0.34), 0.16, c)
        line((0.28, 0.72), (0.72, 0.72), line_width, c)
    elif key == "vision_clara":
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.16, rect.h * 0.28, rect.w * 0.68, rect.h * 0.34), 0, math.tau, line_width)
        circle((0.5, 0.45), 0.075, 0, c)
        die(0.54, 0.56, 0.18, 5, muted)
        line((0.26, 0.76), (0.74, 0.76), 1, muted)
    elif key == "ancla":
        die(0.35, 0.24, 0.3, 4, c)
        line((0.5, 0.54), (0.5, 0.78), line_width, c)
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.28, rect.h * 0.58, rect.w * 0.44, rect.h * 0.28), math.radians(20), math.radians(160), line_width)
        line((0.5, 0.78), (0.34, 0.66), line_width, muted)
        line((0.5, 0.78), (0.66, 0.66), line_width, muted)
    elif key == "apertura":
        die(0.33, 0.36, 0.28, 2, muted)
        line((0.24, 0.72), (0.76, 0.28), line_width, c)
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.38, rect.h * 0.2, rect.w * 0.28, rect.h * 0.3), math.radians(190), math.radians(350), line_width)
        line((0.28, 0.28), (0.42, 0.28), line_width, muted)
    elif key == "pulso_controlado":
        die(0.34, 0.34, 0.28, 4, c)
        arrow_arc((0.18, 0.18, 0.64, 0.64), 215, 25, c)
        line((0.24, 0.7), (0.42, 0.7), 1, muted)
        line((0.58, 0.24), (0.76, 0.24), 1, muted)
    elif key == "dado_duplicador":
        die(0.3, 0.34, 0.34, 2, c)
        die(0.43, 0.27, 0.26, 2, muted)
        text_mark("x2", (0.72, 0.66), 0.17, c)
    elif key == "veto_mercado":
        card(0.28, 0.28, 0.32, 0.44, muted, -4)
        line((0.22, 0.76), (0.78, 0.22), line_width + 1, c)
        circle((0.68, 0.36), 0.12, line_width, c)
    elif key == "mesa_fria":
        circle((0.42, 0.5), 0.2, line_width, c)
        text_mark("G+", (0.42, 0.5), 0.13, c)
        line((0.2, 0.74), (0.76, 0.24), line_width + 1, c)
        for pos in [(0.68, 0.34), (0.74, 0.5), (0.62, 0.62)]:
            circle(pos, 0.022, 0, muted)
    elif key == "matematico":
        die(0.43, 0.58, 0.2, 1, muted)
        line((0.28, 0.74), (0.5, 0.22), line_width, c)
        line((0.72, 0.74), (0.5, 0.22), line_width, c)
        circle((0.5, 0.22), 0.045, 0, c)
        pygame.draw.arc(layer, muted, pygame.Rect(rect.w * 0.28, rect.h * 0.42, rect.w * 0.44, rect.h * 0.3), math.radians(200), math.radians(340), 1)
    elif key == "apostador":
        circle((0.44, 0.5), 0.27, line_width, c)
        die(0.35, 0.41, 0.18, 5, muted)
        line((0.66, 0.28), (0.78, 0.18), line_width, c)
        line((0.66, 0.72), (0.78, 0.82), line_width, muted)
    elif key == "defensivo":
        shield(0.42, 0.5, 0.82, c)
        shield(0.58, 0.5, 0.82, muted)
        die(0.41, 0.42, 0.18, 1, c)
    elif key == "estratega":
        for gx in (0.25, 0.5, 0.75):
            line((gx, 0.2), (gx, 0.8), 1, muted)
        for gy in (0.25, 0.5, 0.75):
            line((0.2, gy), (0.8, gy), 1, muted)
        for pos in [(0.25, 0.75), (0.5, 0.5), (0.75, 0.25)]:
            circle(pos, 0.045, 0, c)
        line((0.25, 0.75), (0.5, 0.5), line_width, c)
        line((0.5, 0.5), (0.75, 0.25), line_width, c)
    elif key == "suertudo":
        die(0.35, 0.42, 0.3, 6, muted)
        star(0.5, 0.3, 0.2, 0.08, c, 0)
        for pos in [(0.24, 0.34), (0.72, 0.28), (0.7, 0.68)]:
            circle(pos, 0.025, 0, c)
    elif key == "conservador":
        rect_line(0.22, 0.28, 0.56, 0.44, line_width, 5, c)
        circle((0.5, 0.5), 0.09, line_width, muted)
        die(0.43, 0.56, 0.14, 1, muted)
        line((0.34, 0.34), (0.66, 0.34), 1, muted)
    elif key == "agresivo":
        die(0.62, 0.42, 0.22, 2, muted)
        poly([(0.14, 0.5), (0.58, 0.28), (0.5, 0.5), (0.58, 0.72)], 0, c)
        line((0.5, 0.5), (0.72, 0.5), line_width, c)
    elif key == "caotico":
        circle((0.5, 0.5), 0.34, line_width, muted)
        line((0.72, 0.22), (0.85, 0.1), line_width, C_BG_DEEP)
        die(0.2, 0.24, 0.18, 1, c, rot=-18)
        die(0.58, 0.22, 0.18, 5, c, rot=16)
        die(0.38, 0.58, 0.18, 3, c, rot=28)
    elif key == "coleccionista":
        card(0.24, 0.28, 0.22, 0.34, muted, -15)
        card(0.38, 0.24, 0.22, 0.34, c, 0)
        card(0.52, 0.28, 0.22, 0.34, muted, 15)
        die(0.41, 0.58, 0.18, 1, c)
    elif key == "precavido":
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.18, rect.h * 0.28, rect.w * 0.64, rect.h * 0.34), 0, math.tau, line_width)
        circle((0.5, 0.45), 0.07, 0, c)
        die(0.52, 0.56, 0.18, 4, muted)
        arrow_arc((0.18, 0.18, 0.54, 0.6), 200, 45, muted)
    elif key == "ambicioso":
        for i in range(4):
            pygame.draw.ellipse(layer, c if i == 3 else muted, pygame.Rect(rect.w * (0.26 + i * 0.05), rect.h * (0.7 - i * 0.12), rect.w * 0.28, rect.h * 0.08), 1)
        line((0.68, 0.74), (0.78, 0.22), line_width, c)
        poly([(0.7, 0.26), (0.8, 0.1), (0.86, 0.28)], 0, c)
    elif key == "tecnico":
        for gx in (0.24, 0.42, 0.6, 0.78):
            line((gx, 0.22), (gx, 0.78), 1, faint)
        line((0.18, 0.7), (0.82, 0.7), line_width, c)
        for x in (0.3, 0.42, 0.54, 0.66):
            line((x, 0.66), (x, 0.74), 1, c)
        die(0.48, 0.34, 0.22, 2, c)
        circle((0.32, 0.42), 0.04, 0, muted)
    elif key == "ilusionista":
        line((0.5, 0.16), (0.5, 0.84), 1, muted)
        die(0.2, 0.36, 0.24, 1, c)
        die(0.56, 0.36, 0.24, 6, c)
        circle((0.5, 0.5), 0.34, line_width, faint)
    elif key == "crupier":
        card(0.26, 0.3, 0.24, 0.38, muted, -10)
        card(0.5, 0.26, 0.24, 0.38, c, 8)
        line((0.2, 0.74), (0.82, 0.74), line_width, c)
        circle((0.5, 0.74), 0.045, 0, c)
    elif key == "audaz":
        die(0.28, 0.4, 0.28, 5, muted)
        line((0.34, 0.72), (0.72, 0.28), line_width, c)
        poly([(0.64, 0.24), (0.84, 0.18), (0.74, 0.38)], 0, c)
    elif key == "tesorero":
        for i in range(3):
            pygame.draw.ellipse(layer, c if i == 2 else muted, pygame.Rect(rect.w * (0.26 + i * 0.11), rect.h * (0.58 - i * 0.08), rect.w * 0.28, rect.h * 0.09), 1)
        text_mark("G+", (0.5, 0.42), 0.13, c)
        line((0.28, 0.74), (0.72, 0.74), line_width, muted)
    elif key == "clasica":
        for i, val in enumerate((1, 2, 3, 4, 5)):
            die(0.12 + i * 0.15, 0.42, 0.12, val, c)
    elif key == "dorada":
        circle((0.5, 0.5), 0.34, line_width, c)
        die(0.36, 0.36, 0.28, 5, c)
    elif key == "espejo_evento":
        die(0.18, 0.34, 0.28, 1, c)
        line((0.5, 0.18), (0.5, 0.82), line_width, muted)
        die(0.54, 0.34, 0.28, 6, c)
    elif key == "austera":
        circle((0.48, 0.5), 0.24, line_width, c)
        line((0.28, 0.72), (0.68, 0.32), line_width, c)
        line((0.68, 0.32), (0.82, 0.22), line_width, muted)
    elif key == "caotica":
        die(0.38, 0.38, 0.24, 3, c)
        for pos in [(0.2, 0.32), (0.74, 0.28), (0.28, 0.76), (0.78, 0.68), (0.5, 0.18)]:
            circle(pos, 0.035, 0, muted)
        arrow_arc((0.18, 0.18, 0.64, 0.64), 20, 280, muted)
    elif key == "defensiva":
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.14, rect.h * 0.22, rect.w * 0.72, rect.h * 0.62), math.radians(190), math.radians(350), line_width)
        for i, val in enumerate((1, 3, 5)):
            die(0.28 + i * 0.16, 0.56, 0.14, val, muted)
    elif key == "apuestas":
        circle((0.38, 0.44), 0.22, line_width, c)
        die(0.58, 0.5, 0.18, 6, muted)
        line((0.18, 0.76), (0.82, 0.28), line_width, c)
    elif key == "descuento":
        poly([(0.24, 0.28), (0.62, 0.28), (0.8, 0.46), (0.46, 0.8), (0.24, 0.58)], line_width, c)
        circle((0.36, 0.4), 0.035, 0, c)
        circle((0.5, 0.56), 0.08, line_width, muted)
        line((0.72, 0.28), (0.72, 0.66), line_width, c)
        poly([(0.62, 0.62), (0.72, 0.78), (0.82, 0.62)], 0, c)
    elif key == "recuperacion":
        die(0.36, 0.36, 0.3, 2, c)
        arrow_arc((0.18, 0.18, 0.64, 0.64), 210, 30, c)
        line((0.42, 0.72), (0.62, 0.54), 1, muted)
    elif key in {"escudo_activo"}:
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.18, rect.h * 0.22, rect.w * 0.64, rect.h * 0.54), math.radians(190), math.radians(350), line_width)
        die(0.4, 0.48, 0.2, 2, muted)
    elif key in {"carta_usada"}:
        card(0.32, 0.24, 0.32, 0.46, c, -10)
        line((0.42, 0.58), (0.5, 0.68), line_width, c)
        line((0.5, 0.68), (0.68, 0.42), line_width, c)
    elif key in {"habilidad_usada"}:
        circle((0.5, 0.5), 0.3, line_width, muted)
        line((0.3, 0.72), (0.72, 0.3), line_width, c)
    elif key in {"candado_activo"}:
        rect_line(0.36, 0.46, 0.36, 0.26, line_width, 4, c)
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.42, rect.h * 0.25, rect.w * 0.24, rect.h * 0.3), math.pi, math.tau, line_width)
        line((0.2, 0.38), (0.36, 0.38), 1, muted)
    elif key == "bonus":
        circle((0.5, 0.5), 0.28, line_width, c)
        text_mark("+", (0.5, 0.5), 0.28, c)
    elif key == "penalizacion":
        circle((0.5, 0.5), 0.28, line_width, c)
        text_mark("-", (0.5, 0.5), 0.32, c)
    elif key == "cooldown":
        pygame.draw.arc(layer, c, pygame.Rect(rect.w * 0.2, rect.h * 0.2, rect.w * 0.6, rect.h * 0.6), math.radians(230), math.radians(80), line_width)
        circle((0.5, 0.5), 0.1, 0, muted)
    else:
        circle((0.5, 0.5), 0.24, line_width, c)
        line((0.34, 0.66), (0.66, 0.34), max(1, line_width - 1), muted)

    surface.blit(layer, rect.topleft)


class AnimationManager:
    def __init__(self):
        self.values = {}

    def pulse(self, key, period=1.0, low=0.0, high=1.0):
        value = low + (high - low) * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 1000 * math.tau / period))
        self.values[key] = value
        return value


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add(self, particle):
        self.particles.append(particle)

    def update(self, dt):
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if particle.life > 0]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


class Panel:
    def __init__(self, rect, title=None):
        self.rect = pygame.Rect(rect)
        self.title = title

    def draw(self, surface, font=None, accent=C_BORDER_SUBTLE):
        draw_panel(surface, self.rect, C_BG_PANEL, accent)
        if self.title and font:
            text = font.render(self.title.upper(), True, C_GRAY_MID)
            surface.blit(text, (self.rect.x + 22, self.rect.y + 18))


class Button:
    def __init__(self, rect, text, variant="primary"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.variant = variant
        self.enabled = True
        self.pressed_until = 0

    def handle_event(self, event, logical_pos):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(logical_pos):
            self.pressed_until = pygame.time.get_ticks() + 120
            return True
        return False

    def draw(self, surface, font, mouse_pos, pulse=False):
        hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        pressed = pygame.time.get_ticks() < self.pressed_until
        scale = 0.97 if pressed else (1.02 if hovered else 1.0)
        rect = pygame.Rect(0, 0, int(self.rect.w * scale), int(self.rect.h * scale))
        rect.center = self.rect.center
        if self.variant == "primary":
            fill = C_WHITE_SOFT if self.enabled else C_BG_ELEVATED
            text_color = C_BG_DEEP if self.enabled else C_GRAY_DARK
            border = C_WHITE if hovered else COLORS["platinum"]
            glow_alpha = 50 if hovered else 24
        elif self.variant == "danger":
            fill = C_RED_ERROR if self.enabled else C_BG_ELEVATED
            text_color = C_WHITE_SOFT if self.enabled else C_GRAY_DARK
            border = C_RED_ERROR
            glow_alpha = 26 if hovered else 8
        else:
            fill = C_BG_ELEVATED if self.enabled else (8, 8, 8)
            text_color = C_WHITE_SOFT if self.enabled else (80, 80, 80)
            border = C_BORDER_ACTIVE if hovered and self.enabled else ((36, 36, 36) if not self.enabled else C_BORDER_SUBTLE)
            glow_alpha = 24 if hovered and self.enabled else 0
        if not self.enabled:
            fill = (8, 8, 8)
            text_color = (80, 80, 80)
            border = (36, 36, 36)
            glow_alpha = 0
        if pulse and self.enabled:
            glow_alpha = 35 + int(28 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260)))
            border = C_GOLD
        if glow_alpha:
            draw_glow(surface, rect, C_GOLD if pulse else C_WHITE, glow_alpha, 18, RADIUS["button"])
        draw_soft_shadow(surface, rect, alpha=90, spread=12, radius=RADIUS["button"], y_offset=5)
        pygame.draw.rect(surface, fill, rect, border_radius=RADIUS["button"])
        pygame.draw.rect(surface, border, rect, width=1, border_radius=RADIUS["button"])
        if hovered and self.enabled:
            shine = pygame.Surface(rect.size, pygame.SRCALPHA)
            x = int((pygame.time.get_ticks() / 5) % (rect.w + 80)) - 80
            pygame.draw.polygon(shine, (255, 255, 255, 26), [(x, 0), (x + 46, 0), (x + 18, rect.h), (x - 28, rect.h)])
            surface.blit(shine, rect.topleft)
        text = font.render(self.text.upper(), True, text_color)
        surface.blit(text, text.get_rect(center=rect.center))


class TextField:
    def __init__(self, rect, label, text="", max_len=14):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = text
        self.max_len = max_len
        self.active = False

    def handle_event(self, event, logical_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(logical_pos)
            return
        if not self.active or event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_TAB):
            self.active = False
        elif len(self.text) < self.max_len and event.unicode.isprintable():
            self.text += event.unicode

    def value(self, fallback):
        stripped = self.text.strip()
        return stripped if stripped else fallback

    def draw(self, surface, label_font, text_font):
        label = label_font.render(self.label.upper(), True, C_GRAY_MID)
        surface.blit(label, (self.rect.x, self.rect.y - 22))
        border = COLORS["platinum"] if self.active else C_BORDER_SUBTLE
        if self.active:
            draw_glow(surface, self.rect, C_WHITE, 20, 12, 14)
        pygame.draw.rect(surface, COLORS["black_abs"], self.rect, border_radius=14)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=14)
        text = text_font.render(trim_text(self.text, text_font, self.rect.w - 34), True, C_WHITE_SOFT)
        surface.blit(text, (self.rect.x + 17, self.rect.centery - text.get_height() // 2))
        if self.active and (pygame.time.get_ticks() // 420) % 2 == 0:
            cursor_x = self.rect.x + 19 + text.get_width()
            pygame.draw.line(surface, C_WHITE_SOFT, (cursor_x, self.rect.y + 15), (cursor_x, self.rect.bottom - 15), 1)


class DiceView:
    PIPS = {
        1: [(0.5, 0.5)],
        2: [(0.28, 0.28), (0.72, 0.72)],
        3: [(0.28, 0.28), (0.5, 0.5), (0.72, 0.72)],
        4: [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)],
        5: [(0.28, 0.28), (0.72, 0.28), (0.5, 0.5), (0.28, 0.72), (0.72, 0.72)],
        6: [(0.28, 0.24), (0.72, 0.24), (0.28, 0.5), (0.72, 0.5), (0.28, 0.76), (0.72, 0.76)],
    }

    @staticmethod
    def draw(surface, rect, value, font, selected=False, hovered=False, rolling=False, marks=None, selectable=False):
        rect = pygame.Rect(rect)
        y_offset = -4 if hovered and not selected else 0
        if rolling:
            y_offset += int(math.sin(pygame.time.get_ticks() / 32 + rect.x) * 7)
        draw_rect = rect.move(0, y_offset)
        fill_top = (255, 248, 229) if not selected else (238, 226, 199)
        fill_bottom = (205, 190, 166) if not selected else (171, 159, 139)
        border = C_GOLD if selected or hovered or selectable else (130, 116, 90)
        if selectable:
            pulse = 34 + int(28 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 160)))
            draw_glow(surface, draw_rect, C_WHITE, pulse, 18, RADIUS["dice"])
        elif hovered:
            draw_glow(surface, draw_rect, C_WHITE, 28, 16, RADIUS["dice"])
        if selected:
            draw_glow(surface, draw_rect.inflate(4, 4), COLORS["platinum"], 26, 10, RADIUS["dice"])
        draw_soft_shadow(surface, draw_rect, alpha=185, spread=18, radius=RADIUS["dice"], y_offset=10)
        draw_vertical_gradient(surface, draw_rect, fill_top, fill_bottom, RADIUS["dice"])
        pygame.draw.rect(surface, (255, 255, 255, 80), draw_rect.inflate(-9, -9), width=1, border_radius=RADIUS["dice"] - 5)
        pygame.draw.rect(surface, border, draw_rect, width=2 if selected else 1, border_radius=RADIUS["dice"])
        pygame.draw.rect(surface, (75, 59, 38), draw_rect.inflate(7, 7), width=1, border_radius=RADIUS["dice"] + 3)
        if selected:
            inset = draw_rect.inflate(-8, -8)
            pygame.draw.rect(surface, (255, 255, 255, 72), inset, width=1, border_radius=RADIUS["dice"] - 4)
            corner = 15
            bracket_color = (*C_GOLD, 190)
            selected_layer = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            points = [
                ((10, 12), (10 + corner, 12)), ((10, 12), (10, 12 + corner)),
                ((draw_rect.w - 10, 12), (draw_rect.w - 10 - corner, 12)), ((draw_rect.w - 10, 12), (draw_rect.w - 10, 12 + corner)),
                ((10, draw_rect.h - 12), (10 + corner, draw_rect.h - 12)), ((10, draw_rect.h - 12), (10, draw_rect.h - 12 - corner)),
                ((draw_rect.w - 10, draw_rect.h - 12), (draw_rect.w - 10 - corner, draw_rect.h - 12)), ((draw_rect.w - 10, draw_rect.h - 12), (draw_rect.w - 10, draw_rect.h - 12 - corner)),
            ]
            for start, end in points:
                pygame.draw.line(selected_layer, bracket_color, start, end, 2)
            pygame.draw.rect(selected_layer, (255, 255, 255, 18), selected_layer.get_rect().inflate(-18, -18), border_radius=RADIUS["dice"] - 8)
            surface.blit(selected_layer, draw_rect.topleft)
        pip_radius = max(7, draw_rect.w // 12)
        pip_color = (19, 17, 14)
        for px, py in DiceView.PIPS.get(value, DiceView.PIPS[1]):
            center = (draw_rect.x + int(draw_rect.w * px), draw_rect.y + int(draw_rect.h * py))
            glow = pygame.Surface((pip_radius * 4, pip_radius * 4), pygame.SRCALPHA)
            local = (pip_radius * 2, pip_radius * 2)
            pygame.draw.circle(glow, (255, 255, 255, 42), (local[0] - 2, local[1] - 2), pip_radius + 1)
            pygame.draw.circle(glow, (0, 0, 0, 54), (local[0] + 1, local[1] + 2), pip_radius + 1)
            surface.blit(glow, glow.get_rect(center=center))
            pygame.draw.circle(surface, (0, 0, 0, 42), (center[0] + 1, center[1] + 2), pip_radius + 1)
            pygame.draw.circle(surface, pip_color, center, pip_radius)
            pygame.draw.circle(surface, (40, 34, 26), center, max(1, pip_radius - 2))
            pygame.draw.circle(surface, (112, 94, 68), (center[0] - 1, center[1] - 1), max(1, pip_radius - 4), 1)
        if marks:
            mark_font = pygame.font.SysFont("JetBrains Mono, Consolas, monospace", 12, bold=True)
            mark = mark_font.render("/".join(marks), True, C_GOLD)
            surface.blit(mark, mark.get_rect(center=(draw_rect.centerx, draw_rect.y - 13)))


class CardView:
    ICONS = {
        "ajuste_fino": "+/-",
        "reintento": "R",
        "espejo": "<>",
        "seguro": "S",
        "reciclaje": "O",
        "mano_estable": "=",
        "correccion_minima": "+1",
        "tirada_extra": "+R",
        "copia": "[]",
        "comodin": "W",
        "escudo": "S",
        "escalera_rota": "4-",
        "ultima_oportunidad": "U",
        "dado_dorado": "G",
        "dado_maestro": "M",
        "duplicador": "x2",
        "rescate": "RS",
        "generala_falsa": "G?",
        "no_cuenta": "NO",
        "milagro_controlado": "M",
        "sabotaje": "/",
        "candado": "L",
        "robo": "R",
        "intercambio": "SW",
        "mano_pesada": "-R",
        "presion": "!",
        "foco_numerico": "+3",
        "vision_clara": "VIS",
        "ancla": "A",
        "apertura": "OP",
        "pulso_controlado": "P",
        "dado_duplicador": "D2",
        "veto_mercado": "VM",
        "mesa_fria": "$-",
    }

    SHORT_TEXT = {
        "ajuste_fino": "+/-1 a un dado",
        "reintento": "Repite un dado",
        "espejo": "Invierte dado",
        "seguro": "Piso de 10",
        "reciclaje": "Cambia carta",
        "mano_estable": "Evita cambio",
        "correccion_minima": "Completa escalera",
        "tirada_extra": "Cuarta tirada",
        "copia": "Copia valor",
        "comodin": "Cuenta cualquiera",
        "escudo": "Bloquea ataque",
        "escalera_rota": "Escalera x15",
        "ultima_oportunidad": "Ultimo reroll",
        "dado_dorado": "+5 al puntaje",
        "dado_maestro": "Fija un dado",
        "duplicador": "+50%, max +15",
        "rescate": "Recupera tachada",
        "generala_falsa": "4 iguales x35",
        "no_cuenta": "Repite turno",
        "milagro_controlado": "Asistida natural",
        "sabotaje": "Rival repite",
        "candado": "Bloquea categoria",
        "robo": "Roba carta",
        "intercambio": "Rival repite",
        "mano_pesada": "-1 tirada rival",
        "presion": "Rival declara",
        "foco_numerico": "+3 en numeros",
        "vision_clara": "Mejor categoria",
        "ancla": "Retiene todos",
        "apertura": "Suelta todos",
        "pulso_controlado": "Repite libres",
        "dado_duplicador": "Doble en numeros",
        "veto_mercado": "Rival no compra",
        "mesa_fria": "Rival sin monedas",
    }

    @staticmethod
    def accent(card_key):
        card = CARD_DEFS[card_key]
        if card_key in ATTACK_CARDS:
            return C_RED_ERROR
        if card.tier == "fuerte":
            return C_GOLD
        if card.tier == "media":
            return COLORS["platinum"]
        return C_GRAY_MID

    @staticmethod
    def blit_alpha(surface, source, pos, alpha):
        if alpha < 255:
            source = source.copy()
            source.set_alpha(alpha)
        surface.blit(source, pos)

    @staticmethod
    def draw_cost_chip(surface, center, radius, value, font, accent, active=True, dimmed=False):
        alpha = 255 if active else (185 if dimmed else 105)
        layer = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
        local = (radius + 5, radius + 5)
        fill = C_WHITE_SOFT if active else (24, 24, 24)
        text_color = C_BG_DEEP if active else (C_WHITE_SOFT if dimmed else C_GRAY_MID)
        pygame.draw.circle(layer, (*accent, 34 if active else 14), local, radius + 3)
        pygame.draw.circle(layer, (*fill, alpha), local, radius)
        pygame.draw.circle(layer, (*accent, 190 if active else 74), local, radius, 1)
        pygame.draw.arc(layer, (255, 255, 255, 92 if active else 30), pygame.Rect(local[0] - radius + 4, local[1] - radius + 4, (radius - 4) * 2, (radius - 4) * 2), math.radians(210), math.radians(322), 1)
        rendered = font.render(str(value), True, text_color)
        layer.blit(rendered, rendered.get_rect(center=(local[0], local[1] - 1)))
        surface.blit(layer, layer.get_rect(center=center))

    @classmethod
    def draw_card_art(cls, surface, rect, card_key, accent, active=True, dimmed=False):
        rect = pygame.Rect(rect)
        alpha = 220 if active else (155 if dimmed else 78)
        art = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg = art.get_rect()
        pygame.draw.rect(art, (*accent, 18 if active else 10), bg, border_radius=12)
        pygame.draw.rect(art, (*accent, 112 if active else 52), bg, width=1, border_radius=12)
        pygame.draw.line(art, (255, 255, 255, 34 if active else 16), (8, 6), (bg.right - 8, 6), 1)
        pygame.draw.line(art, (*accent, 74 if active else 32), (8, bg.bottom - 8), (bg.right - 8, bg.bottom - 8), 2)
        if card_key in ATTACK_CARDS:
            for x in range(-rect.h, rect.w, 12):
                pygame.draw.line(art, (139, 30, 30, 16 if active else 8), (x, rect.h), (x + rect.h, 0), 1)
        icon_rect = bg.inflate(-14, -14)
        if min(rect.w, rect.h) < 48:
            icon_rect = bg.inflate(-10, -10)
        draw_geo_icon(art, icon_rect, card_key, accent if active or dimmed else C_GRAY_DARK, alpha, 2)
        surface.blit(art, rect.topleft)

    @classmethod
    def draw_compact(cls, surface, rect, card_key, fonts, enabled, market, cost, discount, dimmed):
        card = CARD_DEFS[card_key]
        accent = cls.accent(card_key)
        active = enabled and not dimmed
        readable = active or dimmed
        text_alpha = 255 if active else (220 if dimmed else 95)
        quiet_alpha = 185 if active else (158 if dimmed else 75)

        if market:
            coin_size = 30
            coin_center = (rect.x + 29, rect.y + 29)
            text_x = rect.x + 56
            art_rect = pygame.Rect(rect.right - 76, rect.y + 15, 58, rect.h - 30)
            name_y = rect.y + 14
            desc_y = rect.y + 40
            tier_y = rect.bottom - 24
            name_fonts = [fonts["label"], fonts["compact_name"], fonts["compact_name_small"], fonts["compact_name_tiny"]]
            desc_font = fonts["compact_desc"]
            tier_font = fonts["compact_tier"]
            text_max = max(72, art_rect.x - text_x - 10)
        else:
            coin_size = 26
            coin_center = (rect.x + 23, rect.centery)
            text_x = rect.x + 52
            art_rect = pygame.Rect(rect.right - 52, rect.y + 15, 38, rect.h - 30)
            name_y = rect.y + 13
            desc_y = rect.y + 34
            tier_y = rect.bottom - 19
            name_fonts = [fonts["compact_name"], fonts["compact_name_small"], fonts["compact_name_tiny"], fonts["compact_name_micro"]]
            desc_font = fonts["compact_desc"]
            tier_font = fonts["compact_tier"]
            text_max = max(70, art_rect.x - text_x - 8)

        cls.draw_cost_chip(surface, coin_center, coin_size // 2, card.cost if cost is None else cost, fonts["label"], accent, active=active, dimmed=dimmed)
        if discount:
            tag = fonts["hint"].render("-1", True, C_GOLD)
            cls.blit_alpha(surface, tag, (coin_center[0] + 17, coin_center[1] - 14), text_alpha)

        name_font, name_value = fit_text(card.name.upper(), name_fonts, text_max)
        name = name_font.render(name_value, True, C_WHITE_SOFT if readable else C_GRAY_MID)
        cls.blit_alpha(surface, name, (text_x, name_y), text_alpha)

        desc_value = trim_text(cls.SHORT_TEXT.get(card_key, card.text), desc_font, text_max)
        desc = desc_font.render(desc_value, True, C_GRAY_LIGHT if readable else C_GRAY_DARK)
        cls.blit_alpha(surface, desc, (text_x, desc_y), quiet_alpha)

        tier_label = "ATAQUE" if card_key in ATTACK_CARDS else card.tier.upper()
        tier = tier_font.render(tier_label, True, accent if readable else C_GRAY_DARK)
        cls.blit_alpha(surface, tier, (text_x, tier_y), quiet_alpha)

        cls.draw_card_art(surface, art_rect, card_key, accent, active=active or dimmed, dimmed=dimmed)

    @classmethod
    def draw(cls, surface, rect, card_key, fonts, enabled=True, compact=False, market=False, cost=None, selected=False, discount=False, mouse_pos=None, dimmed=False):
        rect = pygame.Rect(rect)
        hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
        active = enabled and not dimmed
        lift = -3 if hovered and active and compact else (-6 if hovered and active else 0)
        rect = rect.move(0, lift)
        if not card_key:
            slot = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(slot, (8, 8, 9, 120), slot.get_rect(), border_radius=RADIUS["card"])
            pygame.draw.rect(slot, (*C_BORDER_SUBTLE, 92), slot.get_rect(), width=1, border_radius=RADIUS["card"])
            pygame.draw.line(slot, (*C_BORDER_SUBTLE, 45), (16, rect.h - 13), (rect.w - 16, rect.h - 13), 1)
            icon_rect = pygame.Rect(14, rect.h // 2 - 12, 24, 24)
            pygame.draw.circle(slot, (5, 5, 6), icon_rect.center, 12)
            pygame.draw.circle(slot, (*C_BORDER_SUBTLE, 100), icon_rect.center, 12, 1)
            draw_geo_icon(slot, icon_rect.inflate(-6, -6), "coleccionista", C_GRAY_DARK, 120, 1)
            label = fonts["hint_bold"].render("SLOT LIBRE", True, C_GRAY_DARK)
            detail = fonts["hint"].render("Carta disponible", True, C_GRAY_DARK)
            slot.blit(label, (48, rect.h // 2 - 14))
            slot.blit(detail, (48, rect.h // 2 + 2))
            surface.blit(slot, rect.topleft)
            return
        card = CARD_DEFS[card_key]
        accent = cls.accent(card_key)
        alpha = 255 if active else (205 if dimmed else 88)
        short_card = rect.h < 145
        if hovered and active:
            glow = 28 if compact else 38
            draw_glow(surface, rect, accent if card.tier == "fuerte" or card_key in ATTACK_CARDS else C_WHITE, glow, 14, RADIUS["card"])
        if not compact:
            if card.tier == "fuerte":
                draw_soft_shadow(surface, rect, alpha=190, spread=18, radius=RADIUS["card"], y_offset=10)
            else:
                draw_soft_shadow(surface, rect, alpha=130, spread=14, radius=RADIUS["card"], y_offset=8)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, (*C_BG_PANEL, alpha), layer.get_rect(), border_radius=RADIUS["card"])
        border_alpha = 175 if active else (130 if dimmed else 70)
        pygame.draw.rect(layer, (*accent, border_alpha), layer.get_rect(), width=2 if selected else 1, border_radius=RADIUS["card"])
        pygame.draw.rect(layer, (255, 236, 178, 22 if active else 10), layer.get_rect().inflate(-5, -5), width=1, border_radius=RADIUS["card"] - 4)
        if card_key in ATTACK_CARDS:
            for x in range(-rect.h, rect.w, 14):
                pygame.draw.line(layer, (139, 30, 30, 7 if active else 3), (x, rect.h), (x + rect.h, 0), 1)
        rail_alpha = 118 if active else (72 if dimmed else 40)
        rail_w = max(34, rect.w // 4)
        pygame.draw.line(layer, (*accent, rail_alpha), (18, rect.h - 9), (18 + rail_w, rect.h - 9), 2)
        if not short_card:
            pygame.draw.circle(layer, (*accent, max(28, rail_alpha // 2)), (rect.w - 20, 18), 5, 1)
        highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(max(1, rect.h // 3)):
            pygame.draw.line(highlight, (255, 255, 255, int(16 * (1 - y / max(1, rect.h // 3)))), (0, y), (rect.w, y))
        layer.blit(highlight, (0, 0))
        layer.blit(rounded_mask(rect.size, RADIUS["card"]), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(layer, rect.topleft)

        cost_value = card.cost if cost is None else cost
        if short_card:
            cls.draw_compact(surface, rect, card_key, fonts, enabled, market, cost_value, discount, dimmed)
            return

        coin_size = 30 if not compact else 26
        coin_rect = pygame.Rect(rect.x + 10, rect.y + 10, coin_size, coin_size)
        cls.draw_cost_chip(surface, coin_rect.center, coin_rect.w // 2, cost_value, fonts["label"], accent, active=active, dimmed=dimmed)
        if discount:
            tag = fonts["hint"].render("-1", True, C_GOLD)
            surface.blit(tag, (coin_rect.right + 4, coin_rect.y + 1))

        name_font = fonts["card_title"] if not compact else fonts["hint_bold"]
        name = name_font.render(trim_text(card.name.upper(), name_font, rect.w - 24), True, C_WHITE_SOFT if active else C_GRAY_MID)
        surface.blit(name, (rect.x + 12, rect.y + (52 if not compact else 44)))

        icon_size = 72 if not compact else 42
        icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
        icon_rect.center = (rect.centerx, rect.y + rect.h * (0.50 if not compact else 0.55))
        draw_geo_icon(surface, icon_rect, card_key, accent if active else C_GRAY_DARK, 125 if active else 62, 3 if not compact else 2)

        if not compact:
            text = fonts["hint"].render(trim_text(card.text, fonts["hint"], rect.w - 24), True, C_GRAY_LIGHT if active else C_GRAY_DARK)
            surface.blit(text, (rect.x + 12, rect.bottom - 48))
            tier = fonts["hint_bold"].render(card.tier.upper(), True, accent if active else C_GRAY_DARK)
            surface.blit(tier, (rect.x + 12, rect.bottom - 26))
        else:
            tier = fonts["hint"].render(card.tier.upper(), True, accent if active else C_GRAY_DARK)
            surface.blit(tier, (rect.x + 12, rect.bottom - 24))


class ScoreSheetView:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw_frame(self, surface):
        draw_panel(surface, self.rect, C_BG_PANEL, C_BORDER_SUBTLE, radius=18, alpha=236)


class PlayerStatusPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw_frame(self, surface):
        draw_panel(surface, self.rect, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=238)


class MarketPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw_frame(self, surface):
        draw_panel(surface, self.rect, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=238)


class EventBanner:
    def __init__(self, title="", detail="", color=C_WHITE_SOFT):
        self.title = title
        self.detail = detail
        self.color = color


class Modal:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw_frame(self, surface):
        draw_panel(surface, self.rect, C_BG_ELEVATED, C_BORDER_ACTIVE, radius=20, alpha=244, glow=True)


class Tooltip:
    def __init__(self, text=""):
        self.text = text

    def draw(self, surface, pos, font):
        if not self.text:
            return
        text = font.render(self.text, True, C_WHITE_SOFT)
        rect = text.get_rect()
        rect.topleft = (pos[0] + 14, pos[1] + 14)
        rect.inflate_ip(20, 12)
        pygame.draw.rect(surface, C_BG_DEEP, rect, border_radius=8)
        pygame.draw.rect(surface, C_BORDER_ACTIVE, rect, width=1, border_radius=8)
        surface.blit(text, text.get_rect(center=rect.center))
