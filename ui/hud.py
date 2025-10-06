import pygame

def draw_hud(surface, p1, p2, remain, round_idx, wins, width, height):
    """Desenha o HUD do jogo Pega-Pega"""
    bar_h = 110
    hud_surf = pygame.Surface((width, bar_h), pygame.SRCALPHA)
    hud_surf.fill((0, 0, 0, 150))
    surface.blit(hud_surf, (0, 0))

    # Função auxiliar para abreviar nomes
    def abbrev(t, n=12):
        t = str(t)
        return t if len(t) <= n else t[:n-1] + "…"

    n1, n2 = abbrev(p1.name), abbrev(p2.name)

    # Título
    font_big = pygame.font.Font(None, 46)
    title = font_big.render("PEGA - PEGA 1V1", True, (240, 240, 240))
    title_rect = title.get_rect(midtop=(width // 2, 6))
    surface.blit(title, title_rect)

    # Round e vitórias
    font_medium = pygame.font.Font(None, 30)
    round_text = font_medium.render(
        f"Round {round_idx}/3 • Vitórias: {n1} {wins[0]} - {wins[1]} {n2}",
        True, (240, 240, 240)
    )
    round_rect = round_text.get_rect(topleft=(16, title_rect.bottom + 2))
    surface.blit(round_text, round_rect)

    # Timer
    font_sc = pygame.font.Font(None, 34)
    def fmt_time(ms):
        ms = max(0, ms)
        s = ms // 1000
        m = s // 60
        s %= 60
        return f"{m}:{s:02d}"
    
    timer = font_sc.render(f"Tempo: {fmt_time(remain)}", True, (255, 210, 0))
    timer_rect = timer.get_rect(topleft=(16, round_rect.bottom + 4))
    surface.blit(timer, timer_rect)

    # Placar
    placar = font_sc.render(f"{n1}: {p1.score:0.1f}   |   {n2}: {p2.score:0.1f}", True, (240, 240, 240))
    placar_rect = placar.get_rect(topright=(width - 16, timer_rect.top))
    surface.blit(placar, placar_rect)

    # Pegador atual
    peg = p1.name if p1.is_it else p2.name
    peg_surf = font_medium.render(f"Pegador: {peg}", True, (255, 210, 0))
    peg_rect = peg_surf.get_rect(midtop=(width // 2, timer_rect.bottom + 4))
    surface.blit(peg_surf, peg_rect)