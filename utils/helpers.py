import math

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

def reset_round():
    """
    Reseta o estado do round para valores iniciais
    Retorna um dicionário com os valores padrão
    """
    return {
        'score': 0,
        'lives': 3,
        'game_over': False,
        'round_complete': False
    }