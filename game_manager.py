import pygame
import math
import random
import os
from games.pega_pega.pega_pega_game import PegaPegaGame
from ui.widgets import Button, Title, ColorPicker, InputBox, load_font

class GameManager:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.current_state = "MENU"
        self.current_game = None
        self.fullscreen = False
        
        # Configurações visuais
        self.setup_visuals()
        self.setup_menu()
        
        # Estados de intro
        self.intro_start = pygame.time.get_ticks()
        self.INTRO_MS = 7000
        
        # Recursos
        self.load_assets()
    
    def setup_visuals(self):
        """Configura cores, fontes e paleta"""
        # Cores
        self.WHITE = (240, 240, 240)
        self.BLACK = (0, 0, 0)
        self.BG = (18, 18, 18)
        self.YELL = (255, 210, 0)
        
        # Paleta para os pickers
        C1 = (255, 109, 106); C2 = (255, 199, 95); C3 = (92, 225, 230); 
        C4 = (159, 105, 255); C5 = (64, 222, 140); C6 = (255, 77, 0);   
        C7 = (255, 230, 0);  C8 = (0, 180, 255);  C9 = (140, 100, 255); 
        C10 = (80, 255, 180)
        self.PALETTE = [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10]
        
        # Fontes
        self.FT_BIG = load_font(46)
        self.FT = load_font(30)
        self.FT_SC = load_font(34)
        self.FT_SM = load_font(22)
        self.FT_MEGA = load_font(64)
    
    def setup_menu(self):
        """Configura o menu principal do Pega-Pega com layout melhorado"""
        # Posições mais espaçadas
        self.menu_y_start = 160
        self.section_spacing = 100  # Espaço entre seções
        self.element_spacing = 60   # Espaço entre elementos dentro da seção
        
        # Player 1 - Seção completa
        player1_y = self.menu_y_start
        
        # Label Player 1
        self.player1_label = self.FT_SM.render("JOGADOR 1", True, self.WHITE)
        
        # Color Picker Player 1
        self.pick1 = ColorPicker(
            x=self.width // 2 - 200, 
            y=player1_y + 25, 
            width=400, 
            height=30, 
            colors=self.PALETTE, 
            initial_color=0
        )
        
        # Input Box Player 1
        self.inp1 = InputBox(
            self.width // 2 - 200, 
            player1_y + 70, 
            400, 50, 
            "Nome do Jogador 1 (WASD)"
        )
        
        # Player 2 - Seção completa (mais espaçada)
        player2_y = player1_y + self.section_spacing
        
        # Label Player 2
        self.player2_label = self.FT_SM.render("JOGADOR 2", True, self.WHITE)
        
        # Color Picker Player 2
        self.pick2 = ColorPicker(
            x=self.width // 2 - 200, 
            y=player2_y + 25, 
            width=400, 
            height=30, 
            colors=self.PALETTE, 
            initial_color=2
        )
        
        # Input Box Player 2
        self.inp2 = InputBox(
            self.width // 2 - 200, 
            player2_y + 70, 
            400, 50, 
            "Nome do Jogador 2 (SETAS)"
        )
        
        # Botão iniciar (bem espaçado dos inputs)
        btn_y = player2_y + self.section_spacing - 20
        self.btn = Button(
            (self.width // 2 - 100, btn_y, 200, 56), 
            "🎮 INICIAR JOGO"
        )
        
        # Botão voltar
        self.back_btn = Button((20, self.height - 60, 120, 40), "← VOLTAR")
        
        # Título
        self.title = Title("CORRIDA MALUCA", self.width//2, 120, 48)
    
    def load_assets(self):
        """Carrega recursos opcionais"""
        self.music_ok = self.tag_ok = self.hit_ok = False
        
        try:
            pygame.mixer.music.load("assets/bg_music.wav")
            pygame.mixer.music.set_volume(0.4)
            self.music_ok = True
        except:
            pass
        
        try:
            self.BG_IMG = pygame.image.load("assets/python.png").convert_alpha()
            self.BG_IMG = pygame.transform.smoothscale(self.BG_IMG, (self.width, self.height))
        except:
            self.BG_IMG = None
    
    def draw_bg(self):
        """Desenha o fundo com imagem ou cor sólida"""
        if self.BG_IMG:
            self.screen.blit(self.BG_IMG, (0, 0))
            sh = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            sh.fill((0, 0, 0, 70))
            self.screen.blit(sh, (0, 0))
        else:
            self.screen.fill(self.BG)
    
    def handle_event(self, event):
        """Gerencia eventos"""
        if self.current_state == "INTRO":
            self.handle_intro_event(event)
        elif self.current_state == "MENU":
            self.handle_menu_event(event)
        elif self.current_state == "GAME" and self.current_game:
            self.current_game.handle_event(event)
            
            # ESC volta ao menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.return_to_menu()
    
    def handle_intro_event(self, event):
        """Gerencia eventos da introdução"""
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.current_state = "MENU"
    
    def handle_menu_event(self, event):
        """Gerencia eventos do menu"""
        # Verifica botão voltar
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.is_clicked(event.pos):
            self.return_to_main_menu()
            return
        
        # Processa inputs dos jogadores
        self.inp1.handle_event(event)
        self.inp2.handle_event(event)
        self.pick1.handle_event(event)
        self.pick2.handle_event(event)
        
        # Inicia o jogo
        if (event.type == pygame.MOUSEBUTTONDOWN and self.btn.is_clicked(event.pos)) or \
           (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self.start_pega_pega()
    
    def start_pega_pega(self):
        """Inicia o jogo Pega-Pega com as configurações do menu"""
        # Passa as configurações do menu para o jogo
        player1_name = self.inp1.text or "Player 1"
        player2_name = self.inp2.text or "Player 2"
        player1_color = self.pick1.get_selected_color()
        player2_color = self.pick2.get_selected_color()
        
        print(f"🎮 Iniciando Corrida Maluca: {player1_name} vs {player2_name}")
        
        # Modo fixo como "TAG" (normal)
        self.current_game = PegaPegaGame(
            self.screen, self.width, self.height,
            player1_name, player2_name,
            player1_color, player2_color,
            "TAG"
        )
        self.current_state = "GAME"
        
        if self.music_ok:
            pygame.mixer.music.play(-1)
    
    def return_to_menu(self):
        """Volta para o menu do jogo"""
        if self.current_game:
            self.current_game.cleanup()
            self.current_game = None
        
        if self.music_ok:
            pygame.mixer.music.stop()
            
        self.current_state = "MENU"
    
    def return_to_main_menu(self):
        """Volta para o menu principal (seletor de jogos)"""
        self.return_to_menu()
        self.current_state = "MAIN_MENU"
    
    def update(self, dt):
        """Atualiza o estado atual"""
        if self.current_state == "INTRO":
            elapsed = pygame.time.get_ticks() - self.intro_start
            if elapsed >= self.INTRO_MS:
                self.current_state = "MENU"
        
        elif self.current_state == "GAME" and self.current_game:
            self.current_game.update(dt)
    
    def draw(self):
        """Desenha o estado atual"""
        self.draw_bg()
        
        if self.current_state == "INTRO":
            self.draw_intro()
        elif self.current_state == "MENU":
            self.draw_menu()
        elif self.current_state == "GAME" and self.current_game:
            self.current_game.draw()
        elif self.current_state == "MAIN_MENU":
            pass
    
    def draw_intro(self):
        """Desenha a tela de introdução animada"""
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 90))
        self.screen.blit(shade, (0, 0))

        elapsed = pygame.time.get_ticks() - self.intro_start
        p = elapsed / self.INTRO_MS

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
        text = self.FT_MEGA.render(txt, True, self.WHITE)
        shadow = self.FT_MEGA.render(txt, True, (0, 0, 0))
        text.set_alpha(alpha)
        shadow.set_alpha(int(alpha * 0.6))
        text = pygame.transform.rotozoom(text, 0, scale)
        shadow = pygame.transform.rotozoom(shadow, 0, scale)
        self.screen.blit(shadow, shadow.get_rect(center=(self.width // 2 + 3, self.height // 2 + 2)))
        self.screen.blit(text, text.get_rect(center=(self.width // 2, self.height // 2)))
    
    def draw_menu(self):
        """Desenha o menu principal com layout organizado"""
        # Sombra do fundo
        if self.BG_IMG:
            sh = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            sh.fill((0, 0, 0, 80))
            self.screen.blit(sh, (0, 0))

        # Brand
        brand = self.FT.render("Vannpipe Game Inc.", True, self.WHITE)
        self.screen.blit(brand, (self.width // 2 - brand.get_width() // 2, 90))

        # Título com efeito
        title_text = "CORRIDA MALUCA"
        for i, a in enumerate([90, 60, 30]):
            s = load_font(46 + i * 2).render(title_text, True, (100, 170, 255))
            s.set_alpha(a)
            self.screen.blit(s, (self.width // 2 - s.get_width() // 2, 125 - i * 2))
        main = self.FT_BIG.render(title_text, True, self.WHITE)
        self.screen.blit(main, (self.width // 2 - main.get_width() // 2, 120))

        # Player 1 - Seção completa
        player1_y = self.menu_y_start
        
        # Label Player 1
        self.screen.blit(self.player1_label, (self.width // 2 - 200, player1_y))
        
        # Instrução cor Player 1
        color_label1 = self.FT_SM.render("Escolha a cor:", True, (200, 200, 200))
        self.screen.blit(color_label1, (self.width // 2 - 200, player1_y + 5))
        
        self.pick1.draw(self.screen)
        self.inp1.draw(self.screen)

        # Player 2 - Seção completa
        player2_y = player1_y + self.section_spacing
        
        # Label Player 2
        self.screen.blit(self.player2_label, (self.width // 2 - 200, player2_y))
        
        # Instrução cor Player 2
        color_label2 = self.FT_SM.render("Escolha a cor:", True, (200, 200, 200))
        self.screen.blit(color_label2, (self.width // 2 - 200, player2_y + 5))
        
        self.pick2.draw(self.screen)
        self.inp2.draw(self.screen)
        
        # Botões
        mouse_pos = pygame.mouse.get_pos()
        self.btn.draw(self.screen, self.btn.is_hovered(mouse_pos))
        self.back_btn.draw(self.screen, self.back_btn.is_hovered(mouse_pos))
        
        # Instruções
        instructions = self.FT_SM.render("Pressione ENTER ou clique em 'INICIAR JOGO' para começar", True, (200, 200, 200))
        self.screen.blit(instructions, (self.width // 2 - instructions.get_width() // 2, self.height - 100))
        
        # Dica adicional
        tip = self.FT_SM.render("Dica: Deixe em branco para usar os nomes padrão", True, (150, 150, 150))
        self.screen.blit(tip, (self.width // 2 - tip.get_width() // 2, self.height - 80))
    
    def update_screen(self, new_screen):
        """Atualiza a referência da tela (para fullscreen)"""
        self.screen = new_screen
        if self.current_game:
            self.current_game.screen = new_screen
    
    def cleanup(self):
        """Limpeza ao sair do jogo"""
        if self.current_game:
            self.current_game.cleanup()
        if self.music_ok and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()