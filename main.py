import pygame
import sys
import math
import random
import os
from maps import get_map, draw_obstacles
from entities import Player, PowerUp, spawn_powerup, apply_powerup
from ui import load_font, InputBox, Button, ColorPicker, ModeSelector, hud
from utils import reset_round, circles_collide, circle_rect, dist

pygame.init()

# ---------------------- Configurações ----------------------
W, H = 900, 520
flags = pygame.SCALED
tela = pygame.display.set_mode((W, H), flags)
pygame.display.set_caption("Pega-pega 1v1 — Rounds, Power-ups e Cores")
FPS = 60
clock = pygame.time.Clock()

# ---------------------- Cores ----------------------
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
BG = (18, 18, 18)
YELL = (255, 210, 0)
GREEN = (50, 255, 100)

# Paleta para os pickers
C1 = (255, 109, 106); C2 = (255, 199, 95); C3 = (92, 225, 230); C4 = (159, 105, 255); C5 = (64, 222, 140)
C6 = (255, 77, 0);   C7 = (255, 230, 0);  C8 = (0, 180, 255);  C9 = (140, 100, 255); C10 = (80, 255, 180)
PALETTE = [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10]

# ---------------------- Fontes ----------------------
FT_BIG = load_font(46)
FT = load_font(30)
FT_SC = load_font(34)
FT_SM = load_font(22)
FT_MEGA = load_font(64)

# ---------------------- Recursos (opcionais) ----------------------
music_ok = tag_ok = hit_ok = False
try:
    pygame.mixer.music.load("assets/bg_music.wav")
    pygame.mixer.music.set_volume(0.4)
    music_ok = True
except:
    pass

try:
    S_TAG = pygame.mixer.Sound("assets/tag.wav")
    S_TAG.set_volume(0.7)
    tag_ok = True
except:
    S_TAG = None

try:
    S_HIT = pygame.mixer.Sound("assets/hit.wav")
    S_HIT.set_volume(0.5)
    hit_ok = True
except:
    S_HIT = None

try:
    BG_IMG = pygame.image.load("assets/python.png").convert_alpha()
    BG_IMG = pygame.transform.smoothscale(BG_IMG, (W, H))
except:
    BG_IMG = None

# ---------------------- Estados ----------------------
INTRO, MENU, GAME, END = "intro", "menu", "game", "end"
state = INTRO
INTRO_MS = 7000
intro_start = pygame.time.get_ticks()

# ---------------------- Variáveis de jogo ----------------------
ROUND_MS = 60 * 1000
COOLDOWN = 500
round_idx = 1
wins = [0, 0]
winner_msg = ""
fullscreen = False

# Mapa atual
current_map = "original"
map_data = get_map(current_map, W, H)
STATIC_RECTS = map_data["static_rects"]
CIRCLES = map_data["circles"]
MOVERS = map_data["movers"]
map_transition_timer = 0
MAP_TRANSITION_TIME = 15000  # Transição a cada 15 segundos

# Modos de jogo
MODES = {"TAG": "Pega-Pega", "RACE": "Corrida", "SURVIVAL": "Sobrevivência"}
current_mode = "TAG"

# ====== MENU WIDGETS ======
y_start = 180
spacing = 120

