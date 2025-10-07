from abc import ABC, abstractmethod
import pygame

class BaseGame(ABC):
    """Classe abstrata base para todos os jogos"""
    
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.running = True
    
    @abstractmethod
    def handle_event(self, event):
        """Processa eventos do jogo"""
        pass
    
    @abstractmethod
    def update(self, dt):
        """Atualiza a lógica do jogo"""
        pass
    
    @abstractmethod
    def draw(self):
        """Desenha o jogo"""
        pass
    
    def cleanup(self):
        """Limpeza quando o jogo termina"""
        pass
    
    def get_game_name(self):
        """Retorna o nome do jogo"""
        return "Game"