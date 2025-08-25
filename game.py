import pygame, sys, math, random, os
pygame.init()

# ---------------------- Janela ----------------------
W, H = 900, 520
# usar SCALED para escalar bonito ao alternar para fullscreen
flags = pygame.SCALED
tela = pygame.display.set_mode((W, H), flags)
pygame.display.set_caption("Pega-pega 1v1 — Rounds, Power-ups e Cores")
FPS = 60
clock = pygame.time.Clock()

# (novo) estado do fullscreen
fullscreen = False

# ---------------------- Cores ----------------------
WHITE=(240,240,240); BLACK=(0,0,0); BG=(18,18,18)
HUD_BG=(0,0,0,150); YELL=(255,210,0)
RED=(235,64,52); BLUE=(52,120,235); GREEN=(30,170,90)

# paleta para os pickers
C1=(255,109,106); C2=(255,199,95); C3=(92,225,230); C4=(159,105,255); C5=(64,222,140)
C6=(255,77,0);   C7=(255,230,0);  C8=(0,180,255);  C9=(140,100,255); C10=(80,255,180)
PALETTE=[C1,C2,C3,C4,C5,C6,C7,C8,C9,C10]

# ---------------------- Fontes ----------------------
def load_font(sz):
    p = os.path.join("assets","Fancy.ttf")
    return pygame.font.Font(p, sz) if os.path.exists(p) else pygame.font.SysFont(None, sz)

FT_BIG=load_font(46); FT=load_font(30); FT_SC=load_font(34); FT_SM=load_font(22)
FT_MEGA = load_font(64)  # para a abertura

# ---------------------- Recursos (opcionais) ----------------------
music_ok=tag_ok=hit_ok=False
try:
    pygame.mixer.music.load("assets/bg_music.wav"); pygame.mixer.music.set_volume(0.4); music_ok=True
except: pass
try:
    S_TAG=pygame.mixer.Sound("assets/tag.wav"); S_TAG.set_volume(0.7); tag_ok=True
except: S_TAG=None
try:
    S_HIT=pygame.mixer.Sound("assets/hit.wav"); S_HIT.set_volume(0.5); hit_ok=True
except: S_HIT=None
try:
    BG_IMG=pygame.image.load("assets/python.png").convert_alpha()
    BG_IMG=pygame.transform.smoothscale(BG_IMG,(W,H))
except: BG_IMG=None

# ---------------------- Utils ----------------------
def clamp(v,a,b): return max(a,min(b,v))
def dist(x1,y1,x2,y2): return math.hypot(x2-x1,y2-y1)
def circles_collide(x1,y1,r1,x2,y2,r2): return dist(x1,y1,x2,y2)<=r1+r2
def circle_rect(cx,cy,cr,rect):
    qx=clamp(cx,rect.left,rect.right); qy=clamp(cy,rect.top,rect.bottom)
    return dist(cx,cy,qx,qy)<=cr
def fmt_time(ms): ms=max(0,ms); s=ms//1000; m=s//60; s%=60; return f"{m}:{s:02d}"
def abbrev(t,n=12): t=str(t); return t if len(t)<=n else t[:n-1]+"…"