# Player 1
pick1 = ColorPicker(W // 2 - 200, y_start, PALETTE, 0)
inp1 = InputBox((W // 2 - 200, y_start + 40, 400, 50), "Player 1 (WASD)")

# Player 2
pick2 = ColorPicker(W // 2 - 200, y_start + spacing, PALETTE, 2)
inp2 = InputBox((W // 2 - 200, y_start + spacing + 40, 400, 50), "Player 2 (SETAS)")

# Seletor de modo
mode_selector = ModeSelector(W // 2 - 220, y_start + spacing * 2 - 50, MODES, 0)

# Botão iniciar
btn = Button((W // 2 - 100, y_start + spacing * 2, 200, 56), "Iniciar")

# Variáveis dos jogadores (serão inicializadas no menu)
p1 = None
p2 = None

# ---------------------- Funções auxiliares ----------------------
def draw_bg():
    if BG_IMG:
        tela.blit(BG_IMG, (0, 0))
        sh = pygame.Surface((W, H), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 70))
        tela.blit(sh, (0, 0))
    else:
        tela.fill(BG)

def show_map_transition_effect(old_map, new_map):
    """Mostra efeito visual durante a transição de mapa"""
    # Fade out
    for alpha in range(0, 255, 25):
        fade_surface = pygame.Surface((W, H))
        fade_surface.fill(BLACK)
        fade_surface.set_alpha(alpha)
        draw_bg()
        draw_obstacles(tela, STATIC_RECTS, MOVERS, CIRCLES)
        if p1: p1.draw(tela)
        if p2: p2.draw(tela)
        tela.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)
    
    # Tela preta completa
    tela.fill(BLACK)
    
    # Texto informativo
    text1 = FT_BIG.render("Mudando de Mapa...", True, WHITE)
    text2 = FT.render(f"{old_map} → {new_map}", True, YELL)
    text3 = FT_SM.render("Reposicionando jogadores...", True, GREEN)
    
    tela.blit(text1, (W//2 - text1.get_width()//2, H//2 - 60))
    tela.blit(text2, (W//2 - text2.get_width()//2, H//2 - 10))
    tela.blit(text3, (W//2 - text3.get_width()//2, H//2 + 40))
    
    pygame.display.flip()
    pygame.time.delay(1000)
    
    # Fade in
    for alpha in range(255, 0, -25):
        fade_surface = pygame.Surface((W, H))
        fade_surface.fill(BLACK)
        fade_surface.set_alpha(alpha)
        draw_bg()
        draw_obstacles(tela, STATIC_RECTS, MOVERS, CIRCLES)
        if p1: p1.draw(tela)
        if p2: p2.draw(tela)
        tela.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

def is_position_safe(x, y, radius):
    """Verifica se uma posição está segura (sem colisão com obstáculos)"""
    # Verifica colisão com obstáculos estáticos
    for rect in STATIC_RECTS:
        if circle_rect(x, y, radius, rect):
            return False
    
    # Verifica colisão com círculos
    for circle in CIRCLES:
        cx, cy, cr = circle
        if dist(x, y, cx, cy) <= radius + cr:
            return False
    
    # Verifica colisão com movers
    for mover in MOVERS:
        if circle_rect(x, y, radius, mover.rect()):
            return False
    
    # Verifica se está dentro da tela (com margem de segurança)
    margin = radius + 10
    if not (margin <= x <= W - margin and margin <= y <= H - margin):
        return False
    
    return True

def find_safe_position_nearby(x, y, radius, max_attempts=20):
    """Encontra uma posição segura próxima da posição atual"""
    attempts = 0
    while attempts < max_attempts:
        # Tenta posições em círculo ao redor
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(30, 100)
        test_x = x + distance * math.cos(angle)
        test_y = y + distance * math.sin(angle)
        
        # Mantém dentro da tela
        test_x = max(radius + 5, min(W - radius - 5, test_x))
        test_y = max(radius + 5, min(H - radius - 5, test_y))
        
        if is_position_safe(test_x, test_y, radius):
            return (test_x, test_y)
        
        attempts += 1
    
    # Fallback: cantos seguros
    corners = [
        (radius + 20, radius + 20),
        (W - radius - 20, radius + 20),
        (radius + 20, H - radius - 20),
        (W - radius - 20, H - radius - 20)
    ]
    
    for corner in corners:
        if is_position_safe(corner[0], corner[1], radius):
            return corner
    
    # Último recurso: centro
    return (W // 2, H // 2)

def safe_reset_round():
    """Função segura para resetar o round com transição de mapa"""
    global STATIC_RECTS, CIRCLES, MOVERS, map_transition_timer, current_map
    
    now = pygame.time.get_ticks()
    map_changed = False
    old_map = current_map
    
    # Verifica transição de mapa
    if now - map_transition_timer > MAP_TRANSITION_TIME:
        current_map = "novo_mapa" if current_map == "original" else "original"
        map_data = get_map(current_map, W, H)
        STATIC_RECTS = map_data["static_rects"]
        CIRCLES = map_data["circles"]
        MOVERS = map_data["movers"]
        map_transition_timer = now
        map_changed = True
    
    # Reseta o round normalmente
    mover_rects = [m.rect() for m in MOVERS] if MOVERS else []
    start_ticks, tag_until, powerups, next_pu = reset_round(
        p1, p2, STATIC_RECTS, mover_rects, CIRCLES, W, H
    )
    
    # Se o mapa mudou OU se os jogadores spawnaram em cima de obstáculos
    if map_changed or p1.is_colliding(STATIC_RECTS, MOVERS, CIRCLES) or p2.is_colliding(STATIC_RECTS, MOVERS, CIRCLES):
        if map_changed:
            show_map_transition_effect(old_map, current_map)
        
        # Reposiciona jogadores se estiverem em posições perigosas
        for player in [p1, p2]:
            if player.is_colliding(STATIC_RECTS, MOVERS, CIRCLES):
                safe_pos = find_safe_position_nearby(player.x, player.y, player.r)
                if safe_pos:
                    player.x, player.y = safe_pos
                    # Ativa proteção por 2 segundos
                    player.stuck_protection = now + 2000
                    print(f"{player.name} spawnou em obstáculo e foi reposicionado!")
        
        # Efeito sonoro de transição
        if tag_ok and S_TAG:
            S_TAG.play()
    
    return start_ticks, tag_until, powerups, next_pu

def check_and_resolve_stuck(player, now, STATIC_RECTS, MOVERS, CIRCLES):
    """Verifica se o jogador está preso e aplica proteção"""
    # Se já está com proteção, não faz nada
    if now < getattr(player, 'stuck_protection', 0):
        return False
        
    # Verifica se está realmente preso (múltiplas colisões)
    mover_rects = [m.rect() for m in MOVERS] if MOVERS else []
    
    if player.is_stuck(STATIC_RECTS, MOVERS, CIRCLES):
        safe_pos = find_safe_position_nearby(player.x, player.y, player.r)
        if safe_pos:
            player.x, player.y = safe_pos
            # Ativa a proteção específica para stuck por 2 segundos
            player.stuck_protection = now + 2000
            print(f"{player.name} estava preso e foi reposicionado!")
            return True
    
    return False

# ---------------------- Loop principal ----------------------
while True:
    dt = clock.get_time() / 1000.0
    t = pygame.time.get_ticks() / 1000.0
    mouse = pygame.mouse.get_pos()

    for e in pygame.event.get():
        # --- toggle F11 ---
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            fullscreen = not fullscreen
            flags = pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0)
            tela = pygame.display.set_mode((W, H), flags)

        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if state == INTRO:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                state = MENU  # permite pular a abertura

        if state == MENU:
            inp1.handle(e)
            inp2.handle(e)
            pick1.handle(e)
            pick2.handle(e)
            new_mode = mode_selector.handle(e)
            if new_mode:
                current_mode = new_mode

            if (e.type == pygame.MOUSEBUTTONDOWN and btn.clicked(e.pos)) or \
               (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
                # Inicializa os jogadores
                p1 = Player(W * 0.25, H * 0.55, 22, pick1.color(), 5.0,
                           {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d},
                           inp1.text or "Player 1")
                p2 = Player(W * 0.75, H * 0.55, 22, pick2.color(), 5.0,
                           {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT},
                           inp2.text or "Player 2")
                wins = [0, 0]
                round_idx = 1
                
                # Reseta o round de forma segura
                start_ticks, tag_until, powerups, next_pu = safe_reset_round()
                
                state = GAME
                if music_ok:
                    pygame.mixer.music.play(-1)

        elif state == GAME:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif state == END:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    state = MENU
                    inp1.text = inp2.text = ""
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    # ------------- RENDER POR ESTADO -------------
    if state == INTRO:
        if BG_IMG:
            tela.blit(BG_IMG, (0, 0))
        else:
            tela.fill(BG)
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 90))
        tela.blit(shade, (0, 0))

        elapsed = pygame.time.get_ticks() - intro_start
        p = elapsed / INTRO_MS

        FI, FO = 0.25, 0.25
        if p < FI:
            alpha = int(255 * (p / FI))
        elif p > 1 - FO:
            alpha = int(255 * ((1 - p) / FO))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        txt = "FAÇAM SUAS APOSTAS!"
        tsec = pygame.time.get_ticks() / 1000.0
        scale = 1.0 + 0.02 * math.sin(tsec * 3.0)
        text = FT_MEGA.render(txt, True, WHITE)
        shadow = FT_MEGA.render(txt, True, (0, 0, 0))
        text.set_alpha(alpha)
        shadow.set_alpha(int(alpha * 0.6))
        text = pygame.transform.rotozoom(text, 0, scale)
        shadow = pygame.transform.rotozoom(shadow, 0, scale)
        tela.blit(shadow, shadow.get_rect(center=(W // 2 + 3, H // 2 + 2)))
        tela.blit(text, text.get_rect(center=(W // 2, H // 2)))

        if elapsed >= INTRO_MS:
            state = MENU

    elif state == MENU:
        if BG_IMG:
            tela.blit(BG_IMG, (0, 0))
            sh = pygame.Surface((W, H), pygame.SRCALPHA)
            sh.fill((0, 0, 0, 80))
            tela.blit(sh, (0, 0))
        else:
            tela.fill(BG)

        brand = FT.render("Vannpipe Game Inc.", True, WHITE)
        tela.blit(brand, (W // 2 - brand.get_width() // 2, 90))

        title = "Pega - Pega 1V1"
        for i, a in enumerate([90, 60, 30]):
            s = load_font(46 + i * 2).render(title, True, (100, 170, 255))
            s.set_alpha(a)
            tela.blit(s, (W // 2 - s.get_width() // 2, 125 - i * 2))
        main = FT_BIG.render(title, True, WHITE)
        tela.blit(main, (W // 2 - main.get_width() // 2, 120))

        lbl1 = FT_SM.render("Cor P1", True, WHITE)
        tela.blit(lbl1, (W // 2 - 200, y_start - 18))
        pick1.draw(tela)
        inp1.draw(tela, FT)

        lbl2 = FT_SM.render("Cor P2", True, WHITE)
        tela.blit(lbl2, (W // 2 - 200, y_start + spacing - 18))
        pick2.draw(tela)
        inp2.draw(tela, FT)

        mode_selector.draw(tela, FT_SM)
        btn.draw(tela, btn.clicked(mouse), t, FT)

    elif state == GAME:
        # Verifica se os jogadores foram inicializados
        if p1 is None or p2 is None:
            state = MENU
            continue
            
        now = pygame.time.get_ticks()
        elapsed = now - start_ticks
        remain = ROUND_MS - elapsed

        # Verifica se é hora de trocar o mapa
        if now - map_transition_timer > MAP_TRANSITION_TIME:
            current_map = "novo_mapa" if current_map == "original" else "original"
            map_data = get_map(current_map, W, H)
            STATIC_RECTS = map_data["static_rects"]
            CIRCLES = map_data["circles"]
            MOVERS = map_data["movers"]
            map_transition_timer = now

        draw_bg()
        mover_rects = [m.rect() for m in MOVERS] if MOVERS else []
        draw_obstacles(tela, STATIC_RECTS, MOVERS, CIRCLES)

        if now >= next_pu and len(powerups) < 3:
            spawn_powerup(powerups, STATIC_RECTS, MOVERS, CIRCLES, W, H)
            next_pu = now + random.randint(3000, 6000)

        # Movimento dos jogadores com detecção de "preso"
        dx1, dy1 = p1.input()
        result1 = p1.move_collide(dx1, dy1, pygame.Rect(0, 0, W, H), STATIC_RECTS, MOVERS, CIRCLES)
        
        dx2, dy2 = p2.input()
        result2 = p2.move_collide(dx2, dy2, pygame.Rect(0, 0, W, H), STATIC_RECTS, MOVERS, CIRCLES)
        
        # Verifica se algum jogador está preso
        if result1 == "stuck" and now > p1.stuck_protection:
            safe_pos = find_safe_position_nearby(p1.x, p1.y, p1.r)
            if safe_pos:
                p1.x, p1.y = safe_pos
                p1.stuck_protection = now + 2000  # 2 segundos de proteção
                print(f"{p1.name} estava preso e foi reposicionado!")
        
        if result2 == "stuck" and now > p2.stuck_protection:
            safe_pos = find_safe_position_nearby(p2.x, p2.y, p2.r)
            if safe_pos:
                p2.x, p2.y = safe_pos
                p2.stuck_protection = now + 2000  # 2 segundos de proteção
                print(f"{p2.name} estava preso e foi reposicionado!")
        
        # Verifica colisões normais para som
        hit1 = result1 not in [False, "stuck"]
        hit2 = result2 not in [False, "stuck"]
        
        if (hit1 or hit2) and hit_ok and S_HIT:
            S_HIT.play()

        nowms = pygame.time.get_ticks()
        if nowms > p1.speed_until:
            p1.speed_mul = 1.0
        if nowms > p2.speed_until:
            p2.speed_mul = 1.0

        if not p1.is_it:
            p1.score += dt
        if not p2.is_it:
            p2.score += dt

        for pu in powerups[:]:
            who = None
            other = None
            if dist(p1.x, p1.y, pu.x, pu.y) <= p1.r + 14:
                who = p1
                other = p2
            elif dist(p2.x, p2.y, pu.x, pu.y) <= p2.r + 14:
                who = p2
                other = p1
            
            if who:
                apply_powerup(who, other, pu.kind, W, H)
                powerups.remove(pu)

        if now >= tag_until and circles_collide(p1.x, p1.y, p1.r, p2.x, p2.y, p2.r):
            tagger = p1 if p1.is_it else p2
            runner = p2 if p1.is_it else p1
            
            if runner.shield:
                runner.shield = 0
            else:
                p1.is_it, p2.is_it = (not p1.is_it), (not p2.is_it)
                if tag_ok and S_TAG:
                    S_TAG.play()
                
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                d = math.hypot(dx, dy) or 1
                over = (p1.r + p2.r) - d + 2
                nx, ny = dx / d, dy / d
                p1.x -= nx * over * 0.5
                p1.y -= ny * over * 0.5
                p2.x += nx * over * 0.5
                p2.y += ny * over * 0.5
            
            tag_until = now + 500

        for pu in powerups:
            pu.draw(tela)
        
        # Desenha jogadores (o efeito de proteção já está no método draw do Player)
        p1.draw(tela)
        p2.draw(tela)
        
        hud(tela, p1, p2, remain, round_idx, wins, W, H, (FT_BIG, FT, FT_SC, FT_SM))

        if remain <= 0:
            if p1.score > p2.score:
                wins[0] += 1
            elif p2.score > p1.score:
                wins[1] += 1
            
            round_idx += 1
            
            if wins[0] == 2 or wins[1] == 2 or round_idx > 3:
                if wins[0] > wins[1]:
                    winner_msg = f"Vencedor: {p1.name}"
                elif wins[1] > wins[0]:
                    winner_msg = f"Vencedor: {p2.name}"
                else:
                    winner_msg = "Empate!"
                
                if music_ok:
                    pygame.mixer.music.stop()
                
                state = END
            else:
                start_ticks, tag_until, powerups, next_pu = safe_reset_round()

    elif state == END:
        draw_bg()
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        tela.blit(shade, (0, 0))
        
        f = FT_BIG.render("Fim de Jogo!", True, WHITE)
        tela.blit(f, (W // 2 - f.get_width() // 2, H // 2 - 80))
        
        wtxt = FT_SC.render(winner_msg, True, YELL)
        tela.blit(wtxt, (W // 2 - wtxt.get_width() // 2, H // 2 - 30))
        
        info = FT.render("Pressione R para Reiniciar ou ESC para Sair", True, WHITE)
        tela.blit(info, (W // 2 - info.get_width() // 2, H // 2 + 20))

    pygame.display.flip()
    clock.tick(FPS)