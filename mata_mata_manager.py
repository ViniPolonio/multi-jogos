import pygame
import random
import math

# MataMataManager - gerencia o modo mata-mata com UI, instruções, mira estável e animação de melee.
# Atualizações nesta versão:
# - Remove "casinhas" do meio do mapa.
# - Melee agora é um dash + "slash" (corte) visual; se acertar, finaliza; se errar, dash curto e aplica cooldown.
# - Jogadores passam a colidir de verdade com paredes (não podem atravessá-las).
# - Velocidade base levemente aumentada; velocidade diminui conforme o jogador carrega mais munição.
# - Spawn de armas permanece raro (configurado).

class MataMataManager:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W = W
        self.H = H
        self.current_state = "INSTRUCTIONS"  # INSTRUCTIONS -> PLAYING -> GAME_OVER -> MAIN_MENU

        # Cores
        self.WHITE = (255, 255, 255)
        self.BLACK = (12, 12, 12)
        self.RED = (220, 60, 60)
        self.BLUE = (80, 150, 255)
        self.GREEN = (100, 230, 130)
        self.YELLOW = (250, 220, 100)
        self.GREY = (60, 60, 60)
        self.UI_BG = (18, 18, 24)

        # Definições que são usadas por load_sprites() — precisam existir antes
        self.player_size = 40
        # aumentei um pouco a velocidade base
        self.player_speed = 240

        # Sprites / assets
        self.load_sprites()

        # Players
        self.player1 = {
            "pos": [100.0, 100.0],
            "color": self.BLUE,
            "direction": "right",
            "attack_cooldown": 0.0,
            "ammo": 0,
            "name": "Ninja Azul",
            "melee_anim": None  # estrutura de animação do melee se estiver ocorrendo
        }
        self.player2 = {
            "pos": [self.W - 140.0, self.H - 140.0],
            "color": self.RED,
            "direction": "left",
            "attack_cooldown": 0.0,
            "ammo": 0,
            "name": "Ninja Vermelho",
            "melee_anim": None
        }

        # Mapa e objetos
        self.walls = self.generate_maze()
        self.weapons = []
        self.weapon_spawn_timer = 0.0
        # spawn muito mais raro em gameplay:
        self.weapon_spawn_interval = 12.0
        self.demo_weapon_spawn_interval = 2.5  # apenas para instruções/demonstração
        self.max_weapons = 3
        self.weapon_sprite = self.create_weapon_sprite()

        # Tiro
        self.bullets = []
        self.bullet_speed = 420.0
        self.bullet_sprite = self.create_bullet_sprite()

        # Melee
        self.melee_range = 50.0
        self.melee_cooldown = 5.0
        self.melee_dash_distance = 60.0  # distância do dash quando erra

        # UI / fontes
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 44)
        self.font_title = pygame.font.Font(None, 72)

        # Background / estética
        self.background = self.create_background()

        # Instruções: animação e timers
        self.instr_time = 0.0
        self.instr_pulse = 0.0

        # Somente para demo: spawn inicial de uma arma
        self.spawn_weapon()

        # Estado de fim de jogo
        self.winner = None

    # -------------------------
    # Assets / geração visual
    # -------------------------
    def load_sprites(self):
        # Gera sprites simples (circulares) para cada jogador e versões direcionais
        s = (self.player_size, self.player_size)
        # Base azul ninja
        base_blue = pygame.Surface(s, pygame.SRCALPHA)
        pygame.draw.circle(base_blue, self.BLUE, (s[0] // 2, s[1] // 2), 16)
        pygame.draw.circle(base_blue, (10, 10, 40), (s[0] // 2, s[1] // 2), 8)
        pygame.draw.rect(base_blue, (20, 80, 200), (6, 10, s[0] - 12, 6))
        # Base red ninja
        base_red = pygame.Surface(s, pygame.SRCALPHA)
        pygame.draw.circle(base_red, self.RED, (s[0] // 2, s[1] // 2), 16)
        pygame.draw.circle(base_red, (40, 10, 10), (s[0] // 2, s[1] // 2), 8)
        pygame.draw.rect(base_red, (180, 20, 30), (6, 10, s[0] - 12, 6))

        # directional sprites by rotating/flipping base (keeps simple look)
        self.ninja_blue_sprites = {
            "right": base_blue,
            "left": pygame.transform.flip(base_blue, True, False),
            "up": pygame.transform.rotate(base_blue, 90),
            "down": pygame.transform.rotate(base_blue, -90)
        }
        self.ninja_red_sprites = {
            "right": base_red,
            "left": pygame.transform.flip(base_red, True, False),
            "up": pygame.transform.rotate(base_red, 90),
            "down": pygame.transform.rotate(base_red, -90)
        }

    def create_weapon_sprite(self):
        surf = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.YELLOW, (11, 11), 9)
        pygame.draw.rect(surf, (120, 120, 120), (9, 2, 4, 12))
        return surf

    def create_bullet_sprite(self):
        surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (240, 240, 140), (4, 4), 4)
        return surf

    def create_background(self):
        bg = pygame.Surface((self.W, self.H))
        bg.fill((28, 28, 34))
        # grid subtle
        for x in range(0, self.W, 40):
            pygame.draw.line(bg, (36, 36, 42), (x, 0), (x, self.H))
        for y in range(0, self.H, 40):
            pygame.draw.line(bg, (36, 36, 42), (0, y), (self.W, y))
        # vignette
        vignette = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 80), vignette.get_rect(), border_radius=0)
        bg.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        return bg

    # -------------------------
    # Mapa / spawning
    # -------------------------
    def generate_maze(self):
        walls = []
        thickness = 20
        # borders
        walls.append(pygame.Rect(0, 0, self.W, thickness))  # top
        walls.append(pygame.Rect(0, self.H - thickness, self.W, thickness))  # bottom
        walls.append(pygame.Rect(0, 0, thickness, self.H))  # left
        walls.append(pygame.Rect(self.W - thickness, 0, thickness, self.H))  # right

        # Some internal walls (mix of horizontal / vertical)
        for _ in range(8):
            if random.random() < 0.6:
                w = random.randint(120, 260)
                h = thickness
            else:
                w = thickness
                h = random.randint(120, 260)
            x = random.randint(60, max(60, self.W - w - 60))
            y = random.randint(60, max(60, self.H - h - 60))
            walls.append(pygame.Rect(x, y, w, h))
        return walls

    def spawn_weapon(self):
        if len(self.weapons) >= self.max_weapons:
            return
        x = random.randint(50, self.W - 50)
        y = random.randint(50, self.H - 50)
        ammo = random.randint(1, 4)
        self.weapons.append({"pos": [float(x), float(y)], "ammo": ammo})

    # -------------------------
    # Input / eventos
    # -------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # instruções -> iniciar
            if self.current_state == "INSTRUCTIONS":
                if event.key == pygame.K_SPACE:
                    self.current_state = "PLAYING"
                    return

            if self.current_state == "PLAYING":
                # melee: P1 = F, P2 = RSHIFT
                if event.key == pygame.K_f and self.player1["attack_cooldown"] <= 0 and not self.player1["melee_anim"]:
                    self.start_melee(self.player1, self.player2)
                if event.key == pygame.K_RSHIFT and self.player2["attack_cooldown"] <= 0 and not self.player2["melee_anim"]:
                    self.start_melee(self.player2, self.player1)

                # tiro: P1 = G, P2 = ENTER
                if event.key == pygame.K_g and self.player1["ammo"] > 0:
                    self.shoot(self.player1)
                if event.key == pygame.K_RETURN and self.player2["ammo"] > 0:
                    self.shoot(self.player2)

            # voltar
            if event.key == pygame.K_ESCAPE:
                self.current_state = "MAIN_MENU"

    # -------------------------
    # Movimento com colisão de paredes
    # -------------------------
    def move_player(self, player, dx, dy):
        """Move o jogador com checagem de colisão com as walls.
           Aplica separadamente em X e em Y para evitar "stuck"."""
        # tentativa eixo X
        orig_x = player["pos"][0]
        orig_y = player["pos"][1]
        if dx != 0:
            player["pos"][0] += dx
            pr = pygame.Rect(int(player["pos"][0]), int(player["pos"][1]), self.player_size, self.player_size)
            collided = False
            for w in self.walls:
                if pr.colliderect(w):
                    collided = True
                    break
            if collided:
                player["pos"][0] = orig_x  # revert X

        # tentativa eixo Y
        if dy != 0:
            player["pos"][1] += dy
            pr = pygame.Rect(int(player["pos"][0]), int(player["pos"][1]), self.player_size, self.player_size)
            collided = False
            for w in self.walls:
                if pr.colliderect(w):
                    collided = True
                    break
            if collided:
                player["pos"][1] = orig_y  # revert Y

    # -------------------------
    # Melee (dash + stab/slash)
    # -------------------------
    def start_melee(self, attacker, target):
        ax, ay = attacker["pos"]
        tx, ty = target["pos"]
        dx = tx - ax
        dy = ty - ay
        dist = math.hypot(dx, dy)

        if dist <= self.melee_range:
            # Hit case: animate a dash/feitiço until near target -> kill
            end_pos = [tx, ty]
            hit = True
        else:
            # Miss: compute a dash end point in direction facing (short distance)
            dirs = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
            dirv = dirs.get(attacker["direction"], (1, 0))
            end_pos = [ax + dirv[0] * self.melee_dash_distance, ay + dirv[1] * self.melee_dash_distance]
            # clamp end_pos inside world bounds
            end_pos[0] = max(10, min(self.W - self.player_size - 10, end_pos[0]))
            end_pos[1] = max(10, min(self.H - self.player_size - 10, end_pos[1]))
            hit = False

        # registro da animação de melee
        attacker["melee_anim"] = {
            "start_pos": [ax, ay],
            "end_pos": [float(end_pos[0]), float(end_pos[1])],
            "time": 0.0,
            "duration": 0.28,
            "hit": hit,
            "target_ref": target if hit else None,
            # a animação vai deslocar visualmente o atacante durante o dash;
            # se miss, aplicamos movimento físico ao final (no update).
            "applied_movement_on_end": not hit
        }

    # -------------------------
    # Tiro
    # -------------------------
    def shoot(self, player):
        dirs = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        dirv = dirs.get(player["direction"], (1, 0))
        bx = player["pos"][0] + self.player_size / 2 + dirv[0] * 20
        by = player["pos"][1] + self.player_size / 2 + dirv[1] * 20
        self.bullets.append({
            "pos": [bx, by],
            "dir": dirv,
            "shooter": player
        })
        player["ammo"] = max(0, player["ammo"] - 1)

    # -------------------------
    # Update principal
    # -------------------------
    def update(self, dt):
        self.instr_time += dt
        self.instr_pulse = (math.sin(self.instr_time * 2.5) + 1.0) / 2.0

        if self.current_state == "INSTRUCTIONS":
            # demo spawn rápido para a tela de instruções
            self.weapon_spawn_timer += dt
            if self.weapon_spawn_timer >= self.demo_weapon_spawn_interval:
                self.weapon_spawn_timer = 0
                if len(self.weapons) < 2:
                    self.spawn_weapon()
            return

        if self.current_state != "PLAYING":
            return

        # MOVIMENTO por teclas (usando move_player para respeitar paredes)
        keys = pygame.key.get_pressed()

        # Função auxiliar: aplica redução de velocidade baseada em munição
        def speed_multiplier_for(player):
            # mais munição -> um pouco mais lento; clamp mínimo 0.45 (não fica parado)
            # 0 bala -> 1.0 ; 4 balas -> 1 - 4*0.06 = 0.76 (exemplo); adjust factor to taste
            factor = 0.06
            mult = 1.0 - player["ammo"] * factor
            return max(0.45, mult)

        # Player 1 - WASD
        dx1 = dy1 = 0.0
        sp1 = self.player_speed * speed_multiplier_for(self.player1)
        if keys[pygame.K_a]:
            dx1 -= sp1 * dt
            self.player1["direction"] = "left"
        if keys[pygame.K_d]:
            dx1 += sp1 * dt
            self.player1["direction"] = "right"
        if keys[pygame.K_w]:
            dy1 -= sp1 * dt
            self.player1["direction"] = "up"
        if keys[pygame.K_s]:
            dy1 += sp1 * dt
            self.player1["direction"] = "down"
        if dx1 != 0 or dy1 != 0:
            self.move_player(self.player1, dx1, dy1)

        # Player 2 - setas
        dx2 = dy2 = 0.0
        sp2 = self.player_speed * speed_multiplier_for(self.player2)
        if keys[pygame.K_LEFT]:
            dx2 -= sp2 * dt
            self.player2["direction"] = "left"
        if keys[pygame.K_RIGHT]:
            dx2 += sp2 * dt
            self.player2["direction"] = "right"
        if keys[pygame.K_UP]:
            dy2 -= sp2 * dt
            self.player2["direction"] = "up"
        if keys[pygame.K_DOWN]:
            dy2 += sp2 * dt
            self.player2["direction"] = "down"
        if dx2 != 0 or dy2 != 0:
            self.move_player(self.player2, dx2, dy2)

        # Atualiza cooldowns
        if self.player1["attack_cooldown"] > 0:
            self.player1["attack_cooldown"] = max(0.0, self.player1["attack_cooldown"] - dt)
        if self.player2["attack_cooldown"] > 0:
            self.player2["attack_cooldown"] = max(0.0, self.player2["attack_cooldown"] - dt)

        # Spawn de armas periódicas (muito mais raro)
        self.weapon_spawn_timer += dt
        if self.weapon_spawn_timer >= self.weapon_spawn_interval:
            self.weapon_spawn_timer = 0.0
            self.spawn_weapon()

        # Atualiza balas
        for b in self.bullets[:]:
            b["pos"][0] += b["dir"][0] * self.bullet_speed * dt
            b["pos"][1] += b["dir"][1] * self.bullet_speed * dt
            br = pygame.Rect(int(b["pos"][0]), int(b["pos"][1]), 8, 8)
            # colisão com paredes
            collided = False
            for w in self.walls:
                if w.colliderect(br):
                    collided = True
                    break
            if collided:
                if b in self.bullets:
                    self.bullets.remove(b)
                continue
            # colisão com players
            target = self.player2 if b["shooter"] is self.player1 else self.player1
            tr = pygame.Rect(int(target["pos"][0]), int(target["pos"][1]), self.player_size, self.player_size)
            if br.colliderect(tr):
                self.current_state = "GAME_OVER"
                self.winner = self.player1["name"] if b["shooter"] is self.player1 else self.player2["name"]
                return

        # coleta de armas
        for w in self.weapons[:]:
            wr = pygame.Rect(int(w["pos"][0]), int(w["pos"][1]), 20, 20)
            p1r = pygame.Rect(int(self.player1["pos"][0]), int(self.player1["pos"][1]), self.player_size, self.player_size)
            p2r = pygame.Rect(int(self.player2["pos"][0]), int(self.player2["pos"][1]), self.player_size, self.player_size)
            if wr.colliderect(p1r):
                self.player1["ammo"] += w["ammo"]
                self.weapons.remove(w)
            elif wr.colliderect(p2r):
                self.player2["ammo"] += w["ammo"]
                self.weapons.remove(w)

        # Atualiza animações de melee (se existirem)
        for p in (self.player1, self.player2):
            if p.get("melee_anim"):
                ma = p["melee_anim"]
                ma["time"] += dt
                t = min(1.0, ma["time"] / ma["duration"])
                sx, sy = ma["start_pos"]
                ex, ey = ma["end_pos"]
                lx = sx + (ex - sx) * t
                ly = sy + (ey - sy) * t
                height = 18.0
                arc = (4 * (t - 0.5) * (t - 0.5) - 1) * -height
                ma["current_pos"] = (lx, ly + arc)

                if t >= 1.0:
                    # animação terminou
                    if ma["hit"]:
                        # hit -> finaliza jogo (o atacante vence)
                        self.current_state = "GAME_OVER"
                        self.winner = p["name"]
                        return
                    else:
                        # miss -> aplicar cooldown e mover jogador fisicamente até end_pos (tentativa de dash)
                        exx, eyy = ma["end_pos"]
                        dx = exx - ma["start_pos"][0]
                        dy = eyy - ma["start_pos"][1]
                        # move com checagem de colisão (pode ser parcial)
                        self.move_player(p, dx, dy)
                        p["attack_cooldown"] = self.melee_cooldown
                        p["melee_anim"] = None

    # -------------------------
    # Desenho / UI
    # -------------------------
    def draw(self):
        if self.current_state == "INSTRUCTIONS":
            self.draw_instructions()
            return

        # cenário
        self.screen.blit(self.background, (0, 0))

        # paredes com sombra
        for w in self.walls:
            shadow = w.inflate(6, 6)
            pygame.draw.rect(self.screen, (30, 30, 30), shadow)
            pygame.draw.rect(self.screen, self.GREY, w)

        # armas
        for w in self.weapons:
            self.screen.blit(self.weapon_sprite, (int(w["pos"][0]), int(w["pos"][1])))

        # balas
        for b in self.bullets:
            bx, by = int(b["pos"][0]), int(b["pos"][1])
            self.screen.blit(self.bullet_sprite, (bx - 4, by - 4))

        # jogadores (priorizando desenho da animação se presente)
        self.draw_player(self.player1, self.ninja_blue_sprites)
        self.draw_player(self.player2, self.ninja_red_sprites)

        # mira / indicador
        self.draw_aim(self.player1)
        self.draw_aim(self.player2)

        # animações de melee: desenha slash/efeito quando presente
        for p in (self.player1, self.player2):
            ma = p.get("melee_anim")
            if ma and ma.get("current_pos"):
                cxf, cyf = ma["current_pos"]
                cx = int(cxf + self.player_size // 2)
                cy = int(cyf + self.player_size // 2)
                # desenha um corte/flash: uma linha curta na direção do dash
                if ma["hit"]:
                    color = (255, 220, 120)
                    length = 30
                else:
                    color = (255, 160, 100)
                    length = 20
                # direção do corte: do start para end
                sx, sy = ma["start_pos"]
                ex, ey = ma["end_pos"]
                ang = math.atan2(ey - sy, ex - sx)
                dx = math.cos(ang) * length
                dy = math.sin(ang) * length
                pygame.draw.line(self.screen, color, (cx - dx / 2, cy - dy / 2), (cx + dx / 2, cy + dy / 2), 6)
                # brilho central
                pygame.draw.circle(self.screen, (255, 240, 180), (cx, cy), 6)

        # UI topo semi-transparente
        self.draw_player_interface()

        # game over screen
        if self.current_state == "GAME_OVER":
            self.draw_game_over()

    def draw_player(self, p, sprites_dict):
        ma = p.get("melee_anim")
        if ma and ma.get("current_pos"):
            cp = ma["current_pos"]
            px = int(cp[0])
            py = int(cp[1])
            spr = sprites_dict.get(p.get("direction", "right"))
            self.screen.blit(spr, (px, py))
        else:
            x = int(p["pos"][0])
            y = int(p["pos"][1])
            spr = sprites_dict.get(p.get("direction", "right"))
            self.screen.blit(spr, (x, y))

    def draw_aim(self, player):
        dirs = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        dirv = dirs.get(player["direction"], (1, 0))
        px = player["pos"][0] + self.player_size / 2
        py = player["pos"][1] + self.player_size / 2
        aim_distance = 44
        ax = int(px + dirv[0] * aim_distance)
        ay = int(py + dirv[1] * aim_distance)

        # linha guia curta
        pygame.draw.line(self.screen, (180, 180, 200), (int(px), int(py)), (ax, ay), 2)
        # retícula
        outer = 10
        inner = 5
        color = (200, 220, 255) if player is self.player1 else (255, 180, 180)
        pygame.draw.circle(self.screen, color, (ax, ay), outer, 2)
        pygame.draw.circle(self.screen, color, (ax, ay), inner)

    def draw_player_interface(self):
        info_h = 46
        surf = pygame.Surface((self.W, info_h), pygame.SRCALPHA)
        surf.fill((10, 10, 12, 220))
        self.screen.blit(surf, (0, 0))

        p1_info = f"{self.player1['name']}  •  Ammo: {self.player1['ammo']}"
        if self.player1["attack_cooldown"] > 0:
            p1_info += f"  |  Cooldown: {self.player1['attack_cooldown']:.1f}s"
        t1 = self.font.render(p1_info, True, self.BLUE)
        self.screen.blit(t1, (12, 10))

        p2_info = f"{self.player2['name']}  •  Ammo: {self.player2['ammo']}"
        if self.player2["attack_cooldown"] > 0:
            p2_info += f"  |  Cooldown: {self.player2['attack_cooldown']:.1f}s"
        t2 = self.font.render(p2_info, True, self.RED)
        self.screen.blit(t2, (self.W - t2.get_width() - 12, 10))

    # -------------------------
    # Instruções melhoradas (tela inicial)
    # -------------------------
    def draw_instructions(self):
        overlay = pygame.Surface((self.W, self.H))
        overlay.fill((6, 6, 8))
        overlay.set_alpha(240)
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("MATA-MATA • INSTRUÇÕES", True, self.YELLOW)
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 30))

        x1, y1 = 80, 120
        subtitle1 = self.font.render("Player 1 • Ninja Azul", True, self.BLUE)
        self.screen.blit(subtitle1, (x1, y1))
        lines_p1 = ["Movimento: W A S D", "Ataque corpo-a-corpo: F", "Atirar: G"]
        yy = y1 + 36
        for l in lines_p1:
            txt = self.font.render(l, True, self.WHITE)
            self.screen.blit(txt, (x1 + 10, yy))
            yy += 28

        x2, y2 = self.W // 2 + 20, 120
        subtitle2 = self.font.render("Player 2 • Ninja Vermelho", True, self.RED)
        self.screen.blit(subtitle2, (x2, y2))
        lines_p2 = ["Movimento: Setas", "Ataque corpo-a-corpo: Right Shift", "Atirar: Enter"]
        yy = y2 + 36
        for l in lines_p2:
            txt = self.font.render(l, True, self.WHITE)
            self.screen.blit(txt, (x2 + 10, yy))
            yy += 28

        tips_x = 80
        tips_y = self.H - 180
        tip_lines = [
            ("• Colete armas (círculos amarelos) para obter munição", self.YELLOW),
            ("• Ataque corpo-a-corpo precisa estar próximo para matar", self.WHITE),
            ("• Se errar o corpo-a-corpo, terá 5s de cooldown e dará um dash curto", self.WHITE)
        ]
        for i, (txts, col) in enumerate(tip_lines):
            t = self.font.render(txts, True, col)
            self.screen.blit(t, (tips_x, tips_y + i * 28))

        demo_w = 140
        demo_h = 120
        demo_x = self.W // 2 - demo_w // 2
        demo_y = self.H // 2 - demo_h // 2 + 30
        pygame.draw.rect(self.screen, (22, 22, 28), (demo_x - 8, demo_y - 8, demo_w + 16, demo_h + 16), border_radius=8)
        pygame.draw.rect(self.screen, (30, 30, 36), (demo_x, demo_y, demo_w, demo_h), border_radius=6)

        t = self.instr_time
        p1_demo_x = demo_x + 30 + math.sin(t * 1.8) * 26
        p1_demo_y = demo_y + 30 + math.cos(t * 1.3) * 8
        p2_demo_x = demo_x + demo_w - 60 + math.cos(t * 1.6) * 26
        p2_demo_y = demo_y + demo_h - 60 + math.sin(t * 1.1) * 8

        small_blue = pygame.transform.smoothscale(self.ninja_blue_sprites["right"], (28, 28))
        small_red = pygame.transform.smoothscale(self.ninja_red_sprites["left"], (28, 28))
        self.screen.blit(small_blue, (int(p1_demo_x), int(p1_demo_y)))
        self.screen.blit(small_red, (int(p2_demo_x), int(p2_demo_y)))

        if (int(self.instr_time) % 4) < 2:
            start = (int(p1_demo_x) + 14, int(p1_demo_y) + 14)
            end = (start[0] + 28, start[1])
            pygame.draw.line(self.screen, (240, 240, 180), start, end, 3)
        else:
            hx = demo_x + demo_w // 2
            hy = demo_y + 18
            pygame.draw.polygon(self.screen, (190, 100, 80), [(hx - 8, hy + 8), (hx, hy - 8), (hx + 8, hy + 8)])
            start = (int(p2_demo_x) + 14, int(p2_demo_y) + 14)
            pygame.draw.line(self.screen, (255, 200, 100), start, (hx, hy), 3)

        # calcula cor pulsante com clamp para evitar valores inválidos (>255)
        pulse = 0.9 + 0.2 * self.instr_pulse

        def clamp8(v):
            return max(0, min(255, int(v)))

        r = clamp8(200 * pulse)
        g = clamp8(240 * pulse)
        b = clamp8(180 * pulse)
        start_text = self.font_big.render("Pressione ESPAÇO para jogar", True, (r, g, b))
        self.screen.blit(start_text, (self.W // 2 - start_text.get_width() // 2, self.H - 72))

        foot = self.font.render("Dica: Mova-se, colete armas e use a mira (indicador à frente do jogador).", True, (160, 160, 160))
        self.screen.blit(foot, (self.W // 2 - foot.get_width() // 2, self.H - 36))

    # -------------------------
    # Game over
    # -------------------------
    def draw_game_over(self):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((4, 4, 6, 200))
        self.screen.blit(overlay, (0, 0))
        txt = self.font_big.render("FIM DE JOGO", True, self.YELLOW)
        sub = self.font.render(f"{self.winner} venceu!", True, self.WHITE)
        info = self.font.render("Pressione ESC para voltar ao menu", True, (180, 180, 180))
        self.screen.blit(txt, (self.W // 2 - txt.get_width() // 2, self.H // 2 - 80))
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, self.H // 2 - 20))
        self.screen.blit(info, (self.W // 2 - info.get_width() // 2, self.H // 2 + 26))