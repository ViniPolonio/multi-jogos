import pygame
import math

class Button:
    def __init__(self, rect, text, font_size=24, color=(100, 170, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.base_rect = self.rect.copy()
    
    def draw(self, surface, hover=False):
        # Cor base com efeito hover
        fill_color = (min(255, self.color[0] + 30), 
                     min(255, self.color[1] + 30), 
                     min(255, self.color[2] + 30)) if hover else self.color
        
        # Desenha botão
        pygame.draw.rect(surface, fill_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (240, 240, 240), self.rect, 2, border_radius=10)
        
        # Texto
        font = pygame.font.Font(None, self.font_size)
        text_surf = font.render(self.text, True, (240, 240, 240))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

class Title:
    def __init__(self, text, x, y, font_size=48, color=(240, 240, 240)):
        self.text = text
        self.x = x
        self.y = y
        self.font_size = font_size
        self.color = color
    
    def draw(self, surface):
        font = pygame.font.Font(None, self.font_size)
        text_surf = font.render(self.text, True, self.color)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        surface.blit(text_surf, text_rect)

class ColorPicker:
    """
    Um seletor de cores simples para o jogo
    """
    def __init__(self, x, y, width, height, colors, initial_color=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.colors = colors
        self.selected_color = initial_color
        self.active = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                # Lógica para selecionar cor baseada na posição do clique
                rel_x = event.pos[0] - self.rect.x
                color_index = min(len(self.colors) - 1, max(0, int(rel_x / (self.rect.width / len(self.colors)))))
                self.selected_color = color_index
                return True
        return False
    
    def draw(self, screen):
        # Desenha o fundo do color picker
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        
        # Desenha as opções de cores
        color_width = self.rect.width / len(self.colors)
        for i, color in enumerate(self.colors):
            color_rect = pygame.Rect(
                self.rect.x + i * color_width,
                self.rect.y,
                color_width,
                self.rect.height
            )
            pygame.draw.rect(screen, color, color_rect)
            
            # Destaca a cor selecionada
            if i == self.selected_color:
                pygame.draw.rect(screen, (255, 255, 255), color_rect, 3)
    
    def get_selected_color(self):
        return self.colors[self.selected_color]

class InputBox:
    """
    Caixa de input para texto
    """
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (100, 100, 100)
        self.text = text
        self.font = pygame.font.Font(None, 32)
        self.active = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Ativa/desativa se clicou na caixa
            self.active = self.rect.collidepoint(event.pos)
            self.color = (150, 150, 150) if self.active else (100, 100, 100)
            return True
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                return True
        return False
    
    def draw(self, screen):
        # Desenha a caixa
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Desenha o texto
        text_surface = self.font.render(self.text, True, (240, 240, 240))
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

class ModeSelector:
    """
    Seletor de modo de jogo
    """
    def __init__(self, x, y, width, height, modes, initial_mode=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.modes = modes
        self.selected_mode = initial_mode
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # Alterna entre modos
                self.selected_mode = (self.selected_mode + 1) % len(self.modes)
                return True
        return False
    
    def draw(self, screen):
        # Desenha o fundo
        pygame.draw.rect(screen, (80, 80, 120), self.rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 200), self.rect, 2, border_radius=8)
        
        # Desenha o texto do modo atual
        font = pygame.font.Font(None, 24)
        text = f"Modo: {self.modes[self.selected_mode]}"
        text_surf = font.render(text, True, (240, 240, 240))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def get_selected_mode(self):
        return self.modes[self.selected_mode]

def load_font(size=24):
    """Carrega uma fonte padrão"""
    return pygame.font.Font(None, size)