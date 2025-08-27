import math
import random
import pygame

# ---------------------- Utils ----------------------
def clamp(v, a, b):
    return max(a, min(b, v))

def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def circles_collide(x1, y1, r1, x2, y2, r2):
    return dist(x1, y1, x2, y2) <= r1 + r2

def circle_rect(cx, cy, cr, rect):
    qx = clamp(cx, rect.left, rect.right)
    qy = clamp(cy, rect.top, rect.bottom)
    return dist(cx, cy, qx, qy) <= cr

def _blocked(x, y, r, rects, circles):
    if any(circle_rect(x, y, r, rc) for rc in rects):
        return True
    if any(dist(x, y, cx, cy) <= r + cr for (cx, cy, cr) in circles):
        return True
    return False

def _find_safe_spawn(side, r, W, H, static_rects, mover_rects, circles):
    if side == "left":
        x_lo, x_hi = 80, int(W * 0.40)
    else:
        x_lo, x_hi = int(W * 0.60), W - 80
    
    # Tentar posições mais seguras primeiro (centro das áreas)
    safe_positions = []
    
    # Posições preferenciais
    if side == "left":
        safe_positions.extend([
            (W * 0.25, H * 0.25),
            (W * 0.25, H * 0.50),
            (W * 0.25, H * 0.75),
            (W * 0.15, H * 0.50),
            (W * 0.35, H * 0.50)
        ])
    else:
        safe_positions.extend([
            (W * 0.75, H * 0.25),
            (W * 0.75, H * 0.50),
            (W * 0.75, H * 0.75),
            (W * 0.85, H * 0.50),
            (W * 0.65, H * 0.50)
        ])
    
    # Testar posições preferenciais primeiro
    for x, y in safe_positions:
        x, y = int(x), int(y)
        if not _blocked(x, y, r, static_rects + mover_rects, circles):
            return float(x), float(y)
    
    # Se não encontrar nas posições preferenciais, tentar aleatório
    for _ in range(100):
        x = random.randint(x_lo, x_hi)
        y = random.randint(110, H - 80)
        if not _blocked(x, y, r, static_rects + mover_rects, circles):
            return float(x), float(y)
    
    # Último recurso: posição fixa
    return (120.0, H / 2.0) if side == "left" else (W - 120.0, H / 2.0)

def reset_round(p1, p2, static_rects, mover_rects, circles, W, H):
    p1.x, p1.y = _find_safe_spawn("left", p1.r, W, H, static_rects, mover_rects, circles)
    p2.x, p2.y = _find_safe_spawn("right", p2.r, W, H, static_rects, mover_rects, circles)
    p1.score = p2.score = 0.0
    p1.speed_mul = p2.speed_mul = 1.0
    p1.speed_until = p2.speed_until = 0
    p1.shield = p2.shield = 0
    p1.frozen_until = p2.frozen_until = 0
    
    # Adicionar proteção de spawn (3 segundos)
    now = pygame.time.get_ticks()
    p1.spawn_protection = now + 3000  # 3 segundos de proteção
    p2.spawn_protection = now + 3000
    
    (p1 if random.choice([True, False]) else p2).is_it = True
    (p2 if p1.is_it else p1).is_it = False
    start = pygame.time.get_ticks()
    tag_block = 0
    powerups = []
    next_pu = start + random.randint(1500, 3000)
    return start, tag_block, powerups, next_pu