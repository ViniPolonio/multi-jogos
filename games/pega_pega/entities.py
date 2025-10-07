import pygame
import math
import random
from utils.helpers import clamp, circle_rect, circles_collide, dist

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
        self.stuck_protection = 0

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
        old_x, old_y = self.x, self.y
        
        # Tenta mover em X
        self.x = clamp(self.x + dx, self.r, arena.right - self.r)
        collision_x = any(circle_rect(self.x, self.y, self.r, r) for r in rects) or \
                     any(circle_rect(self.x, self.y, self.r, m) for m in movers) or \
                     any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles)
        
        if collision_x:
            self.x = old_x
        
        # Tenta mover em Y
        self.y = clamp(self.y + dy, self.r, arena.bottom - self.r)
        collision_y = any(circle_rect(self.x, self.y, self.r, r) for r in rects) or \
                     any(circle_rect(self.x, self.y, self.r, m) for m in movers) or \
                     any(circles_collide(self.x, self.y, self.r, cx, cy, cr) for (cx, cy, cr) in circles)
        
        if collision_y:
            self.y = old_y
        
        return collision_x or collision_y

    def rect(self):
        """Retorna o retângulo de colisão do jogador"""
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def draw(self, surf):
        if self.is_it:
            pygame.draw.circle(surf, (255, 210, 0), (int(self.x), int(self.y)), self.r + 6, 4)
        if self.shield:
            pygame.draw.circle(surf, (120, 240, 255), (int(self.x), int(self.y)), self.r + 2, 2)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.r)

class PowerUp:
    def __init__(self, kind, pos):
        self.kind = kind
        self.x, self.y = pos

    def rect(self):
        """Retorna o retângulo de colisão do power-up"""
        return pygame.Rect(self.x - 14, self.y - 14, 28, 28)

    def draw(self, s):
        colors = {
            "speed": (255, 180, 0), 
            "shield": (120, 240, 255), 
            "freeze": (170, 220, 255),
            "teleport": (180, 100, 240)
        }
        col = colors.get(self.kind, (255, 255, 255))
        pygame.draw.circle(s, col, (int(self.x), int(self.y)), 14)
        
        labels = {"speed": "⚡", "shield": "🛡", "freeze": "❄", "teleport": "🔀"}
        label = labels.get(self.kind, "?")
        font = pygame.font.Font(None, 22)
        t = font.render(label, True, (0, 0, 0))
        s.blit(t, (self.x - t.get_width() / 2, self.y - t.get_height() / 2))

def spawn_powerup(pus, static_rects, movers, circles, W, H):
    for _ in range(100):
        x = random.randint(60, W - 60)
        y = random.randint(110, H - 60)
        mover_rects = [m.rect() for m in movers]
        
        if not any(circle_rect(x, y, 14, rc) for rc in static_rects + mover_rects) and \
           not any(dist(x, y, cx, cy) <= 14 + cr for (cx, cy, cr) in circles):
            pus.append(PowerUp(random.choice(["speed", "shield", "freeze", "teleport"]), (x, y)))
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
        if who.is_it:
            who.x = random.randint(60, W - 60)
            who.y = random.randint(110, H - 60)
        else:
            min_distance = 250
            angle = random.uniform(0, 2 * math.pi)
            who.x = other.x + min_distance * math.cos(angle)
            who.y = other.y + min_distance * math.sin(angle)
            who.x = clamp(who.x, who.r, W - who.r)
            who.y = clamp(who.y, who.r, H - who.r)