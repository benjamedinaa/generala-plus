import math
import os
import random
import socket
import sys
import threading
from dataclasses import dataclass

import pygame

from .audio import SoundManager
from .core.actions import BUY_MARKET_CARD, PASS_BUY, RELEASE_ALL, ROLL_DICE, SCORE_CATEGORY, TOGGLE_HOLD, USE_CARD, Action
from .info_content import CHARACTER_SHORT_TEXT, INFO_TABS, card_detail, character_detail, event_detail, info_items
from .net.pygame_client import PygameOnlineClient
from .net.server import OnlineServer
from .rules import *
from .settings import *
from .version import VERSION
from .visual import (
    AnimationManager,
    CardView,
    DiceView,
    Panel,
    ParticleSystem,
    Button as PremiumButton,
    TextField as PremiumTextField,
    draw_chip,
    draw_geo_icon,
    draw_glow,
    draw_panel as premium_panel,
    draw_premium_coin,
    draw_soft_shadow,
    trim_text as premium_trim_text,
)

CHARACTER_ICONS = {
    "matematico": "+/-",
    "apostador": "!",
    "defensivo": "SH",
    "estratega": "3x3",
    "suertudo": "*",
    "conservador": "SAFE",
    "agresivo": "TRI",
    "caotico": "CHA",
    "coleccionista": "III",
    "precavido": "EYE",
    "ambicioso": "UP",
    "tecnico": "RUL",
}

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    color: tuple
    life: float
    max_life: float
    square: bool = True
    gravity: float = 640
    spin: float = 0
    angle: float = 0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.94
        self.vy = self.vy * 0.94 + self.gravity * dt
        self.angle += self.spin * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * self.life / self.max_life)))
        size = max(2, int(self.size))
        layer = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        center = (size * 2, size * 2)
        if self.square:
            rect = pygame.Rect(0, 0, size, size)
            rect.center = center
            pygame.draw.rect(layer, (*self.color, alpha), rect, border_radius=1)
            layer = pygame.transform.rotate(layer, self.angle)
        else:
            pygame.draw.circle(layer, (*self.color, alpha), center, size)
        surface.blit(layer, layer.get_rect(center=(self.x, self.y)))


@dataclass
class AmbientParticle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    phase: float
    speed: float

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0 or self.x > SCREEN_W:
            self.vx *= -1
        if self.y < 0 or self.y > SCREEN_H:
            self.vy *= -1

    def draw(self, surface, time_value):
        alpha = int(18 + 22 * (0.5 + 0.5 * math.sin(time_value * self.speed + self.phase)))
        radius = max(1, int(self.radius))
        layer = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(layer, (255, 255, 255, alpha), (radius + 2, radius + 2), radius)
        surface.blit(layer, (int(self.x) - radius - 2, int(self.y) - radius - 2))


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    color: tuple
    life: float = 1.0
    max_life: float = 1.0
    vy: float = -34
    size: float = 1.0

    def update(self, dt):
        self.y += self.vy * dt
        self.vy *= 0.96
        self.life -= dt

    def draw(self, surface, font):
        if self.life <= 0:
            return
        progress = max(0, min(1, self.life / self.max_life))
        alpha = int(255 * min(1, progress * 1.55))
        lift = int((1 - progress) * 14)
        text = font.render(self.text, True, self.color)
        if self.size != 1.0:
            text = pygame.transform.smoothscale(
                text,
                (max(1, int(text.get_width() * self.size)), max(1, int(text.get_height() * self.size))),
            )
        layer = pygame.Surface((text.get_width() + 44, text.get_height() + 26), pygame.SRCALPHA)
        bg = pygame.Rect(0, 0, layer.get_width(), layer.get_height())
        pygame.draw.rect(layer, (*self.color, int(30 * progress)), bg.inflate(10, 8), border_radius=18)
        pygame.draw.rect(layer, (3, 3, 4, int(190 * progress)), bg, border_radius=16)
        pygame.draw.rect(layer, (*self.color, int(210 * progress)), bg, width=1, border_radius=16)
        pygame.draw.line(layer, (*self.color, int(180 * progress)), (14, bg.bottom - 7), (bg.right - 14, bg.bottom - 7), 2)
        layer.blit(text, text.get_rect(center=bg.center))
        layer.set_alpha(alpha)
        surface.blit(layer, layer.get_rect(center=(self.x, self.y - lift)))


@dataclass
class CardFlight:
    card_key: str
    start: pygame.Rect
    end: pygame.Rect
    life: float = 0.72
    max_life: float = 0.72
    delay: float = 0.0
    spin: float = 0.0
    glow: bool = True

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        self.life -= dt

    @property
    def done(self):
        return self.life <= 0

    def draw(self, surface, fonts, mouse_pos):
        if self.delay > 0 or self.done:
            return
        raw = 1 - max(0, min(1, self.life / self.max_life))
        t = 1 - (1 - raw) ** 3
        cx = self.start.centerx + (self.end.centerx - self.start.centerx) * t
        cy = self.start.centery + (self.end.centery - self.start.centery) * t - math.sin(t * math.pi) * 42
        w = self.start.w + (self.end.w - self.start.w) * t
        h = self.start.h + (self.end.h - self.start.h) * t
        rect = pygame.Rect(0, 0, max(60, int(w)), max(44, int(h)))
        rect.center = (int(cx), int(cy))
        layer = pygame.Surface(rect.inflate(42, 42).size, pygame.SRCALPHA)
        local_rect = pygame.Rect(21, 21, rect.w, rect.h)
        if self.glow:
            accent = CardView.accent(self.card_key)
            pygame.draw.rect(layer, (*accent, int(58 * (1 - abs(t - 0.55)))), local_rect.inflate(24, 18), border_radius=22)
        CardView.draw(layer, local_rect, self.card_key, fonts, enabled=True, compact=True, market=True, mouse_pos=None)
        if self.spin:
            layer = pygame.transform.rotate(layer, math.sin(t * math.pi) * self.spin)
        surface.blit(layer, layer.get_rect(center=rect.center))


@dataclass
class CoinFlight:
    start: tuple
    end: tuple
    accent: tuple = C_GOLD
    life: float = 0.66
    max_life: float = 0.66
    delay: float = 0.0
    radius: int = 7

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        self.life -= dt

    @property
    def done(self):
        return self.life <= 0

    def draw(self, surface):
        if self.delay > 0 or self.done:
            return
        raw = 1 - max(0, min(1, self.life / self.max_life))
        t = 1 - (1 - raw) ** 3
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t - math.sin(t * math.pi) * 34
        alpha = int(255 * (1 - max(0, raw - 0.82) / 0.18))
        draw_premium_coin(surface, (int(x), int(y)), self.radius, filled=True, alpha=alpha, accent=self.accent)


