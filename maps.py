import pygame
import random
import math

# ---------------------- Obstáculos ----------------------
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

# Definição dos mapas
def get_map(map_name, W, H):
    MAPS = {
        "original": {
            "static_rects": [
                pygame.Rect(W * 0.10, H * 0.20, 200, 24),
                pygame.Rect(W * 0.68, H * 0.60, 180, 24),
                pygame.Rect(W * 0.08, H * 0.78, 240, 20),
            ],
            "circles": [(W * 0.25, H * 0.62, 36), (W * 0.80, H * 0.25, 28)],
            "movers": [
                MovingRect(W * 0.40, H * 0.38, 24, 140, "x", 40, 1.3),
                MovingRect(W * 0.55, H * 0.18, 160, 20, "y", 40, 1.7)
            ]
        },
        "novo_mapa": {
            "static_rects": [
                pygame.Rect(W * 0.15, H * 0.30, 150, 24),
                pygame.Rect(W * 0.70, H * 0.40, 100, 24),
                pygame.Rect(W * 0.20, H * 0.70, 300, 20),
            ],
            "circles": [(W * 0.40, H * 0.30, 40), (W * 0.60, H * 0.60, 32)],
            "movers": [
                MovingRect(W * 0.50, H * 0.50, 30, 120, "x", 60, 1.0),
                MovingRect(W * 0.30, H * 0.20, 120, 20, "y", 50, 1.5)
            ]
        }
    }
    
    return MAPS.get(map_name, MAPS["original"])

def draw_obstacles(s, static_rects, movers, circles):
    for r in static_rects:
        pygame.draw.rect(s, (55, 55, 55), r, 0, 6)
        pygame.draw.rect(s, (90, 90, 90), r.inflate(-6, -6), 0, 6)
    
    for m in movers:
        r = m.rect()
        pygame.draw.rect(s, (75, 75, 75), r, 0, 6)
        pygame.draw.rect(s, (120, 120, 120), r.inflate(-6, -6), 0, 6)
    
    for (cx, cy, cr) in circles:
        pygame.draw.circle(s, (55, 55, 55), (int(cx), int(cy)), int(cr))
        pygame.draw.circle(s, (90, 90, 90), (int(cx), int(cy)), int(max(2, cr - 6)))