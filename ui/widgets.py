import pygame
import math
import os

def load_font(size=24):
    """Tenta carregar a Fancy.ttf em assets/; caso contrário usa a fonte padrão do sistema."""
    path = os.path.join("assets", "Fancy.ttf")
    if os.path.exists(path):
        try:
            return pygame.font.Font(path, size)
        except:
            pass
    # Fallback robusto
    try:
        return pygame.font.SysFont(None, size)
    except:
        return pygame.font.Font(None, size)

class Button:
    def __init__(self, rect, text, font_size=24, color=(100, 170, 255)):
        self.base_rect = pygame.Rect(rect)
        self.rect = self.base_rect.copy()
        self.text = text
        self.font_size = font_size
        self.color = color
        self.font = load_font(self.font_size)

    def draw(self, surface, hover=False, t=None):
        # Pulso suave no botão (sem alterar a API existente)
        if t is None:
            t = pygame.time.get_ticks() / 1000.0
        k = 1.0 + 0.03 * math.sin(t * 2.5)
        self.rect = self.base_rect.copy()
        self.rect.w = int(self.base_rect.w * k)
        self.rect.h = int(self.base_rect.h * k)
        self.rect.center = self.base_rect.center

        fill = (70, 70, 70) if not hover else (95, 95, 95)
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, (120, 120, 120), self.rect, 2, border_radius=10)

        if hover:
            glow = pygame.Surface((self.rect.w + 20, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (100, 170, 255, 90), glow.get_rect())
            surface.blit(glow, (self.rect.centerx - glow.get_width() // 2,
                                self.rect.centery - glow.get_height() // 2))

        txt = self.font.render(self.text, True, (240, 240, 240))
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                           self.rect.centery - txt.get_height() // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

class Title:
    def __init__(self, text, x, y, font_size=48, color=(240, 240, 240)):
        self.text = text
        self.x = x
        self.y = y
        self.font_size = font_size
        self.color = color
        self.font = load_font(self.font_size)

    def draw(self, surface):
        text_surf = self.font.render(self.text, True, self.color)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        surface.blit(text_surf, text_rect)

class ColorPicker:
    """
    Seletor de cores em formato de 'swatches' quadrados, centralizados na largura informada.
    """
    def __init__(self, x, y, width, height, colors, initial_color=0):
        self.colors = list(colors)
        self.selected_color = max(0, min(initial_color, len(self.colors) - 1))
        self.items = []

        # Calcula tamanho do quadrado e posiciona centralizado
        n = len(self.colors)
        # Tenta usar 30px por item com espaçamento 6px
        desired_size = 30
        spacing = 6
        step = desired_size + spacing
        total_w = step * n - spacing

        if total_w > width:
            # Se não couber, recalcula tamanho baseado na largura disponível
            step = max(14, width // n)  # garante mínimo
            desired_size = max(12, step - spacing)
            total_w = step * n - spacing

        start_x = int(x + (width - total_w) // 2)
        for i, c in enumerate(self.colors):
            r = pygame.Rect(start_x + i * step, y, desired_size, desired_size)
            self.items.append((r, c))

        self.rect = pygame.Rect(x, y, width, max(height, desired_size))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, (r, _) in enumerate(self.items):
                if r.collidepoint(event.pos):
                    self.selected_color = i
                    return True
        return False

    def draw(self, screen):
        for i, (r, c) in enumerate(self.items):
            pygame.draw.rect(screen, c, r, border_radius=6)
            pygame.draw.rect(screen, (30, 30, 30), r, 2, border_radius=6)
            if i == self.selected_color:
                pygame.draw.rect(screen, (255, 255, 255), r.inflate(6, 6), 2, border_radius=8)

    def get_selected_color(self):
        return self.colors[self.selected_color]

class InputBox:
    """
    Caixa de texto com placeholder, fundo translúcido e borda que destaca no foco.
    """
    def __init__(self, x, y, w, h, placeholder=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder or ""
        self.text = ""
        self.font = load_font(30)
        self.active = False
        self.max_len = 16

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return True

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode and event.unicode.isprintable() and len(self.text) < self.max_len:
                    self.text += event.unicode
            return True

        return False

    def draw(self, screen):
        # Fundo translúcido
        box = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        box.fill((0, 0, 0, 160))
        screen.blit(box, self.rect.topleft)

        # Borda
        border_col = (100, 170, 255) if self.active else (160, 160, 160)
        pygame.draw.rect(screen, border_col, self.rect, 3, border_radius=10)

        # Texto ou placeholder
        msg = self.text if self.text else self.placeholder
        col = (240, 240, 240) if self.text else (220, 220, 220)
        text_surface = self.font.render(msg, True, col)
        screen.blit(text_surface, (self.rect.x + 12, self.rect.y + (self.rect.h - text_surface.get_height()) // 2))

class ModeSelector:
    """
    Seletor simples de modo de jogo (mantido se você usar em outro lugar).
    """
    def __init__(self, x, y, width, height, modes, initial_mode=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.modes = modes
        self.selected_mode = initial_mode
        self.font = load_font(24)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.selected_mode = (self.selected_mode + 1) % len(self.modes)
            return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, (80, 80, 120), self.rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 200), self.rect, 2, border_radius=8)
        text = f"Modo: {self.modes[self.selected_mode]}"
        text_surf = self.font.render(text, True, (240, 240, 240))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def get_selected_mode(self):
        return self.modes[self.selected_mode]