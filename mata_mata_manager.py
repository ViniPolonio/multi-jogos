import pygame
import random
import math

# MataMataManager - modo Mata-Mata com punch (soco) visual, colisões com paredes, spawn raro de armas,
# velocidade afetada por munição, e tela de instruções estática.
# Esta versão substitui o "dash" por um soco (lunge) com animação e feedback:
# - Ao apertar F / Right Shift o jogador executa um soco curto.
# - Se o soco acertar, elimina o oponente ao término da animação.
# - Se errar, aplica cooldown e um pequeno "stun" (reduz movimento por breve tempo).
# - Jogadores podem se mover normalmente desde o início.
# - cleanup() incluído para reiniciar corretamente ao voltar ao menu.

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

        # Tamanho e velocidade base
        self.player_size = 40
        self.player_speed = 260  # leve aumento de velocidade base

        # sprites
        self.load_sprites()

        # players - posições e estado
        self.player1 = {
            "pos": [100.0, 100.0],
            "direction": "right",
            "attack_cooldown": 0.0,
            "ammo": 0,
            "name": "Ninja Azul",
            "punch": None,   # dict quando punch em andamento
            "stun": 0.0      # tempo de redução de movimento após errar
        }
        self.player2 = {
            "pos": [self.W - 140.0, self.H - 140.0],
            "direction": "left",
            "attack_cooldown": 0.0,
            "ammo": 0,
            "name": "Ninja Vermelho",
            "punch": None,
            "stun": 0.0
        }

        # mapa e objetos
        self.walls = self.generate_maze()
        self.weapons = []
        self.weapon_spawn_timer = 0.0
        self.weapon_spawn_interval = 12.0  # mais raro
        self.demo_weapon_spawn_interval = 2.5  # instruções
        self.max_weapons = 3
        self.weapon_sprite = self.create_weapon_sprite()

        # tiros
        self.bullets = []
        self.bullet_speed = 420.0
        self.bullet_sprite = self.create_bullet_sprite()

        # melee (punch) parâmetros
        self.melee_range = 64.0
        self.melee_duration = 0.20
        self.melee_cooldown = 5.0
        self.melee_stun_time = 0.6  # tempo de "stun" ao errar (reduz movimento)
        self.melee_visual_size = 10

        # UI / fontes
        self.font = pygame.font.Font(None, 28)
        self.font_big = pygame.font.Font(None, 44)
        self.font_title = pygame.font.Font(None, 72)

        # background / estética
        self.background = self.create_background()

        # instruções timers (para efeito de texto pulsante)
        self.instr_time = 0.0
        self.instr_pulse = 0.0

        # demo spawn inicial
        self.spawn_weapon()

        self.winner = None

    # -------------------------
    # cleanup (chamado ao voltar ao menu / reiniciar)
    # -------------------------
    def cleanup(self):
        # Reseta coleções e estados principais de forma segura
        self.bullets.clear()
        self.weapons.clear()
        # reset players states (posições, munição, cooldowns)
        self.player1.update({
            "pos": [100.0, 100.0], "direction": "right", "attack_cooldown": 0.0,
            "ammo": 0, "punch": None, "stun": 0.0
        })
        self.player2.update({
            "pos": [self.W - 140.0, self.H - 140.0], "direction": "left", "attack_cooldown": 0.0,
            "ammo": 0, "punch": None, "stun": 0.0
        })
        self.current_state = "INSTRUCTIONS"
        self.winner = None
        self.weapon_spawn_timer = 0.0

    # -------------------------
    # Assets / sprites / background
    # -------------------------
    def load_sprites(self):
        s = (self.player_size, self.player_size)
        base_blue = pygame.Surface(s, pygame.SRCALPHA)
        pygame.draw.circle(base_blue, self.BLUE, (s[0] // 2, s[1] // 2), 16)
        pygame.draw.circle(base_blue, (10, 10, 40), (s[0] // 2, s[1] // 2), 8)
        pygame.draw.rect(base_blue, (20, 80, 200), (6, 10, s[0] - 12, 6))

        base_red = pygame.Surface(s, pygame.SRCALPHA)
        pygame.draw.circle(base_red, self.RED, (s[0] // 2, s[1] // 2), 16)
        pygame.draw.circle(base_red, (40, 10, 10), (s[0] // 2, s[1] // 2), 8)
        pygame.draw.rect(base_red, (180, 20, 30), (6, 10, s[0] - 12, 6))

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
        for x in range(0, self.W, 40):
            pygame.draw.line(bg, (36, 36, 42), (x, 0), (x, self.H))
        for y in range(0, self.H, 40):
            pygame.draw.line(bg, (36, 36, 42), (0, y), (self.W, y))
        return bg

    # -------------------------
    # Mapa / spawning
    # -------------------------
    def generate_maze(self):
        walls = []
        thickness = 20
        walls.append(pygame.Rect(0, 0, self.W, thickness))
        walls.append(pygame.Rect(0, self.H - thickness, self.W, thickness))
        walls.append(pygame.Rect(0, 0, thickness, self.H))
        walls.append(pygame.Rect(self.W - thickness, 0, thickness, self.H))
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
    # Eventos
    # -------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.current_state == "INSTRUCTIONS":
                if event.key == pygame.K_SPACE:
                    self.current_state = "PLAYING"
                    return

            if self.current_state == "PLAYING":
                # Punch: P1 = F, P2 = RSHIFT
                if event.key == pygame.K_f and self.player1["attack_cooldown"] <= 0:
                    self.start_punch(self.player1, self.player2)
                if event.key == pygame.K_RSHIFT and self.player2["attack_cooldown"] <= 0:
                    self.start_punch(self.player2, self.player1)

                # Shooting
                if event.key == pygame.K_g and self.player1["ammo"] > 0:
                    self.shoot(self.player1)
                if event.key == pygame.K_RETURN and self.player2["ammo"] > 0:
                    self.shoot(self.player2)

            if event.key == pygame.K_ESCAPE:
                self.current_state = "MAIN_MENU"

    # -------------------------
    # Punch: inicia animação de soco curta com detecção imediata de acerto
    # -------------------------
    def start_punch(self, attacker, target):
        # attacker: dict, target: dict
        ax, ay = attacker["pos"]
        pr = pygame.Rect(int(ax), int(ay), self.player_size, self.player_size)
        # rect representando a área frontal do soco
        dirv = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(attacker["direction"], (1, 0))
        # we build a hit rect in front of player
        if dirv[0] != 0:  # horizontal
            if dirv[0] > 0:
                hit_rect = pygame.Rect(pr.right, pr.top + 4, int(self.melee_range), pr.height - 8)
            else:
                hit_rect = pygame.Rect(pr.left - int(self.melee_range), pr.top + 4, int(self.melee_range), pr.height - 8)
        else:  # vertical
            if dirv[1] > 0:
                hit_rect = pygame.Rect(pr.left + 4, pr.bottom, pr.width - 8, int(self.melee_range))
            else:
                hit_rect = pygame.Rect(pr.left + 4, pr.top - int(self.melee_range), pr.width - 8, int(self.melee_range))

        # check immediate hit
        tpr = pygame.Rect(int(target["pos"][0]), int(target["pos"][1]), self.player_size, self.player_size)
        will_hit = hit_rect.colliderect(tpr)

        attacker["punch"] = {
            "start_pos": [ax, ay],
            "dir": dirv,
            "time": 0.0,
            "duration": self.melee_duration,
            "will_hit": will_hit
        }
        # If hit we delay the win until animation finishes for visual feedback.
        if not will_hit:
            # apply cooldown immediately and a short stun (movement penalty)
            attacker["attack_cooldown"] = self.melee_cooldown
            attacker["stun"] = self.melee_stun_time

    # -------------------------
    # Tiro (mantido)
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
    # Movimento com colisão de paredes
    # -------------------------
    def move_player(self, player, dx, dy):
        orig_x = player["pos"][0]
        orig_y = player["pos"][1]
        if dx != 0:
            player["pos"][0] += dx
            pr = pygame.Rect(int(player["pos"][0]), int(player["pos"][1]), self.player_size, self.player_size)
            collided = any(pr.colliderect(w) for w in self.walls)
            if collided:
                player["pos"][0] = orig_x
        if dy != 0:
            player["pos"][1] += dy
            pr = pygame.Rect(int(player["pos"][0]), int(player["pos"][1]), self.player_size, self.player_size)
            collided = any(pr.colliderect(w) for w in self.walls)
            if collided:
                player["pos"][1] = orig_y

    # -------------------------
    # Update principal
    # -------------------------
    def update(self, dt):
        self.instr_time += dt
        self.instr_pulse = (math.sin(self.instr_time * 2.5) + 1.0) / 2.0

        if self.current_state == "INSTRUCTIONS":
            # apenas spawn demo lento
            self.weapon_spawn_timer += dt
            if self.weapon_spawn_timer >= self.demo_weapon_spawn_interval:
                self.weapon_spawn_timer = 0
                if len(self.weapons) < 2:
                    self.spawn_weapon()
            return

        if self.current_state != "PLAYING":
            return

        # Movement input
        keys = pygame.key.get_pressed()

        def speed_multiplier_for(player):
            # penalidade por munição carregada + redução se stun presente
            factor = 0.06
            mult = 1.0 - player.get("ammo", 0) * factor
            mult = max(0.45, mult)
            # stun reduces speed linearly
            stun = player.get("stun", 0.0)
            if stun > 0:
                mult *= 0.4  # during stun move much slower
            return mult

        # Player 1
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

        # Player 2
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

        # cooldowns and stuns
        for p in (self.player1, self.player2):
            if p["attack_cooldown"] > 0:
                p["attack_cooldown"] = max(0.0, p["attack_cooldown"] - dt)
            if p.get("stun", 0.0) > 0:
                p["stun"] = max(0.0, p["stun"] - dt)

        # weapon spawn (rare)
        self.weapon_spawn_timer += dt
        if self.weapon_spawn_timer >= self.weapon_spawn_interval:
            self.weapon_spawn_timer = 0.0
            self.spawn_weapon()

        # update bullets
        for b in self.bullets[:]:
            b["pos"][0] += b["dir"][0] * self.bullet_speed * dt
            b["pos"][1] += b["dir"][1] * self.bullet_speed * dt
            br = pygame.Rect(int(b["pos"][0]), int(b["pos"][1]), 8, 8)
            # collision walls
            if any(w.colliderect(br) for w in self.walls):
                if b in self.bullets:
                    self.bullets.remove(b)
                continue
            # collision with players
            target = self.player2 if b["shooter"] is self.player1 else self.player1
            tr = pygame.Rect(int(target["pos"][0]), int(target["pos"][1]), self.player_size, self.player_size)
            if br.colliderect(tr):
                self.current_state = "GAME_OVER"
                self.winner = self.player1["name"] if b["shooter"] is self.player1 else self.player2["name"]
                return

        # update punch animations and resolve hits at end of animation
        for p, opponent in ((self.player1, self.player2), (self.player2, self.player1)):
            punch = p.get("punch")
            if not punch:
                continue
            punch["time"] += dt
            t = min(1.0, punch["time"] / punch["duration"])
            # at end, resolve
            if punch["time"] >= punch["duration"]:
                if punch["will_hit"]:
                    # kill the opponent
                    self.current_state = "GAME_OVER"
                    self.winner = p["name"]
                    return
                else:
                    # miss: already applied cooldown and stun at start_punch
                    p["punch"] = None

        # collect weapons
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

    # -------------------------
    # Desenho / UI
    # -------------------------
    def draw(self):
        if self.current_state == "INSTRUCTIONS":
            self.draw_instructions()
            return

        self.screen.blit(self.background, (0, 0))

        # walls
        for w in self.walls:
            shadow = w.inflate(6, 6)
            pygame.draw.rect(self.screen, (30, 30, 30), shadow)
            pygame.draw.rect(self.screen, self.GREY, w)

        # weapons
        for w in self.weapons:
            self.screen.blit(self.weapon_sprite, (int(w["pos"][0]), int(w["pos"][1])))

        # bullets
        for b in self.bullets:
            bx, by = int(b["pos"][0]), int(b["pos"][1])
            self.screen.blit(self.bullet_sprite, (bx - 4, by - 4))

        # players
        self.draw_player(self.player1, self.ninja_blue_sprites)
        self.draw_player(self.player2, self.ninja_red_sprites)

        # punch visuals (draw fist/slash in front of player during animation)
        for p in (self.player1, self.player2):
            punch = p.get("punch")
            if punch:
                # compute center of player
                cx = int(p["pos"][0] + self.player_size / 2)
                cy = int(p["pos"][1] + self.player_size / 2)
                dirv = punch["dir"]
                # position the visual slightly ahead depending on t
                t = min(1.0, punch["time"] / punch["duration"])
                reach = int(self.melee_range * (0.3 + 0.7 * t))  # starts near then extends
                vx = cx + int(dirv[0] * reach)
                vy = cy + int(dirv[1] * reach)
                # draw fist / flash
                pygame.draw.circle(self.screen, (255, 200, 120), (vx, vy), self.melee_visual_size)
                # draw slash line
                ang = math.atan2(dirv[1], dirv[0])
                dx = math.cos(ang) * (self.melee_visual_size + 8)
                dy = math.sin(ang) * (self.melee_visual_size + 8)
                pygame.draw.line(self.screen, (255, 240, 200), (vx - dx, vy - dy), (vx + dx, vy + dy), 4)

        # aim indicators
        self.draw_aim(self.player1)
        self.draw_aim(self.player2)

        # UI
        self.draw_player_interface()

        # game over
        if self.current_state == "GAME_OVER":
            self.draw_game_over()

    def draw_player(self, p, sprites_dict):
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
        pygame.draw.line(self.screen, (180, 180, 200), (int(px), int(py)), (ax, ay), 2)
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
    # Instruções (estática)
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
        lines_p1 = ["Movimento: W A S D", "Ataque corpo-a-corpo: F (curto alcance)", "Atirar: G"]
        yy = y1 + 36
        for l in lines_p1:
            txt = self.font.render(l, True, self.WHITE)
            self.screen.blit(txt, (x1 + 10, yy))
            yy += 28

        x2, y2 = self.W // 2 + 20, 120
        subtitle2 = self.font.render("Player 2 • Ninja Vermelho", True, self.RED)
        self.screen.blit(subtitle2, (x2, y2))
        lines_p2 = ["Movimento: Setas", "Ataque corpo-a-corpo: Right Shift (curto alcance)", "Atirar: Enter"]
        yy = y2 + 36
        for l in lines_p2:
            txt = self.font.render(l, True, self.WHITE)
            self.screen.blit(txt, (x2 + 10, yy))
            yy += 28

        tips_x = 80
        tips_y = self.H - 160
        tip_lines = [
            ("• Colete armas (círculos amarelos) para obter munição", self.YELLOW),
            ("• Ataque corpo-a-corpo tem alcance curto e mata se acertar", self.WHITE),
            ("• Se errar, terá 5s de cooldown e ficará um pouco atordoado", self.WHITE)
        ]
        for i, (txts, col) in enumerate(tip_lines):
            t = self.font.render(txts, True, col)
            self.screen.blit(t, (tips_x, tips_y + i * 28))

        start_text = self.font_big.render("Pressione ESPAÇO para começar", True, self.GREEN)
        self.screen.blit(start_text, (self.W // 2 - start_text.get_width() // 2, self.H - 72))

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