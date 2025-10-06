import pygame
import sys
import os
from game_manager import GameManager

def main():
    pygame.init()
    
    # Configurações básicas
    W, H = 900, 520
    flags = pygame.SCALED
    screen = pygame.display.set_mode((W, H), flags)
    pygame.display.set_caption("Arcade Multi-Games")
    clock = pygame.time.Clock()
    FPS = 60
    
    # Cores
    BG = (18, 18, 18)
    WHITE = (240, 240, 240)
    
    # Gerenciador de jogos
    game_manager = GameManager(screen, W, H)
    
    # Loop principal
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Passa eventos para o gerenciador
            game_manager.handle_event(event)
            
            # Tecla F11 para fullscreen
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                current_flags = screen.get_flags()
                if current_flags & pygame.FULLSCREEN:
                    screen = pygame.display.set_mode((W, H), pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.FULLSCREEN)
                game_manager.update_screen(screen)
        
        # Atualiza e desenha
        game_manager.update(dt)
        game_manager.draw()
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()