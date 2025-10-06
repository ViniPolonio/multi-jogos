import pygame
import math
import random
import os
from games.pega_pega.pega_pega_game import PegaPegaGame
from ui.widgets import Button, Title, ColorPicker, InputBox, ModeSelector, load_font

class GameManager:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.current_state = "INTRO"  # INTRO, MENU, GAME
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
        """Configura o menu principal com toda a formatação original"""
        self.menu_y_start = 180
        self.menu_spacing = 120
        
        # Player 1
        self.pick1 = ColorPicker(
            x=self.width // 2 - 200, 
            y=self.menu_y_start, 
            width=400, 
            height=30, 
            colors=self.PALETTE, 
            initial_color=0
        )
        
        self.inp1 = InputBox(self.width // 2 - 200, self.menu_y_start + 40, 400, 50, "Player 1 (WASD)")        
        # Player 2
        self.pick2 = ColorPicker(
            x=self.width // 2 - 200, 
            y=self.menu_y_start + self.menu_spacing, 
            width=400, 
            height=30, 
            colors=self.PALETTE, 
            initial_color=2
        )
        self.inp2 = InputBox(self.width // 2 - 200, self.menu_y_start + self.menu_spacing + 40, 400, 50, "Player 2 (SETAS)")
        
        # Seletor de modo
        self.MODES = {"TAG": "Pega-Pega", "RACE": "Corrida", "SURVIVAL": "Sobrevivência"}
        self.mode_selector = ModeSelector(
            x=self.width // 2 - 220, 
            y=self.menu_y_start + self.menu_spacing * 2 - 50, 
            width=440, 
            height=50, 
            modes=list(self.MODES.keys()),  # Passa apenas as chaves como lista
            initial_mode=0
        )
        self.current_mode = "TAG"
        
        # Botão iniciar
        self.btn = Button((self.width // 2 - 100, self.menu_y_start + self.menu_spacing * 2, 200, 56), "Iniciar")
        
        # Título
        self.title = Title("ARCADE MULTI-GAMES", self.width//2, 120, 48)
    
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
        self.inp1.handle_event(event)
        self.inp2.handle_event(event)
        self.pick1.handle_event(event)
        self.pick2.handle_event(event)
        
        if self.mode_selector.handle_event(event):
            self.current_mode = self.mode_selector.get_selected_mode()
        
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
        
        self.current_game = PegaPegaGame(
            self.screen, self.width, self.height,
            player1_name, player2_name,
            player1_color, player2_color,
            self.current_mode
        )
        self.current_state = "GAME"
        
        if self.music_ok:
            pygame.mixer.music.play(-1)
    
    def return_to_menu(self):
        """Volta para o menu principal"""
        if self.current_game:
            self.current_game.cleanup()
            self.current_game = None
        
        if self.music_ok:
            pygame.mixer.music.stop()
            
        self.current_state = "MENU"
    
    def update(self, dt):
        """Atualiza o estado atual"""
        # Transição automática da intro
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
        """Desenha o menu principal com toda a formatação original"""
        # Sombra do fundo
        if self.BG_IMG:
            sh = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            sh.fill((0, 0, 0, 80))
            self.screen.blit(sh, (0, 0))

        # Brand
        brand = self.FT.render("Vannpipe Game Inc.", True, self.WHITE)
        self.screen.blit(brand, (self.width // 2 - brand.get_width() // 2, 90))

        # Título com efeito
        title_text = "Pega - Pega 1V1"
        for i, a in enumerate([90, 60, 30]):
            s = load_font(46 + i * 2).render(title_text, True, (100, 170, 255))
            s.set_alpha(a)
            self.screen.blit(s, (self.width // 2 - s.get_width() // 2, 125 - i * 2))
        main = self.FT_BIG.render(title_text, True, self.WHITE)
        self.screen.blit(main, (self.width // 2 - main.get_width() // 2, 120))

        # Labels dos players
        lbl1 = self.FT_SM.render("Cor P1", True, self.WHITE)
        self.screen.blit(lbl1, (self.width // 2 - 200, self.menu_y_start - 18))
        self.pick1.draw(self.screen)
        self.inp1.draw(self.screen)

        lbl2 = self.FT_SM.render("Cor P2", True, self.WHITE)
        self.screen.blit(lbl2, (self.width // 2 - 200, self.menu_y_start + self.menu_spacing - 18))
        self.pick2.draw(self.screen)
        self.inp2.draw(self.screen)

        # Seletor de modo e botão
        self.mode_selector.draw(self.screen)
        
        mouse_pos = pygame.mouse.get_pos()
        self.btn.draw(self.screen, self.btn.is_hovered(mouse_pos))
    
    def update_screen(self, new_screen):
        """Atualiza a referência da tela (para fullscreen)"""
        self.screen = new_screen
        if self.current_game:
            self.current_game.screen = new_screen