# ---------------------- UI ----------------------
class InputBox:
    def __init__(self, rect, ph=""):
        self.rect=pygame.Rect(rect); self.text=""; self.ph=ph; self.active=False
    def handle(self,e):
        if e.type==pygame.MOUSEBUTTONDOWN: self.active=self.rect.collidepoint(e.pos)
        if self.active and e.type==pygame.KEYDOWN:
            if e.key==pygame.K_RETURN: self.active=False
            elif e.key==pygame.K_BACKSPACE: self.text=self.text[:-1]
            elif e.unicode.isprintable() and len(self.text)<16: self.text+=e.unicode
    def draw(self,surf):
        box=pygame.Surface(self.rect.size,pygame.SRCALPHA); box.fill((0,0,0,160)); surf.blit(box,self.rect.topleft)
        pygame.draw.rect(surf,(100,170,255) if self.active else (160,160,160),self.rect,3,10)
        msg=self.text if self.text else self.ph; col=WHITE if self.text else (220,220,220)
        t=FT.render(msg,True,col); surf.blit(t,(self.rect.x+12,self.rect.y+(self.rect.h-t.get_height())//2))

class Button:
    def __init__(self, rect, label): self.base=pygame.Rect(rect); self.rect=self.base.copy(); self.label=label
    def draw(self,surf,hover,t):
        k=1.0+0.03*math.sin(t*2.5); self.rect=self.base.copy()
        self.rect.w=int(self.base.w*k); self.rect.h=int(self.base.h*k); self.rect.center=self.base.center
        fill=(70,70,70) if not hover else (95,95,95)
        pygame.draw.rect(surf,fill,self.rect,0,10); pygame.draw.rect(surf,(120,120,120),self.rect,2,10)
        if hover:
            glow=pygame.Surface((self.rect.w+20,self.rect.h+20),pygame.SRCALPHA)
            pygame.draw.ellipse(glow,(100,170,255,90),glow.get_rect()); surf.blit(glow,(self.rect.centerx-glow.get_width()//2,self.rect.centery-glow.get_height()//2))
        txt=FT.render(self.label,True,WHITE); surf.blit(txt,(self.rect.centerx-txt.get_width()//2,self.rect.centery-txt.get_height()//2))
    def clicked(self,pos): return self.rect.collidepoint(pos)

class ColorPicker:
    def __init__(self, x,y, colors, sel):
        self.items=[]; self.sel=sel
        for i,c in enumerate(colors):
            r=pygame.Rect(x+i*36,y,30,30); self.items.append((r,c))
    def handle(self,e):
        if e.type==pygame.MOUSEBUTTONDOWN:
            for i,(r,c) in enumerate(self.items):
                if r.collidepoint(e.pos): self.sel=i
    def color(self): return self.items[self.sel][1]
    def draw(self,surf):
        for i,(r,c) in enumerate(self.items):
            pygame.draw.rect(surf,c,r,0,6); pygame.draw.rect(surf,(30,30,30),r,2,6)
            if i==self.sel: pygame.draw.rect(surf,(255,255,255),r.inflate(6,6),2,8)

# ---------------------- Entidades ----------------------
class Player:
    def __init__(self,x,y,r,color,vel,keys,name=""):
        self.x=x; self.y=y; self.r=r; self.color=color; self.vel=vel; self.keys=keys
        self.score=0.0; self.is_it=False; self.name=name
        self.speed_mul=1.0; self.speed_until=0
        self.shield=0
        self.frozen_until=0
    def input(self):
        k=pygame.key.get_pressed(); dx=dy=0
        if k[self.keys["left"]]: dx-=1
        if k[self.keys["right"]]: dx+=1
        if k[self.keys["up"]]: dy-=1
        if k[self.keys["down"]]: dy+=1
        if dx and dy: inv=1/math.sqrt(2); dx*=inv; dy*=inv
        v=self.vel*self.speed_mul
        if pygame.time.get_ticks()<self.frozen_until: v=0
        return dx*v, dy*v
    def move_collide(self,dx,dy,arena,rects,movers,circles):
        hit=False
        ox=self.x; self.x=clamp(self.x+dx,self.r,arena.right-self.r)
        if any(circle_rect(self.x,self.y,self.r,r) for r in rects+movers) or any(circles_collide(self.x,self.y,self.r,cx,cy,cr) for (cx,cy,cr) in circles):
            self.x=ox; hit=True
        oy=self.y; self.y=clamp(self.y+dy,self.r,arena.bottom-self.r)
        if any(circle_rect(self.x,self.y,self.r,r) for r in rects+movers) or any(circles_collide(self.x,self.y,self.r,cx,cy,cr) for (cx,cy,cr) in circles):
            self.y=oy; hit=True
        return hit
    def draw(self,surf):
        if self.is_it: pygame.draw.circle(surf,YELL,(int(self.x),int(self.y)),self.r+6,4)
        if self.shield: pygame.draw.circle(surf,(120,240,255),(int(self.x),int(self.y)),self.r+2,2)
        pygame.draw.circle(surf,self.color,(int(self.x),int(self.y)),self.r)

# ---------------------- Obstáculos ----------------------
ARENA=pygame.Rect(0,0,W,H)
STATIC_RECTS=[
    pygame.Rect(W*0.10,H*0.20,200,24),
    pygame.Rect(W*0.68,H*0.60,180,24),
    pygame.Rect(W*0.08,H*0.78,240,20),
]
CIRCLES=[(W*0.25,H*0.62,36),(W*0.80,H*0.25,28)]
class MovingRect:
    def __init__(self,x,y,w,h,axis,amp,speed):
        self.base=pygame.Rect(x,y,w,h); self.axis=axis; self.amp=amp; self.speed=speed; self.t0=random.random()*1000
    def rect(self):
        t=(pygame.time.get_ticks()+self.t0)/1000.0; off=math.sin(t*self.speed)*self.amp
        r=self.base.copy()
        if self.axis=="x": r.x=int(self.base.x+off)
        else: r.y=int(self.base.y+off)
        return r
MOVERS=[MovingRect(W*0.40,H*0.38,24,140,"x",40,1.3),
        MovingRect(W*0.55,H*0.18,160,20,"y",40,1.7)]
def draw_obstacles(s):
    for r in STATIC_RECTS: pygame.draw.rect(s,(55,55,55),r,0,6); pygame.draw.rect(s,(90,90,90),r.inflate(-6,-6),0,6)
    for m in MOVERS:
        r=m.rect(); pygame.draw.rect(s,(75,75,75),r,0,6); pygame.draw.rect(s,(120,120,120),r.inflate(-6,-6),0,6)
    for (cx,cy,cr) in CIRCLES:
        pygame.draw.circle(s,(55,55,55),(int(cx),int(cy)),int(cr))
        pygame.draw.circle(s,(90,90,90),(int(cx),int(cy)),int(max(2,cr-6)))

# ---------------------- Power-ups ----------------------
PU_RADIUS=14
PU_TYPES=("speed","shield","freeze")
PU_COLORS={"speed":(255,180,0), "shield":(120,240,255), "freeze":(170,220,255)}
class PowerUp:
    def __init__(self,kind,pos): self.kind=kind; self.x,self.y=pos
    def rect(self): return pygame.Rect(self.x-PU_RADIUS,self.y-PU_RADIUS,PU_RADIUS*2,PU_RADIUS*2)
    def draw(self,s):
        col=PU_COLORS[self.kind]; pygame.draw.circle(s,col,(int(self.x),int(self.y)),PU_RADIUS)
        label={"speed":"⚡","shield":"🛡","freeze":"❄"}[self.kind]
        t=FT_SM.render(label,True,BLACK); s.blit(t,(self.x-t.get_width()/2,self.y-t.get_height()/2))
def spawn_powerup(pus):
    for _ in range(200):
        x=random.randint(60,W-60); y=random.randint(110,H-60)
        if not any(circle_rect(x,y,PU_RADIUS,rc) for rc in STATIC_RECTS+[m.rect() for m in MOVERS]) and \
           not any(dist(x,y,cx,cy)<=PU_RADIUS+cr for (cx,cy,cr) in CIRCLES):
            pus.append(PowerUp(random.choice(PU_TYPES),(x,y))); return

# ---------------------- BG + HUD ----------------------
def draw_bg():
    if BG_IMG: tela.blit(BG_IMG,(0,0)); sh=pygame.Surface((W,H),pygame.SRCALPHA); sh.fill((0,0,0,70)); tela.blit(sh,(0,0))
    else: tela.fill(BG)

def hud(p1, p2, remaining, round_num, victories):
    bar_h = 110
    hud_surf = pygame.Surface((W, bar_h), pygame.SRCALPHA)
    hud_surf.fill(HUD_BG)
    tela.blit(hud_surf, (0, 0))

    n1, n2 = abbrev(p1.name), abbrev(p2.name)

    title = FT_BIG.render("PEGA - PEGA 1V1", True, WHITE)
    title_rect = title.get_rect(midtop=(W // 2, 6))
    tela.blit(title, title_rect)

    round_text = FT.render(
        f"Round {round_num}/3 • Vitórias: {n1} {victories[0]} - {victories[1]} {n2}",
        True, WHITE
    )
    round_rect = round_text.get_rect(topleft=(16, title_rect.bottom + 2))
    tela.blit(round_text, round_rect)

    timer = FT_SC.render(f"Tempo: {fmt_time(remaining)}", True, YELL)
    timer_rect = timer.get_rect(topleft=(16, round_rect.bottom + 4))
    tela.blit(timer, timer_rect)

    placar = FT_SC.render(f"{n1}: {p1.score:0.1f}   |   {n2}: {p2.score:0.1f}", True, WHITE)
    placar_rect = placar.get_rect(topright=(W - 16, timer_rect.top))
    tela.blit(placar, placar_rect)

    peg = p1.name if p1.is_it else p2.name
    peg_surf = FT.render(f"Pegador: {peg}", True, YELL)
    peg_rect = peg_surf.get_rect(midtop=(W // 2, timer_rect.bottom + 4))
    tela.blit(peg_surf, peg_rect)

# ---------------------- Estados / Regras ----------------------
INTRO, MENU, GAME, END = "intro", "menu", "game", "end"
state = INTRO
INTRO_MS = 7000  # 7 segundos
intro_start = pygame.time.get_ticks()

ROUND_MS=60*1000
COOLDOWN=500
round_idx=1; wins=[0,0]
winner_msg=""

# ====== MENU WIDGETS (ALINHADOS) ======
y_start = 180
spacing = 120

#Player 1
pick1 = ColorPicker(W//2 - 200, y_start, PALETTE, 0)
inp1  = InputBox((W//2 - 200, y_start + 40, 400, 50), "Player 1 (WASD)")

#Player 2
pick2 = ColorPicker(W//2 - 200, y_start + spacing, PALETTE, 2)
inp2  = InputBox((W//2 - 200, y_start + spacing + 40, 400, 50), "Player 2 (SETAS)")

btn   = Button((W//2 - 100, y_start + spacing*2, 200, 56), "Iniciar")

# ---------------------- Spawns seguros ----------------------
def _blocked(x, y, r, mover_rects):
    if any(circle_rect(x, y, r, rc) for rc in STATIC_RECTS + mover_rects): return True
    if any(dist(x, y, cx, cy) <= r + cr for (cx,cy,cr) in CIRCLES): return True
    return False

def _find_safe_spawn(side: str, r: int):
    mover_rects = [m.rect() for m in MOVERS]
    if side == "left":  x_lo, x_hi = 80, int(W * 0.40)
    else:               x_lo, x_hi = int(W * 0.60), W - 80
    for _ in range(300):
        x = random.randint(x_lo, x_hi)
        y = random.randint(110, H - 80)
        if not _blocked(x, y, r, mover_rects):
            return float(x), float(y)
    return (120.0, H / 2.0) if side == "left" else (W - 120.0, H / 2.0)

def reset_round(p1, p2):
    p1.x, p1.y = _find_safe_spawn("left",  p1.r)
    p2.x, p2.y = _find_safe_spawn("right", p2.r)
    p1.score = p2.score = 0.0
    p1.speed_mul = p2.speed_mul = 1.0
    p1.speed_until = p2.speed_until = 0
    p1.shield = p2.shield = 0
    p1.frozen_until = p2.frozen_until = 0
    (p1 if random.choice([True, False]) else p2).is_it = True
    (p2 if p1.is_it else p1).is_it = False
    start = pygame.time.get_ticks()
    tag_block = 0
    powerups = []
    next_pu = start + random.randint(1500, 3000)
    return start, tag_block, powerups, next_pu

def apply_powerup(who, other, kind):
    now = pygame.time.get_ticks()
    if kind == "speed":
        who.speed_mul = 1.6
        who.speed_until = now + 3000
    elif kind == "shield":
        who.shield = 1
    elif kind == "freeze":
        if not who.is_it:
            other.frozen_until = now + 2000

# ---------------------- Loop ----------------------
while True:
    dt=clock.get_time()/1000.0; t=pygame.time.get_ticks()/1000.0
    mouse=pygame.mouse.get_pos()

    for e in pygame.event.get():
        # --- toggle F11 ---
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            fullscreen = not fullscreen
            flags = pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0)
            tela = pygame.display.set_mode((W, H), flags)

        if e.type==pygame.QUIT: pygame.quit(); sys.exit()

        if state==INTRO:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                state = MENU  # permite pular a abertura

        if state==MENU:
            inp1.handle(e); inp2.handle(e); pick1.handle(e); pick2.handle(e)
            if (e.type==pygame.MOUSEBUTTONDOWN and btn.clicked(e.pos)) or (e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN):
                p1=Player(W*0.25,H*0.55,22,pick1.color(),5.0,{"up":pygame.K_w,"down":pygame.K_s,"left":pygame.K_a,"right":pygame.K_d},inp1.text or "Player 1")
                p2=Player(W*0.75,H*0.55,22,pick2.color(),5.0,{"up":pygame.K_UP,"down":pygame.K_DOWN,"left":pygame.K_LEFT,"right":pygame.K_RIGHT},inp2.text or "Player 2")
                wins=[0,0]; round_idx=1
                start_ticks, tag_until, powerups, next_pu = reset_round(p1,p2)
                state=GAME
                if music_ok: pygame.mixer.music.play(-1)

        elif state==GAME:
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()

        elif state==END:
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_r: state=MENU; inp1.text=inp2.text=""
                if e.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()

    # ------------- RENDER POR ESTADO -------------
    if state == INTRO:
        if BG_IMG: tela.blit(BG_IMG,(0,0))
        else: tela.fill(BG)
        shade = pygame.Surface((W, H), pygame.SRCALPHA); shade.fill((0,0,0,90)); tela.blit(shade,(0,0))

        elapsed = pygame.time.get_ticks() - intro_start
        p = elapsed / INTRO_MS

        FI, FO = 0.25, 0.25
        if p < FI: alpha = int(255 * (p / FI))
        elif p > 1 - FO: alpha = int(255 * ((1 - p) / FO))
        else: alpha = 255
        alpha = max(0, min(255, alpha))

        txt = "FAÇAM SUAS APOSTAS!"
        tsec = pygame.time.get_ticks() / 1000.0
        scale = 1.0 + 0.02 * math.sin(tsec * 3.0)
        text = FT_MEGA.render(txt, True, WHITE)
        shadow = FT_MEGA.render(txt, True, (0, 0, 0))
        text.set_alpha(alpha); shadow.set_alpha(int(alpha * 0.6))
        text = pygame.transform.rotozoom(text, 0, scale)
        shadow = pygame.transform.rotozoom(shadow, 0, scale)
        tela.blit(shadow, shadow.get_rect(center=(W//2+3, H//2+2)))
        tela.blit(text, text.get_rect(center=(W//2, H//2)))

        if elapsed >= INTRO_MS: state = MENU

    elif state==MENU:
        if BG_IMG: tela.blit(BG_IMG,(0,0)); sh=pygame.Surface((W,H),pygame.SRCALPHA); sh.fill((0,0,0,80)); tela.blit(sh,(0,0))
        else: tela.fill(BG)

        brand=FT.render("Vannpipe Game Inc.",True,WHITE); tela.blit(brand,(W//2-brand.get_width()//2,90))

        title="Pega - Pega 1V1"
        for i,a in enumerate([90,60,30]):
            s=load_font(46+i*2).render(title,True,(100,170,255)); s.set_alpha(a)
            tela.blit(s,(W//2-s.get_width()//2,125-i*2))
        main=FT_BIG.render(title,True,WHITE); tela.blit(main,(W//2-main.get_width()//2,120))

        lbl1=FT_SM.render("Cor P1",True,WHITE); tela.blit(lbl1,(W//2 - 200, y_start - 18))
        pick1.draw(tela); inp1.draw(tela)

        lbl2=FT_SM.render("Cor P2",True,WHITE); tela.blit(lbl2,(W//2 - 200, y_start + spacing - 18))
        pick2.draw(tela); inp2.draw(tela)

        btn.draw(tela, btn.rect.collidepoint(mouse), t)

    elif state==GAME:
        now=pygame.time.get_ticks()
        elapsed=now-start_ticks; remain=ROUND_MS - elapsed

        draw_bg(); draw_obstacles(tela)

        if now>=next_pu and len(powerups)<3:
            spawn_powerup(powerups); next_pu=now+random.randint(3000,6000)

        mover_rects=[m.rect() for m in MOVERS]

        dx1,dy1=p1.input(); hit1=p1.move_collide(dx1,dy1,ARENA,STATIC_RECTS,mover_rects,CIRCLES)
        dx2,dy2=p2.input(); hit2=p2.move_collide(dx2,dy2,ARENA,STATIC_RECTS,mover_rects,CIRCLES)
        if (hit1 or hit2) and hit_ok: S_HIT.play()

        nowms=pygame.time.get_ticks()
        if nowms>p1.speed_until: p1.speed_mul=1.0
        if nowms>p2.speed_until: p2.speed_mul=1.0

        if not p1.is_it: p1.score+=dt
        if not p2.is_it: p2.score+=dt

        for pu in powerups[:]:
            who=None
            if dist(p1.x,p1.y,pu.x,pu.y)<=p1.r+PU_RADIUS: who=p1; other=p2
            elif dist(p2.x,p2.y,pu.x,pu.y)<=p2.r+PU_RADIUS: who=p2; other=p1
            if who:
                apply_powerup(who,other,pu.kind)
                powerups.remove(pu)

        if now>=tag_until and circles_collide(p1.x,p1.y,p1.r,p2.x,p2.y,p2.r):
            tagger=p1 if p1.is_it else p2; runner=p2 if p1.is_it else p1
            if runner.shield:
                runner.shield=0
            else:
                p1.is_it, p2.is_it = (not p1.is_it), (not p2.is_it)
                if tag_ok: S_TAG.play()
                dx=p2.x-p1.x; dy=p2.y-p1.y; d=math.hypot(dx,dy) or 1
                over=(p1.r+p2.r)-d+2; nx,ny=dx/d,dy/d
                p1.x-=nx*over*0.5; p1.y-=ny*over*0.5; p2.x+=nx*over*0.5; p2.y+=ny*over*0.5
            tag_until=now+500

        for pu in powerups: pu.draw(tela)
        p1.draw(tela); p2.draw(tela)
        hud(p1,p2,remain,round_idx,wins)

        if remain<=0:
            if p1.score>p2.score: wins[0]+=1
            elif p2.score>p1.score: wins[1]+=1
            round_idx+=1
            if wins[0]==2 or wins[1]==2 or round_idx>3:
                if wins[0]>wins[1]: winner_msg=f"Vencedor: {p1.name}"
                elif wins[1]>wins[0]: winner_msg=f"Vencedor: {p2.name}"
                else: winner_msg="Empate!"
                if music_ok: pygame.mixer.music.stop()
                state=END
            else:
                start_ticks, tag_until, powerups, next_pu = reset_round(p1,p2)

    elif state==END:
        draw_bg()
        shade=pygame.Surface((W,H),pygame.SRCALPHA); shade.fill((0,0,0,160)); tela.blit(shade,(0,0))
        f=FT_BIG.render("Fim de Jogo!",True,WHITE); tela.blit(f,(W//2-f.get_width()//2,H//2-80))
        wtxt=FT_SC.render(winner_msg,True,YELL); tela.blit(wtxt,(W//2-wtxt.get_width()//2,H//2-30))
        info=FT.render("Pressione R para Reiniciar ou ESC para Sair",True,WHITE)
        tela.blit(info,(W//2-info.get_width()//2,H//2+20))

    pygame.display.flip()
    clock.tick(FPS)
