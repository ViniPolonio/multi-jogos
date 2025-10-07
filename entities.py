import pygame
import math
import random
from utils import clamp, circle_rect, circles_collide, dist

# ---------------------- Entidades ----------------------
class Player:
    def __init__(self, x, y, r, color, vel, keys, name=""):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.vel = vel
        self.keys = keys
        self.score = 0.0
        self.is_it = False
        self.name = name
        self.speed_mul = 1.0
        self.speed_until = 0
        self.shield = 0
        self.frozen_until = 0
        self.stuck_protection = 0  # Proteção anti-trava
        self.last_valid_x = x  # Última posição válida
        self.last_valid_y = y
        self.stuck_timer = 0  # Timer para detectar se está preso

    def input(self):
        k = pygame.key.get_pressed()
        dx = dy = 0
        if k[self.keys["left"]]:
            dx -= 1
        if k[self.keys["right"]]:
            dx += 1
        if k[self.keys["up"]]:
            dy -= 1
        if k[self.keys["down"]]:
            dy += 1
        if dx and dy:
            inv = 1 / math.sqrt(2)
            dx *= inv
            dy *= inv
        
        v = self.vel * self.speed_mul
        if pygame.time.get_ticks() < self.frozen_until:
            v = 0
        return dx * v, dy * v

    def move_collide(self, dx, dy, arena, rects, movers, circles):
        """Movimento com colisão que detecta se o jogador está preso"""
        now = pygame.time.get_ticks()
        
        # Salva posição anterior
        old_x, old_y = self.x, self.y
        
        # Tenta mover em X
        self.x = clamp(self.x + dx, self.r, arena.right - self.r)
        collision_x = any(circle_rect(self.x, self.y, self.r, r) for r in rects) or \
                     any(circle_rect(self.x, self.y, self.r, m.rect()) for m in movers) or \
                     any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles)
        
        if collision_x:
            self.x = old_x  # Reverte movimento X
        
        # Tenta mover em Y
        self.y = clamp(self.y + dy, self.r, arena.bottom - self.r)
        collision_y = any(circle_rect(self.x, self.y, self.r, r) for r in rects) or \
                     any(circle_rect(self.x, self.y, self.r, m.rect()) for m in movers) or \
                     any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles)
        
        if collision_y:
            self.y = old_y  # Reverte movimento Y
        
        # Verifica se está completamente preso (não consegue se mover em nenhuma direção)
        final_collision = any(circle_rect(self.x, self.y, self.r, r) for r in rects) or \
                         any(circle_rect(self.x, self.y, self.r, m.rect()) for m in movers) or \
                         any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles)
        
        # Atualiza timer de "preso"
        if final_collision and (abs(dx) > 0.1 or abs(dy) > 0.1):
            # Está tentando se mover mas não consegue
            if self.stuck_timer == 0:
                self.stuck_timer = now
            elif now - self.stuck_timer > 1000:  # Preso por mais de 1 segundo
                return "stuck"
        else:
            self.stuck_timer = 0  # Reset timer se não está preso
        
        return collision_x or collision_y

    def is_colliding(self, rects, movers, circles):
        """Verifica se está colidindo com algum obstáculo"""
        return (any(circle_rect(self.x, self.y, self.r, r) for r in rects) or
                any(circle_rect(self.x, self.y, self.r, m.rect()) for m in movers) or
                any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles))

    def draw(self, surf):
        # Desenhar efeito de proteção se estiver ativo
        now = pygame.time.get_ticks()
        if now < self.stuck_protection:
            alpha = int(128 + 127 * math.sin(now / 100))
            protection_surf = pygame.Surface((self.r * 2 + 10, self.r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(protection_surf, (100, 255, 100, alpha), (self.r + 5, self.r + 5), self.r + 5, 3)
            surf.blit(protection_surf, (int(self.x) - self.r - 5, int(self.y) - self.r - 5))
        
        if self.is_it:
            pygame.draw.circle(surf, (255, 210, 0), (int(self.x), int(self.y)), self.r + 6, 4)
        if self.shield:
            pygame.draw.circle(surf, (120, 240, 255), (int(self.x), int(self.y)), self.r + 2, 2)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.r)

# ---------------------- Power-ups ----------------------
PU_RADIUS = 14
PU_TYPES = ("speed", "shield", "freeze", "teleport")
PU_COLORS = {
    "speed": (255, 180, 0), 
    "shield": (120, 240, 255), 
    "freeze": (170, 220, 255),
    "teleport": (180, 100, 240)
}

class PowerUp:
    def __init__(self, kind, pos):
        self.kind = kind
        self.x, self.y = pos

    def rect(self):
        return pygame.Rect(self.x - PU_RADIUS, self.y - PU_RADIUS, PU_RADIUS * 2, PU_RADIUS * 2)

    def draw(self, s):
        col = PU_COLORS[self.kind]
        pygame.draw.circle(s, col, (int(self.x), int(self.y)), PU_RADIUS)
        label = {"speed": "⚡", "shield": "🛡", "freeze": "❄", "teleport": "🔀"}[self.kind]
        t = pygame.font.SysFont(None, 22).render(label, True, (0, 0, 0))
        s.blit(t, (self.x - t.get_width() / 2, self.y - t.get_height() / 2))

# Função auxiliar para calcular distância
def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def spawn_powerup(pus, static_rects, movers, circles, W, H):
    for _ in range(200):
        x = random.randint(60, W - 60)
        y = random.randint(110, H - 60)
        mover_rects = [m.rect() for m in movers]
        
        if not any(circle_rect(x, y, PU_RADIUS, rc) for rc in static_rects + mover_rects) and \
           not any(dist(x, y, cx, cy) <= PU_RADIUS + cr for (cx, cy, cr) in circles):
            pus.append(PowerUp(random.choice(PU_TYPES), (x, y)))
            return

def apply_powerup(who, other, kind, W, H):
    now = pygame.time.get_ticks()
    if kind == "speed":
        who.speed_mul = 1.6
        who.speed_until = now + 3000
    elif kind == "shield":
        who.shield = 1
    elif kind == "freeze":
        if not who.is_it:
            other.frozen_until = now + 2000
    elif kind == "teleport":
        # Teleporta o jogador para longe do pegador
        if who.is_it:  # Se for o pegador, teleporta para um local aleatório
            who.x = random.randint(60, W - 60)
            who.y = random.randint(110, H - 60)
        else:  # Se for o fugitivo, teleporta para longe do pegador
            min_distance = 250  # Distância mínima do pegador
            angle = random.uniform(0, 2 * math.pi)
            who.x = other.x + min_distance * math.cos(angle)
            who.y = other.y + min_distance * math.sin(angle)
            # Garante que está dentro da arena
            who.x = clamp(who.x, who.r, W - who.r)
            who.y = clamp(who.y, who.r, H - who.r)

# Sistema de partículas
class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.lifetime = lifetime
        self.age = 0
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.age += 1
        return self.age < self.lifetime
    
    def draw(self, surf):
        alpha = 255 * (1 - self.age / self.lifetime)
        size = 3 * (1 - self.age / self.lifetime)
        s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(alpha)), (int(size), int(size)), size)
        surf.blit(s, (int(self.x - size), int(self.y - size)))