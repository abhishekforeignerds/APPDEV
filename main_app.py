import pygame
import sys
import random
import time
import threading
import json
import requests
import os
from datetime import datetime, timedelta
import globals

import wheel_module
from wheel_module import (
    draw_wheel,
    update_spin,
    draw_left_table,
    handle_click
)
from table_module import draw_table

LAST_SPIN_FILE = "last_spin.json"
CYCLE_DURATION = 120      # seconds (2 minutes)
DASHBOARD_API  = "https://spintofortune.in/api/app_dashboard_data.php"
RESULT_API     = "https://spintofortune.in/api/app_make_result.php"

RED_BG      = (200, 0, 0)
BLUE_RIBBON = (0, 0, 200)
GREEN       = (0, 255, 0)

def compute_final_angle_for_segment(target_index, num_segments=None):
    """
    Returns a fixed “final angle” for each segment index, using explicit if/elif statements.
    The mapping is:
      index 0  → 255.0°
      index 1  → 225.0°
      index 2  → 195.0°
      index 3  → 165.0°
      index 4  → 135.0°
      index 5  → 105.0°
      index 6  →  75.0°
      index 7  →  45.0°
      index 8  →  15.0°
      index 9  → 345.0°
      index 10 → 315.0°
      index 11 → 285.0°
    """
    if target_index == 0:
        return 255.0
    elif target_index == 1:
        return 225.0
    elif target_index == 2:
        return 195.0
    elif target_index == 3:
        return 165.0
    elif target_index == 4:
        return 135.0
    elif target_index == 5:
        return 105.0
    elif target_index == 6:
        return 75.0
    elif target_index == 7:
        return 45.0
    elif target_index == 8:
        return 15.0
    elif target_index == 9:
        return 345.0
    elif target_index == 10:
        return 315.0
    elif target_index == 11:
        return 285.0
    else:
        raise ValueError(f"Invalid segment index: {target_index}")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def save_last_cycle_timestamp(ts):
    """Persist the cycle‐start timestamp."""
    try:
        with open(LAST_SPIN_FILE, 'w') as f:
            json.dump({"last_cycle": ts}, f)
    except Exception:
        pass

def load_last_cycle_timestamp():
    try:
        return json.load(open(LAST_SPIN_FILE)).get("last_cycle", None)
    except Exception:
        return None

def format_withdraw_time(ts):
    return datetime.fromtimestamp(ts).strftime('%H:%M:%S')

def create_gold_gradient_surface(width, height):
    gradient = pygame.Surface((width, height))
    start_color = (255, 215, 0)
    end_color   = (184, 134, 11)
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))
    return gradient

