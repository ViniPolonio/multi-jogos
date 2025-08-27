import pygame
import math
import os

# ---------------------- Fontes ----------------------
def load_font(sz):
    p = os.path.join("assets", "Fancy.ttf")
    return pygame.font.Font(p, sz) if os.path.exists(p) else pygame.font.SysFont(None, sz)

# ---------------------- UI ----------------------
class InputBox:
    def __init__(self, rect, ph=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.ph = ph
        self.active = False

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(e.pos)
        if self.active and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                self.active = False
            elif e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.unicode.isprintable() and len(self.text) < 16:
                self.text += e.unicode

    def draw(self, surf, font):
        box = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        box.fill((0, 0, 0, 160))
        surf.blit(box, self.rect.topleft)
        pygame.draw.rect(surf, (100, 170, 255) if self.active else (160, 160, 160), self.rect, 3, 10)
        msg = self.text if self.text else self.ph
        col = (240, 240, 240) if self.text else (220, 220, 220)
        t = font.render(msg, True, col)
        surf.blit(t, (self.rect.x + 12, self.rect.y + (self.rect.h - t.get_height()) // 2))

class Button:
    def __init__(self, rect, label):
        self.base = pygame.Rect(rect)
        self.rect = self.base.copy()
        self.label = label

    def draw(self, surf, hover, t, font):
        k = 1.0 + 0.03 * math.sin(t * 2.5)
        self.rect = self.base.copy()
        self.rect.w = int(self.base.w * k)
        self.rect.h = int(self.base.h * k)
        self.rect.center = self.base.center
        
        fill = (70, 70, 70) if not hover else (95, 95, 95)
        pygame.draw.rect(surf, fill, self.rect, 0, 10)
        pygame.draw.rect(surf, (120, 120, 120), self.rect, 2, 10)
        
        if hover:
            glow = pygame.Surface((self.rect.w + 20, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (100, 170, 255, 90), glow.get_rect())
            surf.blit(glow, (self.rect.centerx - glow.get_width() // 2, self.rect.centery - glow.get_height() // 2))
        
        txt = font.render(self.label, True, (240, 240, 240))
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

class ColorPicker:
    def __init__(self, x, y, colors, sel):
        self.items = []
        self.sel = sel
        for i, c in enumerate(colors):
            r = pygame.Rect(x + i * 36, y, 30, 30)
            self.items.append((r, c))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for i, (r, c) in enumerate(self.items):
                if r.collidepoint(e.pos):
                    self.sel = i

    def color(self):
        return self.items[self.sel][1]

    def draw(self, surf):
        for i, (r, c) in enumerate(self.items):
            pygame.draw.rect(surf, c, r, 0, 6)
            pygame.draw.rect(surf, (30, 30, 30), r, 2, 6)
            if i == self.sel:
                pygame.draw.rect(surf, (255, 255, 255), r.inflate(6, 6), 2, 8)

class ModeSelector:
    def __init__(self, x, y, modes, sel):
        self.items = []
        self.sel = sel
        for i, (key, name) in enumerate(modes.items()):
            r = pygame.Rect(x + i * 150, y, 140, 40)
            self.items.append((r, key, name))
    
    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for i, (r, key, name) in enumerate(self.items):
                if r.collidepoint(e.pos):
                    self.sel = i
                    return key
        return None
    
    def draw(self, surf, font):
        for i, (r, key, name) in enumerate(self.items):
            color = (100, 170, 255) if i == self.sel else (70, 70, 70)
            pygame.draw.rect(surf, color, r, 0, 8)
            pygame.draw.rect(surf, (120, 120, 120), r, 2, 8)
            txt = font.render(name, True, (240, 240, 240))
            surf.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))

def hud(surf, p1, p2, remaining, round_num, victories, W, H, fonts):
    bar_h = 110
    hud_surf = pygame.Surface((W, bar_h), pygame.SRCALPHA)
    hud_surf.fill((0, 0, 0, 150))
    surf.blit(hud_surf, (0, 0))

    FT_BIG, FT, FT_SC, FT_SM = fonts
    
    def abbrev(t, n=12):
        t = str(t)
        return t if len(t) <= n else t[:n-1] + "…"
    
    n1, n2 = abbrev(p1.name), abbrev(p2.name)

    title = FT_BIG.render("PEGA - PEGA 1V1", True, (240, 240, 240))
    title_rect = title.get_rect(midtop=(W // 2, 6))
    surf.blit(title, title_rect)

    round_text = FT.render(
        f"Round {round_num}/3 • Vitórias: {n1} {victories[0]} - {victories[1]} {n2}",
        True, (240, 240, 240)
    )
    round_rect = round_text.get_rect(topleft=(16, title_rect.bottom + 2))
    surf.blit(round_text, round_rect)

    def fmt_time(ms):
        ms = max(0, ms)
        s = ms // 1000
        m = s // 60
        s %= 60
        return f"{m}:{s:02d}"
    
    timer = FT_SC.render(f"Tempo: {fmt_time(remaining)}", True, (255, 210, 0))
    timer_rect = timer.get_rect(topleft=(16, round_rect.bottom + 4))
    surf.blit(timer, timer_rect)

    placar = FT_SC.render(f"{n1}: {p1.score:0.1f}   |   {n2}: {p2.score:0.1f}", True, (240, 240, 240))
    placar_rect = placar.get_rect(topright=(W - 16, timer_rect.top))
    surf.blit(placar, placar_rect)

    peg = p1.name if p1.is_it else p2.name
    peg_surf = FT.render(f"Pegador: {peg}", True, (255, 210, 0))
    peg_rect = peg_surf.get_rect(midtop=(W // 2, timer_rect.bottom + 4))
    surf.blit(peg_surf, peg_rect)