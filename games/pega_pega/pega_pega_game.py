import pygame
import math
import random
from games.base_game import BaseGame
from games.pega_pega.entities import Player, PowerUp, spawn_powerup, apply_powerup
from games.pega_pega.maps import get_map, draw_obstacles
from utils.helpers import dist, circles_collide, circle_rect, clamp, reset_round

def hud(screen, p1, p2, remain, round_idx, wins, W, H):
    """Desenha o HUD (Heads-Up Display) do jogo"""
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Fundo do HUD
    hud_bg = pygame.Surface((W, 80), pygame.SRCALPHA)
    hud_bg.fill((0, 0, 0, 150))
    screen.blit(hud_bg, (0, 0))
    
    # Nome do jogador 1 com indicador de "pegador"
    p1_text = f"{p1.name} {'🔴' if p1.is_it else '🔵'}"
    p1_surface = font.render(p1_text, True, p1.color)
    screen.blit(p1_surface, (20, 20))
    
    # Nome do jogador 2 com indicador de "pegador" 
    p2_text = f"{'🔴' if p2.is_it else '🔵'} {p2.name}"
    p2_surface = font.render(p2_text, True, p2.color)
    screen.blit(p2_surface, (W - p2_surface.get_width() - 20, 20))
    
    # Round e vitórias
    round_text = small_font.render(f"Round {round_idx} | {wins[0]} - {wins[1]}", True, (200, 200, 200))
    screen.blit(round_text, (W // 2 - round_text.get_width() // 2, 15))
    
    # Tempo restante
    if remain > 0:
        time_text = font.render(f"{remain // 1000}s", True, (255, 255, 255))
        time_rect = time_text.get_rect(center=(W // 2, 50))
        screen.blit(time_text, time_rect)
    
    # Score dos jogadores (se não for modo TAG)
    if not p1.is_it and not p2.is_it:
        score_text = small_font.render(f"Score: {int(p1.score)} - {int(p2.score)}", True, (180, 180, 180))
        score_rect = score_text.get_rect(center=(W // 2, 65))
        screen.blit(score_text, score_rect)

class PegaPegaGame(BaseGame):
    def __init__(self, screen, width, height, player1_name="Player 1", player2_name="Player 2", 
                 player1_color=(255, 109, 106), player2_color=(92, 225, 230), game_mode="TAG"):
        super().__init__(screen, width, height)
        
        # Configurações recebidas do menu
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_color = player1_color
        self.player2_color = player2_color
        self.game_mode = game_mode
        
        # Configurações do jogo
        self.ROUND_MS = 60 * 1000
        self.COOLDOWN = 500
        self.round_idx = 1
        self.wins = [0, 0]
        self.winner_msg = ""
        
        # Estados do jogo
        self.game_state = "PLAYING"
        
        # Inicializa mapa e jogadores
        self.current_map = "original"
        self.load_map()
        self.initialize_players()
        
        # Power-ups e estado do jogo
        self.powerups = []
        self.next_pu = 0
        
        # Transição de mapa - NOVAS VARIÁVEIS
        self.map_transition_timer = pygame.time.get_ticks()
        self.MAP_TRANSITION_TIME = 15000  # 15 segundos entre trocas
        self.transition_warning_start = 5000  # 5 segundos antes começa a piscar
        self.invincible_until = 0  # Timer para invencibilidade pós-transição
        self.INVINCIBILITY_TIME = 2000  # 2 segundos de invencibilidade
        self.transition_warning = False  # Controla a piscada da tela
        self.warning_alpha = 0  # Alpha para o efeito de piscada
        
        # Inicia primeiro round
        self.reset_round()
        
        # Carrega recursos
        self.load_assets()
    
    def initialize_players(self):
        """Inicializa os jogadores com as configurações do menu"""
        self.p1 = Player(
            x=self.width * 0.25, y=self.height * 0.55, r=22, 
            color=self.player1_color, vel=5.0,
            keys={"up": pygame.K_w, "down": pygame.K_s, 
                  "left": pygame.K_a, "right": pygame.K_d},
            name=self.player1_name
        )
        
        self.p2 = Player(
            x=self.width * 0.75, y=self.height * 0.55, r=22,
            color=self.player2_color, vel=5.0,
            keys={"up": pygame.K_UP, "down": pygame.K_DOWN,
                  "left": pygame.K_LEFT, "right": pygame.K_RIGHT},
            name=self.player2_name
        )
    
    def load_assets(self):
        """Carrega recursos específicos do jogo"""
        try:
            self.bg_image = pygame.image.load("assets/python.png").convert_alpha()
            self.bg_image = pygame.transform.smoothscale(self.bg_image, (self.width, self.height))
        except:
            self.bg_image = None
        
        # Sons (opcionais)
        self.sounds = {}
        try:
            self.sounds['tag'] = pygame.mixer.Sound("assets/tag.wav")
            self.sounds['hit'] = pygame.mixer.Sound("assets/hit.wav")
        except:
            self.sounds = {}
    
    def load_map(self):
        """Carrega o mapa atual"""
        map_data = get_map(self.current_map, self.width, self.height)
        self.static_rects = map_data["static_rects"]
        self.circles = map_data["circles"]
        self.movers = map_data["movers"]
    
    def handle_event(self, event):
        """Processa eventos do jogo"""
        if self.game_state == "PLAYING":
            # Eventos específicos durante o jogo podem ser adicionados aqui
            pass
    
    def update(self, dt):
        """Atualiza a lógica do jogo"""
        if self.game_state != "PLAYING":
            return
            
        now = pygame.time.get_ticks()
        elapsed = now - self.start_ticks
        self.remain = self.ROUND_MS - elapsed
        
        # NOVO: Verifica transição de mapa e avisos
        time_until_transition = self.MAP_TRANSITION_TIME - (now - self.map_transition_timer)
        
        # Ativa aviso de transição (piscada) nos últimos 5 segundos
        self.transition_warning = time_until_transition <= self.transition_warning_start
        
        # Controla o alpha para o efeito de piscada
        if self.transition_warning:
            # Pisca a cada 500ms (0.5 segundos)
            self.warning_alpha = 100 if (now // 500) % 2 == 0 else 0
        
        # Executa a transição de mapa
        if time_until_transition <= 0:
            self.switch_map()
            self.invincible_until = now + self.INVINCIBILITY_TIME
        
        # Atualiza obstáculos móveis
        for mover in self.movers:
            mover.update()
        
        # Spawn de power-ups
        if now >= self.next_pu and len(self.powerups) < 3:
            spawn_powerup(self.powerups, self.static_rects, self.movers, 
                         self.circles, self.width, self.height)
            self.next_pu = now + random.randint(3000, 6000)
        
        # Movimento dos jogadores
        self.update_players(dt)
        
        # Verifica colisões entre jogadores
        self.check_player_collision(now)
        
        # Verifica power-ups
        self.check_powerups()
        
        # Verifica fim do round
        if self.remain <= 0:
            self.end_round()
    
    def switch_map(self):
        """Alterna entre mapas"""
        self.current_map = "novo_mapa" if self.current_map == "original" else "original"
        self.load_map()
        self.map_transition_timer = pygame.time.get_ticks()
        
        # Reposiciona jogadores no novo mapa
        self.reposition_players()
    
    def reposition_players(self):
        """Reposiciona jogadores no novo mapa"""
        mover_rects = [m.rect() for m in self.movers]
        self.p1.x, self.p1.y = self.find_safe_spawn("left", self.p1.r, mover_rects)
        self.p2.x, self.p2.y = self.find_safe_spawn("right", self.p2.r, mover_rects)
    
    def find_safe_spawn(self, side, radius, mover_rects):
        """Encontra posição segura para spawn"""
        if side == "left":
            x_range = (80, int(self.width * 0.40))
        else:
            x_range = (int(self.width * 0.60), self.width - 80)
        
        for _ in range(100):
            x = random.randint(x_range[0], x_range[1])
            y = random.randint(110, self.height - 80)
            
            # Verifica colisão com obstáculos
            collision = (any(circle_rect(x, y, radius, r) for r in self.static_rects + mover_rects) or
                        any(circles_collide(x, y, radius, cx, cy, cr) for (cx, cy, cr) in self.circles))
            
            if not collision:
                return float(x), float(y)
        
        # Fallback
        if side == "left":
            return self.width * 0.25, self.height * 0.5
        else:
            return self.width * 0.75, self.height * 0.5
    
    def update_players(self, dt):
        """Atualiza movimento dos jogadores"""
        mover_rects = [m.rect() for m in self.movers]
        
        dx1, dy1 = self.p1.input()
        
        # NOVO: Aplica invencibilidade - ignora colisões durante transição
        if pygame.time.get_ticks() < self.invincible_until:
            # Movimento sem colisão durante invencibilidade
            self.p1.x = clamp(self.p1.x + dx1, self.p1.r, self.width - self.p1.r)
            self.p1.y = clamp(self.p1.y + dy1, self.p1.r, self.height - self.p1.r)
            hit1 = False
        else:
            # Movimento normal com colisão
            hit1 = self.p1.move_collide(dx1, dy1, pygame.Rect(0, 0, self.width, self.height),
                               self.static_rects, mover_rects, self.circles)
        
        dx2, dy2 = self.p2.input()
        
        # NOVO: Aplica invencibilidade - ignora colisões durante transição
        if pygame.time.get_ticks() < self.invincible_until:
            # Movimento sem colisão durante invencibilidade
            self.p2.x = clamp(self.p2.x + dx2, self.p2.r, self.width - self.p2.r)
            self.p2.y = clamp(self.p2.y + dy2, self.p2.r, self.height - self.p2.r)
            hit2 = False
        else:
            # Movimento normal com colisão
            hit2 = self.p2.move_collide(dx2, dy2, pygame.Rect(0, 0, self.width, self.height),
                               self.static_rects, mover_rects, self.circles)
        
        # Efeito sonoro de colisão (apenas quando não invencível)
        if (hit1 or hit2) and 'hit' in self.sounds and pygame.time.get_ticks() >= self.invincible_until:
            self.sounds['hit'].play()
        
        # Atualiza timers de power-ups
        nowms = pygame.time.get_ticks()
        if nowms > self.p1.speed_until:
            self.p1.speed_mul = 1.0
        if nowms > self.p2.speed_until:
            self.p2.speed_mul = 1.0
        
        # Atualiza scores
        if not self.p1.is_it:
            self.p1.score += dt
        if not self.p2.is_it:
            self.p2.score += dt
    
    def check_player_collision(self, now):
        """Verifica colisão entre jogadores"""
        # NOVO: Ignora colisão entre jogadores durante invencibilidade
        if pygame.time.get_ticks() < self.invincible_until:
            return
            
        if (now >= self.tag_until and 
            circles_collide(self.p1.x, self.p1.y, self.p1.r, 
                          self.p2.x, self.p2.y, self.p2.r)):
            
            tagger = self.p1 if self.p1.is_it else self.p2
            runner = self.p2 if self.p1.is_it else self.p1
            
            if runner.shield:
                runner.shield = 0
            else:
                # Troca de pegador
                self.p1.is_it, self.p2.is_it = not self.p1.is_it, not self.p2.is_it
                if 'tag' in self.sounds:
                    self.sounds['tag'].play()
                
                # Efeito de repulsão
                dx = self.p2.x - self.p1.x
                dy = self.p2.y - self.p1.y
                d = math.hypot(dx, dy) or 1
                over = (self.p1.r + self.p2.r) - d + 2
                nx, ny = dx / d, dy / d
                self.p1.x -= nx * over * 0.5
                self.p1.y -= ny * over * 0.5
                self.p2.x += nx * over * 0.5
                self.p2.y += ny * over * 0.5
            
            self.tag_until = now + 500
    
    def check_powerups(self):
        """Verifica coleta de power-ups"""
        for pu in self.powerups[:]:
            who = None
            other = None
            
            if dist(self.p1.x, self.p1.y, pu.x, pu.y) <= self.p1.r + 14:
                who, other = self.p1, self.p2
            elif dist(self.p2.x, self.p2.y, pu.x, pu.y) <= self.p2.r + 14:
                who, other = self.p2, self.p1
            
            if who:
                apply_powerup(who, other, pu.kind, self.width, self.height)
                self.powerups.remove(pu)
    
    def end_round(self):
        """Finaliza o round atual"""
        if self.p1.score > self.p2.score:
            self.wins[0] += 1
        elif self.p2.score > self.p1.score:
            self.wins[1] += 1
        
        self.round_idx += 1
        
        # Verifica fim do jogo
        if self.wins[0] == 2 or self.wins[1] == 2 or self.round_idx > 3:
            self.game_state = "GAME_END"
            if self.wins[0] > self.wins[1]:
                self.winner_msg = f"Vencedor: {self.p1.name}"
            elif self.wins[1] > self.wins[0]:
                self.winner_msg = f"Vencedor: {self.p2.name}"
            else:
                self.winner_msg = "Empate!"
        else:
            # Próximo round
            self.reset_round()
    
    def reset_round(self):
        """Reseta para um novo round"""
        # Reposiciona jogadores
        mover_rects = [m.rect() for m in self.movers]
        self.p1.x, self.p1.y = self.find_safe_spawn("left", self.p1.r, mover_rects)
        self.p2.x, self.p2.y = self.find_safe_spawn("right", self.p2.r, mover_rects)
        
        # Reseta estados
        self.p1.score = self.p2.score = 0.0
        self.p1.speed_mul = self.p2.speed_mul = 1.0
        self.p1.speed_until = self.p2.speed_until = 0
        self.p1.shield = self.p2.shield = 0
        self.p1.frozen_until = self.p2.frozen_until = 0
        
        # Escolhe pegador aleatório
        if random.choice([True, False]):
            self.p1.is_it, self.p2.is_it = True, False
        else:
            self.p1.is_it, self.p2.is_it = False, True
        
        self.start_ticks = pygame.time.get_ticks()
        self.tag_until = 0
        self.powerups = []
        self.next_pu = self.start_ticks + random.randint(1500, 3000)
        self.game_state = "PLAYING"
        
        # NOVO: Reseta timer de transição de mapa
        self.map_transition_timer = pygame.time.get_ticks()
        self.invincible_until = 0
        self.transition_warning = False
    
    def draw(self):
        """Desenha o jogo"""
        # Fundo
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 70))
            self.screen.blit(shade, (0, 0))
        else:
            self.screen.fill((18, 18, 18))
        
        if self.game_state == "PLAYING":
            self.draw_playing()
        elif self.game_state == "GAME_END":
            self.draw_game_end()
    
    def draw_playing(self):
        """Desenha o jogo durante gameplay"""
        # Obstáculos
        draw_obstacles(self.screen, self.static_rects, self.movers, self.circles)
        
        # Power-ups
        for pu in self.powerups:
            pu.draw(self.screen)
        
        # Jogadores
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        
        # NOVO: Efeito de piscada para aviso de transição
        if self.transition_warning and self.warning_alpha > 0:
            warning_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            warning_overlay.fill((255, 255, 0, self.warning_alpha))  # Amarelo piscante
            self.screen.blit(warning_overlay, (0, 0))
        
        # NOVO: Efeito de invencibilidade nos jogadores
        now = pygame.time.get_ticks()
        if now < self.invincible_until:
            # Desenha aura de invencibilidade
            invincibility_alpha = 128 + int(127 * math.sin(now * 0.01))  # Efeito pulsante
            for player in [self.p1, self.p2]:
                aura = pygame.Surface((player.r * 4, player.r * 4), pygame.SRCALPHA)
                pygame.draw.circle(aura, (255, 255, 0, invincibility_alpha), 
                                 (player.r * 2, player.r * 2), player.r * 2)
                self.screen.blit(aura, (player.x - player.r * 2, player.y - player.r * 2))
        
        # HUD
        hud(self.screen, self.p1, self.p2, self.remain, 
            self.round_idx, self.wins, self.width, self.height)
    
    def draw_game_end(self):
        """Desenha tela de fim de jogo"""
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        self.screen.blit(shade, (0, 0))
        
        # Mensagem de vitória
        font_big = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 32)
        
        text = font_big.render(self.winner_msg, True, (255, 210, 0))
        self.screen.blit(text, (self.width//2 - text.get_width()//2, self.height//2 - 50))
        
        # Instruções
        info = font_medium.render("Pressione ESC para voltar ao menu", True, (240, 240, 240))
        self.screen.blit(info, (self.width//2 - info.get_width()//2, self.height//2 + 20))
    
    def get_game_name(self):
        return "Pega-Pega 1v1"
    
    def cleanup(self):
        """Limpeza ao sair do jogo"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()