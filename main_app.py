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
RESULT_API = "https://spintofortune.in/api/app_make_result.php"

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

def create_gold_gradient_surface(width, height):
    # Create a new surface for the gradient
    gradient = pygame.Surface((width, height))

    # Define start and end gold colors
    start_color = (255, 215, 0)   # Light gold
    end_color   = (184, 134, 11)  # Darker gold

    for y in range(height):
        ratio = y / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))

    return gradient

def send_withdraw_request(withdraw_time, user_id):
    try:
        payload = {
            "withdraw_time": withdraw_time,
            "user_id":       str(user_id)
        }
        resp = requests.post(
            RESULT_API,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("Sent payload:", payload)
        print("Raw response:", resp.text)
    except Exception as e:
        print("Request error:", e)
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
    # ───── COLORS ─────
    WOOD_BLACK = (34, 21, 11)       # a very dark brown/black, “wood” feel
    VIOLET     = (148, 0, 211)      # deep violet for borders
    YELLOW_BG  = (255, 255, 0)      # solid yellow for hover


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

    dt_withdraw = datetime.fromtimestamp(next_withdraw_ts)
    if dt_withdraw.minute % 2 == 1:
        next_withdraw_ts -= 60

    withdraw_str = format_withdraw_time(next_withdraw_ts)
    globals.Withdraw_time = withdraw_str
    wheel_module.print_withdraw_time()

    mapped_list = []
    result_sent = False

    def api_loop():
        nonlocal mapped_list, last_auto, next_spin_time, next_withdraw_ts, withdraw_str, result_sent
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

                    dt_withdraw = datetime.fromtimestamp(next_withdraw_ts)
                    if dt_withdraw.minute % 2 == 1:
                        next_withdraw_ts -= 60

                    withdraw_str = format_withdraw_time(next_withdraw_ts)
                    globals.Withdraw_time = withdraw_str
                    result_sent = False
            except Exception:
                pass

    threading.Thread(target=api_loop, daemon=True).start()

    clock = pygame.time.Clock()
    spinning = False
    current_ang = 0.0
    spin_start = 0.0
    total_rot = 0.0
    show_mode = 'wheel'

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
        return remaining

    def draw_withdraw_time_label():
        pass

    while True:
        now = time.time()
        remaining = max(0, int(next_spin_time - now))
        if remaining <= 5 and not result_sent:
            send_withdraw_request(withdraw_str, user_data['id'])
            result_sent = True

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

            dt_withdraw = datetime.fromtimestamp(next_withdraw_ts)
            if dt_withdraw.minute % 2 == 1:
                next_withdraw_ts -= 60

            withdraw_str = format_withdraw_time(next_withdraw_ts)
            globals.Withdraw_time = withdraw_str
            result_sent = False

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
            screen.blit(bg_img, (0, 0))
            # 1) Draw the top margin with a “wooden‐black” solid fill:
            pygame.draw.rect(screen, WOOD_BLACK, (0, 0, sw, margin_top))
            pygame.draw.rect(screen, WOOD_BLACK, (0, 0, sw, margin_top))

            # 2) Draw a 2px‐thick red line exactly at the bottom edge of the header:
            border_thickness = 2
            y_border = margin_top - border_thickness  # flush at the very bottom
            pygame.draw.line(
                screen,
                (255, 0, 0),            # red
                (0,            y_border),
                (sw,           y_border),
                border_thickness
            )
            mx, my = pygame.mouse.get_pos()

            # ─── PREPARE DEFAULT‐SIZE GRADIENTS (for non‐hover state) ───
            close_gradient = create_gold_gradient_surface(close_btn.width, close_btn.height)
            min_gradient   = create_gold_gradient_surface(min_btn.width, min_btn.height)


            # ─── CLOSE BUTTON ("X") ───
            is_hover_close = close_btn.collidepoint(mx, my)

            if is_hover_close:
                # 1) Inflate the rect by (4, 4) for hover (→ 2px on each side)
                hover_rect = close_btn.inflate(6, 6)
                # 2) Create a slightly larger gradient for the inflated rect
                hover_grad = create_gold_gradient_surface(hover_rect.width, hover_rect.height)
                # 3) Draw solid-yellow background (you can also blur this if you want consistent look)
                #    (If you prefer still using a gradient on hover, just blit hover_grad instead of drawing YELLOW_BG.)
                pygame.draw.rect(screen, YELLOW_BG, hover_rect)

                # 4) Draw violet border around the inflated rect
                pygame.draw.rect(screen, VIOLET, hover_rect, 2)

                # 5) Draw the “X” symbol centered on the original center (inflated has same center)
                cx, cy = close_btn.center
                off = 8  # fixed offset from center to endpoints
                pygame.draw.line(screen, VIOLET, (cx - off, cy - off), (cx + off, cy + off), 3)
                pygame.draw.line(screen, VIOLET, (cx - off, cy + off), (cx + off, cy - off), 3)

            else:
                # Non‐hover: draw the gold gradient at original size
                hover_rect = close_btn.inflate(4, 4)
                # 2) Create a slightly larger gradient for the inflated rect
                hover_grad = create_gold_gradient_surface(hover_rect.width, hover_rect.height)
                # 3) Draw solid-yellow background (you can also blur this if you want consistent look)
                #    (If you prefer still using a gradient on hover, just blit hover_grad instead of drawing YELLOW_BG.)
                pygame.draw.rect(screen, YELLOW_BG, hover_rect)

                # Draw “X” in white
                cx, cy = close_btn.center
                off = 8
                pygame.draw.line(screen, BLACK, (cx - off, cy - off), (cx + off, cy + off), 3)
                pygame.draw.line(screen, BLACK, (cx - off, cy + off), (cx + off, cy - off), 3)


            player_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
            player_surf = font.render(player_name, True, YELLOW_BG)
            player_rect = player_surf.get_rect()

            balance_text = f"Balance : {user_data.get('points', 0)}"
            balance_surf = font.render(balance_text, True, YELLOW_BG)
            balance_rect = balance_surf.get_rect()

            # spacing between balance‐border and minimize button
            spacing = 10  
            # padding inside the balance border (x– and y–)
            border_padding_x = 10  
            border_padding_y = 4   

            # Create the border rect around the “Balance” text
            balance_border = balance_rect.inflate(border_padding_x, border_padding_y)
            balance_border.right = min_btn.left - spacing

            # **Vertically center both player_rect and balance_border inside the header:**
            vertical_center = margin_top // 2
            player_rect.centery = vertical_center
            balance_border.centery = vertical_center

            # Now position the balance text itself inside that border:
            balance_rect.left = balance_border.left + (border_padding_x // 2)
            balance_rect.top  = balance_border.top  + (border_padding_y // 2)

            # Finally, push the player name so it sits just left of the balance border:
            gap = 10  # horizontal gap between player name and balance-border
            player_rect.right = balance_border.left - gap

            # 4) Blit everything in order:
            screen.blit(player_surf, player_rect)
            pygame.draw.rect(screen, YELLOW_BG, balance_border, width=1)  # 1px yellow border
            screen.blit(balance_surf, balance_rect)

            # 5) Draw to screen
            screen.blit(player_surf, (player_rect.left, player_rect.top))
            pygame.draw.rect(screen, YELLOW_BG, balance_border, 2)
            screen.blit(balance_surf, (balance_rect.left, balance_rect.top))
            # ─── MINIMIZE BUTTON ("–") ───
            is_hover_min = min_btn.collidepoint(mx, my)

            if is_hover_min:
                hover_rect = min_btn.inflate(6, 6)
                hover_grad = create_gold_gradient_surface(hover_rect.width, hover_rect.height)
                pygame.draw.rect(screen, YELLOW_BG, hover_rect)
                pygame.draw.rect(screen, VIOLET, hover_rect, 2)

                # Draw “–” in BLACK (centered at the same center as original)
                mx_c, my_c = min_btn.center
                off = 8
                pygame.draw.line(screen, BLACK, (mx_c - off, my_c), (mx_c + off, my_c), 3)

            else:
                hover_rect = min_btn.inflate(4, 4)
                hover_grad = create_gold_gradient_surface(hover_rect.width, hover_rect.height)
                pygame.draw.rect(screen, YELLOW_BG, hover_rect)
                pygame.draw.rect(screen, BLACK, hover_rect, 2)

                mx_c, my_c = min_btn.center
                off = 8
                pygame.draw.line(screen, BLACK, (mx_c - off, my_c), (mx_c + off, my_c), 3)


            current_clock = datetime.now().strftime('%H:%M:%S')
            current_date = datetime.now().strftime('%d-%m-%Y')
            info_txt = (
                f"{current_date}  "
                f"{current_clock}   "
                f"Win:{user_data.get('winning_points',0)}"
            )
            text_surf = pygame.font.Font(None, 30).render(info_txt, True, YELLOW_BG)
            screen.blit(text_surf, (20, (margin_top - text_surf.get_height()) // 2))

            draw_left_table(
                screen, now, labels_kjq, labels_suits,
                x0=50, y0=100 + margin_top,
                label_size=label_size, suit_size=suit_size,
                small_font=small_font
            )

            if spinning:
                current_ang, spinning = update_spin(now, spin_start, total_rot)

            draw_wheel(
                screen, wheel_center, outer_radius, mid_radius,
                inner_radius, num_segments, outer_colors,
                mid_colors, labels_kjq, labels_suits, current_ang
            )

            draw_countdown(now)
            draw_withdraw_time_label()

            for btn, txt in [(account_btn, "Account"),
                             (history_btn, "History"),
                             (simple_btn, "Card History")]:
                pygame.draw.rect(screen, ORANGE, btn)
                w, h = font.size(txt)
                screen.blit(
                    font.render(txt, True, BLACK),
                    (btn.x + (btn.width - w) // 2, btn.y + (btn.height - h) // 2)
                )

        elif show_mode == 'history':
            cols = ["card_type", "ticket_serial", "bet_amount", "claim_point", "unclaim_point", "status", "action"]
            draw_table(
                screen, cols, mapped_list, "History",
                pygame.font.SysFont("Arial", 32, bold=True),
                small_font, sw
            )
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(
                pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),
                (back_btn.x + 20, back_btn.y + 5)
            )

        elif show_mode == 'summary':
            total_sale = sum(float(i.get('bet_amount', 0)) for i in mapped_list)
            total_win = sum(float(i.get('claim_point', 0)) for i in mapped_list)
            total_comm = total_sale * 0.03
            net = total_sale - total_win - total_comm
            row = {
                k.lower(): round(v, 2)
                for k, v in zip(
                    ["Total Sale", "Total Win", "Total Commission", "Net Point"],
                    [total_sale, total_win, total_comm, net]
                )
            }
            cols = ["Total Sale", "Total Win", "Total Commission", "Net Point"]
            draw_table(
                screen, cols, [row], "Account",
                pygame.font.SysFont("Arial", 32, bold=True),
                small_font, sw
            )
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(
                pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),
                (back_btn.x + 20, back_btn.y + 5)
            )

        else:
            cols = ["card_type", "ticket_serial", "bet_amount", "claim_point", "unclaim_point"]
            draw_table(
                screen, cols, mapped_list, "Card History",
                pygame.font.SysFont("Arial", 32, bold=True),
                small_font, sw
            )
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(
                pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),
                (back_btn.x + 20, back_btn.y + 5)
            )

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    dummy = {
        "id": 0,
        "username": "guest",
        "first_name": "Guest",
        "last_name": "",
        "points": 0,
        "winning_points": 0
    }
    launch_main_app(dummy)
