import pygame
import sys
import os
from game_manager import GameManager

class ArcadeMultiGames:
    def __init__(self):
        pygame.init()
        
        # Configurações básicas
        self.W, self.H = 900, 520
        flags = pygame.SCALED
        self.screen = pygame.display.set_mode((self.W, self.H), flags)
        pygame.display.set_caption("Arcade Multi-Games")
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        # Estados do sistema
        self.running = True
        self.current_screen = "GAME_SELECTOR"  # GAME_SELECTOR, GAME
        self.selected_game = None
        
        # Gerenciador de jogos
        self.game_manager = None
        
        # Cores
        self.BG = (18, 18, 18)
        self.WHITE = (240, 240, 240)
        self.BLUE = (100, 170, 255)
        self.RED = (255, 100, 100)
        
        # Fontes
        self.font_big = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Jogos disponíveis
        self.games = {
            "CORRIDA_MALUCA": {
                "name": "CORRIDA MALUCA",
                "description": "Pega-Pega caótico com power-ups!",
                "color": self.BLUE,
                "icon": "🏃‍♂️"
            },
            "GUERRA_RELAMPAGO": {
                "name": "GUERRA RELÂMPAGO", 
                "description": "Modo Mata-Mata competitivo!",
                "color": self.RED,
                "icon": "⚔️",
                "coming_soon": True
            }
        }
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.current_screen == "GAME_SELECTOR":
                self.handle_game_selector_events(event)
            elif self.current_screen == "GAME" and self.game_manager:
                self.game_manager.handle_event(event)
            
            # Tecla F11 para fullscreen
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
    
    def handle_game_selector_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # Área do botão Corrida Maluca
            corrida_rect = pygame.Rect(self.W // 2 - 220, self.H // 2 - 60, 200, 120)
            # Área do botão Guerra Relâmpago
            guerra_rect = pygame.Rect(self.W // 2 + 20, self.H // 2 - 60, 200, 120)
            
            if corrida_rect.collidepoint(mouse_pos):
                self.start_game("CORRIDA_MALUCA")
            elif guerra_rect.collidepoint(mouse_pos):
                if not self.games["GUERRA_RELAMPAGO"]["coming_soon"]:
                    self.start_game("GUERRA_RELAMPAGO")
    
    def start_game(self, game_id):
        """Inicia o jogo selecionado"""
        self.selected_game = game_id
        
        if game_id == "CORRIDA_MALUCA":
            self.game_manager = GameManager(self.screen, self.W, self.H)
            self.current_screen = "GAME"
        elif game_id == "GUERRA_RELAMPAGO":
            # Placeholder para futuro jogo Mata-Mata
            print("🚀 Iniciando Guerra Relâmpago (Em desenvolvimento)")
            # self.game_manager = MataMataGameManager(self.screen, self.W, self.H)
            # self.current_screen = "GAME"
    
    def return_to_menu(self):
        """Volta para o seletor de jogos"""
        if self.game_manager:
            self.game_manager.cleanup()
            self.game_manager = None
        self.current_screen = "GAME_SELECTOR"
        self.selected_game = None
    
    def toggle_fullscreen(self):
        """Alterna entre tela cheia e janela"""
        current_flags = self.screen.get_flags()
        if current_flags & pygame.FULLSCREEN:
            self.screen = pygame.display.set_mode((self.W, self.H), pygame.SCALED)
        else:
            self.screen = pygame.display.set_mode((self.W, self.H), pygame.SCALED | pygame.FULLSCREEN)
        
        if self.game_manager:
            self.game_manager.update_screen(self.screen)
    
    def draw_game_selector(self):
        """Desenha a tela de seleção de jogos"""
        # Fundo
        self.screen.fill(self.BG)
        
        # Título
        title = self.font_big.render("ARCADE MULTI-GAMES", True, self.WHITE)
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 80))
        
        # Subtítulo
        subtitle = self.font_small.render("Selecione seu jogo favorito!", True, (200, 200, 200))
        self.screen.blit(subtitle, (self.W // 2 - subtitle.get_width() // 2, 140))
        
        # Botão Corrida Maluca
        corrida_rect = pygame.Rect(self.W // 2 - 220, self.H // 2 - 60, 200, 120)
        corrida_color = self.games["CORRIDA_MALUCA"]["color"]
        corrida_hover = self.is_mouse_over(corrida_rect)
        
        pygame.draw.rect(self.screen, corrida_color, corrida_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.WHITE, corrida_rect, 3, border_radius=15)
        
        # Ícone e texto
        icon = self.font_medium.render("🏃‍♂️", True, self.WHITE)
        self.screen.blit(icon, (corrida_rect.centerx - icon.get_width() // 2, corrida_rect.centery - 30))
        
        name = self.font_small.render("CORRIDA MALUCA", True, self.WHITE)
        self.screen.blit(name, (corrida_rect.centerx - name.get_width() // 2, corrida_rect.centery))
        
        desc = self.font_small.render("Pega-Pega Caótico", True, (230, 230, 230))
        self.screen.blit(desc, (corrida_rect.centerx - desc.get_width() // 2, corrida_rect.centery + 20))
        
        # Botão Guerra Relâmpago
        guerra_rect = pygame.Rect(self.W // 2 + 20, self.H // 2 - 60, 200, 120)
        guerra_data = self.games["GUERRA_RELAMPAGO"]
        guerra_color = guerra_data["color"]
        guerra_hover = self.is_mouse_over(guerra_rect)
        
        # Efeito de "em breve"
        if guerra_data["coming_soon"]:
            guerra_color = (100, 100, 100)  # Cinza para indicar desabilitado
        
        pygame.draw.rect(self.screen, guerra_color, guerra_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.WHITE, guerra_rect, 3, border_radius=15)
        
        # Ícone e texto
        icon = self.font_medium.render("⚔️", True, self.WHITE)
        self.screen.blit(icon, (guerra_rect.centerx - icon.get_width() // 2, guerra_rect.centery - 30))
        
        name = self.font_small.render("GUERRA RELÂMPAGO", True, self.WHITE)
        self.screen.blit(name, (guerra_rect.centerx - name.get_width() // 2, guerra_rect.centery))
        
        if guerra_data["coming_soon"]:
            coming_soon = self.font_small.render("EM BREVE!", True, (255, 255, 0))
            self.screen.blit(coming_soon, (guerra_rect.centerx - coming_soon.get_width() // 2, guerra_rect.centery + 20))
        else:
            desc = self.font_small.render("Mata-Mata", True, (230, 230, 230))
            self.screen.blit(desc, (guerra_rect.centerx - desc.get_width() // 2, guerra_rect.centery + 20))
        
        # Rodapé
        footer = self.font_small.render("Pressione F11 para tela cheia • Vannpipe Game Inc.", True, (150, 150, 150))
        self.screen.blit(footer, (self.W // 2 - footer.get_width() // 2, self.H - 40))
    
    def is_mouse_over(self, rect):
        """Verifica se o mouse está sobre um retângulo"""
        return rect.collidepoint(pygame.mouse.get_pos())
    
    def update(self):
        """Atualiza a lógica do jogo"""
        dt = self.clock.tick(self.FPS) / 1000.0
        
        if self.current_screen == "GAME" and self.game_manager:
            self.game_manager.update(dt)
            
            # VERIFICA SE O JOGO QUER VOLTAR AO MENU PRINCIPAL
            if hasattr(self.game_manager, 'current_state') and self.game_manager.current_state == "MAIN_MENU":
                self.return_to_menu()
    
    def draw(self):
        """Desenha a tela atual"""
        if self.current_screen == "GAME_SELECTOR":
            self.draw_game_selector()
        elif self.current_screen == "GAME" and self.game_manager:
            self.game_manager.draw()
        
        pygame.display.flip()
    
    def run(self):
        """Loop principal do jogo"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

def main():
    arcade = ArcadeMultiGames()
    arcade.run()

if __name__ == "__main__":
    main()