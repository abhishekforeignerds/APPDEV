import pygame
import sys
import random
import time
import threading
import json
import requests
import os
from datetime import datetime
import globals
import wheel_module
from wheel_module import draw_wheel, update_spin, draw_left_table, handle_click
from table_module import draw_table

LAST_SPIN_FILE = "last_spin.json"
SPIN_DURATION = 120
WITHDRAW_BUFFER = 60
DASHBOARD_API = "https://spintofortune.in/api/app_dashboard_data.php"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def save_last_spin_timestamp(ts):
    try:
        with open(LAST_SPIN_FILE, 'w') as f:
            json.dump({"last_spin": ts}, f)
    except Exception:
        pass

def load_last_spin_timestamp():
    try:
        with open(LAST_SPIN_FILE, 'r') as f:
            return json.load(f).get("last_spin", None)
    except Exception:
        return None

def format_withdraw_time(ts):
    return datetime.fromtimestamp(ts).strftime('%H:%M')

def launch_main_app(user_data):
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Main App - Spinning Wheel and History")
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    ORANGE = (255, 152, 0)
    RED_BG = (200, 0, 0)
    font = pygame.font.SysFont("Arial", 24, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)
    label_size = int(min(sw, sh) * 0.05)
    labels_kjq = {}
    for key in ['K', 'J', 'Q']:
        img = pygame.image.load(resource_path(f"golden-{key.lower()}.png")).convert_alpha()
        labels_kjq[key] = pygame.transform.smoothscale(img, (label_size, label_size))
    suit_size = int(min(sw, sh) * 0.04)
    labels_suits = {}
    for suit in ['clubs', 'diamond', 'hearts', 'spades']:
        img = pygame.image.load(resource_path(f"golden-{suit}.png")).convert_alpha()
        labels_suits[suit.capitalize()] = pygame.transform.smoothscale(img, (suit_size, suit_size))
    bg_img = pygame.image.load(resource_path("overlay-bg.jpg")).convert()
    bg_img = pygame.transform.scale(bg_img, (sw, sh))
    num_segments = 12
    outer_radius = int(min(sw, sh) * 0.2)
    mid_radius = outer_radius // 2
    inner_radius = mid_radius // 2
    wheel_center = (int(sw * 0.75), int(sh // 2))
    outer_colors = [(150, 0, 0)] * num_segments
    mid_colors = [(0, 0, 100) if i % 2 == 0 else (0, 0, 50) for i in range(num_segments)]
    padding = 10
    icon_size = int(min(sw, sh) * 0.03)
    margin_top = icon_size + padding * 2
    close_btn = pygame.Rect(sw - icon_size - padding, padding, icon_size, icon_size)
    min_btn = pygame.Rect(close_btn.x - icon_size - padding, padding, icon_size, icon_size)
    btn_w = int(sw * 0.1)
    btn_h = int(sh * 0.05)
    top_y = margin_top + padding
    pad = 10
    total_w = btn_w * 3 + pad * 2
    start_x = sw - pad - total_w
    account_btn = pygame.Rect(start_x, top_y, btn_w, btn_h)
    history_btn = pygame.Rect(start_x + btn_w + pad, top_y, btn_w, btn_h)
    simple_btn = pygame.Rect(start_x + 2*(btn_w + pad), top_y, btn_w, btn_h)
    back_btn = pygame.Rect(50, sh - 70, 100, 40)

    persisted_ts = load_last_spin_timestamp()
    last_auto = persisted_ts or time.time()
    next_spin_time = last_auto + SPIN_DURATION
    next_withdraw_ts = last_auto + SPIN_DURATION + WITHDRAW_BUFFER
    withdraw_str = format_withdraw_time(next_withdraw_ts)
    globals.Withdraw_time = withdraw_str
    wheel_module.print_withdraw_time()
    mapped_list = []

    def api_loop():
        nonlocal mapped_list, last_auto, next_spin_time, next_withdraw_ts, withdraw_str
        while True:
            time.sleep(2)
            try:
                resp = requests.post(DASHBOARD_API, data={"ID": str(user_data['id'])})
                data = resp.json()
                globals.User_id = str(user_data['id'])
                mapped_list = data.get('mapped', [])
                srv_last = data.get('last_spin_timestamp')
                if srv_last:
                    last_auto = srv_last
                    save_last_spin_timestamp(srv_last)
                    next_spin_time = last_auto + SPIN_DURATION
                    next_withdraw_ts = last_auto + SPIN_DURATION + WITHDRAW_BUFFER
                    withdraw_str = format_withdraw_time(next_withdraw_ts)
                    globals.Withdraw_time = withdraw_str
            except Exception:
                pass

    threading.Thread(target=api_loop, daemon=True).start()
    clock = pygame.time.Clock()
    spinning = False
    current_ang = 0.0
    spin_start = 0.0
    total_rot = 0.0
    show_mode = 'wheel'

    def draw_pointer():
        p = (wheel_center[0], wheel_center[1] - outer_radius - 10)
        l = (p[0] - 10, p[1] + 20)
        r = (p[0] + 10, p[1] + 20)
        pygame.draw.polygon(screen, ORANGE, [p, l, r])

    def draw_timer_ring(surface, center, radius, remaining, total):
        fraction = remaining / total
        start_ang = -90 * (3.14/180)
        end_ang = (360 * fraction - 90) * (3.14/180)
        rect = pygame.Rect(0, 0, radius*2, radius*2)
        rect.center = center
        pygame.draw.circle(surface, (50,50,50), center, radius, 4)
        pygame.draw.arc(surface, ORANGE, rect, start_ang, end_ang, 4)

    def draw_countdown(now_ts):
        remaining = max(0, int(next_spin_time - now_ts))
        radius = int(min(sw, sh) * 0.05)
        padding_br = 20
        center = (sw - radius - padding_br, sh - radius - padding_br)
        draw_timer_ring(screen, center, radius, remaining, SPIN_DURATION)
        fs = int(min(sw, sh) * 0.04)
        countdown_font = pygame.font.SysFont("Arial", fs, bold=True)
        txt_surf = countdown_font.render(f"{remaining}s", True, WHITE)
        screen.blit(txt_surf, (center[0] - txt_surf.get_width()//2, center[1] - txt_surf.get_height()//2))

    def draw_withdraw_time_label():
        padding_br = 20
        fs = int(min(sw, sh) * 0.025)
        lbl_font = pygame.font.SysFont("Arial", fs)
        lbl = lbl_font.render(f"Withdraw: {withdraw_str}", True, WHITE)
        radius = int(min(sw, sh) * 0.05)
        x = sw - radius - padding_br - lbl.get_width()//2
        y = sh - radius - padding_br + radius + 5
        screen.blit(lbl, (x, y))

    while True:
        now = time.time()
        if show_mode == 'wheel' and not spinning and now - last_auto >= SPIN_DURATION:
            spins = random.randint(3, 6)
            seg = random.randrange(num_segments)
            half = 360 / (2 * num_segments)
            final_ang = seg * (360 / num_segments) + half
            total_rot = spins * 360 + final_ang
            spin_start = now
            spinning = True
            last_auto = now
            save_last_spin_timestamp(now)
            next_spin_time = last_auto + SPIN_DURATION
            next_withdraw_ts = last_auto + SPIN_DURATION + WITHDRAW_BUFFER
            withdraw_str = format_withdraw_time(next_withdraw_ts)
            globals.Withdraw_time = withdraw_str

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if close_btn.collidepoint(ev.pos):
                    pygame.quit()
                    sys.exit()
                if min_btn.collidepoint(ev.pos):
                    pygame.display.iconify()
                if show_mode == 'wheel':
                    if account_btn.collidepoint(ev.pos):
                        show_mode = 'summary'
                    elif history_btn.collidepoint(ev.pos):
                        show_mode = 'history'
                    elif simple_btn.collidepoint(ev.pos):
                        show_mode = 'simple'
                    else:
                        handle_click(ev.pos)
                else:
                    if back_btn.collidepoint(ev.pos):
                        show_mode = 'wheel'

        screen.fill(BLACK)

        if show_mode == 'wheel':
            screen.blit(bg_img, (0,0))
            pygame.draw.rect(screen, RED_BG, (0, 0, sw, margin_top))
            pygame.draw.rect(screen, RED_BG, close_btn)
            cx, cy = close_btn.center
            off = 8
            pygame.draw.line(screen, WHITE, (cx-off, cy-off), (cx+off, cy+off), 3)
            pygame.draw.line(screen, WHITE, (cx-off, cy+off), (cx+off, cy-off), 3)
            pygame.draw.rect(screen, RED_BG, min_btn)
            mx, my = min_btn.center
            pygame.draw.line(screen, WHITE, (mx-10, my), (mx+10, my), 3)
            info_txt = (f"ID:{user_data['id']}   User:{user_data['username']}   Name:{user_data.get('first_name','')} {user_data.get('last_name','')}   Pts:{user_data.get('points',0)}   Win:{user_data.get('winning_points',0)}")
            text_surf = pygame.font.Font(None, 16).render(info_txt, True, WHITE)
            screen.blit(text_surf, (20, (margin_top - text_surf.get_height())//2))
            draw_left_table(screen, now, labels_kjq, labels_suits, x0=50, y0=100+margin_top, label_size=label_size, suit_size=suit_size, small_font=small_font)
            if spinning:
                current_ang, spinning = update_spin(now, spin_start, total_rot)
            draw_wheel(screen, wheel_center, outer_radius, mid_radius, inner_radius, num_segments, outer_colors, mid_colors, labels_kjq, labels_suits, current_ang)
            draw_pointer()
            draw_countdown(now)
            draw_withdraw_time_label()
            for btn, txt in [(account_btn,"Account"),(history_btn,"History"),(simple_btn,"Card History")]:
                pygame.draw.rect(screen, ORANGE, btn)
                w, h = font.size(txt)
                screen.blit(font.render(txt, True, BLACK),(btn.x + (btn.width - w)//2, btn.y + (btn.height - h)//2))

        elif show_mode == 'history':
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point","status","action"]
            draw_table(screen, cols, mapped_list, "History", pygame.font.SysFont("Arial", 32, bold=True), small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),(back_btn.x + 20, back_btn.y + 5))

        elif show_mode == 'summary':
            total_sale = sum(float(i.get('bet_amount',0)) for i in mapped_list)
            total_win = sum(float(i.get('claim_point',0)) for i in mapped_list)
            total_comm = total_sale * 0.03
            net = total_sale - total_win - total_comm
            row = {k.lower(): round(v,2) for k,v in zip(["Total Sale","Total Win","Total Commission","Net Point"],[total_sale,total_win,total_comm,net])}
            cols = ["Total Sale","Total Win","Total Commission","Net Point"]
            draw_table(screen, cols, [row], "Account", pygame.font.SysFont("Arial", 32, bold=True), small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),(back_btn.x + 20, back_btn.y + 5))

        else:
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point"]
            draw_table(screen, cols, mapped_list, "Card History", pygame.font.SysFont("Arial", 32, bold=True), small_font, sw)
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),(back_btn.x + 20, back_btn.y + 5))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    dummy = {"id": 0,"username": "guest","first_name": "Guest","last_name": "","points": 0,"winning_points": 0}
    launch_main_app(dummy)
