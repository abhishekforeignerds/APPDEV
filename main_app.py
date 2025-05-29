import pygame
import sys
import random
import time
import threading
import json
import requests
import os
import math
from datetime import datetime

# Import refactored modules
from wheel_module import draw_wheel, update_spin
from table_module import draw_table, draw_left_table

LAST_SPIN_FILE = "last_spin.json"

# Utility for resource paths
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

# Persistence helpers
def save_last_spin_timestamp(ts):
    try:
        with open(LAST_SPIN_FILE, 'w') as f:
            json.dump({"last_spin": ts}, f)
    except:
        pass

def load_last_spin_timestamp():
    try:
        with open(LAST_SPIN_FILE, 'r') as f:
            data = json.load(f)
            return data.get("last_spin", None)
    except:
        return None

# Main launcher
def launch_main_app(user_data):
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Main App - Spinning Wheel and History")

    # Layout margins
    padding = 10
    icon_size = 30
    margin_top = icon_size + padding * 2

    # Colors & fonts
    BLACK = (0,0,0)
    ORANGE = (255,152,0)
    DARK_RED = (150,0,0)
    DARKER_RED = (100,0,0)
    RED_BG = (200,0,0)
    NAVY_BLUE = (0,0,100)
    DARK_BLUE = (0,0,50)
    WHITE = (255,255,255)
    YELLOW = (200,200,0)
    TABLE_BG = (0x35,0x0b,0x2d)
    GRID = (80,80,80)

    font = pygame.font.SysFont("Arial", 24, bold=True)
    big_font = pygame.font.SysFont("Arial", 32, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)

    # Load label images
    label_size = 40
    labels_kjq = {}
    for key in ['K','J','Q']:
        img = pygame.image.load(resource_path(f"golden-{key.lower()}.png")).convert_alpha()
        labels_kjq[key] = pygame.transform.smoothscale(img, (label_size, label_size))

    suit_size = 32
    labels_suits = {}
    for suit in ['clubs','diamond','hearts','spades']:
        img = pygame.image.load(resource_path(f"golden-{suit}.png")).convert_alpha()
        labels_suits[suit.capitalize()] = pygame.transform.smoothscale(img, (suit_size, suit_size))

    # Background
    bg_img = pygame.image.load(resource_path("overlay-bg.jpg")).convert()
    bg_img = pygame.transform.scale(bg_img, (sw, sh))

    # Wheel config
    num_segments = 12
    outer_radius = 250
    mid_radius = outer_radius // 2
    inner_radius = mid_radius // 2
    wheel_center = (int(sw * 0.75), int(sh // 2 + margin_top / 2))
    outer_colors = [DARK_RED] * num_segments
    mid_colors = [NAVY_BLUE if i%2==0 else DARK_BLUE for i in range(num_segments)]

    # Controls: close and minimize
    close_btn = pygame.Rect(sw - icon_size - padding, padding, icon_size, icon_size)
    min_btn = pygame.Rect(close_btn.x - icon_size - padding, padding, icon_size, icon_size)

    # Other buttons
    btn_w, btn_h = 140, 40
    top_y = margin_top + padding
    pad = 10
    total_w = btn_w*3 + pad*2
    start_x = sw - pad - total_w
    account_btn = pygame.Rect(start_x, top_y, btn_w, btn_h)
    history_btn = pygame.Rect(start_x + btn_w + pad, top_y, btn_w, btn_h)
    simple_btn = pygame.Rect(start_x + 2*(btn_w + pad), top_y, btn_w, btn_h)
    back_btn = pygame.Rect(50, sh - 70, 100, 40)

    # Pointer
    def draw_pointer():
        p = (wheel_center[0], wheel_center[1] - outer_radius - 10)
        l = (p[0] - 10, p[1] + 20)
        r = (p[0] + 10, p[1] + 20)
        pygame.draw.polygon(screen, ORANGE, [p, l, r])

    # State
    spinning = False
    current_ang = 0.0
    spin_start = 0.0
    total_rot = 0.0
    mapped_list = []
    show_mode = 'wheel'

    persisted = load_last_spin_timestamp()
    last_auto = persisted or time.time()

    # API thread
    def api_loop():
        nonlocal mapped_list, last_auto
        while True:
            time.sleep(2)
            try:
                resp = requests.post(
                    "https://spintofortune.in/api/app_dashboard_data.php",
                    data={"ID": str(user_data['id'])}
                )
                data = resp.json()
                mapped_list = data.get('mapped', [])
                srv_last = data.get('last_spin_timestamp')
                if srv_last:
                    last_auto = srv_last
                    save_last_spin_timestamp(srv_last)
            except:
                pass
    threading.Thread(target=api_loop, daemon=True).start()

    clock = pygame.time.Clock()

    def draw_countdown(now):
        nxt = max(0, 20 - int(now - last_auto))
        txt = font.render(f"Next spin in: {nxt}s", True, WHITE)
        screen.blit(txt, (wheel_center[0] - txt.get_width()//2, wheel_center[1] + outer_radius + 30))

    # Main loop
    while True:
        now = time.time()
        # Auto-spin
        if show_mode=='wheel' and not spinning and now - last_auto >= 20:
            spins = random.randint(3,6)
            seg = random.randrange(num_segments)
            half = 360/(2*num_segments)
            final = seg*(360/num_segments) + half
            total_rot = spins*360 + final
            spin_start = now
            spinning = True
            last_auto = now
            save_last_spin_timestamp(now)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1:
                if close_btn.collidepoint(ev.pos):
                    pygame.quit(); sys.exit()
                if min_btn.collidepoint(ev.pos):
                    pygame.display.iconify()
                if show_mode=='wheel':
                    if account_btn.collidepoint(ev.pos): show_mode='summary'
                    elif history_btn.collidepoint(ev.pos): show_mode='history'
                    elif simple_btn.collidepoint(ev.pos): show_mode='simple'
                else:
                    if back_btn.collidepoint(ev.pos): show_mode='wheel'

        screen.fill(BLACK)
        if show_mode=='wheel':
            screen.blit(bg_img, (0,0))

            # Draw top controls background
            pygame.draw.rect(screen, RED_BG, (0, 0, sw, margin_top))
            # Close button (white cross)
            pygame.draw.rect(screen, RED_BG, close_btn)
            cx, cy = close_btn.center
            offset = 8
            pygame.draw.line(screen, WHITE, (cx-offset, cy-offset), (cx+offset, cy+offset), 3)
            pygame.draw.line(screen, WHITE, (cx-offset, cy+offset), (cx+offset, cy-offset), 3)
            # Minimize button (white dash)
            pygame.draw.rect(screen, RED_BG, min_btn)
            mx, my = min_btn.center
            pygame.draw.line(screen, WHITE, (mx-10, my), (mx+10, my), 3)

            # Header info
            info_txt = f"ID:{user_data['id']} User:{user_data['username']} Name:{user_data.get('first_name','')} {user_data.get('last_name','')}"
            pts_txt = f"Pts:{user_data.get('points',0)} Win:{user_data.get('winning_points',0)}"
            screen.blit(font.render(info_txt, True, WHITE), (20, margin_top + 10))
            screen.blit(font.render(pts_txt, True, WHITE), (20, margin_top + 40))

            # Left table
            draw_left_table(screen, now, labels_kjq, labels_suits,
                            x0=50, y0=100 + margin_top,
                            label_size=label_size, suit_size=suit_size,
                            small_font=small_font)
            # Wheel & pointer
            current_ang, spinning = update_spin(now, spin_start, total_rot)
            draw_wheel(screen, wheel_center, outer_radius,
                       mid_radius, inner_radius,
                       num_segments, outer_colors,
                       mid_colors,
                       labels_kjq, labels_suits,
                       current_ang)
            draw_pointer()
            draw_countdown(now)

            # Buttons
            for btn, txt in [(account_btn,"Account"),(history_btn,"History"),(simple_btn,"Card History")]:
                pygame.draw.rect(screen, ORANGE, btn)
                w,h = font.size(txt)
                screen.blit(font.render(txt, True, BLACK),
                            (btn.x + (btn.width-w)//2, btn.y + (btn.height-h)//2))

        elif show_mode=='history':
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point","status","action"]
            draw_table(screen, cols, mapped_list, "History", big_font, small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(big_font.render("Close", True, BLACK), (back_btn.x+20, back_btn.y+5))
        elif show_mode=='summary':
            total_sale = sum(float(i.get('bet_amount',0)) for i in mapped_list)
            total_win = sum(float(i.get('claim_point',0)) for i in mapped_list)
            total_comm = total_sale*0.03
            net = total_sale - total_win - total_comm
            row = {k.lower():round(v,2) for k,v in zip(
                ["Total Sale","Total Win","Total Commission","Net Point"],[total_sale,total_win,total_comm,net])}
            cols = ["Total Sale","Total Win","Total Commission","Net Point"]
            draw_table(screen, cols, [row], "Account", big_font, small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(big_font.render("Close", True, BLACK), (back_btn.x+20, back_btn.y+5))
        else:
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point"]
            draw_table(screen, cols, mapped_list, "Card History", big_font, small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(big_font.render("Close", True, BLACK), (back_btn.x+20, back_btn.y+5))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    dummy = {"id":0,"username":"guest","first_name":"Guest","last_name":"","points":0,"winning_points":0}
    launch_main_app(dummy)