@dataclass
class RoundTransition:
    title: str
    detail: str
    color: tuple
    life: float = 1.05
    max_life: float = 1.05

    def update(self, dt):
        self.life -= dt

    @property
    def done(self):
        return self.life <= 0

    def draw(self, surface, title_font, detail_font):
        if self.done:
            return
        raw = 1 - max(0, min(1, self.life / self.max_life))
        intro = min(1, raw / 0.25)
        outro = min(1, self.life / 0.25)
        alpha = int(180 * min(intro, outro))
        sweep_x = int(-SCREEN_W * 0.15 + SCREEN_W * 1.3 * raw)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, alpha), (0, 0, SCREEN_W, SCREEN_H))
        for offset in (-46, 0, 46):
            pygame.draw.line(overlay, (*self.color, int(82 * min(intro, outro))), (sweep_x + offset, 76), (sweep_x + offset + 210, SCREEN_H - 20), 2)
        panel = pygame.Rect(0, 0, 560, 118)
        panel.center = (SCREEN_W // 2, 152)
        pygame.draw.rect(overlay, (5, 5, 6, int(220 * min(intro, outro))), panel, border_radius=22)
        pygame.draw.rect(overlay, (*self.color, int(185 * min(intro, outro))), panel, width=1, border_radius=22)
        title = title_font.render(self.title, True, C_WHITE_SOFT)
        detail = detail_font.render(self.detail, True, C_GRAY_LIGHT)
        title.set_alpha(int(255 * min(intro, outro)))
        detail.set_alpha(int(210 * min(intro, outro)))
        overlay.blit(title, title.get_rect(center=(panel.centerx, panel.y + 42)))
        overlay.blit(detail, detail.get_rect(center=(panel.centerx, panel.y + 77)))
        surface.blit(overlay, (0, 0))


class Button:
    def __init__(self, rect, text, variant="primary"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.variant = variant
        self.enabled = True

    def handle_event(self, event, logical_pos):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(logical_pos)
        return False

    def draw(self, surface, font, mouse_pos, pulse=False):
        hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        if self.enabled and self.variant == "secondary":
            bg = C_BG_ELEVATED if hovered else C_BG_PANEL
            fg = C_WHITE if hovered else C_GRAY_LIGHT
            border = C_BORDER_ACTIVE if hovered else C_BORDER_SUBTLE
            glow_alpha = 12 if hovered else 0
        elif self.enabled:
            bg = (232, 232, 232) if hovered else C_WHITE
            fg = C_BG_DEEP
            border = None
            glow_alpha = 50 if hovered else 30
        else:
            bg = C_BG_PANEL if self.variant == "secondary" else C_BG_ELEVATED
            fg = C_GRAY_DARK
            border = C_BORDER_SUBTLE
            glow_alpha = 0

        if pulse:
            glow_alpha = 35 + int(25 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 240)))
        if glow_alpha:
            draw_glow_rect(surface, self.rect, C_WHITE, glow_alpha, 18)
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        if border:
            pygame.draw.rect(surface, border, self.rect, width=1, border_radius=8)
        text = font.render(self.text, True, fg)
        surface.blit(text, text.get_rect(center=self.rect.center))


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
        surface.blit(label, (self.rect.x, self.rect.y - 24))
        border = C_WHITE if self.active else C_BORDER_ACTIVE
        pygame.draw.rect(surface, C_BG_PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=8)
        text = text_font.render(trim_text(self.text, text_font, self.rect.w - 30), True, C_WHITE_SOFT)
        surface.blit(text, (self.rect.x + 15, self.rect.centery - text.get_height() // 2))


Button = PremiumButton
TextField = PremiumTextField


class Generala:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("GENERALA")

        self.fullscreen = os.environ.get("SDL_VIDEODRIVER", "").lower() != "dummy"
        self.screen = None
        self.last_window_size = (WINDOW_W, WINDOW_H)
        self.scale = 1
        self.offset = (0, 0)
        self.draw_size = (SCREEN_W, SCREEN_H)
        self.configure_screen()

        self.canvas = pygame.Surface((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        self.font_display = pygame.font.SysFont("Space Grotesk, Sohne, Neue Haas Grotesk, Arial", 76, bold=True)
        self.font_brand = pygame.font.SysFont("Space Grotesk, Sohne, Neue Haas Grotesk, Arial", 88, bold=True)
        self.font_turn = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 42, bold=True)
        self.font_score = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 28, bold=True)
        self.font_total = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 42, bold=True)
        self.font_sheet_score = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 15, bold=True)
        self.font_sheet_total = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 22, bold=True)
        self.font_sheet_label = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 10)
        self.font_sheet_label_bold = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 10, bold=True)
        self.font_dice = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 58, bold=True)
        self.font_body = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 19)
        self.font_body_bold = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 19, bold=True)
        self.font_label = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 13, bold=True)
        self.font_hint = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 11)
        self.font_hint_bold = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 11, bold=True)
        self.font_button = pygame.font.SysFont("Space Grotesk, Inter, Arial", 20, bold=True)
        self.font_card_title = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 15, bold=True)
        self.font_card_icon = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 34, bold=True)
        self.font_card_compact_name = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 11, bold=True)
        self.font_card_compact_name_small = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 10, bold=True)
        self.font_card_compact_name_tiny = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 9, bold=True)
        self.font_card_compact_name_micro = pygame.font.SysFont("Inter, SF Pro Display, Helvetica Neue, Arial", 8, bold=True)
        self.font_card_compact_desc = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 9)
        self.font_card_compact_tier = pygame.font.SysFont("IBM Plex Mono, JetBrains Mono, Consolas, monospace", 8, bold=True)
        self.font_card_compact_icon = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 20, bold=True)
        self.font_card_compact_icon_small = pygame.font.SysFont("Space Grotesk, DIN Condensed, Arial", 16, bold=True)
        self.font_mono = pygame.font.SysFont("JetBrains Mono, IBM Plex Mono, Consolas, monospace", 14)
        self.card_fonts = {
            "label": self.font_label,
            "hint": self.font_hint,
            "hint_bold": self.font_hint_bold,
            "body_bold": self.font_body_bold,
            "card_title": self.font_card_title,
            "card_icon": self.font_card_icon,
            "compact_name": self.font_card_compact_name,
            "compact_name_small": self.font_card_compact_name_small,
            "compact_name_tiny": self.font_card_compact_name_tiny,
            "compact_name_micro": self.font_card_compact_name_micro,
            "compact_desc": self.font_card_compact_desc,
            "compact_tier": self.font_card_compact_tier,
            "compact_icon": self.font_card_compact_icon,
            "compact_icon_small": self.font_card_compact_icon_small,
        }

        self.field_1 = TextField((380, 286, 520, 48), "Jugador 1", "Jugador 1")
        self.field_2 = TextField((380, 358, 520, 48), "Jugador 2", "Jugador 2")
        self.online_name_field = TextField((380, 286, 520, 48), "Tu nombre", "Jugador 1")
        self.online_ip_field = TextField((380, 358, 520, 48), "IP del host", "127.0.0.1", max_len=24)
        self.fields = [self.field_1, self.field_2]

        self.roll_button = Button((500, 340, 280, 56), "TIRAR DADOS")
        self.release_button = Button((397, 412, 150, 42), "SOLTAR", "secondary")
        self.start_button = Button((380, 570, 250, 58), "LOCAL")
        self.online_button = Button((650, 570, 250, 58), "ONLINE", "secondary")
        self.online_host_button = Button((380, 430, 250, 52), "HOSTEAR")
        self.online_join_button = Button((650, 430, 250, 52), "UNIRSE", "secondary")
        self.online_back_button = Button((380, 592, 520, 44), "VOLVER", "secondary")
        self.restart_button = Button((SCREEN_W // 2 - 130, 620, 260, BUTTON_H), "NUEVA PARTIDA")
        self.continue_button = Button((SCREEN_W // 2 - 120, 408, 240, 50), "CONTINUAR")
        self.pause_resume_button = Button((470, 272, 340, 48), "CONTINUAR")
        self.pause_info_button = Button((470, 334, 340, 44), "INFORMACION", "secondary")
        self.pause_settings_button = Button((470, 390, 340, 44), "SONIDO", "secondary")
        self.pause_menu_button = Button((470, 446, 340, 44), "SALIR AL MENU", "secondary")
        self.pause_quit_button = Button((470, 502, 340, 44), "CERRAR JUEGO", "danger")
        self.pause_sfx_down_button = Button((468, 374, 48, 36), "-", "secondary")
        self.pause_sfx_up_button = Button((734, 374, 48, 36), "+", "secondary")
        self.pause_music_down_button = Button((468, 426, 48, 36), "-", "secondary")
        self.pause_music_up_button = Button((734, 426, 48, 36), "+", "secondary")
        self.pause_mute_button = Button((526, 478, 256, 38), "MUTE", "secondary")
        self.mode_button = Button((380, 430, 520, 42), "MODO PLUS", "secondary")
        self.char_buttons = [
            Button((380, 484, 250, 62), "P1 PERSONAJE", "secondary"),
            Button((650, 484, 250, 62), "P2 PERSONAJE", "secondary"),
        ]
        self.ability_button = Button((565, 412, 150, 42), "HABILIDAD", "secondary")
        self.event_button = Button((733, 412, 150, 42), "EVENTO", "secondary")
        self.pass_button = Button((1000, 646, 220, 38), "PASAR", "secondary")
        self.info_tab = "PLUS"
        self.info_tab_rects = {}
        self.info_scroll = {tab: 0 for tab in INFO_TABS}

        self.mouse_pos = (0, 0)
        self.state = "start"
        self.paused = False
        self.show_help = False
        self.show_sound_settings = False
        self.online_client = None
        self.online_server = None
        self.online_server_thread = None
        self.online_message = "Hostea una mesa o unite por IP."
        self.online_pending_card = None
        self.online_selected_die = None
        self.plus_mode = True
        self.selected_characters = ["matematico", "estratega"]
        self.players = []
        self.turn = 0
        self.dice = [1, 2, 3, 4, 5]
        self.held = [False] * DICE_COUNT
        self.rolls = 0
        self.max_rolls_current = MAX_ROLLS
        self.rolling = False
        self.roll_timer = 0
        self.roll_tick = 0
        self.phase = "turn"
        self.message = "Tira los dados para empezar el turno."
        self.banner = None
        self.deck = []
        self.market = []
        self.discard = []
        self.active_event = None
        self.active_event_round = 0
        self.golden_bonus_used_round = 0
        self.discount_buyers = set()
        self.round_scores = {}
        self.card_used_this_turn = False
        self.ability_used_this_turn = False
        self.turn_assisted = False
        self.no_coins_this_turn = False
        self.pending_action = None
        self.pending_turn_attack = None
        self.pending_card_index = None
        self.copy_source_index = None
        self.wildcard_indexes = set()
        self.golden_indexes = set()
        self.duplicator_indexes = set()
        self.score_overrides = {}
        self.score_multiplier = False
        self.force_natural_score = False
        self.declarations = []
        self.ambitious_bonus = False
        self.event_action_used = False
        self.event_caos_done = False
        self.turn_missions = set()
        self.chaotic_card_key = None
        self.hand_rect_cache = []
        self.market_rect_cache = []
        self.animations = AnimationManager()
        self.particle_system = ParticleSystem()
        self.particles = []
        self.floaters = []
        self.card_flights = []
        self.coin_flights = []
        self.round_transition = None
        self.buy_transition_timer = 0
        self.buy_transition_pending = False
        self.ambient = self.create_ambient_particles()
        self.table_texture = self.create_table_texture()
        self.noise = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.scanlines = self.create_scanlines()
        self.vignette = self.create_vignette()
        self.noise_frame = 0
        self.rebuild_noise()
        self.sound = SoundManager()
        self.sound.start_music()

    def configure_screen(self):
        try:
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode(self.last_window_size, pygame.RESIZABLE)
        except pygame.error:
            self.fullscreen = False
            self.screen = pygame.display.set_mode(self.last_window_size, pygame.RESIZABLE)
        self.recalculate_scale()

    def recalculate_scale(self):
        width, height = self.screen.get_size()
        self.scale = max(0.1, min(width / SCREEN_W, height / SCREEN_H))
        draw_w = int(SCREEN_W * self.scale)
        draw_h = int(SCREEN_H * self.scale)
        self.draw_size = (draw_w, draw_h)
        self.offset = ((width - draw_w) // 2, (height - draw_h) // 2)

    def toggle_fullscreen(self):
        if not self.fullscreen:
            self.last_window_size = self.screen.get_size()
        self.fullscreen = not self.fullscreen
        self.configure_screen()

    def logical_pos(self, pos):
        return ((pos[0] - self.offset[0]) / self.scale, (pos[1] - self.offset[1]) / self.scale)

    def create_ambient_particles(self):
        return [
            AmbientParticle(
                random.randint(0, SCREEN_W),
                random.randint(0, SCREEN_H),
                random.uniform(-9, 9),
                random.uniform(-9, 9),
                random.uniform(0.8, 2.2),
                random.random() * math.tau,
                random.uniform(0.35, 1.25),
            )
            for _ in range(34)
        ]

    def create_scanlines(self):
        layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(layer, (0, 0, 0, 18), (0, y), (SCREEN_W, y))
        for x in range(-SCREEN_H, SCREEN_W, 34):
            pygame.draw.line(layer, (255, 255, 255, 4), (x, SCREEN_H), (x + SCREEN_H, 0), 1)
        return layer

    def create_table_texture(self):
        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        center = (SCREEN_W // 2, int(SCREEN_H * 0.54))
        max_dist = math.hypot(SCREEN_W // 2, SCREEN_H // 2)
        for y in range(SCREEN_H):
            for x in range(0, SCREEN_W, 4):
                dx = x - center[0]
                dy = y - center[1]
                t = min(1, math.hypot(dx, dy) / max_dist)
                vertical = min(1, max(0, (y - 64) / (SCREEN_H - 64)))
                felt = interpolate((16, 30, 22), (8, 12, 10), vertical * 0.45)
                base = interpolate(felt, C_BG_DEEP, t * 0.38)
                surface.fill(base, pygame.Rect(x, y, 4, 1))
        felt = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 3):
            alpha = 4 if y % 2 == 0 else 2
            pygame.draw.line(felt, (255, 255, 255, alpha), (0, y), (SCREEN_W, y))
        surface.blit(felt, (0, 0))
        return surface

    def create_vignette(self):
        small_w, small_h = 320, 180
        small = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
        cx, cy = small_w / 2, small_h / 2
        max_dist = math.hypot(cx, cy)
        for y in range(small_h):
            for x in range(small_w):
                dx = (x - cx) / cx
                dy = (y - cy) / cy
                dist = min(1, math.hypot(dx, dy) / 1.18)
                alpha = int(max(0, (dist - 0.42) / 0.58) ** 2 * 112)
                small.set_at((x, y), (0, 0, 0, alpha))
        return pygame.transform.smoothscale(small, (SCREEN_W, SCREEN_H))

    def rebuild_noise(self):
        self.noise.fill((0, 0, 0, 0))
        for _ in range(3100):
            x = random.randrange(0, SCREEN_W)
            y = random.randrange(0, SCREEN_H)
            alpha = random.randrange(4, 14)
            self.noise.set_at((x, y), (255, 255, 255, alpha))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            self.mouse_pos = self.logical_pos(pygame.mouse.get_pos())
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.last_window_size = (max(800, event.w), max(450, event.h))
            self.configure_screen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            self.show_help = not self.show_help
            self.sound.play("ui_click")
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "start":
                pygame.quit()
                sys.exit()
            if self.state == "online_setup":
                self.state = "start"
                return
            if self.state == "game":
                self.paused = not self.paused
                self.show_sound_settings = False
                self.sound.play("pause_open" if self.paused else "pause_close")
            if self.state == "online_game":
                self.state = "online_setup"
                self.close_online()
            return

        if self.paused or self.show_help:
            if self.show_help and event.type == pygame.MOUSEWHEEL:
                self.info_scroll[self.info_tab] = max(0, self.info_scroll.get(self.info_tab, 0) - event.y * 38)
                return
            if self.show_help and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.event_pos(event)
                for tab, rect in self.info_tab_rects.items():
                    if rect.collidepoint(pos):
                        self.info_tab = tab
                        self.info_scroll.setdefault(tab, 0)
                        self.sound.play("ui_click")
                        return
            if self.paused and not self.show_help and self.handle_pause_event(event):
                return
            if self.continue_button.handle_event(event, self.event_pos(event)):
                self.paused = False
                self.show_help = False
            return

        pos = self.event_pos(event)
        self.update_buttons()

        if self.state == "start":
            for field in self.fields:
                field.handle_event(event, pos)
            if self.mode_button.handle_event(event, pos):
                self.plus_mode = not self.plus_mode
                self.mode_button.text = "MODO PLUS" if self.plus_mode else "MODO CLASICO"
                return
            if self.plus_mode:
                for index, button in enumerate(self.char_buttons):
                    if button.handle_event(event, pos):
                        self.cycle_character(index)
                        return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.start_game()
            if self.start_button.handle_event(event, pos):
                self.start_game()
            if self.online_button.handle_event(event, pos):
                self.state = "online_setup"
                self.online_message = "Hostea una mesa o unite por IP."
            return

        if self.state == "online_setup":
            self.online_name_field.handle_event(event, pos)
            self.online_ip_field.handle_event(event, pos)
            if self.online_host_button.handle_event(event, pos):
                self.start_online_host_and_join()
            if self.online_join_button.handle_event(event, pos):
                self.start_online_join()
            if self.online_back_button.handle_event(event, pos):
                self.state = "start"
            return

        if self.state == "online_game":
            self.handle_online_game_event(event, pos)
            return

        if self.state == "game":
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 3
                and self.phase == "turn"
                and not self.rolling
                and not self.pending_action
                and self.rolls > 0
            ):
                if any(self.held) and any(self.die_rect(index).inflate(16, 16).collidepoint(pos) for index in range(DICE_COUNT)):
                    self.release_all()
                    return
            if self.plus_mode and self.handle_plus_event(event, pos):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.rolling:
                if self.rolls > 0 and self.toggle_die_at(pos):
                    return
                category = self.category_at(pos)
                if category:
                    self.score_category(category)
                    return
            if event.type == pygame.KEYDOWN and not self.rolling:
                if event.key == pygame.K_SPACE:
                    self.roll_dice()
                elif event.key == pygame.K_l:
                    self.release_all()
                elif self.rolls > 0 and pygame.K_1 <= event.key <= pygame.K_5:
                    self.toggle_hold(event.key - pygame.K_1)
            if self.roll_button.handle_event(event, pos):
                self.roll_dice()
            if self.release_button.handle_event(event, pos):
                self.release_all()
            return

        if self.state == "end":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            if self.restart_button.handle_event(event, pos):
                self.reset()

    def event_pos(self, event):
        if hasattr(event, "pos"):
            return self.logical_pos(event.pos)
        return self.mouse_pos

    def update_buttons(self):
        self.roll_button.enabled = (
            self.state == "game"
            and not self.rolling
            and self.phase == "turn"
            and self.rolls < self.max_rolls_current
            and not all(self.held)
        )
        self.release_button.enabled = self.state == "game" and self.phase == "turn" and any(self.held) and not self.rolling
        self.roll_button.text = "ULTIMO TIRO" if self.rolls == self.max_rolls_current - 1 else "TIRAR DADOS"
        if self.plus_mode:
            self.ability_button.enabled = self.can_use_active_ability()
            self.event_button.enabled = self.can_use_event_action()
            self.pass_button.enabled = self.phase == "buy" and not self.buy_transition_pending

    def handle_pause_event(self, event):
        pos = self.event_pos(event)
        if self.pause_resume_button.handle_event(event, pos):
            self.paused = False
            self.show_sound_settings = False
            self.sound.play("pause_close")
            return True
        if self.show_sound_settings:
            if self.pause_settings_button.handle_event(event, pos):
                self.show_sound_settings = False
                self.sound.play("ui_back")
                return True
            if self.pause_sfx_down_button.handle_event(event, pos):
                self.sound.set_sfx_volume(self.sound.sfx_volume - 0.1)
                self.sound.play("ui_click")
                return True
            if self.pause_sfx_up_button.handle_event(event, pos):
                self.sound.set_sfx_volume(self.sound.sfx_volume + 0.1)
                self.sound.play("ui_click")
                return True
            if self.pause_music_down_button.handle_event(event, pos):
                self.sound.set_music_volume(self.sound.music_volume - 0.1)
                self.sound.play("ui_click")
                return True
            if self.pause_music_up_button.handle_event(event, pos):
                self.sound.set_music_volume(self.sound.music_volume + 0.1)
                self.sound.play("ui_click")
                return True
            if self.pause_mute_button.handle_event(event, pos):
                self.sound.toggle_enabled()
                return True
            return False
        if self.pause_info_button.handle_event(event, pos):
            self.show_help = True
            self.sound.play("ui_click")
            return True
        if self.pause_menu_button.handle_event(event, pos):
            self.sound.play("ui_back")
            self.reset()
            return True
        if self.pause_quit_button.handle_event(event, pos):
            self.sound.play("ui_back")
            pygame.quit()
            sys.exit()
        if self.pause_settings_button.handle_event(event, pos):
            self.show_sound_settings = not self.show_sound_settings
            self.sound.play("ui_click")
            return True
        return False

    def start_game(self):
        self.players = [
            Player(self.field_1.value("Jugador 1"), character_key=self.selected_characters[0]),
            Player(self.field_2.value("Jugador 2"), character_key=self.selected_characters[1]),
        ]
        if self.plus_mode:
            self.setup_plus_game()
        self.state = "game"
        self.turn = 0
        self.prepare_turn()
        title = "GENERALA PLUS" if self.plus_mode else "GENERALA"
        detail = "Dados primero. Cartas con maximo una por turno." if self.plus_mode else "Hasta 3 tiradas. Una categoria por turno."
        self.sound.play("event")
        self.show_banner(title, detail, C_WHITE)

    def reset(self):
        self.close_online()
        self.state = "start"
        self.paused = False
        self.show_help = False
        self.show_sound_settings = False
        self.players = []
        self.turn = 0
        self.rolls = 0
        self.phase = "turn"
        self.rolling = False
        self.particles.clear()
        self.floaters.clear()
        self.card_flights.clear()
        self.coin_flights.clear()
        self.round_transition = None
        self.buy_transition_timer = 0
        self.buy_transition_pending = False
        self.banner = None
        self.deck = []
        self.market = []
        self.discard = []
        self.active_event = None
        self.active_event_round = 0
        self.round_scores = {}

    def close_online(self):
        if self.online_client:
            self.online_client.close()
        if self.online_server:
            self.online_server.stop()
        self.online_client = None
        self.online_server = None
        self.online_server_thread = None
        self.online_pending_card = None
        self.online_selected_die = None

    def start_online_host_and_join(self):
        self.close_online()
        self.online_message = "Abriendo servidor local..."
        self.online_server = OnlineServer("0.0.0.0", 8765)
        self.online_server_thread = threading.Thread(target=self.online_server.serve_forever, daemon=True)
        self.online_server_thread.start()
        self.start_online_join(host_override="127.0.0.1")

    def start_online_join(self, host_override=None):
        host = host_override or self.online_ip_field.value("127.0.0.1")
        name = self.online_name_field.value("Jugador")
        self.online_client = PygameOnlineClient(host, 8765, name)
        try:
            self.online_client.connect()
        except OSError as exc:
            self.online_message = f"No pude conectar: {exc}"
            self.online_client = None
            return
        self.online_message = "Conectando con la mesa..."
        self.state = "online_game"

    def online_snapshot(self):
        if not self.online_client:
            return {"state": None, "player_index": None, "info": self.online_message, "error": "", "connected": False}
        return self.online_client.snapshot()

    def send_online_action(self, kind, payload=None):
        snap = self.online_snapshot()
        player_index = snap.get("player_index")
        if self.online_client and player_index is not None:
            self.online_client.send_action(Action(kind, player_index, payload or {}))

    def handle_online_game_event(self, event, pos):
        snap = self.online_snapshot()
        state = snap.get("state")
        player_index = snap.get("player_index")
        if not state or player_index is None:
            return
        my_turn = state["active_player_index"] == player_index
        if event.type == pygame.KEYDOWN:
            if self.online_pending_card and self.online_pending_card.get("type") == "value" and pygame.K_1 <= event.key <= pygame.K_6:
                value = str(event.key - pygame.K_0)
                args = [str(self.online_selected_die + 1), value]
                self.send_online_action(USE_CARD, {"hand_index": self.online_pending_card["hand_index"], "args": args})
                self.online_pending_card = None
                self.online_selected_die = None
                return
            if my_turn and state["phase"] == "turn":
                if event.key == pygame.K_SPACE:
                    self.send_online_action(ROLL_DICE)
                elif event.key == pygame.K_l:
                    self.send_online_action(RELEASE_ALL)
                elif state["rolls"] > 0 and pygame.K_1 <= event.key <= pygame.K_5:
                    self.send_online_action(TOGGLE_HOLD, {"index": event.key - pygame.K_1})
            return
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        if self.online_pending_card and state["phase"] == "turn" and state["rolls"] > 0:
            for index in range(DICE_COUNT):
                if self.die_rect(index).inflate(16, 16).collidepoint(pos):
                    self.finish_online_card_selection(index, event.button)
                    return
        if not my_turn:
            return
        if state["phase"] == "turn":
            if self.roll_button.handle_event(event, pos):
                self.send_online_action(ROLL_DICE)
                return
            if self.release_button.handle_event(event, pos):
                self.send_online_action(RELEASE_ALL)
                return
            if state["rolls"] > 0:
                for index in range(DICE_COUNT):
                    if self.die_rect(index).inflate(16, 16).collidepoint(pos):
                        if event.button == 3:
                            self.send_online_action(RELEASE_ALL)
                        elif event.button == 1:
                            self.send_online_action(TOGGLE_HOLD, {"index": index})
                        return
                category = self.online_category_at(pos, state)
                if category:
                    self.send_online_action(SCORE_CATEGORY, {"category": category})
                    return
                for index, rect in self.online_hand_rects(state).items():
                    if rect.collidepoint(pos):
                        self.start_online_card_use(index, state["players"][player_index]["hand"][index])
                        return
        elif state["phase"] == "buy":
            if self.pass_button.handle_event(event, pos):
                self.send_online_action(PASS_BUY)
                return
            for index, rect in self.online_market_rects(state).items():
                if rect.collidepoint(pos):
                    self.send_online_action(BUY_MARKET_CARD, {"index": index})
                    return

    def start_online_card_use(self, hand_index, card_key):
        no_arg = {"tirada_extra", "duplicador", "seguro", "escalera_rota", "generala_falsa", "milagro_controlado", "foco_numerico", "ancla", "apertura", "pulso_controlado", "ultima_oportunidad"}
        one_die = {"reintento", "espejo", "comodin", "dado_dorado", "dado_duplicador"}
        if card_key in no_arg:
            self.send_online_action(USE_CARD, {"hand_index": hand_index, "args": []})
            return
        if card_key == "ajuste_fino":
            self.online_pending_card = {"hand_index": hand_index, "card_key": card_key, "type": "adjust"}
            return
        if card_key == "dado_maestro":
            self.online_pending_card = {"hand_index": hand_index, "card_key": card_key, "type": "master"}
            return
        if card_key == "copia":
            self.online_pending_card = {"hand_index": hand_index, "card_key": card_key, "type": "copy_source"}
            return
        if card_key in one_die:
            self.online_pending_card = {"hand_index": hand_index, "card_key": card_key, "type": "one_die"}
            return
        self.online_message = "Esa carta todavia no esta disponible en online visual."

    def finish_online_card_selection(self, die_index, button):
        pending = self.online_pending_card
        if not pending:
            return
        if pending["type"] == "adjust":
            direction = "-" if button == 3 else "+"
            self.send_online_action(USE_CARD, {"hand_index": pending["hand_index"], "args": [str(die_index + 1), direction]})
            self.online_pending_card = None
        elif pending["type"] == "one_die":
            self.send_online_action(USE_CARD, {"hand_index": pending["hand_index"], "args": [str(die_index + 1)]})
            self.online_pending_card = None
        elif pending["type"] == "master":
            self.online_selected_die = die_index
            pending["type"] = "value"
        elif pending["type"] == "copy_source":
            self.online_selected_die = die_index
            pending["type"] = "copy_target"
        elif pending["type"] == "copy_target":
            self.send_online_action(USE_CARD, {"hand_index": pending["hand_index"], "args": [str(self.online_selected_die + 1), str(die_index + 1)]})
            self.online_pending_card = None
            self.online_selected_die = None

    def online_hand_rects(self, state):
        hand = state["players"][state.get("active_player_index", 0)]["hand"]
        if not isinstance(hand, list):
            return {}
        return {index: pygame.Rect(56, 370 + index * 84, 196, 74) for index in range(min(4, len(hand)))}

    def online_market_rects(self, state):
        return {index: pygame.Rect(995, 326 + index * 106, MARKET_CARD_W, MARKET_CARD_H) for index, _ in enumerate(state.get("market", []))}

    def online_category_rects(self, state):
        panel = pygame.Rect(SCORE_SHEET_RECT)
        return {key: pygame.Rect(panel.x + 18, panel.y + 34 + row * 13, panel.w - 36, 13) for row, (key, _) in enumerate(CATEGORIES)}

    def online_category_at(self, pos, state):
        for key, rect in self.online_category_rects(state).items():
            if rect.collidepoint(pos):
                return key
        return None

    def prepare_turn(self, grant_start_coin=True):
        self.dice = [1, 2, 3, 4, 5]
        self.held = [False] * DICE_COUNT
        self.rolls = 0
        self.max_rolls_current = MAX_ROLLS
        self.rolling = False
        self.phase = "turn"
        if self.plus_mode:
            self.prepare_plus_turn(grant_start_coin=grant_start_coin)
            return
        self.message = f"Turno de {self.current_player().name}. Tira los 5 dados."

    def cycle_character(self, player_index):
        current_key = self.selected_characters[player_index]
        current_index = next(index for index, character in enumerate(CHARACTERS) if character.key == current_key)
        self.selected_characters[player_index] = CHARACTERS[(current_index + 1) % len(CHARACTERS)].key

    def setup_plus_game(self):
        self.deck = build_deck()
        self.market = []
        self.discard = []
        self.active_event = None
        self.active_event_round = 0
        self.golden_bonus_used_round = 0
        self.discount_buyers = set()
        self.round_scores = {}
        self.fill_market()
        for player in self.players:
            player.coins = PLUS_STARTING_COINS
            player.hand.clear()
            player.bonus_total = 0
            player.pending_attack.clear()
            player.blocked_category = None
            player.attacked_round = 0
            player.temp_shield = False
            player.temp_shield_until_turn = None
            player.cancel_attack_used = False
            player.turns_played = 0
            player.ability_last_turn = -999
            player.ability_once_used = False
            player.no_tach_streak = 0
            player.full_count = 0
            player.previous_scored_assisted = False
            player.generala_valid = False
            player.round_points.clear()
            player.offered_market_cards.clear()
            player.market_blocked = False
            if player.character_key == "tesorero":
                player.coins = min(PLUS_MAX_COINS, player.coins + 1)
            if player.character_key == "defensivo":
                player.hand.append("escudo")

    def draw_card_from_deck(self, exclude=None):
        exclude = set(exclude or ())
        for _ in range(2):
            if not self.deck:
                if self.discard:
                    self.deck = self.discard[:]
                    self.discard.clear()
                    random.shuffle(self.deck)
                else:
                    self.deck = build_deck()
            allowed = [index for index, card_key in enumerate(self.deck) if card_key not in exclude]
            if allowed:
                return self.deck.pop(random.choice(allowed))
            if self.discard:
                self.deck.extend(self.discard)
                self.discard.clear()
                random.shuffle(self.deck)
        if not self.deck:
            self.deck = build_deck()
        return self.deck.pop(random.randrange(len(self.deck)))

    def market_exclusions_for(self, player=None):
        exclusions = set(self.market)
        if player:
            exclusions.update(player.offered_market_cards)
        return exclusions

    def fill_market(self, player=None, record_offer=False):
        while len(self.market) < PLUS_MARKET_SIZE:
            self.market.append(self.draw_card_from_deck(self.market_exclusions_for(player)))
        if record_offer and player:
            player.offered_market_cards.update(self.market)

    def prepare_market_for_player(self, player, record_offer=False):
        clean_market = []
        seen = set()
        for card_key in self.market:
            if card_key in seen or card_key in player.offered_market_cards:
                self.discard.append(card_key)
            else:
                clean_market.append(card_key)
                seen.add(card_key)
        self.market = clean_market
        self.fill_market(player, record_offer=record_offer)

    def replace_market_card(self, index, player=None, record_offer=False):
        exclusions = self.market_exclusions_for(player)
        if index < len(self.market):
            exclusions.discard(self.market[index])
        self.market[index] = self.draw_card_from_deck(exclusions)
        if record_offer and player:
            player.offered_market_cards.add(self.market[index])

    def start_plus_round_if_needed(self):
        round_no = self.round_number()
        if self.active_event_round == round_no:
            return
        for player in self.players:
            if player.temp_shield and player.temp_shield_until_turn is None:
                player.temp_shield = False
        self.active_event_round = round_no
        self.active_event = choose_round_event(round_no)
        self.golden_bonus_used_round = 0
        self.discount_buyers = set()
        self.round_scores.setdefault(round_no, {})
        if self.active_event and self.active_event.key == "defensiva":
            for player in self.players:
                player.temp_shield = True
                player.temp_shield_until_turn = None
        if self.active_event:
            self.sound.play("round_classic" if self.active_event.key == "clasica" else "event")
            color = C_GOLD if self.active_event.key in ("clasica", "dorada", "descuento") else (C_RED_ERROR if self.active_event.key in ("caotica", "presion", "austera") else C_WHITE)
            self.show_banner(self.active_event.name.upper(), self.active_event.text, color)
            self.show_round_transition(self.active_event.name.upper(), self.active_event.text, color)
        else:
            self.show_round_transition(f"RONDA {round_no:02d}", "Mesa limpia. Dados primero.", C_BORDER_ACTIVE)

    def reset_plus_turn_state(self):
        self.card_used_this_turn = False
        self.ability_used_this_turn = False
        self.turn_assisted = False
        self.no_coins_this_turn = False
        self.pending_action = None
        self.pending_turn_attack = None
        self.pending_card_index = None
        self.copy_source_index = None
        self.wildcard_indexes = set()
        self.golden_indexes = set()
        self.duplicator_indexes = set()
        self.score_overrides = {}
        self.score_multiplier = False
        self.force_natural_score = False
        self.declarations = []
        self.ambitious_bonus = False
        self.event_action_used = False
        self.event_caos_done = False
        self.turn_missions = set()
        self.chaotic_card_key = None

    def prepare_plus_turn(self, grant_start_coin=True):
        self.start_plus_round_if_needed()
        self.reset_plus_turn_state()
        player = self.current_player()
        if player.temp_shield and player.temp_shield_until_turn is not None and self.turn >= player.temp_shield_until_turn:
            player.temp_shield = False
            player.temp_shield_until_turn = None
        player.turns_played += 1
        attack = player.pending_attack.copy()
        player.pending_attack.clear()
        player.blocked_category = None
        if attack.get("type") == "mano_pesada":
            self.max_rolls_current = max(1, MAX_ROLLS - 1)
        elif attack.get("type") == "presion":
            self.declarations.append({"source": "presion_ataque", "category": None, "bonus": 0, "penalty": 0, "coin": 0, "no_coins_on_fail": True})
        elif attack.get("type") == "candado":
            player.blocked_category = attack.get("category")
        elif attack.get("type") == "veto_mercado":
            player.market_blocked = True
        elif attack.get("type") == "mesa_fria":
            self.no_coins_this_turn = True
        elif attack:
            self.pending_turn_attack = attack
        if self.active_event and self.active_event.key == "presion":
            self.declarations.append({"source": "presion_evento", "category": None, "bonus": 0, "penalty": 0, "coin": 1, "no_coins_on_fail": False})
        if player.character_key == "caotico" and len(player.hand) < hand_limit(player):
            card_key = self.draw_card_from_deck()
            player.hand.append(card_key)
            self.chaotic_card_key = card_key
        self.prepare_market_for_player(player, record_offer=True)
        event_text = f" | {self.active_event.name}" if self.active_event else ""
        start_coin = 0
        if grant_start_coin and player.coins <= 4 and not self.no_coins_this_turn:
            start_coin = add_coins(player, 1)
            if start_coin:
                self.emit_coin_feedback(start_coin, 150, 272)
        economy_text = "+1 moneda" if start_coin else "sin ingreso pasivo"
        self.message = f"Turno de {player.name}. {economy_text}. Tira los 5 dados.{event_text}"
        if self.needs_forced_declaration():
            self.message = f"{player.name} debe declarar categoria antes de tirar."

    def active_event_key(self):
        return self.active_event.key if self.active_event else None

    def is_classic_round(self):
        return self.active_event_key() == "clasica"

    def opponent_player(self):
        if len(self.players) < 2:
            return None
        return self.players[(self.turn + 1) % len(self.players)]

    def needs_forced_declaration(self):
        return any(declaration["category"] is None for declaration in self.declarations)

    def can_use_active_ability(self):
        if not self.plus_mode or self.state != "game" or self.phase != "turn" or self.rolling:
            return False
        if self.is_classic_round() or self.ability_used_this_turn:
            return False
        player = self.current_player()
        character = player.character
        if character.passive:
            return False
        if character.once and player.ability_once_used:
            return False
        if player.turns_played - player.ability_last_turn < character.cooldown:
            return False
        if character.key in ("matematico", "tecnico") and self.rolls == 0:
            return False
        if character.key in ("ilusionista", "audaz") and self.rolls == 0:
            return False
        if character.key == "audaz" and self.rolls < 2:
            return False
        if character.key == "apostador" and self.rolls != 0:
            return False
        if character.key == "precavido":
            return self.rolls >= self.max_rolls_current
        return True

    def can_use_event_action(self):
        return (
            self.plus_mode
            and self.state == "game"
            and self.phase == "turn"
            and not self.rolling
            and not self.is_classic_round()
            and self.active_event_key() == "espejo"
            and self.rolls > 0
            and not self.event_action_used
        )

    def handle_plus_event(self, event, pos):
        if event.type == pygame.KEYDOWN and not self.rolling:
            if self.pending_action and self.pending_action.get("type") == "set_die_value" and pygame.K_1 <= event.key <= pygame.K_6:
                self.finish_set_die_value(event.key - pygame.K_1 + 1)
                return True
        if self.phase == "buy":
            return self.handle_buy_event(event, pos)
        if event.type != pygame.MOUSEBUTTONDOWN or self.rolling:
            return False
        if self.pending_action:
            return self.handle_pending_plus_click(event, pos)
        if self.ability_button.handle_event(event, pos):
            self.activate_ability()
            return True
        if self.event_button.handle_event(event, pos):
            self.activate_event_action()
            return True
        hand_rects = self.hand_card_rects()
        for index in reversed(range(len(hand_rects))):
            rect = hand_rects[index]
            if rect.collidepoint(pos):
                self.activate_card(index)
                return True
        if self.rolls == 0 and self.needs_forced_declaration():
            category = self.category_at(pos)
            if category:
                self.set_forced_declaration(category)
                return True
        return False

    def handle_buy_event(self, event, pos):
        if self.buy_transition_pending:
            return True
        if self.pass_button.handle_event(event, pos):
            self.end_buy_phase()
            return True
        if event.type != pygame.MOUSEBUTTONDOWN:
            return True
        market_rects = self.market_card_rects()
        for index in reversed(range(len(market_rects))):
            rect = market_rects[index]
            if rect.collidepoint(pos):
                if event.button == 3:
                    self.renew_market_card(index)
                elif event.button == 1:
                    self.buy_market_card(index)
                return True
        if event.button == 1:
            hand_rects = self.hand_card_rects()
            for index in reversed(range(len(hand_rects))):
                rect = hand_rects[index]
                if rect.collidepoint(pos):
                    self.discard_hand_card(index)
                    return True
        return True

    def hand_card_rects(self):
        rects = []
        limit = hand_limit(self.current_player()) if self.players else PLUS_HAND_LIMIT
        x = LEFT_PANEL[0] + (LEFT_PANEL[2] - HAND_CARD_W) // 2
        y = 370
        card_h = HAND_CARD_H if limit <= 3 else 60
        gap = 9
        for index in range(limit):
            rects.append(pygame.Rect(x, y + index * (card_h + gap), HAND_CARD_W, card_h))
        self.hand_rect_cache = rects
        return rects

    def market_card_rects(self):
        rects = []
        x = 995
        y = 326
        for index in range(PLUS_MARKET_SIZE):
            rects.append(pygame.Rect(x, y + index * 106, MARKET_CARD_W, MARKET_CARD_H))
        self.market_rect_cache = rects
        return rects

    def activate_ability(self):
        if not self.can_use_active_ability():
            self.message = "La habilidad no esta disponible."
            return
        player = self.current_player()
        character_key = player.character_key
        self.ability_used_this_turn = True
        player.ability_last_turn = player.turns_played
        if character_key == "matematico":
            self.pending_action = {"type": "adjust_die", "source": "ability"}
            self.turn_assisted = True
            self.message = "Calculo preciso: click izq sube, click der baja un dado."
        elif character_key == "apostador":
            bonus, penalty = self.declaration_values()
            self.pending_action = {"type": "declare_category", "source": "apostador", "bonus": bonus, "penalty": penalty}
            self.turn_assisted = True
            self.message = "Declaracion arriesgada: elegi una categoria antes de tirar."
        elif character_key == "estratega":
            self.discard.extend(self.market)
            self.market = []
            self.fill_market(player, record_offer=True)
            self.message = "El Estratega renovo gratis todo el mercado."
        elif character_key == "conservador":
            player.ability_once_used = True
            self.score_overrides["conservador"] = True
            self.turn_assisted = True
            self.message = "No arriesgar de mas: la proxima tachada vale 5."
        elif character_key == "precavido":
            self.pending_action = {"type": "reroll_die", "source": "ability"}
            self.turn_assisted = True
            self.message = "Plan B: elegi un dado para repetir."
        elif character_key == "ambicioso":
            self.ambitious_bonus = True
            self.turn_assisted = True
            self.message = "Todo o nada: el proximo bonus o penalizacion se duplica."
        elif character_key == "tecnico":
            best_key, points = best_category_for_dice(self.dice, player, self.rolls, assisted=self.turn_assisted)
            label = category_name(best_key) if best_key else "ninguna"
            self.message = f"Optimizacion: mejor opcion actual, {label} por {points}."
        elif character_key == "ilusionista":
            self.pending_action = {"type": "mirror_die", "source": "ability"}
            self.turn_assisted = True
            self.message = "Reflejo privado: elegi un dado para invertir."
        elif character_key == "crupier":
            if self.market:
                self.discard.append(self.market[0])
                self.replace_market_card(0, player, record_offer=True)
            self.message = "Corte de mazo: el Crupier cambio la primera carta del mercado."
        elif character_key == "audaz":
            self.pending_action = {"type": "reroll_die", "source": "ability"}
            self.turn_assisted = True
            self.message = "Impulso final: elegi un dado para repetir."

    def declaration_values(self):
        bonus = 10 if self.active_event_key() == "apuestas" else 8
        penalty = 6 if self.active_event_key() == "apuestas" else 5
        if self.ambitious_bonus:
            bonus *= 2
            penalty *= 2
            self.ambitious_bonus = False
        return bonus, penalty

    def activate_event_action(self):
        if not self.can_use_event_action():
            self.message = "No hay accion de evento disponible."
            return
        self.pending_action = {"type": "mirror_die", "source": "event"}
        self.event_action_used = True
        self.turn_assisted = True
        self.message = "Ronda espejo: elegi un dado para invertir gratis."

    def pending_instruction(self):
        if not self.pending_action:
            return ""
        action_type = self.pending_action.get("type")
        messages = {
            "adjust_die": "Elegí un dado: click izquierdo +1 / derecho -1",
            "reroll_die": "Elegí un dado para repetir",
            "mirror_die": "Elegí un dado para invertir",
            "copy_source": "Elegí el dado origen",
            "copy_target": "Elegí el dado destino",
            "wildcard_die": "Elegí el dado comodín",
            "golden_die": "Elegí el dado dorado",
            "duplicator_die": "Elegí el dado duplicador",
            "set_die_choose": "Elegí un dado y presioná 1-6",
            "set_die_value": "Presioná 1-6 para fijar el valor",
            "declare_category": "Seleccioná una categoría para declarar",
            "rescue_category": "Seleccioná una categoría tachada",
            "attack_candado": "Seleccioná la categoría bloqueada",
            "recycle_market": "Elegí una carta del mercado para cambiar",
        }
        return messages.get(action_type, "Seleccioná un objetivo")

    def activate_card(self, index):
        player = self.current_player()
        if self.is_classic_round():
            self.message = "Ronda clasica: no se pueden usar cartas."
            self.sound.play("ui_denied")
            return
        if self.card_used_this_turn:
            self.message = "Ya usaste una carta este turno."
            self.sound.play("ui_denied")
            return
        if index >= len(player.hand):
            self.sound.play("ui_denied")
            return
        card_key = player.hand[index]
        if player.character_key == "caotico" and self.chaotic_card_key == card_key:
            if player.coins < 1:
                self.message = "El Caotico necesita 1 moneda extra para usar esa carta ahora."
                self.sound.play("ui_denied")
                return
            player.coins -= 1
            self.chaotic_card_key = None
        if card_key in ATTACK_CARDS:
            self.activate_attack_card(index, card_key)
            return
        if self.rolls == 0 and card_key not in ("escudo", "rescate", "reciclaje", "tirada_extra", "no_cuenta", "vision_clara"):
            self.message = "Primero tira los dados para usar esa carta."
            self.sound.play("ui_denied")
            return
        self.pending_card_index = index
        if card_key == "ajuste_fino":
            self.pending_action = {"type": "adjust_die", "source": "card"}
            self.message = "Ajuste fino: click izq sube, click der baja un dado."
        elif card_key == "reintento":
            self.pending_action = {"type": "reroll_die", "source": "card"}
            self.message = "Reintento: elegi un dado para repetir."
        elif card_key == "espejo":
            self.pending_action = {"type": "mirror_die", "source": "card"}
            self.message = "Espejo: elegi un dado para invertir."
        elif card_key == "reciclaje":
            self.pending_action = {"type": "recycle_market", "source": "card"}
            self.message = "Reciclaje: elegi una carta del mercado para cambiarla."
        elif card_key == "copia":
            self.pending_action = {"type": "copy_source", "source": "card"}
            self.message = "Copia: elegi el dado origen."
        elif card_key == "comodin":
            self.pending_action = {"type": "wildcard_die", "source": "card"}
            self.message = "Comodin: elegi el dado que contara como cualquiera."
        elif card_key == "dado_dorado":
            self.pending_action = {"type": "golden_die", "source": "card"}
            self.message = "Dado dorado: elegi el dado que sumara +5 si participa."
        elif card_key == "dado_duplicador":
            self.pending_action = {"type": "duplicator_die", "source": "card"}
            self.message = "Dado duplicador: elegi el dado que valdra doble en categorias numericas."
        elif card_key == "dado_maestro":
            self.pending_action = {"type": "set_die_choose", "source": "card"}
            self.message = "Dado maestro: elegi un dado y despues presiona 1-6."
        elif card_key == "rescate":
            self.pending_action = {"type": "rescue_category", "source": "card"}
            self.message = "Rescate: elegi una categoria tachada para recuperarla."
        elif card_key == "correccion_minima":
            if self.apply_minimal_straight_correction():
                self.consume_pending_card()
                self.score_overrides["correccion_minima"] = True
            else:
                self.pending_card_index = None
                self.pending_action = None
                self.message = "No estas a un solo ajuste de una escalera."
                self.sound.play("ui_denied")
        elif card_key == "ultima_oportunidad":
            if self.rolls >= MAX_ROLLS and not self.any_special_available() and not all(self.held):
                self.dice = [value if held else random.randint(1, 6) for value, held in zip(self.dice, self.held)]
                self.rolls += 1
                self.consume_pending_card()
                self.message = "Ultima oportunidad: los dados libres se repitieron."
            else:
                self.pending_card_index = None
                self.message = "Ultima oportunidad solo va tras la tercera tirada sin jugada especial."
                self.sound.play("ui_denied")
        else:
            self.use_immediate_card(card_key)

    def use_immediate_card(self, card_key):
        player = self.current_player()
        if card_key == "seguro":
            self.score_overrides["seguro"] = True
            self.consume_pending_card()
            self.message = "Seguro activo: una mala anotacion puede valer 10."
        elif card_key == "mano_estable":
            self.score_overrides["mano_estable"] = True
            self.consume_pending_card()
            self.message = "Mano estable activa contra cambios forzados."
        elif card_key == "tirada_extra":
            self.max_rolls_current += 1
            self.consume_pending_card()
            self.message = "Tirada extra: este turno tiene una tirada mas."
        elif card_key == "escudo":
            player.temp_shield = True
            player.temp_shield_until_turn = self.turn + len(self.players)
            self.consume_pending_card()
            self.message = "Escudo activo hasta tu proximo turno o hasta bloquear."
        elif card_key == "escalera_rota":
            self.score_overrides["escalera_rota"] = True
            self.consume_pending_card()
            self.message = "Escalera rota activa: 4 consecutivos valen 15."
        elif card_key == "duplicador":
            self.score_multiplier = True
            self.consume_pending_card()
            self.message = "Duplicador activo: +50% maximo +15, no sobre Generala doble."
        elif card_key == "generala_falsa":
            self.score_overrides["generala_falsa"] = True
            self.consume_pending_card()
            self.message = "Generala falsa activa: 4 iguales pueden valer 35."
        elif card_key == "milagro_controlado":
            self.force_natural_score = True
            self.consume_pending_card()
            self.message = "Milagro controlado: asistida puntua como natural, nunca servida."
        elif card_key == "no_cuenta":
            self.consume_pending_card()
            self.dice = [1, 2, 3, 4, 5]
            self.held = [False] * DICE_COUNT
            self.rolls = 0
            self.max_rolls_current = MAX_ROLLS
            self.no_coins_this_turn = True
            self.message = "No cuenta: turno reiniciado. Este turno no gana monedas."
        elif card_key == "foco_numerico":
            self.score_overrides["foco_numerico"] = True
            self.consume_pending_card()
            self.message = "Foco numerico activo: si anotas una categoria numerica, suma +3."
        elif card_key == "vision_clara":
            best_key, points = best_category_for_dice(self.dice, player, self.rolls, assisted=self.turn_assisted)
            label = category_name(best_key) if best_key else "ninguna"
            self.consume_pending_card(assisted=False)
            self.message = f"Vision clara: mejor opcion actual, {label} por {points}."
        elif card_key == "pulso_controlado":
            if self.rolls > 0 and not all(self.held):
                self.dice = [value if held else random.randint(1, 6) for value, held in zip(self.dice, self.held)]
                self.consume_pending_card()
                self.message = "Pulso controlado: los dados libres se repitieron."
            else:
                self.pending_card_index = None
                self.message = "Pulso controlado necesita al menos un dado libre tras tirar."
                self.sound.play("ui_denied")
        elif card_key == "ancla":
            if self.rolls > 0:
                self.held = [True] * DICE_COUNT
                self.consume_pending_card(assisted=False)
                self.message = "Ancla: todos los dados quedaron retenidos."
            else:
                self.pending_card_index = None
                self.message = "Ancla se usa despues de tirar."
                self.sound.play("ui_denied")
        elif card_key == "apertura":
            if self.rolls > 0:
                self.held = [False] * DICE_COUNT
                self.consume_pending_card(assisted=False)
                self.message = "Apertura: todos los dados quedaron libres."
            else:
                self.pending_card_index = None
                self.message = "Apertura se usa despues de tirar."
                self.sound.play("ui_denied")

    def activate_attack_card(self, index, card_key):
        if self.rolls > 0:
            self.message = "Los ataques solo se juegan antes de tirar."
            self.sound.play("ui_denied")
            return
        target = self.opponent_player()
        if not target:
            return
        round_no = self.round_number()
        if target.attacked_round == round_no:
            self.message = f"{target.name} ya fue atacado en esta ronda."
            self.sound.play("ui_denied")
            return
        if self.target_blocks_attack(target):
            target.attacked_round = round_no
            self.consume_card(index)
            return
        if card_key == "candado":
            self.pending_card_index = index
            self.pending_action = {"type": "attack_candado", "target": target}
            self.message = "Candado: elegi la categoria que no podra anotar el rival."
            return
        if card_key == "robo":
            if target.hand:
                stolen = target.hand.pop(random.randrange(len(target.hand)))
                if len(self.current_player().hand) < hand_limit(self.current_player()):
                    self.current_player().hand.append(stolen)
                else:
                    self.discard.append(stolen)
                self.message = f"Robo: carta tomada de {target.name}."
            else:
                self.message = f"Robo no encontro cartas en {target.name}."
        elif card_key == "intercambio":
            target.pending_attack = {"type": "intercambio"}
            gained = add_coins(self.current_player(), 1)
            if gained:
                self.emit_coin_feedback(gained, 150, 272)
            self.message = "Intercambio simplificado: el rival repetira un dado y ganas 1 moneda."
        else:
            target.pending_attack = {"type": card_key}
            self.message = f"{CARD_DEFS[card_key].name} preparado contra {target.name}."
        target.attacked_round = round_no
        self.sound.play("attack")
        self.consume_card(index)

    def target_blocks_attack(self, target):
        if target.temp_shield:
            target.temp_shield = False
            target.temp_shield_until_turn = None
            self.sound.play("shield")
            self.show_banner("ESCUDO", f"{target.name} bloqueo el ataque.", C_GOLD)
            return True
        if target.character_key == "defensivo" and not target.cancel_attack_used:
            target.cancel_attack_used = True
            self.sound.play("shield")
            self.show_banner("GUARDIA ALTA", f"{target.name} cancelo un ataque.", C_GOLD)
            return True
        return False

    def handle_pending_plus_click(self, event, pos):
        action_type = self.pending_action.get("type")
        category = self.category_at(pos)
        if action_type == "declare_category" and category:
            bonus = self.pending_action.get("bonus", 0)
            penalty = self.pending_action.get("penalty", 0)
            self.declarations.append({"source": self.pending_action.get("source"), "category": category, "bonus": bonus, "penalty": penalty, "coin": 0, "no_coins_on_fail": False})
            self.pending_action = None
            self.message = f"Declaraste {category_name(category)}."
            return True
        if action_type == "rescue_category" and category:
            player = self.current_player()
            if player.sheet.get(category) == 0:
                player.sheet[category] = None
                self.consume_pending_card()
                self.message = f"Rescate recupero {category_name(category)}."
            else:
                self.message = "Rescate necesita una categoria tachada."
            return True
        if action_type == "attack_candado" and category:
            target = self.pending_action["target"]
            target.pending_attack = {"type": "candado", "category": category}
            target.attacked_round = self.round_number()
            self.consume_pending_card()
            self.message = f"Candado: {target.name} no podra anotar {category_name(category)}."
            return True
        if action_type == "recycle_market":
            for index, rect in enumerate(self.market_card_rects()):
                if rect.collidepoint(pos):
                    player = self.current_player()
                    old_card = player.hand.pop(self.pending_card_index)
                    player.hand.append(self.market[index])
                    self.discard.append(old_card)
                    self.replace_market_card(index, player, record_offer=True)
                    self.card_used_this_turn = True
                    self.turn_assisted = True
                    self.pending_card_index = None
                    self.pending_action = None
                    self.message = "Reciclaje cambio una carta por el mercado."
                    return True
            return True
        for index in range(DICE_COUNT):
            if self.die_rect(index).inflate(16, 16).collidepoint(pos):
                self.apply_pending_die_action(index, event.button)
                return True
        return True

    def apply_pending_die_action(self, index, button):
        action_type = self.pending_action.get("type")
        if action_type == "adjust_die":
            delta = -1 if button == 3 else 1
            self.dice[index] = max(1, min(6, self.dice[index] + delta))
            if self.pending_action.get("source") == "card":
                self.consume_pending_card()
            else:
                self.pending_action = None
            self.message = "Dado ajustado."
        elif action_type == "reroll_die":
            self.dice[index] = random.randint(1, 6)
            if self.pending_action.get("source") == "card":
                self.consume_pending_card()
            else:
                self.pending_action = None
            self.message = "Dado repetido."
        elif action_type == "mirror_die":
            self.dice[index] = invert_die(self.dice[index])
            if self.pending_action.get("source") == "card":
                self.consume_pending_card()
            else:
                self.pending_action = None
            self.message = "Dado invertido."
        elif action_type == "copy_source":
            self.copy_source_index = index
            self.pending_action["type"] = "copy_target"
            self.message = "Copia: elegi el dado destino."
        elif action_type == "copy_target":
            self.dice[index] = self.dice[self.copy_source_index]
            self.copy_source_index = None
            self.consume_pending_card()
            self.message = "Valor copiado."
        elif action_type == "wildcard_die":
            self.wildcard_indexes.add(index)
            self.consume_pending_card()
            self.message = "Comodin marcado. La jugada sera asistida."
        elif action_type == "golden_die":
            self.golden_indexes.add(index)
            self.consume_pending_card()
            self.message = "Dado dorado marcado."
        elif action_type == "duplicator_die":
            self.duplicator_indexes.add(index)
            self.consume_pending_card()
            self.message = "Dado duplicador marcado para categorias numericas."
        elif action_type == "set_die_choose":
            self.pending_action = {"type": "set_die_value", "index": index, "source": "card"}
            self.message = "Presiona 1, 2, 3, 4, 5 o 6 para fijar el dado."

    def finish_set_die_value(self, value):
        index = self.pending_action["index"]
        self.dice[index] = value
        self.consume_pending_card()
        self.message = f"Dado maestro fijo un {value}."

    def consume_card(self, index, discard_card=True, assisted=True):
        player = self.current_player()
        source_rect = self.hand_card_rects()[index].copy() if index < len(self.hand_card_rects()) else pygame.Rect(LEFT_PANEL[0] + 50, 400, HAND_CARD_W, HAND_CARD_H)
        card_key = player.hand.pop(index)
        if discard_card:
            self.discard.append(card_key)
        self.card_used_this_turn = True
        if assisted:
            self.turn_assisted = True
        self.sound.play("card_use")
        self.show_banner(CARD_DEFS[card_key].name.upper(), "Carta usada. La jugada sera asistida si modifica el turno.", C_GOLD if CARD_DEFS[card_key].tier == "fuerte" else C_BORDER_ACTIVE)
        self.spawn_card_flight(card_key, source_rect, pygame.Rect(SCREEN_W // 2 - 86, DICE_Y - 120, 172, 112), spin=2.5)
        self.emit_particles(SCREEN_W // 2, DICE_Y + 20, C_GOLD if CARD_DEFS[card_key].tier == "fuerte" else C_WHITE_SOFT, 26, speed=(90, 300), life=(0.35, 1.0), square=False)
        self.pending_card_index = None
        self.pending_action = None

    def consume_pending_card(self, discard_card=True, assisted=True):
        if self.pending_card_index is not None:
            self.consume_card(self.pending_card_index, discard_card=discard_card, assisted=assisted)
        else:
            self.pending_action = None

    def apply_minimal_straight_correction(self):
        for index, value in enumerate(self.dice):
            for delta in (-1, 1):
                new_value = value + delta
                if not 1 <= new_value <= 6:
                    continue
                candidate = self.dice[:]
                candidate[index] = new_value
                if is_straight(candidate):
                    self.dice = candidate
                    self.message = "Correccion minima completo una escalera asistida."
                    return True
        return False

    def any_special_available(self):
        return any(self.preview_plus_score(key).points > 0 for key in SPECIAL_CATEGORIES)

    def apply_plus_after_roll(self):
        if self.rolls == 1 and self.pending_turn_attack:
            attack_type = self.pending_turn_attack.get("type")
            index = random.randrange(DICE_COUNT)
            self.dice[index] = random.randint(1, 6)
            self.pending_turn_attack = None
            self.sound.play("attack")
            self.show_banner("ATAQUE", f"{attack_type}: un dado fue repetido.", C_RED_ERROR)
        if self.active_event_key() == "caotica" and self.rolls == 2 and not self.event_caos_done:
            self.event_caos_done = True
            if self.score_overrides.get("mano_estable"):
                self.sound.play("shield")
                self.show_banner("MANO ESTABLE", "Evitaste el cambio caotico.", C_GOLD)
                return
            index = random.randrange(DICE_COUNT)
            old_value = self.dice[index]
            choices = [value for value in range(1, 7) if value != old_value]
            self.dice[index] = random.choice(choices)
            self.turn_assisted = True
            self.sound.play("event")
            self.show_banner("RONDA CAOTICA", "Un dado cambio de valor.", C_RED_ERROR)

    def set_forced_declaration(self, category):
        for declaration in self.declarations:
            if declaration["category"] is None:
                declaration["category"] = category
                self.message = f"Declaraste {category_name(category)}."
                return

    def preview_plus_score(self, key):
        player = self.current_player()
        return evaluate_plus_score(
            key,
            self.dice,
            self.rolls,
            player,
            assisted=self.turn_assisted,
            wildcard_indexes=self.wildcard_indexes,
            golden_indexes=self.golden_indexes,
            duplicator_indexes=self.duplicator_indexes,
            score_multiplier=self.score_multiplier,
            score_overrides=self.score_overrides,
            force_natural=self.force_natural_score,
        )

    def score_plus_category(self, key):
        player = self.current_player()
        if self.phase != "turn":
            self.sound.play("ui_denied")
            return
        if self.rolls == 0:
            if self.needs_forced_declaration():
                self.set_forced_declaration(key)
            else:
                self.message = "Primero tenes que tirar los dados."
                self.sound.play("ui_denied")
            return
        if self.needs_forced_declaration():
            self.message = "Primero declara la categoria obligatoria."
            self.sound.play("ui_denied")
            return
        if player.sheet[key] is not None:
            self.message = "Esa categoria ya esta usada."
            self.sound.play("ui_denied")
            return
        if player.blocked_category == key:
            self.message = f"Candado activo: no podes anotar {category_name(key)} este turno."
            self.sound.play("ui_denied")
            return
        declaration_bonus, penalty, extra_coins, no_coins_fail = self.resolve_declarations(key)
        event_bonus = 0
        if self.active_event_key() == "dorada" and not self.golden_bonus_used_round and key in SPECIAL_CATEGORIES:
            event_bonus = 5
            self.turn_assisted = True
        result = evaluate_plus_score(
            key,
            self.dice,
            self.rolls,
            player,
            assisted=self.turn_assisted,
            wildcard_indexes=self.wildcard_indexes,
            golden_indexes=self.golden_indexes,
            duplicator_indexes=self.duplicator_indexes,
            score_multiplier=self.score_multiplier,
            score_overrides=self.score_overrides,
            force_natural=self.force_natural_score,
            event_bonus=event_bonus,
            declaration_bonus=declaration_bonus,
        )
        if event_bonus and result.special:
            self.golden_bonus_used_round = self.round_number()
        if no_coins_fail:
            self.no_coins_this_turn = True
        if penalty:
            player.bonus_total -= penalty
        player.sheet[key] = result.points
        if key == "generala" and result.base_points > 0 and not result.false_generala:
            player.generala_valid = True
        label = category_name(key)
        if result.points == 0:
            self.sound.play("tachada")
            self.show_banner("TACHADA", f"{label}: 0 puntos.", C_RED_ERROR)
            self.emit_floating_text("TACHADA", SCREEN_W // 2, 424, C_RED_ERROR)
        else:
            color = C_GOLD if result.served or result.bonus_points else C_GREEN_SUCCESS
            suffix = " natural" if result.natural else (" asistida" if result.assisted else "")
            if key in ("generala", "generala_doble"):
                self.sound.play("generala")
            elif result.special or result.bonus_points:
                self.sound.play("score_special")
            else:
                self.sound.play("score")
            self.show_banner(label.upper(), f"{result.points} puntos{suffix}.", color)
            self.emit_success_particles(color, 80 if result.points >= 40 else 40)
            self.emit_score_feedback(result.points, color)
        if penalty:
            self.message = f"Penalizacion de declaracion: -{penalty} puntos extra."
        self.award_plus_rewards(player, key, result, extra_coins)
        self.round_scores.setdefault(self.round_number(), {})[self.players.index(player)] = result.points
        self.check_round_mission()
        if all(player.complete for player in self.players):
            self.state = "end"
            self.sound.play("win")
            self.emit_success_particles(C_GOLD, 200)
            return
        self.enter_buy_phase()

    def resolve_declarations(self, key):
        bonus = 0
        penalty = 0
        extra_coins = 0
        no_coins_fail = False
        for declaration in self.declarations:
            category = declaration.get("category")
            if not category:
                continue
            if category == key:
                bonus += declaration.get("bonus", 0)
                extra_coins += declaration.get("coin", 0)
            else:
                penalty += declaration.get("penalty", 0)
                if declaration.get("no_coins_on_fail"):
                    no_coins_fail = True
        return bonus, penalty, extra_coins, no_coins_fail

    def award_plus_rewards(self, player, key, result, extra_coins):
        if self.no_coins_this_turn:
            player.previous_scored_assisted = result.assisted
            return
        before_coins = player.coins
        earned = 0
        if result.tachada:
            earned += 2 if self.active_event_key() == "recuperacion" else 1
            player.no_tach_streak = 0
        else:
            player.no_tach_streak += 1
            if key in NUMBER_CATEGORIES:
                if result.points >= 15:
                    earned += 1
            elif result.special:
                if key in ("generala", "generala_doble") and not result.false_generala:
                    earned += 2
                else:
                    earned += 1
        if not self.card_used_this_turn and player.character_key != "coleccionista" and result.points > 0 and player.coins <= 6:
            earned += 1
        earned += extra_coins
        earned += self.award_mission_rewards(player, key, result)
        earned = min(3, earned)
        add_coins(player, earned)
        if earned > 0 and player.coins > before_coins:
            self.sound.play("coin")
            gained = player.coins - before_coins
            self.emit_coin_feedback(gained, 150, 272)
        player.previous_scored_assisted = result.assisted or (self.turn_assisted and result.base_points > 0)

    def award_mission_rewards(self, player, key, result):
        reward = 0
        counts = Counter(self.dice)
        if "trio" not in self.turn_missions and max(counts.values()) >= 3:
            self.turn_missions.add("trio")
        if key == "escalera" and result.points > 0:
            reward += 1
        if "tres_seises" not in self.turn_missions and counts[6] >= 3:
            self.turn_missions.add("tres_seises")
        if key == "full" and result.points > 0:
            player.full_count += 1
            if player.full_count == 2:
                reward += 2
        if result.natural and player.previous_scored_assisted:
            reward += 1
        if player.no_tach_streak and player.no_tach_streak % 5 == 0 and len(player.hand) < hand_limit(player) and self.market:
            player.hand.append(self.market.pop(0))
            self.fill_market(player, record_offer=True)
        return reward

    def check_round_mission(self):
        scores = self.round_scores.get(self.round_number(), {})
        if len(scores) != len(self.players):
            return
        best_index, best_score = max(scores.items(), key=lambda item: item[1])
        low_score = min(scores.values())
        if best_score - low_score <= 20:
            return
        winner = self.players[best_index]
        if len(winner.hand) < hand_limit(winner):
            common_cards = [key for key, card in CARD_DEFS.items() if card.tier == "comun"]
            winner.hand.append(random.choice(common_cards))

    def enter_buy_phase(self):
        player = self.current_player()
        if self.active_event_key() == "austera" or player.complete:
            self.end_buy_phase()
            return
        if player.market_blocked:
            player.market_blocked = False
            self.message = "Veto de mercado: este turno no hay compra."
            self.show_banner("VETO DE MERCADO", f"{player.name} pierde la fase de compra.", C_RED_ERROR)
            self.end_buy_phase()
            return
        self.phase = "buy"
        self.pending_action = None
        self.message = "Fin de turno: compra 1 carta, descarta de tu mano o pasa."

    def end_buy_phase(self):
        self.turn += 1
        if all(player.complete for player in self.players):
            self.state = "end"
            self.sound.play("win")
            self.emit_success_particles(C_GOLD, 200)
            return
        self.prepare_turn()

    def buy_market_card(self, index):
        player = self.current_player()
        if self.buy_transition_pending:
            return
        if self.active_event_key() == "austera":
            self.message = "Ronda austera: no se pueden comprar cartas."
            self.sound.play("ui_denied")
            return
        if index >= len(self.market):
            self.sound.play("ui_denied")
            return
        if len(player.hand) >= hand_limit(player):
            self.message = "Mano llena. Descarta una carta de tu mano para comprar."
            self.sound.play("ui_denied")
            return
        discount_available = self.players.index(player) not in self.discount_buyers
        cost = display_card_cost(self.market[index], player, self.active_event_key(), discount_available)
        if player.coins < cost:
            self.message = "No tenes monedas suficientes."
            self.sound.play("ui_denied")
            return
        source_rect = self.market_card_rects()[index].copy()
        hand_rects = self.hand_card_rects()
        target_index = min(len(player.hand), len(hand_rects) - 1)
        target_rect = hand_rects[target_index].copy() if hand_rects else pygame.Rect(70, 370, HAND_CARD_W, HAND_CARD_H)
        player.coins -= cost
        card_key = self.market.pop(index)
        player.hand.append(card_key)
        if self.active_event_key() == "descuento":
            self.discount_buyers.add(self.players.index(player))
        if player.character_key == "suertudo" and CARD_DEFS[card_key].cost >= 4:
            gained = add_coins(player, 1)
            if gained:
                self.emit_coin_feedback(gained, 150, 272)
        self.fill_market()
        self.sound.play("card_buy")
        self.sound.play("coin")
        self.spawn_card_flight(card_key, source_rect, target_rect, spin=5.0)
        self.emit_spend_feedback(cost, source_rect.centerx, source_rect.centery)
        self.emit_particles(source_rect.centerx, source_rect.centery, CardView.accent(card_key), 42, speed=(100, 360), life=(0.35, 1.05), square=False)
        self.show_banner("CARTA COMPRADA", CARD_DEFS[card_key].name, C_GOLD if CARD_DEFS[card_key].tier == "fuerte" else C_BORDER_ACTIVE)
        self.message = f"{CARD_DEFS[card_key].name} comprada. Preparando siguiente turno..."
        self.buy_transition_pending = True
        self.buy_transition_timer = 0.82

    def renew_market_card(self, index):
        player = self.current_player()
        if self.buy_transition_pending:
            return
        if index >= len(self.market):
            self.sound.play("ui_denied")
            return
        if player.coins < 1:
            self.message = "Renovar una carta cuesta 1 moneda."
            self.sound.play("ui_denied")
            return
        player.coins -= 1
        card_key = self.market[index]
        source_rect = self.market_card_rects()[index].copy()
        discard_rect = pygame.Rect(RIGHT_PANEL[0] + 122, RIGHT_PANEL[1] + 152, 104, 34)
        self.discard.append(self.market[index])
        self.replace_market_card(index, player, record_offer=True)
        self.message = "Carta del mercado renovada."
        self.sound.play("card_renew")
        self.sound.play("coin")
        self.spawn_card_flight(card_key, source_rect, discard_rect, spin=-5.0)
        self.spawn_card_flight(self.market[index], pygame.Rect(RIGHT_PANEL[0] + 22, RIGHT_PANEL[1] + 152, 88, 34), source_rect, delay=0.16, spin=4.0)
        self.emit_spend_feedback(1, source_rect.centerx, source_rect.centery)

    def discard_hand_card(self, index):
        player = self.current_player()
        if index >= len(player.hand):
            self.sound.play("ui_denied")
            return
        card_key = player.hand[index]
        if index < len(self.hand_card_rects()):
            self.spawn_card_flight(card_key, self.hand_card_rects()[index], pygame.Rect(RIGHT_PANEL[0] + 122, RIGHT_PANEL[1] + 152, 104, 34), spin=-4.0)
        self.discard.append(player.hand.pop(index))
        self.message = "Carta descartada. Ahora podes comprar."
        self.sound.play("card_discard")

    def current_player(self):
        return self.players[self.turn % len(self.players)]

    def round_number(self):
        return self.turn // len(self.players) + 1

    def roll_dice(self):
        if self.rolling or self.phase != "turn" or self.rolls >= self.max_rolls_current:
            self.sound.play("ui_denied")
            return
        if self.plus_mode and self.needs_forced_declaration():
            self.message = "Declara una categoria antes de tirar."
            self.sound.play("ui_denied")
            return
        if all(self.held):
            self.message = "Todos los dados estan retenidos. Libera alguno o anota."
            self.sound.play("ui_denied")
            return
        self.rolling = True
        self.roll_timer = ROLL_DURATION
        self.roll_tick = 0
        self.sound.play("dice_roll")
        self.emit_roll_particles()

    def finish_roll(self):
        if self.rolls == 0:
            self.dice = [random.randint(1, 6) for _ in range(DICE_COUNT)]
        else:
            self.dice = [
                value if held else random.randint(1, 6)
                for value, held in zip(self.dice, self.held)
            ]
        self.rolls += 1
        self.rolling = False
        self.sound.play("dice_land")
        if self.plus_mode:
            self.apply_plus_after_roll()
        self.message = "Retene dados utiles o anota una categoria."
        if self.is_served_generala():
            self.sound.play("generala")
            self.show_banner("GENERALA SERVIDA", "60 puntos en Generala.", C_GOLD)
            self.emit_success_particles(C_GOLD, 200)

    def is_served_generala(self):
        return self.rolls == 1 and len(set(self.dice)) == 1

    def die_rect(self, index):
        total_w = DICE_COUNT * DIE_SIZE + (DICE_COUNT - 1) * DIE_GAP
        start_x = SCREEN_W // 2 - total_w // 2
        return pygame.Rect(start_x + index * (DIE_SIZE + DIE_GAP), DICE_Y - DIE_SIZE // 2, DIE_SIZE, DIE_SIZE)

    def toggle_die_at(self, pos):
        for index in range(DICE_COUNT):
            if self.die_rect(index).inflate(16, 16).collidepoint(pos):
                self.toggle_hold(index)
                return True
        return False

    def toggle_hold(self, index):
        if self.rolls == 0:
            self.sound.play("ui_denied")
            return
        self.held[index] = not self.held[index]
        self.message = "Dado retenido." if self.held[index] else "Dado liberado."
        self.sound.play("die_hold" if self.held[index] else "die_release")
        center = self.die_rect(index).center
        self.emit_particles(center[0], center[1], C_WHITE if self.held[index] else C_GRAY_MID, 12)

    def release_all(self):
        had_held = any(self.held)
        self.held = [False] * DICE_COUNT
        self.message = "Todos los dados fueron liberados."
        if had_held:
            self.sound.play("release_all")
            for index in range(DICE_COUNT):
                center = self.die_rect(index).center
                self.emit_particles(center[0], center[1], C_GOLD, 4, speed=(40, 120), life=(0.25, 0.55), square=False)
        else:
            self.sound.play("ui_denied")

    def category_rects(self):
        sheet = pygame.Rect(SCORE_SHEET_RECT)
        table_w = COL_CAT + COL_PLAYER * len(self.players)
        start_x = sheet.x + (sheet.w - table_w) // 2
        rects = {}
        y = sheet.y + 29
        for index, (key, _) in enumerate(CATEGORIES):
            rects[key] = pygame.Rect(start_x, y + index * ROW_H, COL_CAT + COL_PLAYER * len(self.players), ROW_H)
        return rects

    def category_at(self, pos):
        for key, rect in self.category_rects().items():
            if rect.collidepoint(pos):
                return key
        return None

    def score_category(self, key):
        if self.plus_mode:
            self.score_plus_category(key)
            return
        player = self.current_player()
        if self.rolls == 0:
            self.message = "Primero tenes que tirar los dados."
            self.sound.play("ui_denied")
            return
        if player.sheet[key] is not None:
            self.message = "Esa categoria ya esta usada."
            self.sound.play("ui_denied")
            return
        points = score_category(key, self.dice, self.rolls, player.sheet)
        player.sheet[key] = points
        label = category_name(key)
        if points == 0:
            self.sound.play("tachada")
            self.show_banner("TACHADA", f"{label}: 0 puntos.", C_RED_ERROR)
            self.emit_floating_text("TACHADA", SCREEN_W // 2, 424, C_RED_ERROR)
        else:
            color = C_GOLD if key == "generala" and points == 60 else C_GREEN_SUCCESS
            if key in ("generala", "generala_doble"):
                self.sound.play("generala")
            elif key in SPECIAL_CATEGORIES:
                self.sound.play("score_special")
            else:
                self.sound.play("score")
            self.show_banner(label.upper(), f"{points} puntos anotados.", color)
            self.emit_success_particles(color, 80 if points >= 40 else 40)
            self.emit_score_feedback(points, color)
        self.turn += 1
        if all(player.complete for player in self.players):
            self.state = "end"
            self.sound.play("win")
            self.emit_success_particles(C_GOLD, 200)
            return
        self.prepare_turn()

    def update(self, dt):
        time_value = pygame.time.get_ticks() / 1000
        for particle in self.ambient:
            particle.update(dt)
        if self.buy_transition_pending:
            self.buy_transition_timer -= dt
            if self.buy_transition_timer <= 0:
                self.buy_transition_pending = False
                self.buy_transition_timer = 0
                self.end_buy_phase()
        if self.rolling:
            self.roll_timer -= dt
            self.roll_tick -= dt
            if self.roll_tick <= 0:
                self.roll_tick = ROLL_TICK
                self.dice = [
                    value if held else random.randint(1, 6)
                    for value, held in zip(self.dice, self.held)
                ]
                self.emit_roll_particles(light=True)
            if self.roll_timer <= 0:
                self.finish_roll()
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if particle.life > 0]
        for floater in self.floaters:
            floater.update(dt)
        self.floaters = [floater for floater in self.floaters if floater.life > 0]
        for card_flight in self.card_flights:
            card_flight.update(dt)
        self.card_flights = [card_flight for card_flight in self.card_flights if not card_flight.done]
        for coin_flight in self.coin_flights:
            coin_flight.update(dt)
        self.coin_flights = [coin_flight for coin_flight in self.coin_flights if not coin_flight.done]
        if self.round_transition:
            self.round_transition.update(dt)
            if self.round_transition.done:
                self.round_transition = None
        if self.banner:
            self.banner["time"] -= dt
            if self.banner["time"] <= 0:
                self.banner = None
        self.noise_frame += 1
        if self.noise_frame >= 3:
            self.noise_frame = 0
            self.rebuild_noise()

    def show_banner(self, title, detail, color, visual_key=None):
        self.banner = {"title": title, "detail": detail, "color": color, "key": visual_key or self.banner_visual_key(title), "time": 1.7, "duration": 1.7}

    def show_round_transition(self, title, detail, color):
        self.round_transition = RoundTransition(title=title, detail=detail, color=color)

    def banner_visual_key(self, title):
        normalized = title.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        for key, card in CARD_DEFS.items():
            if card.name.lower() == normalized:
                return key
        for event in ROUND_EVENTS + [CLASSIC_EVENT]:
            if event.name.lower() == normalized:
                return event.key
        special = {
            "escalera": "correccion_minima",
            "full": "clasica",
            "poker": "duplicador",
            "generala": "dado_dorado",
            "generala servida": "dado_dorado",
            "tachada": "sabotaje",
            "ataque": "sabotaje",
            "escudo": "escudo",
            "carta comprada": "coleccionista",
        }
        return special.get(normalized, "clasica")

    def emit_roll_particles(self, light=False):
        count = 8 if light else 35
        for index, held in enumerate(self.held):
            if held:
                continue
            center = self.die_rect(index).center
            self.emit_particles(center[0], center[1], random.choice([C_BORDER_ACTIVE, C_GRAY_DARK, C_WHITE]), count)

    def emit_success_particles(self, color, count):
        self.emit_particles(SCREEN_W // 2, DICE_Y, color, count, speed=(280, 920), life=(0.7, 2.4), square=False)

    def emit_floating_text(self, text, x, y, color=C_GOLD, life=1.0, size=1.0, vy=-34):
        self.floaters.append(FloatingText(text=text, x=x, y=y, color=color, life=life, max_life=life, size=size, vy=vy))

    def emit_score_feedback(self, points, color):
        self.emit_particles(SCREEN_W // 2, 330, color, 36 if points < 40 else 54, speed=(160, 520), life=(0.45, 1.1), square=False)
        self.emit_floating_text(f"+{points}", SCREEN_W // 2, 326, color, life=1.35, size=1.65, vy=-48)

    def emit_coin_feedback(self, amount, x, y):
        self.emit_particles(x, y, C_GOLD, min(42, 12 + amount * 8), speed=(120, 360), life=(0.45, 1.2), square=False)
        self.emit_floating_text(f"+{amount} moneda" if amount == 1 else f"+{amount} monedas", x + 46, y - 26, C_GOLD, life=1.25, size=1.15, vy=-42)
        self.spawn_coin_stream(amount, (x + 120, y - 42), (x, y), C_GOLD)

    def emit_spend_feedback(self, amount, x, y):
        self.emit_particles(x, y, C_GOLD, min(36, 12 + amount * 5), speed=(90, 290), life=(0.35, 0.95), square=False)
        self.emit_floating_text(f"-{amount}", x, y - 30, C_GOLD, life=1.05, size=1.35, vy=-38)
        self.spawn_coin_stream(amount, (150, 272), (x, y), C_GOLD)

    def spawn_coin_stream(self, amount, start, end, accent=C_GOLD):
        count = max(1, min(7, amount))
        for index in range(count):
            jitter_start = (start[0] + random.randint(-8, 8), start[1] + random.randint(-8, 8))
            jitter_end = (end[0] + random.randint(-14, 14), end[1] + random.randint(-12, 12))
            self.coin_flights.append(
                CoinFlight(
                    start=jitter_start,
                    end=jitter_end,
                    accent=accent,
                    delay=index * 0.055,
                    radius=random.randint(6, 8),
                )
            )

    def spawn_card_flight(self, card_key, start_rect, end_rect, delay=0.0, spin=3.0):
        self.card_flights.append(
            CardFlight(
                card_key=card_key,
                start=pygame.Rect(start_rect),
                end=pygame.Rect(end_rect),
                delay=delay,
                spin=spin,
            )
        )

    def draw_motion_animations(self):
        for coin_flight in self.coin_flights:
            coin_flight.draw(self.canvas)
        for card_flight in self.card_flights:
            card_flight.draw(self.canvas, self.card_fonts, self.mouse_pos)
        if self.round_transition:
            self.round_transition.draw(self.canvas, self.font_turn, self.font_body)

    def emit_particles(self, x, y, color, count, speed=(120, 520), life=(0.35, 0.9), square=True):
        for _ in range(count):
            angle = random.random() * math.tau
            velocity = random.uniform(*speed)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * velocity,
                    vy=math.sin(angle) * velocity - random.uniform(20, 120),
                    size=random.uniform(2, 5),
                    color=color,
                    life=random.uniform(*life),
                    max_life=life[1],
                    square=square,
                    gravity=random.uniform(420, 760),
                    spin=random.uniform(-360, 360),
                )
            )

    def draw(self):
        self.canvas.fill(C_BG_DEEP)
        self.draw_background()
        if self.state == "start":
            self.draw_start()
        elif self.state == "online_setup":
            self.draw_online_setup()
        elif self.state == "online_game":
            self.draw_online_game()
        elif self.state == "game":
            self.draw_game()
        else:
            self.draw_end()
        if not self.paused and not self.show_help:
            self.draw_context_tooltip()
        if self.state != "end":
            self.draw_banner()
        if self.state != "end":
            for particle in self.particles:
                particle.draw(self.canvas)
        self.draw_motion_animations()
        for floater in self.floaters:
            floater.draw(self.canvas, self.font_label)
        self.draw_vignette()
        self.canvas.blit(self.noise, (0, 0))
        if self.paused:
            self.draw_pause_menu()
        if self.show_help:
            self.draw_help()
        self.screen.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(self.canvas, self.draw_size)
        self.screen.blit(scaled, self.offset)

    def draw_background(self):
        self.canvas.blit(self.table_texture, (0, 0))
        time_value = pygame.time.get_ticks() / 1000
        for particle in self.ambient:
            particle.draw(self.canvas, time_value)
        self.canvas.blit(self.scanlines, (0, 0))

    def draw_start(self):
        t = pygame.time.get_ticks() / 1000
        logo_scale = 1 + 0.012 * math.sin(t * 1.4)
        logo_font = pygame.font.SysFont("Space Grotesk, Sohne, Arial", int(78 * logo_scale), bold=True)
        logo = logo_font.render("GENERALA", True, C_WHITE_SOFT)
        logo_rect = logo.get_rect(center=(SCREEN_W // 2, 96))
        if logo_rect.y < 36:
            logo_rect.y = 36
        self.canvas.blit(logo, logo_rect)
        subtitle_text = "PLUS EDITION" if self.plus_mode else "CASINO TABLE MODE"
        subtitle = self.font_mono.render(subtitle_text, True, C_GOLD if self.plus_mode else C_GRAY_LIGHT)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 150)))
        panel = pygame.Rect(326, 215, 628, 440)
        premium_panel(self.canvas, panel, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=226, glow=False)
        for field in self.fields:
            field.draw(self.canvas, self.font_label, self.font_body)
        mode_rect = self.mode_button.rect
        pygame.draw.rect(self.canvas, C_BG_DEEP, mode_rect, border_radius=18)
        pygame.draw.rect(self.canvas, C_BORDER_SUBTLE, mode_rect, width=1, border_radius=18)
        classic_rect = pygame.Rect(mode_rect.x + 6, mode_rect.y + 6, mode_rect.w // 2 - 9, mode_rect.h - 12)
        plus_rect = pygame.Rect(mode_rect.centerx + 3, mode_rect.y + 6, mode_rect.w // 2 - 9, mode_rect.h - 12)
        for label, rect, active in (("MODO CLASICO", classic_rect, not self.plus_mode), ("MODO PLUS", plus_rect, self.plus_mode)):
            if active:
                draw_glow(self.canvas, rect, C_WHITE, 24, 10, 14)
                pygame.draw.rect(self.canvas, C_BG_ELEVATED, rect, border_radius=14)
                pygame.draw.rect(self.canvas, C_BORDER_ACTIVE, rect, width=1, border_radius=14)
            else:
                pygame.draw.rect(self.canvas, (12, 12, 13), rect, border_radius=14)
                pygame.draw.rect(self.canvas, C_BORDER_SUBTLE, rect, width=1, border_radius=14)
            color = C_WHITE_SOFT if active else C_GRAY_MID
            text = self.font_label.render(label, True, color)
            self.canvas.blit(text, text.get_rect(center=rect.center))
        if self.plus_mode:
            for index, button in enumerate(self.char_buttons):
                character = CHARACTER_BY_KEY[self.selected_characters[index]]
                rect = button.rect
                hovered = rect.collidepoint(self.mouse_pos)
                if hovered:
                    draw_glow(self.canvas, rect, C_WHITE, 18, 10, 16)
                pygame.draw.rect(self.canvas, C_BG_ELEVATED, rect, border_radius=18)
                pygame.draw.rect(self.canvas, C_BORDER_ACTIVE if hovered else C_BORDER_SUBTLE, rect, width=1, border_radius=18)
                icon_box = pygame.Rect(rect.x + 14, rect.y + 14, 38, 38)
                pygame.draw.circle(self.canvas, C_BG_DEEP, icon_box.center, 19)
                accent = C_GOLD if character.key in ("suertudo", "ambicioso") else (C_BORDER_ACTIVE if hovered else C_GRAY_MID)
                pygame.draw.circle(self.canvas, accent, icon_box.center, 19, 1)
                draw_geo_icon(self.canvas, icon_box.inflate(-8, -8), character.key, C_WHITE_SOFT, 190 if hovered else 145, 2)
                name = self.font_label.render(character.name.upper(), True, C_WHITE_SOFT)
                self.canvas.blit(name, (rect.x + 64, rect.y + 15))
                desc_text = CHARACTER_SHORT_TEXT.get(character.key, character.text)
                desc = self.font_hint.render(trim_text(desc_text, self.font_hint, rect.w - 78), True, C_GRAY_LIGHT)
                self.canvas.blit(desc, (rect.x + 64, rect.y + 40))
            hint_text = "Click en personaje para cambiar   H ayuda   F11 pantalla   ESC salir"
        else:
            hint_text = "H ayuda   F11 pantalla   ESC salir"
        hint = self.font_hint.render(hint_text, True, C_GRAY_DARK)
        self.canvas.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 682)))
        version = self.font_hint.render(f"v{VERSION}", True, C_GRAY_MID)
        self.canvas.blit(version, version.get_rect(bottomright=(SCREEN_W - 36, SCREEN_H - 28)))
        self.start_button.draw(self.canvas, self.font_button, self.mouse_pos)
        self.online_button.draw(self.canvas, self.font_button, self.mouse_pos)

    def draw_online_setup(self):
        logo = self.font_display.render("GENERALA PLUS ONLINE", True, C_WHITE_SOFT)
        self.canvas.blit(logo, logo.get_rect(center=(SCREEN_W // 2, 96)))
        subtitle = self.font_mono.render("MESA PRIVADA PLUS POR IP", True, C_GOLD)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 150)))
        panel = pygame.Rect(326, 215, 628, 440)
        premium_panel(self.canvas, panel, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=226, glow=False)
        self.online_name_field.draw(self.canvas, self.font_label, self.font_body)
        self.online_ip_field.draw(self.canvas, self.font_label, self.font_body)
        self.online_host_button.draw(self.canvas, self.font_button, self.mouse_pos)
        self.online_join_button.draw(self.canvas, self.font_button, self.mouse_pos)
        info = [
            "HOSTEAR abre una mesa Plus y te conecta como jugador.",
            "UNIRSE usa la IP del host. Puerto fijo: 8765.",
            "Para internet: misma Wi-Fi, Radmin VPN, Hamachi o ZeroTier.",
        ]
        y = 502
        for line in info:
            text = self.font_hint.render(line, True, C_GRAY_LIGHT)
            self.canvas.blit(text, text.get_rect(center=(SCREEN_W // 2, y)))
            y += 22
        if self.online_message:
            msg = self.font_hint_bold.render(trim_text(self.online_message, self.font_hint_bold, 540), True, C_GOLD)
            self.canvas.blit(msg, msg.get_rect(center=(SCREEN_W // 2, 558)))
        ip_hint = self.font_hint.render(trim_text(f"Tus IP posibles: {self.local_ip_hint()}", self.font_hint, 540), True, C_GRAY_MID)
        self.canvas.blit(ip_hint, ip_hint.get_rect(center=(SCREEN_W // 2, 578)))
        self.online_back_button.draw(self.canvas, self.font_label, self.mouse_pos)

    def local_ip_hint(self):
        try:
            host = socket.gethostname()
            addresses = socket.gethostbyname_ex(host)[2]
            ips = [ip for ip in addresses if not ip.startswith("127.")]
            return ", ".join(ips[:3]) if ips else "127.0.0.1"
        except OSError:
            return "127.0.0.1"

    def draw_online_game(self):
        snap = self.online_snapshot()
        state = snap.get("state")
        player_index = snap.get("player_index")
        if not state or player_index is None:
            self.draw_online_waiting(snap)
            return
        my_turn = state["active_player_index"] == player_index
        self.draw_online_header(state, player_index)
        self.draw_online_status(state, snap, my_turn)
        self.draw_online_dice(state)
        self.draw_online_left_panel(state, player_index)
        self.draw_online_right_panel(state, player_index)
        self.draw_online_scorecard(state, player_index)

        self.roll_button.enabled = my_turn and state["phase"] == "turn" and state["rolls"] < state["max_rolls"] and not all(state["held"])
        self.release_button.enabled = my_turn and state["phase"] == "turn" and any(state["held"])
        self.pass_button.enabled = my_turn and state["phase"] == "buy"
        self.roll_button.text = "ULTIMO TIRO" if state["rolls"] == state["max_rolls"] - 1 else "TIRAR DADOS"
        if state["phase"] == "turn":
            self.roll_button.draw(self.canvas, self.font_button, self.mouse_pos, pulse=self.roll_button.text == "ULTIMO TIRO")
            self.release_button.draw(self.canvas, self.font_label, self.mouse_pos)
        elif state["phase"] == "buy":
            self.pass_button.draw(self.canvas, self.font_button, self.mouse_pos)

    def draw_online_waiting(self, snap):
        self.draw_header_bar_title("GENERALA PLUS")
        panel = pygame.Rect(340, 230, 600, 230)
        premium_panel(self.canvas, panel, C_BG_PANEL, C_BORDER_ACTIVE, radius=22, alpha=230, glow=True)
        title = self.font_turn.render("ESPERANDO MESA", True, C_WHITE_SOFT)
        self.canvas.blit(title, title.get_rect(center=(panel.centerx, panel.y + 72)))
        msg = snap.get("error") or snap.get("info") or self.online_message
        text = self.font_body.render(trim_text(msg, self.font_body, panel.w - 80), True, C_GRAY_LIGHT)
        self.canvas.blit(text, text.get_rect(center=(panel.centerx, panel.y + 128)))
        hint = self.font_hint.render("ESC vuelve al menu online", True, C_GRAY_MID)
        self.canvas.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 176)))

    def draw_header_bar_title(self, title_text):
        header = pygame.Rect(HEADER_RECT)
        pygame.draw.rect(self.canvas, C_BG_DEEP, header)
        pygame.draw.line(self.canvas, C_BORDER_SUBTLE, (24, header.bottom), (SCREEN_W - 24, header.bottom), 1)
        title = self.font_turn.render(title_text, True, C_WHITE_SOFT)
        self.canvas.blit(title, (42, 20))

    def draw_online_header(self, state, player_index):
        self.draw_header_bar_title("GENERALA PLUS")
        badge = pygame.Rect(292, 30, 74, 20)
        pygame.draw.rect(self.canvas, C_BG_ELEVATED, badge, border_radius=10)
        pygame.draw.rect(self.canvas, C_GOLD, badge, width=1, border_radius=10)
        badge_text = self.font_hint_bold.render("ONLINE", True, C_GOLD)
        self.canvas.blit(badge_text, badge_text.get_rect(center=badge.center))
        active = state["players"][state["active_player_index"]]["name"].upper()
        turn_label = self.font_label.render(f"TURNO DE {active}", True, C_WHITE_SOFT)
        self.canvas.blit(turn_label, turn_label.get_rect(center=(SCREEN_W // 2, 28)))
        round_label = self.font_hint.render(f"RONDA {state['round_number']:02d}   VOS: JUGADOR {player_index + 1}", True, C_GRAY_MID)
        self.canvas.blit(round_label, round_label.get_rect(center=(SCREEN_W // 2, 52)))
        rolls = self.font_label.render(f"TIRADAS {state['rolls']}/{state['max_rolls']}", True, C_WHITE_SOFT)
        self.canvas.blit(rolls, rolls.get_rect(midright=(SCREEN_W - 190, 28)))
        menu = self.font_hint.render("H AYUDA   ESC SALIR ONLINE", True, C_GRAY_MID)
        self.canvas.blit(menu, menu.get_rect(midright=(SCREEN_W - 42, 53)))

    def draw_online_status(self, state, snap, my_turn):
        rect = pygame.Rect(STATUS_RECT)
        pygame.draw.rect(self.canvas, C_BG_DEEP, rect, border_radius=18)
        pygame.draw.rect(self.canvas, C_GOLD if my_turn else C_BORDER_SUBTLE, rect, width=1, border_radius=18)
        msg = snap.get("error") or state.get("message") or snap.get("info") or ""
        if self.online_pending_card:
            if self.online_pending_card["type"] == "value":
                msg = "Presiona 1-6 para fijar el valor del dado."
            elif self.online_pending_card["type"] == "copy_target":
                msg = "Elegi el dado destino para Copia."
            else:
                msg = "Elegi un dado. Click derecho baja Ajuste fino."
        text = self.font_hint.render(trim_text(msg, self.font_hint, rect.w - 44), True, C_WHITE_SOFT)
        self.canvas.blit(text, text.get_rect(center=rect.center))

    def draw_online_dice(self, state):
        for index, value in enumerate(state["dice"]):
            rect = self.die_rect(index)
            hover = rect.inflate(16, 16).collidepoint(self.mouse_pos)
            selectable = bool(self.online_pending_card)
            marks = []
            if index in state.get("wildcard_indexes", []):
                marks.append("W")
            if index in state.get("golden_indexes", []):
                marks.append("G")
            if index in state.get("duplicator_indexes", []):
                marks.append("x2")
            DiceView.draw(self.canvas, rect, value, self.font_dice, selected=state["held"][index], hovered=hover, marks=marks, selectable=selectable)

    def draw_online_left_panel(self, state, player_index):
        left = pygame.Rect(LEFT_PANEL)
        premium_panel(self.canvas, left, C_BG_PANEL, C_BORDER_SUBTLE, radius=22, alpha=226, glow=False)
        me = state["players"][player_index]
        self.canvas.blit(self.font_hint_bold.render("PLUS ONLINE / TU MESA", True, C_GRAY_MID), (left.x + 22, left.y + 18))
        self.canvas.blit(self.font_body_bold.render(me["name"].upper(), True, C_WHITE_SOFT), (left.x + 22, left.y + 48))
        coins = self.font_score.render(f"{me['coins']}/10", True, C_GOLD)
        self.canvas.blit(coins, (left.right - 92, left.y + 92))
        self.canvas.blit(self.font_hint.render("MONEDAS", True, C_GRAY_MID), (left.x + 22, left.y + 98))
        hand = me["hand"] if isinstance(me["hand"], list) else []
        self.canvas.blit(self.font_label.render(f"MANO {len(hand)}/3", True, C_WHITE_SOFT), (left.x + 22, 350))
        rects = self.online_hand_rects(state)
        for index in range(3):
            rect = rects.get(index, pygame.Rect(56, 370 + index * 84, 196, 74))
            if index < len(hand):
                CardView.draw(self.canvas, rect, hand[index], self.card_fonts, compact=True, market=True, mouse_pos=self.mouse_pos, dimmed=state["phase"] != "turn")
            else:
                pygame.draw.rect(self.canvas, (5, 5, 6), rect, border_radius=16)
                pygame.draw.rect(self.canvas, C_BORDER_SUBTLE, rect, width=1, border_radius=16)
                empty = self.font_hint.render("VACIO", True, C_GRAY_DARK)
                self.canvas.blit(empty, empty.get_rect(center=rect.center))

    def draw_online_right_panel(self, state, player_index):
        right = pygame.Rect(RIGHT_PANEL)
        premium_panel(self.canvas, right, C_BG_PANEL, C_BORDER_SUBTLE, radius=22, alpha=226, glow=False)
        self.canvas.blit(self.font_hint_bold.render("MERCADO ONLINE", True, C_GRAY_MID), (right.x + 22, right.y + 212))
        for index, rect in self.online_market_rects(state).items():
            card_key = state["market"][index]
            CardView.draw(self.canvas, rect, card_key, self.card_fonts, compact=True, market=True, mouse_pos=self.mouse_pos, dimmed=state["phase"] != "buy")
        footer = "Compra una carta o PASAR." if state["phase"] == "buy" else "Mercado disponible tras anotar."
        text = self.font_hint.render(trim_text(footer, self.font_hint, right.w - 44), True, C_GRAY_MID)
        self.canvas.blit(text, (right.x + 22, right.bottom - 58))

    def draw_online_scorecard(self, state, player_index):
        panel = pygame.Rect(SCORE_SHEET_RECT)
        premium_panel(self.canvas, panel, C_BG_PANEL, C_BORDER_SUBTLE, radius=18, alpha=205, glow=False)
        self.canvas.blit(self.font_sheet_label_bold.render("CATEGORIA", True, C_GRAY_MID), (panel.x + 20, panel.y + 10))
        for index, player in enumerate(state["players"]):
            color = C_WHITE_SOFT if index == state["active_player_index"] else C_GRAY_MID
            label = self.font_sheet_label_bold.render(trim_text(player["name"].upper(), self.font_sheet_label_bold, 108), True, color)
            self.canvas.blit(label, label.get_rect(center=(panel.x + 265 + index * 150, panel.y + 16)))
        for row, (key, label) in enumerate(CATEGORIES):
            rect = self.online_category_rects(state)[key]
            hovered = rect.collidepoint(self.mouse_pos)
            if hovered:
                pygame.draw.rect(self.canvas, (255, 255, 255, 14), rect, border_radius=4)
            name = self.font_sheet_label.render(label.upper(), True, C_WHITE_SOFT if hovered else C_GRAY_MID)
            self.canvas.blit(name, (rect.x + 4, rect.y + 2))
            for index, player in enumerate(state["players"]):
                value = player["sheet"].get(key)
                color = C_GRAY_MID if value is None else (C_RED_ERROR if value == 0 else C_WHITE_SOFT)
                text = self.font_sheet_score.render("-" if value is None else str(value), True, color)
                self.canvas.blit(text, text.get_rect(center=(panel.x + 265 + index * 150, rect.centery)))
        total_y = panel.bottom - 30
        pygame.draw.line(self.canvas, C_BORDER_SUBTLE, (panel.x + 18, total_y - 8), (panel.right - 18, total_y - 8), 1)
        self.canvas.blit(self.font_label.render("TOTAL", True, C_WHITE_SOFT), (panel.x + 20, total_y))
        for index, player in enumerate(state["players"]):
            color = C_GOLD if index == player_index else C_WHITE_SOFT
            text = self.font_sheet_total.render(str(player["total"]), True, color)
            self.canvas.blit(text, text.get_rect(center=(panel.x + 265 + index * 150, total_y + 8)))

    def draw_game(self):
        self.update_buttons()
        self.draw_header()
        self.draw_status_capsule()
        self.draw_dice_area()
        if self.plus_mode:
            self.draw_plus_panels()
        self.draw_scorecard()
        if self.plus_mode and self.phase == "buy":
            overlay = pygame.Surface((SCORE_SHEET_RECT[2], SCORE_SHEET_RECT[3]), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 70))
            self.canvas.blit(overlay, (SCORE_SHEET_RECT[0], SCORE_SHEET_RECT[1]))
        self.roll_button.draw(self.canvas, self.font_button, self.mouse_pos, pulse=self.rolls == self.max_rolls_current - 1)
        self.release_button.draw(self.canvas, self.font_label, self.mouse_pos)
        if self.plus_mode:
            self.ability_button.draw(self.canvas, self.font_label, self.mouse_pos)
            self.event_button.draw(self.canvas, self.font_label, self.mouse_pos)
            if self.phase == "buy":
                self.pass_button.draw(self.canvas, self.font_button, self.mouse_pos)

    def draw_header(self):
        header = pygame.Rect(HEADER_RECT)
        pygame.draw.rect(self.canvas, C_BG_DEEP, header)
        pygame.draw.line(self.canvas, C_BORDER_SUBTLE, (24, header.bottom), (SCREEN_W - 24, header.bottom), 1)
        title_text = "GENERALA PLUS" if self.plus_mode else "GENERALA"
        title = self.font_turn.render(title_text, True, C_WHITE_SOFT)
        self.canvas.blit(title, (42, 20))
        active = self.current_player().name.upper()
        turn_label = self.font_label.render(f"TURNO DE {active}", True, C_WHITE_SOFT)
        self.canvas.blit(turn_label, turn_label.get_rect(center=(SCREEN_W // 2, 28)))
        round_label = self.font_hint.render(f"RONDA {self.round_number():02d}", True, C_GRAY_MID)
        self.canvas.blit(round_label, round_label.get_rect(center=(SCREEN_W // 2, 52)))
        rolls = self.font_label.render(f"TIRADAS {self.rolls}/{self.max_rolls_current}", True, C_WHITE_SOFT)
        self.canvas.blit(rolls, rolls.get_rect(midright=(SCREEN_W - 190, 28)))
        menu = self.font_hint.render("H AYUDA   F11 PANTALLA", True, C_GRAY_MID)
        self.canvas.blit(menu, menu.get_rect(midright=(SCREEN_W - 42, 53)))

    def draw_status_capsule(self):
        pulse = self.rolls == self.max_rolls_current - 1 and self.rolls > 0
        rect = pygame.Rect(STATUS_RECT)
        border = C_GOLD if pulse else C_BORDER_SUBTLE
        if pulse:
            draw_glow(self.canvas, rect, C_GOLD, 24 + 18 * math.sin(pygame.time.get_ticks() / 180), 16, 18)
        pygame.draw.rect(self.canvas, (*C_BG_DEEP, 255), rect, border_radius=18)
        pygame.draw.rect(self.canvas, border, rect, width=1, border_radius=18)
        message = self.font_hint.render(trim_text(self.message, self.font_hint, rect.w - 44), True, C_WHITE_SOFT)
        self.canvas.blit(message, message.get_rect(center=rect.center))

    def draw_dice_area(self):
        player = self.current_player()
        if self.pending_action and self.pending_action.get("type") not in ("declare_category", "rescue_category", "attack_candado", "recycle_market"):
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 92))
            self.canvas.blit(overlay, (0, 0))
        for index, value in enumerate(self.dice):
            rect = self.die_rect(index)
            hover = rect.inflate(16, 16).collidepoint(self.mouse_pos)
            selected = self.held[index]
            marks = []
            if self.plus_mode:
                if index in self.golden_indexes:
                    marks.append("G")
                if index in self.wildcard_indexes:
                    marks.append("W")
                if index in self.duplicator_indexes:
                    marks.append("x2")
            selectable = bool(self.pending_action) and self.pending_action.get("type") not in ("declare_category", "rescue_category", "attack_candado", "recycle_market")
            DiceView.draw(
                self.canvas,
                rect,
                value,
                self.font_dice,
                selected=selected,
                hovered=hover,
                rolling=self.rolling and not selected,
                marks=marks,
                selectable=selectable,
            )
            if self.phase == "buy":
                dim = pygame.Surface(rect.inflate(8, 8).size, pygame.SRCALPHA)
                pygame.draw.rect(dim, (0, 0, 0, 96), dim.get_rect(), border_radius=RADIUS["dice"])
                self.canvas.blit(dim, rect.inflate(8, 8).topleft)
        if self.pending_action:
            instruction = self.pending_instruction()
            if instruction:
                label = self.font_label.render(instruction.upper(), True, C_WHITE_SOFT)
                self.canvas.blit(label, label.get_rect(center=(SCREEN_W // 2, 168)))

    def draw_scorecard(self):
        players_count = len(self.players)
        table_w = COL_CAT + COL_PLAYER * players_count
        panel = pygame.Rect(SCORE_SHEET_RECT)
        start_x = panel.x + (panel.w - table_w) // 2
        table_layer = pygame.Surface(panel.size, pygame.SRCALPHA)
        base = table_layer.get_rect()
        pygame.draw.rect(table_layer, (5, 5, 6, 156), base, border_radius=18)
        pygame.draw.rect(table_layer, (244, 241, 234, 26), base, width=1, border_radius=18)
        pygame.draw.rect(table_layer, (255, 255, 255, 10), pygame.Rect(0, 0, panel.w, 28), border_radius=18)
        pygame.draw.rect(table_layer, (0, 0, 0, 58), pygame.Rect(0, panel.h - 34, panel.w, 34), border_radius=18)
        self.canvas.blit(table_layer, panel.topleft)

        self.canvas.blit(self.font_sheet_label_bold.render("CATEGORIA", True, C_GRAY_MID), (start_x + 12, panel.y + 9))
        rects = self.category_rects()
        row_start = next(iter(rects.values())).y if rects else panel.y + 29
        total_y = panel.bottom - 30
        for index, player in enumerate(self.players):
            x = start_x + COL_CAT + index * COL_PLAYER
            active = player is self.current_player()
            if active:
                header_tab = pygame.Rect(x + 12, panel.y + 6, COL_PLAYER - 30, 19)
                tab_layer = pygame.Surface(header_tab.size, pygame.SRCALPHA)
                pygame.draw.rect(tab_layer, (255, 255, 255, 22), tab_layer.get_rect(), border_radius=9)
                pygame.draw.rect(tab_layer, (201, 201, 201, 52), tab_layer.get_rect(), width=1, border_radius=9)
                self.canvas.blit(tab_layer, header_tab.topleft)
            name_color = C_WHITE if active else C_GRAY_MID
            text = self.font_sheet_label_bold.render(trim_text(player.name.upper(), self.font_sheet_label_bold, COL_PLAYER - 18), True, name_color)
            self.canvas.blit(text, text.get_rect(center=(x + COL_PLAYER // 2 - 8, panel.y + 17)))

        header_line_y = panel.y + 26
        pygame.draw.line(self.canvas, (74, 74, 74), (start_x + 8, header_line_y), (start_x + table_w - 8, header_line_y), 1)

        hover_key = self.category_at(self.mouse_pos)
        active_player = self.current_player()
        for row, (key, label) in enumerate(CATEGORIES):
            rect = rects[key]
            y = rect.y
            if row % 2 == 1:
                row_layer = pygame.Surface((table_w - 16, ROW_H), pygame.SRCALPHA)
                pygame.draw.rect(row_layer, (255, 255, 255, 5), row_layer.get_rect(), border_radius=3)
                self.canvas.blit(row_layer, (start_x + 8, y))
            if row in (6, 10):
                pygame.draw.line(self.canvas, (86, 86, 86), (start_x + 8, y - 3), (start_x + table_w - 8, y - 3), 1)
            hovered = hover_key == key and self.rolls > 0 and active_player.sheet[key] is None
            blocked = self.plus_mode and active_player.blocked_category == key
            if hovered or blocked:
                bg = C_BG_ELEVATED if hovered else (18, 9, 9)
                pygame.draw.rect(self.canvas, bg, rect, border_radius=4)
            pygame.draw.line(self.canvas, (24, 24, 24), (start_x + 10, y + ROW_H - 1), (start_x + table_w - 10, y + ROW_H - 1), 1)
            if blocked:
                for x in range(rect.x, rect.right, 12):
                    pygame.draw.line(self.canvas, (139, 30, 30, 55), (x, rect.bottom), (x + ROW_H, rect.y), 1)
            if hovered:
                pygame.draw.line(self.canvas, C_WHITE, (rect.x, rect.y + 3), (rect.x, rect.bottom - 3), 2)
                self.spawn_hover_sparks(rect)
            label_color = C_WHITE if hovered else C_GRAY_MID
            if blocked:
                label_color = C_RED_ERROR
            if key == "generala" and active_player.sheet.get("generala") == 60:
                label_color = C_GOLD
            self.canvas.blit(self.font_sheet_label_bold.render(label.upper(), True, label_color), (start_x + 12, y + 3))
            for player_index, player in enumerate(self.players):
                x = start_x + COL_CAT + player_index * COL_PLAYER
                value = player.sheet[key]
                is_active_cell = player is active_player
                if value is None:
                    if blocked and is_active_cell:
                        text_value = "BLOQ"
                        color = C_RED_ERROR
                    elif is_active_cell and self.rolls > 0:
                        preview = self.preview_plus_score(key).points if self.plus_mode else score_category(key, self.dice, self.rolls, player.sheet)
                        if preview:
                            text_value = f"({preview})"
                            color = C_GOLD if key in SPECIAL_CATEGORIES else C_GRAY_LIGHT
                        else:
                            text_value = "-"
                            color = C_GRAY_DARK
                    else:
                        text_value = "-"
                        color = C_GRAY_DARK
                else:
                    text_value = "0" if value == 0 else str(value)
                    color = C_RED_ERROR if value == 0 else C_WHITE
                    if key == "generala" and value == 60:
                        color = C_GOLD
                rendered = self.font_sheet_score.render(text_value, True, color)
                self.canvas.blit(rendered, rendered.get_rect(center=(x + COL_PLAYER // 2 - 8, y + ROW_H // 2)))
                if value == 0:
                    pygame.draw.line(self.canvas, C_RED_ERROR, (x + 22, y + ROW_H - 4), (x + COL_PLAYER - 36, y + 4), 1)

        pygame.draw.line(self.canvas, (96, 96, 96), (start_x + 8, total_y), (start_x + table_w - 8, total_y), 1)
        self.canvas.blit(self.font_label.render("TOTAL", True, C_WHITE_SOFT), (start_x + 10, total_y + 9))
        for index, player in enumerate(self.players):
            x = start_x + COL_CAT + index * COL_PLAYER
            color = C_WHITE if player is active_player else C_GRAY_LIGHT
            total = self.font_sheet_total.render(str(player.total), True, color)
            self.canvas.blit(total, total.get_rect(center=(x + COL_PLAYER // 2 - 8, total_y + 16)))

    def draw_plus_panels(self):
        player = self.current_player()
        left = pygame.Rect(LEFT_PANEL)
        right = pygame.Rect(RIGHT_PANEL)
        premium_panel(self.canvas, left, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=210)
        premium_panel(self.canvas, right, C_BG_PANEL, C_BORDER_SUBTLE, radius=20, alpha=210)

        phase_text = "COMPRA" if self.phase == "buy" else "TURNO"
        self.canvas.blit(self.font_hint_bold.render(f"PLUS / {phase_text}", True, C_GRAY_MID), (left.x + 22, left.y + 18))
        name = self.font_body_bold.render(trim_text(player.name.upper(), self.font_body_bold, 220), True, C_WHITE)
        self.canvas.blit(name, (left.x + 22, left.y + 44))
        character = player.character
        avatar = pygame.Rect(left.x + 22, left.y + 78, 54, 54)
        pygame.draw.circle(self.canvas, C_BG_DEEP, avatar.center, 27)
        avatar_accent = C_GOLD if character.key in ("ambicioso", "suertudo") else C_BORDER_ACTIVE
        pygame.draw.circle(self.canvas, avatar_accent, avatar.center, 27, 1)
        pygame.draw.circle(self.canvas, (*avatar_accent, 40), avatar.center, 20, 1)
        draw_geo_icon(self.canvas, avatar.inflate(-14, -14), character.key, C_WHITE_SOFT, 185, 2)
        self.canvas.blit(self.font_label.render(character.name.upper(), True, C_WHITE_SOFT), (left.x + 88, left.y + 78))
        self.canvas.blit(self.font_hint.render(trim_text(character.ability, self.font_hint, 160), True, C_GRAY_LIGHT), (left.x + 88, left.y + 99))
        short_character = CHARACTER_SHORT_TEXT.get(character.key, character.text)
        self.canvas.blit(self.font_hint.render(trim_text(short_character, self.font_hint, 160), True, C_GRAY_MID), (left.x + 88, left.y + 116))
        if character.passive:
            status_text = "PASIVA"
            status_border = C_BORDER_ACTIVE
        elif self.ability_used_this_turn:
            status_text = "USADA"
            status_border = C_GRAY_DARK
        elif self.can_use_active_ability():
            status_text = "LISTA"
            status_border = C_GOLD
        else:
            remaining = max(0, character.cooldown - (player.turns_played - player.ability_last_turn))
            status_text = f"CD {remaining}" if remaining else "NO LISTA"
            status_border = C_BORDER_SUBTLE
        draw_chip(self.canvas, pygame.Rect(left.x + 88, left.y + 134, 78, 18), status_text, self.font_hint, C_GRAY_LIGHT, status_border, fill=C_BG_DEEP)
        for dot in range(max(1, character.cooldown)):
            dot_x = left.x + 174 + dot * 9
            filled = dot < max(0, min(character.cooldown, player.turns_played - player.ability_last_turn))
            pygame.draw.circle(self.canvas, C_GOLD if filled and not character.passive else C_GRAY_DARK, (dot_x, left.y + 143), 3)
        self.canvas.blit(self.font_hint_bold.render("MONEDAS", True, C_GRAY_MID), (left.x + 22, left.y + 154))
        for index in range(PLUS_MAX_COINS):
            cx = left.x + 24 + index * 16
            cy = left.y + 184
            filled = index < player.coins
            draw_premium_coin(self.canvas, (cx, cy), 7, filled=filled, alpha=255 if filled else 96)
        coin_text = self.font_score.render(f"{player.coins}/{PLUS_MAX_COINS}", True, C_GOLD)
        self.canvas.blit(coin_text, coin_text.get_rect(midright=(left.right - 22, left.y + 184)))
        extra_total = self.font_hint.render(f"EXTRAS {player.bonus_total:+d}", True, C_GOLD if player.bonus_total > 0 else (C_RED_ERROR if player.bonus_total < 0 else C_GRAY_MID))
        self.canvas.blit(extra_total, (left.x + 22, left.y + 202))
        extras = []
        if player.temp_shield:
            extras.append("ESCUDO")
        if player.blocked_category:
            extras.append(f"CANDADO: {category_name(player.blocked_category).upper()}")
        if self.card_used_this_turn:
            extras.append("CARTA USADA")
        if self.ability_used_this_turn:
            extras.append("HABILIDAD USADA")
        chip_x = left.x + 22
        chip_y = left.y + 226
        for text in extras[:4]:
            border = C_GOLD if "BONUS" in text else (C_RED_ERROR if "CANDADO" in text else C_BORDER_ACTIVE)
            draw_chip(self.canvas, pygame.Rect(chip_x, chip_y, min(104, 28 + len(text) * 6), 24), text, self.font_hint, C_GRAY_LIGHT, border)
            chip_x += min(112, 36 + len(text) * 6)
            if chip_x > left.right - 95:
                chip_x = left.x + 22
                chip_y += 28

        self.ability_button.text = "USAR HABILIDAD"
        self.event_button.text = "USAR EVENTO"
        hand_color = C_WHITE_SOFT if len(player.hand) >= hand_limit(player) else C_GRAY_MID
        hand_label = self.font_label.render(f"MANO {len(player.hand)}/{hand_limit(player)}", True, hand_color)
        self.canvas.blit(hand_label, (left.x + 22, left.y + 260))
        for index, rect in enumerate(self.hand_card_rects()):
            card_key = player.hand[index] if index < len(player.hand) else None
            hand_enabled = card_key is not None and self.phase in ("turn", "buy")
            self.draw_card_slot(rect, card_key, enabled=hand_enabled, compact=True)
        if self.phase == "buy":
            discard_hint = self.font_hint.render("Click en tu mano descarta.", True, C_GRAY_DARK)
            self.canvas.blit(discard_hint, (left.x + 22, left.bottom - 28))

        round_no = self.round_number()
        event_name = self.active_event.name if self.active_event else "Sin evento"
        self.canvas.blit(self.font_hint_bold.render(f"RONDA {round_no:02d}", True, C_GRAY_MID), (right.x + 22, right.y + 18))
        event_rect = pygame.Rect(right.x + 22, right.y + 44, 232, 86)
        event_border = C_GOLD if self.active_event_key() == "dorada" else (C_RED_ERROR if self.active_event_key() in ("caotica", "presion") else C_BORDER_ACTIVE)
        event_layer = pygame.Surface(event_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(event_layer, (*C_BG_DEEP, 246), event_layer.get_rect(), border_radius=18)
        pygame.draw.rect(event_layer, (*event_border, 168), event_layer.get_rect(), width=1, border_radius=18)
        event_layer.blit(pygame.Surface(event_rect.size, pygame.SRCALPHA), (0, 0))
        self.canvas.blit(event_layer, event_rect.topleft)
        icon_key = self.active_event_key() or "clasica"
        icon_rect = pygame.Rect(event_rect.x + 14, event_rect.y + 20, 34, 34)
        pygame.draw.circle(self.canvas, C_BG_PANEL, icon_rect.center, 18)
        pygame.draw.circle(self.canvas, event_border, icon_rect.center, 18, 1)
        draw_geo_icon(self.canvas, icon_rect.inflate(-7, -7), icon_key, event_border, 165, 2)
        event = self.font_label.render(trim_text(event_name.upper(), self.font_label, event_rect.w - 76), True, C_GOLD if self.active_event_key() == "dorada" else C_WHITE_SOFT)
        self.canvas.blit(event, (event_rect.x + 58, event_rect.y + 16))
        detail_text = self.active_event.text if self.active_event else "Mesa limpia. Sin evento activo."
        detail = self.font_hint.render(trim_text(detail_text, self.font_hint, event_rect.w - 76), True, C_GRAY_LIGHT)
        self.canvas.blit(detail, (event_rect.x + 58, event_rect.y + 43))
        deck_a = pygame.Rect(right.x + 22, right.y + 152, 88, 34)
        deck_b = pygame.Rect(right.x + 122, right.y + 152, 104, 34)
        draw_chip(self.canvas, deck_a, f"MAZO {len(self.deck)}", self.font_hint, C_GRAY_LIGHT, C_BORDER_SUBTLE)
        draw_chip(self.canvas, deck_b, f"DESCARTE {len(self.discard)}", self.font_hint, C_GRAY_LIGHT, C_BORDER_SUBTLE)
        self.canvas.blit(self.font_label.render("MERCADO", True, C_GRAY_MID), (right.x + 22, right.y + 206))
        for index, rect in enumerate(self.market_card_rects()):
            card_key = self.market[index] if index < len(self.market) else None
            enabled = self.phase == "buy" and self.active_event_key() != "austera"
            self.draw_card_slot(rect, card_key, enabled=enabled, market=True, market_index=index, compact=True)
        if self.phase == "buy":
            hint = "Click compra. Click derecho renueva por 1."
        elif self.is_classic_round():
            hint = "Ronda clasica: solo dados."
        else:
            hint = "Compra disponible despues de anotar."
        hint_y = 632 if self.phase == "buy" else right.bottom - 28
        self.canvas.blit(self.font_hint.render(trim_text(hint, self.font_hint, 240), True, C_GRAY_DARK), (right.x + 22, hint_y))

    def draw_card_slot(self, rect, card_key, enabled=False, market=False, market_index=0, compact=False):
        cost = None
        discount = False
        if market and card_key:
            player = self.current_player()
            discount = self.active_event_key() == "descuento" and self.players.index(player) not in self.discount_buyers
            cost = display_card_cost(card_key, player, self.active_event_key(), discount)
            if player.coins < cost or self.active_event_key() == "austera":
                enabled = False
        CardView.draw(
            self.canvas,
            rect,
            card_key,
            self.card_fonts,
            enabled=enabled,
            compact=compact,
            market=market,
            cost=cost,
            discount=discount,
            mouse_pos=self.mouse_pos,
            dimmed=market and self.phase != "buy",
        )

    def draw_context_tooltip(self):
        data = self.tooltip_data_at_mouse()
        if not data:
            return
        self.draw_premium_tooltip(**data)

    def tooltip_data_at_mouse(self):
        if self.state == "start":
            return self.start_tooltip()
        if self.state == "end":
            if self.restart_button.rect.collidepoint(self.mouse_pos):
                return {
                    "title": "NUEVA PARTIDA",
                    "lines": ["Reinicia la mesa y vuelve al menu principal.", "Tambien puedes presionar R en la pantalla final."],
                    "anchor": self.restart_button.rect,
                    "icon_key": "clasica",
                    "accent": C_GOLD,
                }
            return None
        if self.state != "game":
            return None
        if self.plus_mode:
            data = self.plus_tooltip()
            if data:
                return data
        return self.core_game_tooltip()

    def start_tooltip(self):
        for index, button in enumerate(self.char_buttons):
            if self.plus_mode and button.rect.collidepoint(self.mouse_pos):
                character = CHARACTER_BY_KEY[self.selected_characters[index]]
                return {
                    "title": character.name.upper(),
                    "lines": [self.info_character_detail(character), "Click para cambiar el personaje de este jugador antes de iniciar."],
                    "anchor": button.rect,
                    "icon_key": character.key,
                    "accent": C_GOLD if character.key in ("suertudo", "ambicioso") else C_BORDER_ACTIVE,
                }
        if self.mode_button.rect.collidepoint(self.mouse_pos):
            return {
                "title": "MODO DE JUEGO",
                "lines": ["Alterna entre Generala clasica y Generala Plus.", "Plus conserva la base de dados y suma cartas, monedas, personajes, eventos y mercado visible."],
                "anchor": self.mode_button.rect,
                "icon_key": "comodin",
                "accent": C_BORDER_ACTIVE,
            }
        if self.start_button.rect.collidepoint(self.mouse_pos):
            return {
                "title": "INICIAR PARTIDA",
                "lines": ["Crea la mesa con los nombres, modo y personajes seleccionados.", "En Plus cada jugador empieza con 1 moneda y mano vacia."],
                "anchor": self.start_button.rect,
                "icon_key": "dado_dorado",
                "accent": C_GOLD,
            }
        return None

    def plus_tooltip(self):
        player = self.current_player()
        for index, rect in enumerate(self.hand_card_rects()):
            if index < len(player.hand) and rect.collidepoint(self.mouse_pos):
                return self.card_tooltip(player.hand[index], rect, source="mano")
            if index >= len(player.hand) and rect.collidepoint(self.mouse_pos):
                return {
                    "title": "SLOT VACIO",
                    "lines": [f"Espacio disponible en la mano. Limite actual: {hand_limit(player)} carta(s).", "Compra cartas al final del turno para llenar estos espacios."],
                    "anchor": rect,
                    "icon_key": "coleccionista",
                    "accent": C_GRAY_MID,
                }
        for index, rect in enumerate(self.market_card_rects()):
            if index < len(self.market) and rect.collidepoint(self.mouse_pos):
                return self.card_tooltip(self.market[index], rect, source="mercado")

        coins_rect = pygame.Rect(LEFT_PANEL[0] + 18, LEFT_PANEL[1] + 148, LEFT_PANEL[2] - 36, 48)
        if coins_rect.collidepoint(self.mouse_pos):
            return {
                "title": f"MONEDAS {player.coins}/{PLUS_MAX_COINS}",
                "lines": ["Recurso del modo Plus para comprar cartas y renovar mercado.", "Ganas monedas al iniciar turno, anotar categorias, hacer jugadas especiales, tachar o no usar cartas.", "No puedes superar el limite maximo."],
                "anchor": coins_rect,
                "icon_key": "dado_dorado",
                "accent": C_GOLD,
            }

        character_rect = pygame.Rect(LEFT_PANEL[0] + 20, LEFT_PANEL[1] + 76, LEFT_PANEL[2] - 40, 78)
        if character_rect.collidepoint(self.mouse_pos):
            character = player.character
            return {
                "title": character.name.upper(),
                "lines": [self.info_character_detail(character), self.ability_status_text()],
                "anchor": character_rect,
                "icon_key": character.key,
                "accent": C_GOLD if character.key in ("suertudo", "ambicioso") else C_BORDER_ACTIVE,
            }

        event_rect = pygame.Rect(RIGHT_PANEL[0] + 22, RIGHT_PANEL[1] + 44, 232, 86)
        if event_rect.collidepoint(self.mouse_pos):
            event = self.active_event or CLASSIC_EVENT
            key = self.active_event_key() or "clasica"
            icon_key = key if key != "espejo" else "espejo_evento"
            return {
                "title": event.name.upper() if self.active_event else "SIN EVENTO",
                "lines": [self.info_event_detail(event) if self.active_event else "Mesa limpia: no hay regla global activa en esta ronda.", self.event_action_status_text()],
                "anchor": event_rect,
                "icon_key": icon_key,
                "accent": C_GOLD if key == "dorada" else (C_RED_ERROR if key in ("caotica", "presion") else C_BORDER_ACTIVE),
            }

        deck_rect = pygame.Rect(RIGHT_PANEL[0] + 22, RIGHT_PANEL[1] + 152, 204, 34)
        if deck_rect.collidepoint(self.mouse_pos):
            return {
                "title": "MAZO Y DESCARTE",
                "lines": [f"Mazo: {len(self.deck)} carta(s). Descarte: {len(self.discard)} carta(s).", "Cuando compras una carta, sale del mercado y se repone desde el mazo."],
                "anchor": deck_rect,
                "icon_key": "reciclaje",
                "accent": C_BORDER_ACTIVE,
            }

        market_title_rect = pygame.Rect(RIGHT_PANEL[0] + 18, RIGHT_PANEL[1] + 198, RIGHT_PANEL[2] - 36, 28)
        if market_title_rect.collidepoint(self.mouse_pos):
            return {
                "title": "MERCADO",
                "lines": ["Muestra 3 cartas visibles para reducir azar oculto.", "En fase compra: click izquierdo compra, click derecho renueva una carta por 1 moneda."],
                "anchor": market_title_rect,
                "icon_key": "reciclaje",
                "accent": C_BORDER_ACTIVE,
            }

        if self.ability_button.rect.collidepoint(self.mouse_pos):
            character = player.character
            return {
                "title": "USAR HABILIDAD",
                "lines": [self.info_character_detail(character), self.ability_status_text()],
                "anchor": self.ability_button.rect,
                "icon_key": character.key,
                "accent": C_GOLD if self.can_use_active_ability() else C_GRAY_MID,
            }
        if self.event_button.rect.collidepoint(self.mouse_pos):
            return {
                "title": "USAR EVENTO",
                "lines": [self.event_action_status_text(), "Solo algunos eventos tienen accion manual. La Ronda Espejo permite invertir un dado gratis una vez."],
                "anchor": self.event_button.rect,
                "icon_key": "espejo_evento",
                "accent": C_GOLD if self.can_use_event_action() else C_GRAY_MID,
            }
        if self.phase == "buy" and self.pass_button.rect.collidepoint(self.mouse_pos):
            return {
                "title": "PASAR COMPRA",
                "lines": ["Termina la fase de compra sin adquirir ni renovar cartas.", "El turno pasa al siguiente jugador."],
                "anchor": self.pass_button.rect,
                "icon_key": "clasica",
                "accent": C_BORDER_ACTIVE,
            }
        return None

    def core_game_tooltip(self):
        for index in range(DICE_COUNT):
            rect = self.die_rect(index).inflate(16, 16)
            if rect.collidepoint(self.mouse_pos):
                value = self.dice[index]
                state = "retenido" if self.held[index] else "libre"
                lines = [f"Dado {index + 1}: valor {value}, estado {state}.", "Click izquierdo retiene o libera este dado. Click derecho sobre cualquier dado libera todos los dados retenidos."]
                if self.pending_action:
                    lines.append(self.pending_instruction())
                elif self.rolls == 0:
                    lines.append("Primero tira los dados para poder retener.")
                return {
                    "title": "DADO",
                    "lines": lines,
                    "anchor": rect,
                    "icon_key": "clasica",
                    "accent": C_GOLD if self.held[index] else C_BORDER_ACTIVE,
                }

        category = self.category_at(self.mouse_pos)
        if category:
            rect = self.category_rects()[category]
            label = category_name(category)
            player = self.current_player()
            value = player.sheet[category]
            lines = []
            if value is None:
                if self.plus_mode and player.blocked_category == category:
                    lines.append("Esta categoria esta bloqueada por Candado durante este turno.")
                elif self.rolls > 0:
                    result = self.preview_plus_score(category) if self.plus_mode else None
                    preview = result.points if result else score_category(category, self.dice, self.rolls, player.sheet)
                    lines.append(f"Preview actual: {preview if preview else 0} puntos.")
                    if self.plus_mode and result and result.special:
                        lines.append("Natural si no usaste ayuda; asistida si hubo carta, habilidad o evento.")
                    lines.append("Click para anotar esta categoria.")
                else:
                    lines.append("Tira los dados antes de anotar una categoria.")
            else:
                lines.append(f"Categoria ya anotada con {value} punto(s).")
                if value == 0:
                    lines.append("Fue tachada: no puede volver a usarse.")
            return {
                "title": label.upper(),
                "lines": lines,
                "anchor": rect,
                "icon_key": "candado_activo" if self.plus_mode and player.blocked_category == category else ("penalizacion" if value == 0 else "tecnico"),
                "accent": C_RED_ERROR if (value == 0 or (self.plus_mode and player.blocked_category == category)) else C_GOLD,
            }

        if self.roll_button.rect.collidepoint(self.mouse_pos):
            lines = ["Tira los dados libres del turno."]
            if not self.roll_button.enabled:
                lines.append(self.roll_disabled_reason())
            elif self.rolls == self.max_rolls_current - 1:
                lines.append("Esta es tu ultima tirada disponible.")
            return {
                "title": self.roll_button.text,
                "lines": lines,
                "anchor": self.roll_button.rect,
                "icon_key": "tirada_extra",
                "accent": C_GOLD if self.roll_button.enabled else C_GRAY_MID,
            }
        if self.release_button.rect.collidepoint(self.mouse_pos):
            return {
                "title": "SOLTAR",
                "lines": ["Libera todos los dados retenidos.", "Tambien puedes presionar L o hacer click derecho sobre un dado." if any(self.held) else "No hay dados retenidos ahora."],
                "anchor": self.release_button.rect,
                "icon_key": "mano_estable",
                "accent": C_BORDER_ACTIVE if self.release_button.enabled else C_GRAY_MID,
            }
        return None

    def card_tooltip(self, card_key, anchor, source):
        card = CARD_DEFS[card_key]
        player = self.current_player()
        accent = CardView.accent(card_key)
        tier = "ATAQUE" if card_key in ATTACK_CARDS else card.tier.upper()
        if source == "mercado":
            discount = self.active_event_key() == "descuento" and self.players.index(player) not in self.discount_buyers
            cost = display_card_cost(card_key, player, self.active_event_key(), discount)
            lines = [self.info_card_detail(card_key, card)]
            if cost != card.cost:
                lines.append(f"Costo actual en este mercado: {cost} moneda(s), modificado por descuento o personaje.")
            lines.append(self.market_card_status_text(cost))
        else:
            lines = [self.info_card_detail(card_key, card), self.hand_card_status_text(card_key)]
        return {
            "title": card.name.upper(),
            "lines": lines,
            "anchor": anchor,
            "icon_key": card_key,
            "accent": accent,
        }

    def hand_card_status_text(self, card_key):
        if self.is_classic_round():
            return "No se puede usar ahora: la ronda clasica bloquea cartas, habilidades y ataques."
        if self.phase != "turn":
            return "No se puede usar ahora: las cartas de mano se usan durante la fase de turno."
        if self.card_used_this_turn:
            return "No se puede usar ahora: ya usaste la carta permitida este turno."
        if card_key in ATTACK_CARDS and self.rolls > 0:
            return "No se puede usar ahora: los ataques solo se juegan antes de tirar."
        if self.rolls == 0 and card_key not in ("escudo", "rescate", "reciclaje", "tirada_extra", "no_cuenta") and card_key not in ATTACK_CARDS:
            return "Primero tira los dados para que esta carta tenga objetivo."
        return "Disponible: click para preparar o usar esta carta."

    def market_card_status_text(self, cost):
        player = self.current_player()
        if self.phase != "buy":
            return "Compra disponible despues de anotar categoria, durante la fase de compra."
        if self.active_event_key() == "austera":
            return "No se puede comprar: Ronda Austera bloquea compras."
        if len(player.hand) >= hand_limit(player):
            return "No se puede comprar: tu mano esta llena. Descarta una carta antes."
        if player.coins < cost:
            return f"No se puede comprar: necesitas {cost} moneda(s) y tienes {player.coins}."
        return "Disponible: click izquierdo compra. Click derecho renueva por 1 moneda."

    def ability_status_text(self):
        if self.can_use_active_ability():
            return "Disponible: puedes usar esta habilidad ahora."
        if not self.plus_mode or self.state != "game":
            return "No disponible fuera de una partida Plus."
        if self.phase != "turn":
            return "No disponible: las habilidades se usan durante la fase de turno."
        if self.rolling:
            return "No disponible mientras los dados estan rodando."
        if self.is_classic_round():
            return "No disponible: la Ronda Clasica bloquea habilidades."
        if self.ability_used_this_turn:
            return "No disponible: ya usaste una habilidad este turno."
        player = self.current_player()
        character = player.character
        if character.passive:
            return "Habilidad pasiva: no usa boton, se aplica automaticamente cuando corresponde."
        if character.once and player.ability_once_used:
            return "No disponible: esta habilidad de uso unico ya fue usada."
        remaining = character.cooldown - (player.turns_played - player.ability_last_turn)
        if remaining > 0:
            return f"No disponible: cooldown activo, falta(n) {remaining} turno(s)."
        if character.key in ("matematico", "tecnico") and self.rolls == 0:
            return "No disponible: primero tira los dados para evaluar o modificar."
        if character.key == "apostador" and self.rolls != 0:
            return "No disponible: El Apostador debe declarar antes de tirar."
        if character.key == "precavido" and self.rolls < self.max_rolls_current:
            return "No disponible: Plan B solo aparece tras agotar las tiradas."
        return "No disponible en este momento."

    def event_action_status_text(self):
        if self.can_use_event_action():
            return "Disponible: puedes activar la accion manual del evento."
        if not self.active_event:
            return "No hay evento activo en esta ronda."
        if self.is_classic_round():
            return "Ronda Clasica: no hay acciones especiales."
        if self.active_event_key() != "espejo":
            return "Este evento no tiene boton manual; su efecto se aplica automaticamente."
        if self.phase != "turn":
            return "La accion del evento solo se usa durante la fase de turno."
        if self.rolls == 0:
            return "Primero tira los dados para poder elegir un dado."
        if self.event_action_used:
            return "Ya usaste la accion del evento en este turno."
        return "No disponible en este momento."

    def roll_disabled_reason(self):
        if self.rolling:
            return "Los dados ya estan rodando."
        if self.phase != "turn":
            return "No puedes tirar durante la fase de compra."
        if self.rolls >= self.max_rolls_current:
            return "No quedan tiradas disponibles."
        if all(self.held):
            return "Todos los dados estan retenidos; libera alguno o anota."
        return "No disponible en este momento."

    def draw_premium_tooltip(self, title, lines, anchor, icon_key="tecnico", accent=C_BORDER_ACTIVE):
        anchor = pygame.Rect(anchor)
        width = 344
        max_text_w = width - 76
        wrapped = []
        for index, line in enumerate(lines):
            if index:
                wrapped.append("")
            wrapped.extend(self.wrap_info_text(line, self.font_hint, max_text_w))
        height = max(96, 62 + len(wrapped) * 13)
        max_height = SCREEN_H - 128
        truncated = height > max_height
        height = min(height, max_height)
        x = anchor.right + 14
        if x + width > SCREEN_W - 24:
            x = anchor.left - width - 14
        if x < 24:
            x = SCREEN_W // 2 - width // 2
        y = anchor.y + anchor.h // 2 - height // 2
        y = max(88, min(SCREEN_H - height - 24, y))
        rect = pygame.Rect(x, y, width, height)
        draw_glow(self.canvas, rect, accent, 16, 12, 16)
        draw_soft_shadow(self.canvas, rect, alpha=170, spread=14, radius=16, y_offset=7)
        pygame.draw.rect(self.canvas, (5, 5, 6), rect, border_radius=16)
        pygame.draw.rect(self.canvas, accent, rect, width=1, border_radius=16)
        pygame.draw.line(self.canvas, (*accent, 120), (rect.x + 18, rect.y + 48), (rect.right - 18, rect.y + 48), 1)
        icon_rect = pygame.Rect(rect.x + 16, rect.y + 14, 28, 28)
        pygame.draw.circle(self.canvas, C_BG_PANEL, icon_rect.center, 15)
        pygame.draw.circle(self.canvas, accent, icon_rect.center, 15, 1)
        draw_geo_icon(self.canvas, icon_rect.inflate(-6, -6), icon_key, accent, 180, 2)
        title_surf = self.font_label.render(trim_text(title.upper(), self.font_label, width - 72), True, C_WHITE_SOFT)
        self.canvas.blit(title_surf, (rect.x + 54, rect.y + 16))
        text_y = rect.y + 60
        bottom_limit = rect.bottom - 14
        footer = "H abre informacion completa."
        for line in wrapped:
            if text_y + 12 > bottom_limit - (18 if truncated else 0):
                break
            if not line:
                text_y += 5
                continue
            color = C_GOLD if line.startswith("Disponible") else (C_RED_ERROR if line.startswith("No se puede") or line.startswith("No disponible") else C_GRAY_LIGHT)
            surf = self.font_hint.render(line, True, color)
            self.canvas.blit(surf, (rect.x + 18, text_y))
            text_y += 13
        if truncated:
            pygame.draw.line(self.canvas, (*accent, 70), (rect.x + 18, rect.bottom - 30), (rect.right - 18, rect.bottom - 30), 1)
            self.canvas.blit(self.font_hint.render(footer, True, C_GOLD), (rect.x + 18, rect.bottom - 24))

    def spawn_hover_sparks(self, rect):
        if random.random() > 0.18:
            return
        self.emit_particles(rect.x + random.randint(20, rect.w - 20), rect.y + rect.h // 2, C_WHITE, 1, speed=(30, 80), life=(0.45, 0.85), square=False)

    def draw_banner(self):
        if not self.banner:
            return
        t = max(0, min(1, self.banner["time"] / self.banner["duration"]))
        appear = 1 - abs(t - 0.5) * 2
        alpha = int(230 * min(1, t * 2))
        zone = pygame.Rect(PLAY_BANNER_RECT)
        rect = zone.inflate(-24, -8).move(0, -int((1 - t) * 8))
        layer = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(layer, (*C_BG_DEEP, alpha), pygame.Rect(0, 0, rect.w, rect.h), border_radius=20)
        pygame.draw.rect(layer, (*self.banner["color"], 180), pygame.Rect(0, 0, rect.w, rect.h), width=1, border_radius=20)
        rail_y = rect.h - 9
        rail_gap = 190
        pygame.draw.line(layer, (*self.banner["color"], 72), (34, rail_y), (rect.w // 2 - rail_gap // 2, rail_y), 1)
        pygame.draw.line(layer, (*self.banner["color"], 72), (rect.w // 2 + rail_gap // 2, rail_y), (rect.w - 34, rail_y), 1)
        if self.banner["color"] == C_GOLD:
            draw_glow(self.canvas, rect, C_GOLD, 30 * appear, 10, 20)
        self.canvas.blit(layer, rect.topleft)
        icon_rect = pygame.Rect(rect.x + 22, rect.y + 15, 34, 34)
        pygame.draw.circle(self.canvas, C_BG_PANEL, icon_rect.center, 18)
        pygame.draw.circle(self.canvas, self.banner["color"], icon_rect.center, 18, 1)
        draw_geo_icon(self.canvas, icon_rect.inflate(-7, -7), self.banner.get("key"), self.banner["color"], 190, 2)
        title_font = pygame.font.SysFont("Space Grotesk, Inter, Arial", 24, bold=True)
        text_center_x = rect.centerx + 10
        title = title_font.render(trim_text(self.banner["title"], title_font, rect.w - 118), True, self.banner["color"])
        detail = self.font_hint.render(trim_text(self.banner["detail"], self.font_hint, rect.w - 118), True, C_GRAY_LIGHT)
        self.canvas.blit(title, title.get_rect(center=(text_center_x, rect.y + 21)))
        self.canvas.blit(detail, detail.get_rect(center=(text_center_x, rect.y + 39)))

    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 214))
        self.canvas.blit(overlay, (0, 0))

        panel = pygame.Rect(390, 118, 500, 504)
        draw_glow(self.canvas, panel, C_GOLD, 18, 22, 24)
        premium_panel(self.canvas, panel, C_BG_ELEVATED, C_BORDER_ACTIVE, radius=24, alpha=246, glow=False)

        medallion = pygame.Rect(panel.centerx - 34, panel.y + 34, 68, 68)
        pygame.draw.circle(self.canvas, C_BG_DEEP, medallion.center, 34)
        pygame.draw.circle(self.canvas, C_GOLD, medallion.center, 34, 1)
        pygame.draw.circle(self.canvas, (*C_GOLD, 45), medallion.center, 24, 1)
        draw_geo_icon(self.canvas, medallion.inflate(-18, -18), "clasica", C_GOLD, 190, 2)

        title = self.font_turn.render("PAUSA", True, C_WHITE_SOFT)
        self.canvas.blit(title, title.get_rect(center=(panel.centerx, panel.y + 128)))
        subtitle = self.font_hint.render("Mesa suspendida. Elige como seguir.", True, C_GRAY_MID)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 158)))

        self.pause_resume_button.rect = pygame.Rect(470, 272, 340, 48)
        self.pause_resume_button.draw(self.canvas, self.font_button, self.mouse_pos)
        if self.show_sound_settings:
            self.pause_settings_button.rect = pygame.Rect(526, 548, 256, 36)
            self.pause_settings_button.text = "VOLVER"
            self.pause_mute_button.text = "SONIDO ON" if self.sound.enabled else "SONIDO OFF"
            self.draw_sound_settings(panel)
            self.pause_settings_button.draw(self.canvas, self.font_label, self.mouse_pos)
        else:
            self.pause_info_button.rect = pygame.Rect(470, 334, 340, 44)
            self.pause_settings_button.rect = pygame.Rect(470, 390, 340, 44)
            self.pause_menu_button.rect = pygame.Rect(470, 446, 340, 44)
            self.pause_quit_button.rect = pygame.Rect(470, 502, 340, 44)
            self.pause_settings_button.text = "SONIDO"
            self.pause_info_button.draw(self.canvas, self.font_label, self.mouse_pos)
            self.pause_settings_button.draw(self.canvas, self.font_label, self.mouse_pos)
            self.pause_menu_button.draw(self.canvas, self.font_label, self.mouse_pos)
            self.pause_quit_button.draw(self.canvas, self.font_label, self.mouse_pos)

            info_icon = pygame.Rect(self.pause_info_button.rect.right - 42, self.pause_info_button.rect.y + 10, 24, 24)
            pygame.draw.circle(self.canvas, C_BG_DEEP, info_icon.center, 12)
            pygame.draw.circle(self.canvas, C_BORDER_ACTIVE, info_icon.center, 12, 1)
            info_text = self.font_hint_bold.render("i", True, C_WHITE_SOFT)
            self.canvas.blit(info_text, info_text.get_rect(center=(info_icon.centerx, info_icon.centery - 1)))

        hint = self.font_hint.render("ESC continuar   H informacion   F11 pantalla completa", True, C_GOLD)
        self.canvas.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 20)))

    def draw_sound_settings(self, panel):
        title = self.font_label.render("AJUSTES DE SONIDO", True, C_GOLD)
        self.canvas.blit(title, title.get_rect(center=(panel.centerx, 340)))

        rows = [
            ("EFECTOS", self.sound.sfx_volume, self.pause_sfx_down_button, self.pause_sfx_up_button, 392),
            ("AMBIENTE", self.sound.music_volume, self.pause_music_down_button, self.pause_music_up_button, 444),
        ]
        for label, value, down_button, up_button, y in rows:
            text = self.font_hint_bold.render(label, True, C_GRAY_LIGHT)
            self.canvas.blit(text, (526, y - 20))
            bar = pygame.Rect(526, y - 4, 198, 8)
            pygame.draw.rect(self.canvas, C_BG_DEEP, bar, border_radius=4)
            pygame.draw.rect(self.canvas, C_BORDER_SUBTLE, bar, width=1, border_radius=4)
            fill = pygame.Rect(bar.x, bar.y, int(bar.w * value), bar.h)
            pygame.draw.rect(self.canvas, C_GOLD if value else C_GRAY_DARK, fill, border_radius=4)
            pct = self.font_hint.render(f"{int(value * 100):02d}%", True, C_GRAY_MID)
            self.canvas.blit(pct, pct.get_rect(midright=(724, y - 20)))
            down_button.draw(self.canvas, self.font_button, self.mouse_pos)
            up_button.draw(self.canvas, self.font_button, self.mouse_pos)

        self.pause_mute_button.draw(self.canvas, self.font_label, self.mouse_pos)
        status = "Mixer activo" if self.sound.ready else "Audio no disponible en este dispositivo"
        status_surf = self.font_hint.render(status, True, C_GRAY_DARK if self.sound.ready else C_RED_ERROR)
        self.canvas.blit(status_surf, status_surf.get_rect(center=(panel.centerx, 536)))

    def draw_modal(self, title, detail):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        self.canvas.blit(overlay, (0, 0))
        panel = pygame.Rect(430, 210, 420, 300)
        premium_panel(self.canvas, panel, C_BG_ELEVATED, C_BORDER_ACTIVE, radius=20, alpha=242, glow=True)
        title_surf = self.font_turn.render(title.upper(), True, C_WHITE_SOFT)
        self.canvas.blit(title_surf, title_surf.get_rect(center=(panel.centerx, panel.y + 58)))
        detail_surf = self.font_hint.render(detail.upper(), True, C_GRAY_MID)
        self.canvas.blit(detail_surf, detail_surf.get_rect(center=(panel.centerx, panel.y + 96)))
        draw_chip(self.canvas, pygame.Rect(panel.x + 74, panel.y + 134, 272, 30), "AYUDA CON H / MENU CON ESC", self.font_hint, C_GRAY_LIGHT, C_BORDER_SUBTLE)
        draw_chip(self.canvas, pygame.Rect(panel.x + 74, panel.y + 174, 272, 30), "SALIR AL MENU: REINICIAR PARTIDA", self.font_hint, C_GRAY_LIGHT, C_BORDER_SUBTLE)
        self.continue_button.rect = pygame.Rect(SCREEN_W // 2 - 120, 408, 240, 50)
        self.continue_button.text = "CONTINUAR"
        self.continue_button.draw(self.canvas, self.font_button, self.mouse_pos)

    def draw_help(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 236))
        self.canvas.blit(overlay, (0, 0))
        panel = pygame.Rect(150, 70, 980, 590)
        pygame.draw.rect(self.canvas, C_BG_ELEVATED, panel, border_radius=20)
        premium_panel(self.canvas, panel, C_BG_ELEVATED, C_BORDER_ACTIVE, radius=20, alpha=255, glow=False)
        title = self.font_turn.render("INFORMACION DE MESA", True, C_WHITE_SOFT)
        self.canvas.blit(title, title.get_rect(center=(panel.centerx, panel.y + 42)))
        subtitle = self.font_hint.render("Reglas, cartas, eventos, personajes y controles del modo Plus.", True, C_GRAY_MID)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 70)))

        self.info_tab_rects = {}
        tab_w = 101
        tab_gap = 6
        tab_x = panel.x + 62
        for label in INFO_TABS:
            rect = pygame.Rect(tab_x, panel.y + 96, tab_w, 30)
            active = self.info_tab == label
            self.info_tab_rects[label] = rect
            pygame.draw.rect(self.canvas, C_BG_DEEP if not active else C_BG_PANEL, rect, border_radius=15)
            pygame.draw.rect(self.canvas, C_GOLD if active else C_BORDER_SUBTLE, rect, width=1, border_radius=15)
            txt = self.font_hint_bold.render(label, True, C_WHITE_SOFT if active else C_GRAY_MID)
            self.canvas.blit(txt, txt.get_rect(center=rect.center))
            tab_x += tab_w + tab_gap

        content = pygame.Rect(panel.x + 54, panel.y + 148, panel.w - 108, 368)
        pygame.draw.rect(self.canvas, (5, 5, 5, 120), content, border_radius=16)
        pygame.draw.rect(self.canvas, (*C_BORDER_SUBTLE, 130), content, width=1, border_radius=16)
        self.draw_info_content(content)

        hint = self.font_hint.render("Click en una pestana para cambiar seccion  /  H o CONTINUAR para cerrar", True, C_GOLD)
        self.canvas.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 22)))
        self.continue_button.rect = pygame.Rect(panel.right - 172, panel.bottom - 58, 132, 36)
        self.continue_button.text = "CONTINUAR"
        self.continue_button.draw(self.canvas, self.font_label, self.mouse_pos)

    def wrap_info_text(self, text, font, max_width):
        lines = []
        for paragraph in str(text).split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if font.size(candidate)[0] <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def info_card_detail(self, key, card):
        return card_detail(key, card)

    def info_character_detail(self, character):
        return character_detail(character)

    def info_event_detail(self, event):
        return event_detail(event)

    def draw_info_content(self, rect):
        tab = self.info_tab
        items = info_items(tab)
        item_w = rect.w - 70
        gap_y = 14
        layout = []
        y_cursor = 76
        for icon_key, heading, detail in items:
            heading_lines = self.wrap_info_text(heading, self.font_label, item_w - 84)
            detail_lines = self.wrap_info_text(detail, self.font_hint, item_w - 84)
            item_h = max(78, 42 + len(heading_lines) * 16 + len(detail_lines) * 14)
            layout.append((pygame.Rect(26, y_cursor, item_w, item_h), icon_key, heading_lines, detail_lines))
            y_cursor += item_h + gap_y
        content_h = y_cursor + 16
        max_scroll = max(0, content_h - rect.h + 8)
        scroll = min(self.info_scroll.get(tab, 0), max_scroll)
        self.info_scroll[tab] = scroll

        inner = pygame.Surface((rect.w, content_h), pygame.SRCALPHA)
        title = self.font_body_bold.render(tab, True, C_GOLD)
        inner.blit(title, (24, 18))
        intro = self.font_hint.render("Rueda del mouse para desplazarte dentro de esta seccion." if max_scroll else "Seccion completa.", True, C_GRAY_MID)
        inner.blit(intro, (24, 45))

        for item_rect, icon_key, heading_lines, detail_lines in layout:
            pygame.draw.rect(inner, (15, 15, 16, 215), item_rect, border_radius=14)
            pygame.draw.rect(inner, (*C_BORDER_SUBTLE, 150), item_rect, width=1, border_radius=14)
            icon_rect = pygame.Rect(item_rect.x + 16, item_rect.y + 18, 34, 34)
            accent = C_GOLD if icon_key in ("dorada", "dado_dorado", "descuento", "bonus", "dado_maestro", "milagro_controlado") else (C_RED_ERROR if icon_key in ("sabotaje", "agresivo", "caotica", "presion", "penalizacion") else C_BORDER_ACTIVE)
            pygame.draw.circle(inner, C_BG_DEEP, icon_rect.center, 18)
            pygame.draw.circle(inner, accent, icon_rect.center, 18, 1)
            draw_geo_icon(inner, icon_rect.inflate(-7, -7), icon_key, accent, 180, 2)
            text_x = item_rect.x + 64
            text_y = item_rect.y + 13
            for line in heading_lines:
                h = self.font_label.render(line, True, C_WHITE_SOFT)
                inner.blit(h, (text_x, text_y))
                text_y += 16
            text_y += 5
            for line in detail_lines:
                d = self.font_hint.render(line, True, C_GRAY_LIGHT)
                inner.blit(d, (text_x, text_y))
                text_y += 14

        self.canvas.blit(inner, rect.topleft, pygame.Rect(0, scroll, rect.w, rect.h))
        if max_scroll:
            track = pygame.Rect(rect.right - 12, rect.y + 16, 4, rect.h - 32)
            pygame.draw.rect(self.canvas, C_BORDER_SUBTLE, track, border_radius=2)
            thumb_h = max(34, int(track.h * rect.h / content_h))
            thumb_y = track.y + int((track.h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(self.canvas, C_GOLD, pygame.Rect(track.x, thumb_y, track.w, thumb_h), border_radius=2)
    def draw_end(self):
        winner = max(self.players, key=lambda player: player.total)
        tied = len({player.total for player in self.players}) == 1
        title = "EMPATE" if tied else "GANADOR"
        title_surf = self.font_label.render(title, True, C_GOLD if not tied else C_WHITE_SOFT)
        self.canvas.blit(title_surf, title_surf.get_rect(center=(SCREEN_W // 2, 58)))
        name_text = "MESA CERRADA" if tied else winner.name.upper()
        name = self.font_display.render(trim_text(name_text, self.font_display, 640), True, C_WHITE_SOFT)
        self.canvas.blit(name, name.get_rect(center=(SCREEN_W // 2, 112)))
        subtitle = self.font_hint.render("RESULTADOS FINALES / GENERALA PLUS" if self.plus_mode else "RESULTADOS FINALES / GENERALA", True, C_GRAY_MID)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 158)))

        hero = pygame.Rect(230, 184, 820, 392)
        hero_layer = pygame.Surface(hero.size, pygame.SRCALPHA)
        pygame.draw.rect(hero_layer, (7, 7, 8, 204), hero_layer.get_rect(), border_radius=24)
        pygame.draw.rect(hero_layer, (244, 241, 234, 34), hero_layer.get_rect(), width=1, border_radius=24)
        self.canvas.blit(hero_layer, hero.topleft)

        categories_top = {"unos", "doses", "treses", "cuatros", "cincos", "seises"}
        for index, player in enumerate(self.players):
            rect = pygame.Rect(hero.x + 34 + index * 396, hero.y + 34, 356, 312)
            is_winner = player is winner and not tied
            border = C_GOLD if is_winner else C_BORDER_ACTIVE
            card = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(card, (18, 18, 19, 230), card.get_rect(), border_radius=20)
            pygame.draw.rect(card, (*border, 120 if is_winner else 70), card.get_rect(), width=1, border_radius=20)
            if is_winner:
                pygame.draw.rect(card, (198, 161, 91, 28), pygame.Rect(0, 0, rect.w, 82), border_radius=20)
            self.canvas.blit(card, rect.topleft)

            label = "VICTORIA" if is_winner else "RESULTADO"
            self.canvas.blit(self.font_hint_bold.render(label, True, C_GOLD if is_winner else C_GRAY_MID), (rect.x + 24, rect.y + 20))
            pname = self.font_body_bold.render(trim_text(player.name.upper(), self.font_body_bold, rect.w - 48), True, C_WHITE_SOFT)
            self.canvas.blit(pname, (rect.x + 24, rect.y + 40))
            total = self.font_display.render(str(player.total), True, C_GOLD if is_winner else C_WHITE_SOFT)
            self.canvas.blit(total, total.get_rect(midright=(rect.right - 24, rect.y + 58)))

            top_points = sum((player.sheet.get(key) or 0) for key in categories_top)
            special_points = sum((player.sheet.get(key) or 0) for key, _ in CATEGORIES if key not in categories_top)
            rows = [
                ("NUMERICAS", top_points),
                ("ESPECIALES", special_points),
                ("EXTRAS", player.bonus_total if self.plus_mode else 0),
                ("MONEDAS", player.coins if self.plus_mode else "-"),
                ("PERSONAJE", player.character.name.upper() if self.plus_mode else "CLASICO"),
            ]
            y = rect.y + 104
            for row_label, row_value in rows:
                pygame.draw.line(self.canvas, (42, 42, 42), (rect.x + 24, y - 8), (rect.right - 24, y - 8), 1)
                left = self.font_hint_bold.render(row_label, True, C_GRAY_MID)
                self.canvas.blit(left, (rect.x + 24, y))
                value_text = str(row_value)
                value_color = C_GOLD if row_label == "EXTRAS" and isinstance(row_value, int) and row_value > 0 else C_GRAY_LIGHT
                right = self.font_label.render(trim_text(value_text, self.font_label, 168), True, value_color)
                self.canvas.blit(right, right.get_rect(midright=(rect.right - 24, y + 7)))
                y += 34

            best_key, best_label = max(CATEGORIES, key=lambda item: player.sheet.get(item[0]) or 0)
            best_value = player.sheet.get(best_key) or 0
            chip = pygame.Rect(rect.x + 24, rect.bottom - 44, rect.w - 48, 26)
            draw_chip(self.canvas, chip, f"MEJOR: {best_label.upper()} {best_value}", self.font_hint, C_WHITE_SOFT, C_GOLD if is_winner else C_BORDER_SUBTLE)

        self.restart_button.rect = pygame.Rect(SCREEN_W // 2 - 140, 604, 280, 54)
        self.restart_button.draw(self.canvas, self.font_button, self.mouse_pos)
        hint = self.font_hint.render("R REINICIAR   F11 PANTALLA", True, C_GRAY_DARK)
        self.canvas.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 672)))

    def draw_logo(self, x, y):
        text = self.font_display.render("GENERALA", True, C_WHITE)
        self.canvas.blit(text, text.get_rect(center=(x, y)))
        underline = pygame.Rect(x - 170, y + 48, 340, 1)
        pygame.draw.rect(self.canvas, C_BORDER_ACTIVE, underline)

    def draw_vignette(self):
        self.canvas.blit(self.vignette, (0, 0))


def draw_die(surface, rect, value, selected=False, hovered=False, hint_font=None):
    scale = 1.11 if selected else 1.0
    size = int(rect.w * scale)
    draw_rect = pygame.Rect(0, 0, size, size)
    draw_rect.center = rect.center
    radius = int(size * 0.18)
    if selected:
        draw_glow_rect(surface, draw_rect, C_WHITE, 95, 22)
        top = (255, 255, 255)
        bottom = (232, 232, 232)
        pip = C_BG_DEEP
        border = C_WHITE
    else:
        draw_glow_rect(surface, draw_rect, C_WHITE, 16 if hovered else 8, 18)
        top = (30, 30, 30)
        bottom = (13, 13, 13)
        pip = C_WHITE
        border = C_BORDER_ACTIVE if hovered else (51, 51, 51)
    draw_vertical_gradient(surface, draw_rect, top, bottom, radius)
    pygame.draw.rect(surface, border, draw_rect, width=1, border_radius=radius)
    highlight = pygame.Surface((draw_rect.w, draw_rect.h // 2), pygame.SRCALPHA)
    for y in range(highlight.get_height()):
        alpha = int(18 * (1 - y / max(1, highlight.get_height())))
        pygame.draw.line(highlight, (255, 255, 255, alpha), (0, y), (draw_rect.w, y))
    surface.blit(highlight, draw_rect.topleft)
    draw_pips(surface, draw_rect, value, pip)
    if selected:
        accent = pygame.Rect(draw_rect.x + draw_rect.w // 4, draw_rect.bottom - 7, draw_rect.w // 2, 3)
        pygame.draw.rect(surface, C_GOLD, accent, border_radius=2)


def draw_pips(surface, rect, value, color):
    gap = rect.w // 4
    positions = {
        "tl": (rect.x + gap, rect.y + gap),
        "tc": (rect.centerx, rect.y + gap),
        "tr": (rect.right - gap, rect.y + gap),
        "c": rect.center,
        "bl": (rect.x + gap, rect.bottom - gap),
        "bc": (rect.centerx, rect.bottom - gap),
        "br": (rect.right - gap, rect.bottom - gap),
    }
    mapping = {
        1: ["c"],
        2: ["tl", "br"],
        3: ["tl", "c", "br"],
        4: ["tl", "tr", "bl", "br"],
        5: ["tl", "tr", "c", "bl", "br"],
        6: ["tl", "tr", "bl", "br", "tc", "bc"],
    }
    radius = max(6, rect.w // 10)
    for key in mapping[value]:
        pygame.draw.circle(surface, color, positions[key], radius)


def draw_panel(surface, rect, fill, border, radius):
    premium_panel(surface, rect, fill, border, radius=radius, alpha=236)


def draw_glow_rect(surface, rect, color, alpha, spread):
    if alpha <= 0:
        return
    layer = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), pygame.Rect(spread, spread, rect.w, rect.h), border_radius=14)
    small = pygame.transform.smoothscale(layer, (max(1, layer.get_width() // 3), max(1, layer.get_height() // 3)))
    layer = pygame.transform.smoothscale(small, layer.get_size())
    surface.blit(layer, (rect.x - spread, rect.y - spread))


def draw_vertical_gradient(surface, rect, top, bottom, radius):
    layer = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for y in range(rect.h):
        t = y / max(1, rect.h - 1)
        color = interpolate(top, bottom, t)
        pygame.draw.line(layer, color, (0, y), (rect.w, y))
    mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=radius)
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(layer, rect.topleft)


def trim_text(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    result = text
    while result and font.size(result + "...")[0] > max_width:
        result = result[:-1]
    return result + "..."


def aclarar(color, amount):
    return tuple(min(255, channel + amount) for channel in color)


def interpolate(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
