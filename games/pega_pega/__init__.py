"""
Pega-Pega game package
"""

from .pega_pega_game import PegaPegaGame
from .entities import Player, PowerUp, spawn_powerup, apply_powerup
from .maps import get_map, draw_obstacles, MovingRect

__all__ = [
    'PegaPegaGame', 
    'Player', 
    'PowerUp', 
    'spawn_powerup', 
    'apply_powerup',
    'get_map', 
    'draw_obstacles', 
    'MovingRect'
]