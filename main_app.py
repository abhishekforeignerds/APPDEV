# main_app.py

import pygame
import sys
import math
import random
import time
import threading
import json
import requests
import os
from datetime import datetime

LAST_SPIN_FILE = "last_spin.json"

def resource_path(relative_path):
    """
    Get the absolute path to a resource, whether running as
    a PyInstaller bundle or as a normal script.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

# Number of segments
num_segments = 12

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

def launch_main_app(user_data):
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Main App - Spinning Wheel and History")

    # Darker color palette
    DARK_RED    = (150,   0,   0)
    DARKER_RED  = (100,   0,   0)
    NAVY_BLUE   = (0,    0,  100)
    DARK_BLUE   = (0,    0,   50)
    WHITE       = (255, 255, 255)
    ORANGE      = (255, 152,   0)
    BLACK       = (0,     0,    0)
    GRID        = (80,   80,   80)
    YELLOW      = (200, 200,   0)
    TABLE_BG    = (0x35, 0x0b, 0x2d)

    # Wheel configuration
    outer_radius   = 250                          # outer wheel radius
    mid_radius     = outer_radius // 2            # mid-level circle radius (125)
    inner_radius   = mid_radius // 2              # smallest circle radius (62)
    wheel_center   = (int(sw * 0.75), sh // 2)     # moved 25% toward the right

    # Colors per segment for outer (all dark red) and mid (alternating navy/dark blue)
    outer_segment_colors = [DARK_RED] * num_segments
    mid_segment_colors   = [NAVY_BLUE if i % 2 == 0 else DARK_BLUE for i in range(num_segments)]

    # Load label images for outer ring (K, J, Q)
    labels_kjq = {
        'K': pygame.image.load(resource_path("golden-k.png")).convert_alpha(),
        'J': pygame.image.load(resource_path("golden-j.png")).convert_alpha(),
        'Q': pygame.image.load(resource_path("golden-q.png")).convert_alpha(),
    }
    # Resize K/J/Q labels
    label_size = 40
    for key in labels_kjq:
        labels_kjq[key] = pygame.transform.smoothscale(labels_kjq[key], (label_size, label_size))

    # Load suit images for mid-level circle (Clubs, Diamond, Hearts, Spades)
    labels_suits = {
        'Clubs':   pygame.image.load(resource_path("golden-clubs.png")).convert_alpha(),
        'Diamond': pygame.image.load(resource_path("golden-diamond.png")).convert_alpha(),
        'Hearts':  pygame.image.load(resource_path("golden-hearts.png")).convert_alpha(),
        'Spades':  pygame.image.load(resource_path("golden-spades.png")).convert_alpha(),
    }
    # Resize suit icons
    suit_size = 32
    for key in labels_suits:
        labels_suits[key] = pygame.transform.smoothscale(labels_suits[key], (suit_size, suit_size))

    # Load background from bundled resource
    bg_path = resource_path("overlay-bg.jpg")
    background_img = pygame.image.load(bg_path).convert()
    background_img = pygame.transform.scale(background_img, (sw, sh))

    # Fonts
    font       = pygame.font.SysFont("Arial", 24, bold=True)
    big_font   = pygame.font.SysFont("Arial", 32, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)

    clock = pygame.time.Clock()

    # Window control & navigation buttons
    padding   = 10
    icon_size = 30
    close_btn = pygame.Rect(sw - icon_size - padding, padding, icon_size, icon_size)
    min_btn   = pygame.Rect(close_btn.x - 20, padding + 5, 20, 20)

    btn_w, btn_h, pad = 140, 40, 10
    top_y = int(sh * 0.1)
    total_w = btn_w * 3 + pad * 2
    start_x = sw - pad - total_w
    account_btn = pygame.Rect(start_x,                top_y, btn_w, btn_h)
    history_btn = pygame.Rect(start_x + (btn_w + pad),  top_y, btn_w, btn_h)
    simple_btn  = pygame.Rect(start_x + 2 * (btn_w + pad), top_y, btn_w, btn_h)
    back_btn    = pygame.Rect(50, sh - 70, 100, 40)

    # State variables for spinning
    last_fetch     = time.time()
    # Load last_auto_spin from file (persisted)
    persisted_ts = load_last_spin_timestamp()
    if persisted_ts is None:
        last_auto_spin = time.time()
    else:
        last_auto_spin = persisted_ts

    mapped_list    = []
    show_mode      = 'wheel'
    spinning       = False
    current_ang    = 0.0
    spin_start     = 0.0
    total_rotation = 0.0

    def draw_text_center(surf, text, fnt, col, pos):
        txt = fnt.render(text, True, col)
        rect = txt.get_rect(center=pos)
        surf.blit(txt, rect)

    def draw_text_left(surf, text, fnt, col, pos):
        txt = fnt.render(text, True, col)
        surf.blit(txt, pos)

    def draw_pointer(surf):
        p = (wheel_center[0], wheel_center[1] - outer_radius - 10)
        l = (p[0] - 10, p[1] + 20)
        r = (p[0] + 10, p[1] + 20)
        pygame.draw.polygon(surf, ORANGE, [p, l, r])

    def draw_table(surf, cols, rows, title):
        m = 20
        tw = sw - 2 * m
        cw = tw // len(cols)
        hh, rh = 40, 30
        surf.fill(TABLE_BG)
        draw_text_center(surf, title, big_font, ORANGE, (sw // 2, m + hh // 2))
        # headers
        for i, h in enumerate(cols):
            x = m + i * cw
            pygame.draw.rect(surf, YELLOW, (x, m, cw, hh))
            lab = small_font.render(h, True, WHITE)
            surf.blit(lab, (x + 5, m + (hh - lab.get_height()) // 2))
        # grid & rows
        for r in range(len(rows) + 1):
            y = m + hh + r * rh
            pygame.draw.line(surf, GRID, (m, y), (m + tw, y))
        for c in range(len(cols) + 1):
            x = m + c * cw
            pygame.draw.line(surf, GRID, (x, m), (x, m + hh + rh * len(rows)))
        for ridx, row in enumerate(rows):
            for cidx, key in enumerate(cols):
                txt = str(row.get(key.lower(), ''))
                surf.blit(
                    small_font.render(txt, True, WHITE),
                    (m + cidx * cw + 5, m + hh + ridx * rh + 5)
                )
        pygame.draw.rect(surf, ORANGE, back_btn)
        draw_text_center(surf, "Close", big_font, BLACK, back_btn.center)

    def draw_left_table(surf, now):
        """
        Draw a table on the left side with borders. Layout:
        - 5 columns: first column wide for text or rank image; next 4 columns are narrower.
        - 4 rows: header row (Withdraw time + 4 suit icons) and 3 rows for K/Q/J images paired with suits.
        """
        x0 = 50
        y0 = 100
        # Define column widths and uniform row height
        col_widths = [200, 75, 75, 75, 75]
        cell_height = 50
        rows = 4
        cols = 5

        # Draw cell borders
        # Vertical lines
        x = x0
        for w in col_widths:
            pygame.draw.line(surf, WHITE, (x, y0), (x, y0 + rows * cell_height), 2)
            x += w
        pygame.draw.line(surf, WHITE, (x, y0), (x, y0 + rows * cell_height), 2)

        # Horizontal lines
        y = y0
        for _ in range(rows + 1):
            pygame.draw.line(surf, WHITE, (x0, y), (x0 + sum(col_widths), y), 2)
            y += cell_height

        # Row 0: "Withdraw time : HH:MM:SS" in col 0; suits in cols 1-4
        time_str = datetime.fromtimestamp(now).strftime("%H:%M:%S")
        text = f"Withdraw time: {time_str}"
        # Center text within first cell
        cell_rect = pygame.Rect(x0, y0, col_widths[0], cell_height)
        draw_text_center(surf, text, small_font, WHITE, cell_rect.center)

        suit_order = ['Spades', 'Diamond', 'Clubs', 'Hearts']
        for i, suit in enumerate(suit_order, start=1):
            img = labels_suits[suit]
            cell_x = x0 + sum(col_widths[:i])
            cell_y = y0
            cell_rect = pygame.Rect(cell_x, cell_y, col_widths[i], cell_height)
            # Center suit image
            rect = img.get_rect(center=cell_rect.center)
            surf.blit(img, rect)

        # Rows 1-3: rank + (rank+suit) pairs
        ranks = ['K', 'Q', 'J']
        for ridx, rank in enumerate(ranks, start=1):
            # Column 0: rank image centered
            img_rank = labels_kjq[rank]
            cell_x = x0
            cell_y = y0 + ridx * cell_height
            cell_rect = pygame.Rect(cell_x, cell_y, col_widths[0], cell_height)
            rect_rank = img_rank.get_rect(center=cell_rect.center)
            surf.blit(img_rank, rect_rank)

            # Columns 1-4: in each cell, place rank then suit side by side
            for cidx, suit in enumerate(suit_order, start=1):
                img_suit = labels_suits[suit]
                cell_x = x0 + sum(col_widths[:cidx])
                cell_y = y0 + ridx * cell_height
                cell_rect = pygame.Rect(cell_x, cell_y, col_widths[cidx], cell_height)
                # Compute positions so that both images fit inside cell with small gap
                total_width = label_size + suit_size + 10  # 10 px gap
                start_x = cell_rect.centerx - total_width / 2
                y_center = cell_rect.centery
                # Draw rank
                rect_rank = img_rank.get_rect(center=(start_x + label_size / 2, y_center))
                surf.blit(img_rank, rect_rank)
                # Draw suit next to rank
                rect_suit = img_suit.get_rect(center=(start_x + label_size + 10 + suit_size / 2, y_center))
                surf.blit(img_suit, rect_suit)

    def draw_wheel(surf, now):
        nonlocal spinning, current_ang, spin_start, total_rotation, last_auto_spin

        # Update current_ang during spin
        if spinning:
            elapsed = now - spin_start
            duration = 4.0  # total spin time in seconds
            if elapsed >= duration:
                elapsed = duration
            # First 3 seconds: linear until 75% of total_rotation
            if elapsed <= 3.0:
                t = elapsed / 3.0
                angle_part = (total_rotation * 0.75) * t
            else:
                # Last 1 second: quadratic ease-out for remaining 25%
                u = (elapsed - 3.0) / 1.0
                eased_u = 1 - (1 - u) * (1 - u)
                angle_part = (total_rotation * 0.75) + (total_rotation * 0.25) * eased_u
            current_ang = angle_part % 360
            if elapsed >= duration:
                spinning = False
                # Compute winning segment index (centered)
                win_seg = int(((360 - current_ang + (360/num_segments)/2) % 360) // (360/num_segments))
                print("Wheel stopped on segment:", win_seg)

        # 1) Draw outer ring segments (dark red) with black borders
        for i in range(num_segments):
            start_angle = math.radians(i * 360 / num_segments + current_ang)
            end_angle   = start_angle + math.radians(360 / num_segments)
            pts         = [wheel_center]
            for step in range(31):
                a = start_angle + (end_angle - start_angle) * (step / 30)
                x = wheel_center[0] + outer_radius * math.cos(a)
                y = wheel_center[1] + outer_radius * math.sin(a)
                pts.append((x, y))
            pygame.draw.polygon(surf, outer_segment_colors[i], pts)
            pygame.draw.polygon(surf, BLACK, pts, 2)

        # Draw K/J/Q images on outer circle at centers between segments
        for i in range(num_segments):
            rank_list = ['K', 'J', 'Q']
            img = labels_kjq[rank_list[i % 3]]
            angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
            pos_x = wheel_center[0] + (outer_radius * 0.7) * math.cos(angle)
            pos_y = wheel_center[1] + (outer_radius * 0.7) * math.sin(angle)
            rect = img.get_rect(center=(pos_x, pos_y))
            surf.blit(img, rect)

        # 2) Draw mid-level segmented circle (alternating navy/dark blue) with black borders
        for i in range(num_segments):
            start_angle = math.radians(i * 360 / num_segments + current_ang)
            end_angle   = start_angle + math.radians(360 / num_segments)
            pts         = [wheel_center]
            for step in range(31):
                a = start_angle + (end_angle - start_angle) * (step / 30)
                x = wheel_center[0] + mid_radius * math.cos(a)
                y = wheel_center[1] + mid_radius * math.sin(a)
                pts.append((x, y))
            pygame.draw.polygon(surf, mid_segment_colors[i], pts)
            pygame.draw.polygon(surf, BLACK, pts, 2)

        # Draw suit images on mid-level circle just inside its circumference
        suit_list = ['Spades', 'Diamond', 'Clubs', 'Hearts']
        for i in range(num_segments):
            img = labels_suits[suit_list[i % 4]]
            angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
            pos_x = wheel_center[0] + (mid_radius * 0.85) * math.cos(angle)
            pos_y = wheel_center[1] + (mid_radius * 0.85) * math.sin(angle)
            rect = img.get_rect(center=(pos_x, pos_y))
            surf.blit(img, rect)

        # 3) Draw innermost solid circle (white) with black border (no segments, no images)
        pygame.draw.circle(surf, WHITE, wheel_center, inner_radius)
        pygame.draw.circle(surf, BLACK, wheel_center, inner_radius, 2)

        # 4) Draw countdown until next auto-spin below the wheel
        next_spin_in = max(0, 20 - int(now - last_auto_spin))
        countdown_text = f"Next spin in: {next_spin_in}s"
        draw_text_center(surf, countdown_text, font,
                         WHITE, (wheel_center[0], wheel_center[1] + outer_radius + 30))

    # Background thread to fetch API data every 2 seconds
    def api_fetch_loop():
        nonlocal mapped_list, last_fetch, last_auto_spin
        while True:
            time.sleep(2)
            try:
                resp = requests.post(
                    "https://spintofortune.in/api/app_dashboard_data.php",
                    data={"ID": str(user_data["id"])}
                )
                data = resp.json()
                mapped_list = data.get("mapped", [])
                server_last = data.get("last_spin_timestamp")
                if server_last is not None:
                    last_auto_spin = server_last
                    save_last_spin_timestamp(last_auto_spin)
            except:
                pass

    threading.Thread(target=api_fetch_loop, daemon=True).start()

    # Main loop
    while True:
        now = time.time()

        # auto-spin every 20 seconds if on wheel mode
        if show_mode == 'wheel' and not spinning and now - last_auto_spin >= 20:
            spins = random.randint(3, 6)
            seg_index = random.randint(0, num_segments - 1)
            half_seg = 360 / (2 * num_segments)
            final = seg_index * (360 / num_segments) + half_seg
            total_rotation = spins * 360 + final
            spin_start = now
            spinning = True
            last_auto_spin = now
            save_last_spin_timestamp(last_auto_spin)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if close_btn.collidepoint(ev.pos):
                    pygame.quit(); sys.exit()
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
                    if back_btn.collidepoint(ev.pos):
                        show_mode = 'wheel'

        screen.fill(BLACK)

        if show_mode == 'wheel':
            screen.blit(background_img, (0, 0))
            draw_text_center(
                screen,
                f"ID:{user_data['id']}  User:{user_data['username']}  "
                f"Name:{user_data.get('first_name','')} {user_data.get('last_name','')}  "
                f"Pts:{user_data.get('points',0)}  Win:{user_data.get('winning_points',0)}",
                font, WHITE, (200, 30)
            )

            # Draw the left-side table with borders
            draw_left_table(screen, now)

            # Draw the wheel and pointer
            draw_wheel(screen, now)
            draw_pointer(screen)

            for btn, txt in ((account_btn, "Account"), (history_btn, "History"), (simple_btn, "Card History")):
                pygame.draw.rect(screen, ORANGE, btn)
                draw_text_center(screen, txt, font, BLACK, btn.center)

        elif show_mode == 'history':
            cols = ["card_type", "ticket_serial", "bet_amount", "claim_point", "unclaim_point", "status", "action"]
            draw_table(screen, cols, mapped_list, "History")

        elif show_mode == 'summary':
            total_sale       = sum(float(item.get('bet_amount', 0)) for item in mapped_list)
            total_win        = sum(float(item.get('claim_point', 0)) for item in mapped_list)
            total_commission = total_sale * 0.03
            net_point        = total_sale - total_win - total_commission
            cols = ["Total Sale", "Total Win", "Total Commission", "Net Point"]
            row  = {k.lower(): round(v, 2) for k, v in zip(cols, [total_sale, total_win, total_commission, net_point])}
            draw_table(screen, cols, [row], "Account")

        else:  # simple/card history
            cols = ["card_type", "ticket_serial", "bet_amount", "claim_point", "unclaim_point"]
            draw_table(screen, cols, mapped_list, "Card History")

        # Draw window controls
        pygame.draw.rect(screen, DARKER_RED, close_btn)
        draw_text_center(screen, "X", font, WHITE, close_btn.center)
        pygame.draw.rect(screen, BLACK, min_btn)
        ly = min_btn.y + min_btn.height // 2
        pygame.draw.line(screen, WHITE, (min_btn.x + 2, ly), (min_btn.x + min_btn.width - 2, ly), 2)

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
