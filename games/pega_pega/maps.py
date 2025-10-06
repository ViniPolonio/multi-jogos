import pygame
import math
import random

class MovingRect:
    def __init__(self, x, y, w, h, axis, amp, speed):
        self.base = pygame.Rect(x, y, w, h)
        self.axis = axis
        self.amp = amp
        self.speed = speed
        self.t0 = random.random() * 1000
    
    def rect(self):
        t = (pygame.time.get_ticks() + self.t0) / 1000.0
        off = math.sin(t * self.speed) * self.amp
        r = self.base.copy()
        if self.axis == "x":
            r.x = int(self.base.x + off)
        else:
            r.y = int(self.base.y + off)
        return r
    
    def update(self):
        # Para compatibilidade - atualização do mover
        pass

def get_map(map_name, W, H):
    if map_name == "original":
        static_rects = [
            pygame.Rect(W*0.10, H*0.20, 200, 24),
            pygame.Rect(W*0.68, H*0.60, 180, 24),
            pygame.Rect(W*0.08, H*0.78, 240, 20),
        ]
        circles = [(W*0.25, H*0.62, 36), (W*0.80, H*0.25, 28)]
        movers = [
            MovingRect(W*0.40, H*0.38, 24, 140, "x", 40, 1.3),
            MovingRect(W*0.55, H*0.18, 160, 20, "y", 40, 1.7)
        ]
    else:  # novo_mapa
        static_rects = [
            pygame.Rect(W*0.30, H*0.30, 150, 24),
            pygame.Rect(W*0.50, H*0.60, 24, 120),
            pygame.Rect(W*0.70, H*0.20, 180, 20),
        ]
        circles = [(W*0.60, H*0.40, 32), (W*0.25, H*0.70, 28)]
        movers = [
            MovingRect(W*0.20, H*0.50, 120, 24, "x", 60, 1.1),
            MovingRect(W*0.60, H*0.70, 24, 100, "y", 50, 1.5)
        ]
    
    return {
        "static_rects": static_rects,
        "circles": circles,
        "movers": movers
    }

def draw_obstacles(surf, static_rects, movers, circles):
    # Desenhar obstáculos estáticos
    for r in static_rects:
        pygame.draw.rect(surf, (55, 55, 55), r, 0, 6)
        pygame.draw.rect(surf, (90, 90, 90), r.inflate(-6, -6), 0, 6)
    
    # Desenhar obstáculos móveis
    for m in movers:
        r = m.rect()
        pygame.draw.rect(surf, (75, 75, 75), r, 0, 6)
        pygame.draw.rect(surf, (120, 120, 120), r.inflate(-6, -6), 0, 6)
    
    # Desenhar círculos
    for (cx, cy, cr) in circles:
        pygame.draw.circle(surf, (55, 55, 55), (int(cx), int(cy)), int(cr))
        pygame.draw.circle(surf, (90, 90, 90), (int(cx), int(cy)), int(max(2, cr-6)))