def launch_main_app(user_data):
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Main App - Spinning Wheel and History")

    # ───── COLORS ─────────────────────────────────────────────────────────────────
    BLACK      = (0, 0, 0)
    WHITE      = (255, 255, 255)
    ORANGE     = (255, 152, 0)
    WOOD_BLACK = (34, 21, 11)
    VIOLET     = (148, 0, 211)
    YELLOW_BG  = (255, 255, 0)

    # ───── FONTS ──────────────────────────────────────────────────────────────────
    font = pygame.font.SysFont("Arial", 24, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)

    # ───── LOAD ICONS ──────────────────────────────────────────────────────────────
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

    # ───── WHEEL SETUP ───────────────────────────────────────────────────────────
    num_segments   = 12
    outer_radius   = int(min(sw, sh) * 0.20)
    mid_radius     = outer_radius // 2
    inner_radius   = mid_radius // 2
    wheel_center   = (int(sw * 0.75), int(sh // 2))

    outer_colors   = [(150, 0, 0)] * num_segments
    mid_colors     = [(0, 0, 100) if i % 2 == 0 else (0, 0, 50) for i in range(num_segments)]

    initial_ang   = compute_final_angle_for_segment(0, num_segments)
    current_ang   = initial_ang
    spin_base_ang = current_ang
    total_rot     = 0.0
    spin_start    = 0.0

    padding    = 10
    icon_size  = int(min(sw, sh) * 0.03)
    margin_top = icon_size + padding * 2

    close_btn = pygame.Rect(sw - icon_size - padding, padding, icon_size, icon_size)
    min_btn   = pygame.Rect(close_btn.x - icon_size - padding, padding, icon_size, icon_size)

    btn_w = int(sw * 0.1)
    btn_h = int(sh * 0.05)
    top_y = margin_top + padding
    pad   = 10
    total_w = btn_w * 3 + pad * 2
    start_x = sw - pad - total_w

    account_btn = pygame.Rect(start_x, top_y, btn_w, btn_h)
    history_btn = pygame.Rect(start_x + btn_w + pad, top_y, btn_w, btn_h)
    simple_btn  = pygame.Rect(start_x + 2 * (btn_w + pad), top_y, btn_w, btn_h)

    back_btn = pygame.Rect(50, sh - 70, 100, 40)

    # ───── FETCH INITIAL SERVER TIME ──────────────────────────────────────────────
    try:
        resp = requests.post(DASHBOARD_API, data={"ID": str(user_data['id'])})
        data = resp.json()
        globals.history_json = data.get('game_results_history', [])
        #print("Response from RESULT_API (at remaining==5):", globals.history_json)
        server_ts = data.get("server_timestamp", time.time())
    except Exception:
        server_ts = time.time()

    base_server_ts = server_ts
    base_local_ts  = time.time()

    # ───── “NEXT WITHDRAW” ON AN EVEN :00 ─────────────────────────────────────────
    server_dt = datetime.fromtimestamp(base_server_ts)
    if server_dt.minute % 2 == 1:
        candidate = server_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    else:
        candidate = server_dt.replace(second=0, microsecond=0) + timedelta(minutes=2)

    next_action_ts = candidate.timestamp()

    # ───── SET CYCLE START (120s countdown) ──────────────────────────────────────
    cycle_start_ts = next_action_ts - CYCLE_DURATION
    save_last_cycle_timestamp(cycle_start_ts)

    # ───── IMMEDIATELY STORE the raw numeric timestamp for withdraw ─────────────
    withdraw_ts = next_action_ts
    globals.Withdraw_time = format_withdraw_time(withdraw_ts)
    wheel_module.print_withdraw_time()

    # ───── INITIALIZE balance ONCE FROM user_data('points') ─────────────────────
    #     After this, we’ll always use globals.user_data_points and let handle_click() update it.
    globals.user_data_points = user_data.get('points', 0)
    globals.total_win_today = user_data.get('winning_points', 0)
    #print(f"Updated initial globals.total_win_today → {globals.total_win_today}")

    mapped_list      = []
    waiting_for_blink= False
    blink_mode       = False
    blink_start_time = 0.0
    highlight_on     = False

    spinning        = False
    result_index    = None
    anim_offset     = 0.0
    anim_speed      = 5.0  # ~5 labels/sec

    # ───── LOAD LAST CYCLE FROM DISK ─────────────────────────────────────────────
    persisted_start = load_last_cycle_timestamp()
    if persisted_start is not None:
        last_cycle = persisted_start
        while last_cycle + CYCLE_DURATION <= base_server_ts:
            last_cycle += CYCLE_DURATION
        cycle_start_ts = last_cycle
        next_action_ts = cycle_start_ts + CYCLE_DURATION
        withdraw_ts     = next_action_ts

        globals.Withdraw_time = format_withdraw_time(withdraw_ts)
        wheel_module.print_withdraw_time()
        save_last_cycle_timestamp(cycle_start_ts)

    def api_loop():
        nonlocal mapped_list, base_server_ts, base_local_ts
        nonlocal next_action_ts, withdraw_ts, cycle_start_ts
        nonlocal waiting_for_blink

        while True:
            time.sleep(2)
            try:
                resp = requests.post(DASHBOARD_API, data={"ID": str(user_data['id'])})
                data = resp.json()
                globals.User_id = str(user_data['id'])
                mapped_list = data.get('mapped', [])

                srv_now = data.get('server_timestamp')
                if srv_now:
                    base_server_ts = srv_now
                    base_local_ts  = time.time()

                srv_last = data.get('last_spin_timestamp')
                if srv_last:
                    srv_dt = datetime.fromtimestamp(srv_last)
                    aligned_min = srv_dt.minute - (srv_dt.minute % 2)
                    aligned_cycle_dt = srv_dt.replace(minute=aligned_min, second=0, microsecond=0)
                    last_cycle = aligned_cycle_dt.timestamp()

                    while last_cycle + CYCLE_DURATION <= base_server_ts:
                        last_cycle += CYCLE_DURATION

                    cycle_start_ts = last_cycle
                    next_action_ts = cycle_start_ts + CYCLE_DURATION
                    withdraw_ts     = next_action_ts

                    globals.Withdraw_time = format_withdraw_time(withdraw_ts)
                    wheel_module.print_withdraw_time()
                    save_last_cycle_timestamp(cycle_start_ts)

                if base_server_ts >= next_action_ts:
                    cycle_start_ts = next_action_ts
                    next_action_ts = cycle_start_ts + CYCLE_DURATION
                    withdraw_ts    = next_action_ts

                    globals.Withdraw_time = format_withdraw_time(withdraw_ts)
                    wheel_module.print_withdraw_time()
                    save_last_cycle_timestamp(cycle_start_ts)

                    # Reset for the next‐spin blink logic
                    waiting_for_blink = False

            except Exception:
                pass

    threading.Thread(target=api_loop, daemon=True).start()

    clock = pygame.time.Clock()
    show_mode = 'wheel'

    def draw_timer_ring(surface, center, radius, remaining, total):
        fraction = max(0.0, min(1.0, remaining / total))
        start_ang = -90 * (3.14 / 180)
        end_ang   = (360 * fraction - 90) * (3.14 / 180)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = center
        pygame.draw.circle(surface, (50, 50, 50), center, radius, 4)
        pygame.draw.arc(surface, ORANGE, rect, start_ang, end_ang, 4)

    def compute_countdown():
        curr_local = time.time()
        elapsed = curr_local - base_local_ts
        current_server_ts = base_server_ts + elapsed
        remaining = max(0, int((cycle_start_ts + CYCLE_DURATION) - current_server_ts))
        return remaining, current_server_ts

    def draw_withdraw_time_label():
        label = f""
        fs = int(min(sw, sh) * 0.03)
        lbl_font = pygame.font.SysFont("Arial", fs, bold=True)
        surf = lbl_font.render(label, True, YELLOW_BG)
        padding = 20
        x = sw - surf.get_width() - padding
        y = sh - surf.get_height() - padding - int(min(sw, sh) * 0.05) - 10
        screen.blit(surf, (x, y))

    def segment_to_cell(idx):
        """
        0→(1,1),  1→(1,2),  2→(1,3),  3→(1,4)
        4→(2,1),  5→(2,2),  6→(2,3),  7→(2,4)
        8→(3,1),  9→(3,2), 10→(3,3), 11→(3,4)
        """
        if idx < 0 or idx > 11:
            return None
        ridx = idx // 4 + 1
        cidx = idx % 4 + 1
        return (ridx, cidx)

    while True:
        dt = clock.get_time() / 1000.0
        now_local = time.time()
        remaining, current_server_ts = compute_countdown()

        # ─── Fetch forced segment exactly when remaining == 5 ───
        if remaining == 5:
            try:
                payload = {
                    # Numeric timestamp
                    "withdraw_time": int(withdraw_ts),
                    "user_id":       str(user_data['id'])
                }
                resp = requests.post(
                    RESULT_API,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                resp_data = resp.json()

                # Print entire JSON response each time
                #print("Response from RESULT_API (at remaining==5):", resp_data)

                choosen = resp_data.get("choosenindex")
                if choosen is not None:
                    globals.FORCED_SEGMENT = int(choosen)
                    #print(f"Updated globals.FORCED_SEGMENT → {globals.FORCED_SEGMENT}")
                waiting_for_blink = True
            except Exception as e:
                print("Error fetching forced segment:", e)

        # ─── When countdown hits 0, schedule forced spin ───
        if remaining <= 0 and not spinning:
            spins    = random.randint(3, 6)
            target_i = globals.FORCED_SEGMENT
            win_value = int(resp_data.get("chooseindexpoint", 0))

            if win_value is not None:
                #print(f"Updated before globals.total_win_today → {globals.total_win_today}")
                def delayed_update():
                    time.sleep(5)
                    globals.total_win_today = int(globals.total_win_today) + win_value * 10

                threading.Thread(target=delayed_update).start()
                #print(f"Updated after globals.total_win_today → {globals.total_win_today}")

            desired_final_ang = compute_final_angle_for_segment(target_i, num_segments)
            delta_ang = (desired_final_ang - spin_base_ang) % 360.0
            total_rot   = spins * 360.0 + delta_ang
            spin_start  = current_server_ts
            spinning    = True
            result_index = None

            #print(f"*** Spinning wheel → stopping on segment #{target_i}; "f"desired_final_ang={desired_final_ang:.1f}°, "f"spin_base_ang={spin_base_ang:.1f}°, delta={delta_ang:.1f}°, " f"total_rot={total_rot:.1f}° ***")

            # Schedule next cycle immediately
            cycle_start_ts = cycle_start_ts + CYCLE_DURATION
            next_action_ts = cycle_start_ts + CYCLE_DURATION
            withdraw_ts    = next_action_ts
            globals.Withdraw_time = format_withdraw_time(withdraw_ts)
            wheel_module.print_withdraw_time()
            save_last_cycle_timestamp(cycle_start_ts)

        # ─── Handle events ───
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
                        # ─── Player clicked on the wheel to place a bet ───
                        bet_amt = handle_click(ev.pos)
                        if isinstance(bet_amt, (int, float)):
                            # Subtract the bet amount from globals.user_data_points
                            globals.user_data_points = max(0, globals.user_data_points - bet_amt)
                            #print(f"Bet placed: {bet_amt}, New balance = {globals.user_data_points}")
                else:
                    if back_btn.collidepoint(ev.pos):
                        show_mode = 'wheel'

        # ─── Update rotation + scrolling text offset ───
        if spinning:
            delta_ang, still_spinning = update_spin(now_local, spin_start, total_rot)
            current_ang = spin_base_ang + delta_ang

            anim_offset += anim_speed * dt

            if not still_spinning:
                spinning = False
                globals.history_json = resp_data.get('game_results_history', [])
                spin_base_ang = current_ang
                result_index = globals.FORCED_SEGMENT
                if waiting_for_blink:
                    blink_mode = True
                    blink_start_time = time.time()
                    waiting_for_blink = False

        # ─── Draw UI ───
        screen.fill(BLACK)
        screen.blit(bg_img, (0, 0))

        # Header + border
        pygame.draw.rect(screen, WOOD_BLACK, (0, 0, sw, margin_top))
        pygame.draw.line(screen, (255, 0, 0),
                         (0, margin_top - 2), (sw, margin_top - 2), 2)

        mx, my = pygame.mouse.get_pos()

        # Close & Minimize
        is_hover_close = close_btn.collidepoint(mx, my)
        if is_hover_close:
            hr = close_btn.inflate(6, 6)
            pygame.draw.rect(screen, YELLOW_BG, hr)
            pygame.draw.rect(screen, VIOLET, hr, 2)
            cx, cy = close_btn.center
            off = 8
            pygame.draw.line(screen, VIOLET,
                             (cx - off, cy - off), (cx + off, cy + off), 3)
            pygame.draw.line(screen, VIOLET,
                             (cx - off, cy + off), (cx + off, cy - off), 3)
        else:
            hr = close_btn.inflate(4, 4)
            pygame.draw.rect(screen, YELLOW_BG, hr)
            cx, cy = close_btn.center
            off = 8
            pygame.draw.line(screen, BLACK,
                             (cx - off, cy - off), (cx + off, cy + off), 3)
            pygame.draw.line(screen, BLACK,
                             (cx - off, cy + off), (cx + off, cy - off), 3)

        is_hover_min = min_btn.collidepoint(mx, my)
        if is_hover_min:
            hr2 = min_btn.inflate(6, 6)
            pygame.draw.rect(screen, YELLOW_BG, hr2)
            pygame.draw.rect(screen, VIOLET, hr2, 2)
            mx_c, my_c = min_btn.center
            off = 8
            pygame.draw.line(screen, BLACK,
                             (mx_c - off, my_c), (mx_c + off, my_c), 3)
        else:
            hr2 = min_btn.inflate(4, 4)
            pygame.draw.rect(screen, YELLOW_BG, hr2)
            pygame.draw.rect(screen, BLACK, hr2, 2)
            mx_c, my_c = min_btn.center
            off = 8
            pygame.draw.line(screen, BLACK,
                             (mx_c - off, my_c), (mx_c + off, my_c), 3)

        # Player name & balance
        # Player name & balance
        player_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
        player_surf = font.render(player_name, True, YELLOW_BG)
        player_rect = player_surf.get_rect()

        # ─── BALANCE DISPLAY ─────────────────────────────────────────────────────────
        balance_text = f"Balance : {globals.user_data_points}"
        balance_surf = font.render(balance_text, True, YELLOW_BG)
        balance_rect = balance_surf.get_rect()
        spacing = 10
        bp_x = 10
        bp_y = 4
        balance_border = balance_rect.inflate(bp_x, bp_y)
        balance_border.right = min_btn.left - spacing
        v_center = margin_top // 2
        player_rect.centery = v_center
        balance_border.centery = v_center
        balance_rect.left = balance_border.left + (bp_x // 2)
        balance_rect.top = balance_border.top + (bp_y // 2)
        gap = 10
        player_rect.right = balance_border.left - gap

        screen.blit(player_surf, player_rect)
        pygame.draw.rect(screen, YELLOW_BG, balance_border, 2)
        screen.blit(balance_surf, balance_rect)


        # Current date/time & wins
        current_clock = datetime.now().strftime('%H:%M:%S')
        current_date  = datetime.now().strftime('%d-%m-%Y')
        info_txt = (
            f"{current_date}  "
            f"{current_clock}   "
            f"Win:{globals.total_win_today}"
        )
        text_surf = pygame.font.Font(None, 30).render(info_txt, True, YELLOW_BG)
        screen.blit(text_surf, (20, (margin_top - text_surf.get_height()) // 2))

        # ─── Draw Left Table (possibly blinking ribbon) ───
        if blink_mode:
            elapsed_blink = time.time() - blink_start_time
            if elapsed_blink < 5.0:
                highlight_on = (int((elapsed_blink * 1000) // 500) % 2 == 0)
            else:
                blink_mode = False
                highlight_on = False

            blink_cell = segment_to_cell(globals.FORCED_SEGMENT)
            draw_left_table(
                screen, current_server_ts, labels_kjq, labels_suits,
                x0=50, y0=100 + margin_top,
                label_size=label_size, suit_size=suit_size,
                small_font=small_font,
                highlight_cell=blink_cell,
                highlight_on=highlight_on
            )
        else:
            draw_left_table(
                screen, current_server_ts, labels_kjq, labels_suits,
                x0=50, y0=100 + margin_top,
                label_size=label_size, suit_size=suit_size,
                small_font=small_font
            )

        # ─── Draw & update the wheel ───
        if blink_mode:
            elapsed_blink2 = time.time() - blink_start_time
            if elapsed_blink2 < 5.0:
                highlight_on2 = (int((elapsed_blink2 * 1000) // 500) % 2 == 0)
            else:
                highlight_on2 = False

            draw_wheel(
                screen, wheel_center, outer_radius, mid_radius, inner_radius,
                num_segments, outer_colors, mid_colors,
                labels_kjq, labels_suits,
                current_ang,
                is_spinning=spinning,
                anim_offset=anim_offset,
                result_index=result_index,
                highlight_index=globals.FORCED_SEGMENT,
                highlight_on=highlight_on2
            )
        else:
            draw_wheel(
                screen, wheel_center, outer_radius, mid_radius, inner_radius,
                num_segments, outer_colors, mid_colors,
                labels_kjq, labels_suits,
                current_ang,
                is_spinning=spinning,
                anim_offset=anim_offset,
                result_index=result_index,
                highlight_index=None,
                highlight_on=False
            )

        # ─── Draw countdown ring & timer ───
        radius = int(min(sw, sh) * 0.05)
        padding_br = 20
        center = (sw - radius - padding_br, sh - radius - padding_br)
        draw_timer_ring(screen, center, radius, remaining, CYCLE_DURATION)
        fs = int(min(sw, sh) * 0.04)
        countdown_font = pygame.font.SysFont("Arial", fs, bold=True)
        txt_surf = countdown_font.render(f"{remaining}s", True, WHITE)
        screen.blit(txt_surf, (center[0] - txt_surf.get_width() // 2,
                               center[1] - txt_surf.get_height() // 2))

        # ─── Draw “Withdraw @ HH:MM:00” ───
        draw_withdraw_time_label()

        # ─── Draw nav buttons ───
        for btn, txt in [(account_btn, "Account"),
                         (history_btn, "History"),
                         (simple_btn, "Card History")]:
            pygame.draw.rect(screen, ORANGE, btn)
            w, h = font.size(txt)
            screen.blit(
                font.render(txt, True, BLACK),
                (btn.x + (btn.width - w) // 2, btn.y + (btn.height - h) // 2)
            )

        # “History” screen
        if show_mode == 'history':
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

        # “Summary” screen
        elif show_mode == 'summary':
            total_sale = sum(float(i.get('bet_amount', 0)) for i in mapped_list)
            total_win  = sum(float(i.get('claim_point', 0)) for i in mapped_list)
            total_comm = total_sale * 0.03
            net = total_sale - total_win - total_comm
            row = {
                k.lower(): round(v, 2)
                for k, v in zip(
                    ["Total Sale", "Total Win", "Total Commission", "Net Point"],
                    [total_sale, total_win, total_comm, net]
                )
            }
            cols2 = ["Total Sale", "Total Win", "Total Commission", "Net Point"]
            draw_table(
                screen, cols2, [row], "Account",
                pygame.font.SysFont("Arial", 32, bold=True),
                small_font, sw
            )
            pygame.draw.rect(screen, ORANGE, back_btn)
            screen.blit(
                pygame.font.SysFont("Arial", 32, bold=True).render("Close", True, BLACK),
                (back_btn.x + 20, back_btn.y + 5)
            )

        # “Simple” screen
        elif show_mode == 'simple':
            cols3 = ["card_type", "ticket_serial", "bet_amount", "claim_point", "unclaim_point"]
            draw_table(
                screen, cols3, mapped_list, "Card History",
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
