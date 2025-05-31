import pygame
import pygame.gfxdraw
import requests
import math
import sys
import json
import platform
import subprocess


from datetime import datetime
import globals
new_withdraw_time = None

def print_withdraw_time():
    # This will only run when you explicitly call it, so by then main_app.py has set it
    print("Withdraw_time (from wheel_module):", globals.Withdraw_time)
    new_withdraw_time = globals.Withdraw_time

# --------------------------------------------------
# COLORS
# --------------------------------------------------
WHITE    = (255, 255, 255)
RED      = (200, 30, 30)
TABLE_BG = (0x35, 0x0b, 0x2d)
GRID     = (80, 80, 80)
BLUE_BG  = (30, 60, 200)
BUTTON_BG = (50, 50, 50)
BUTTON_BORDER = (200, 200, 200)

# --------------------------------------------------
# GLOBAL STATE FOR CHIP SELECTION / PLACEMENT
# --------------------------------------------------
selected_chip = None  # Index of the currently selected chip in the tray
placed_chips = {}     # key: (row, col), value: total amount in that cell

chip_rects = []
cell_rects = {}
rank_icon_rects = {}
suit_icon_rects = {}
bet_button_rect = None  # Will hold pygame.Rect for the "Bet" button

# --------------------------------------------------
# CHIP DEFINITIONS (color + amount)
# --------------------------------------------------
chip_defs = [
    {'color': (200, 0, 0),   'amount': 10},
    {'color': (0, 150, 0),   'amount': 50},
    {'color': (0, 0, 200),   'amount': 100},
    {'color': (200, 200, 0), 'amount': 500},
]

# --------------------------------------------------
# DRAW FUNCTIONS
# --------------------------------------------------

import platform
import json
import subprocess

def print_json_silent(data_dict, printer_name=None):
    """
    Sends the given Python dictionary (as pretty-printed JSON) directly to the default printer,
    without any user‐visible dialog. Works on Windows and on Linux/macOS.

    – data_dict: the Python dict you want to print.
    – printer_name (optional): a string name of a specific printer. If omitted, uses the system default.
    """

    # Serialize your dict to a JSON string
    json_text = json.dumps(data_dict, indent=2)
    system = platform.system()
    print(f"[Printer] Detected OS: {system}")

    if system == "Windows":
        # ---------------------
        # Windows (silent, using win32print)
        # ---------------------
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            import win32print
        except ImportError:
            print("[Printer][Error] On Windows, silent printing requires 'pywin32'.")
            print("[Printer][Error] Please install it with: pip install pywin32")
            return

        # 1) Determine which printer to open:
        try:
            if printer_name:
                printer_to_open = printer_name
            else:
                printer_to_open = win32print.GetDefaultPrinter() or ""
        except Exception as e:
            print(f"[Printer][Error] Could not retrieve default printer: {e}")
            return

        if not printer_to_open:
            print("[Printer] No default printer found on the system.")
            return
        else:
            print(f"[Printer] Found printer: '{printer_to_open}'. Sending job now...")

        # 2) Open the printer handle
        try:
            hPrinter = win32print.OpenPrinter(printer_to_open)
        except Exception as e:
            print(f"[Printer][Error] Could not open printer '{printer_to_open}': {e}")
            return

        # 3) Prepare document information (RAW means we send bytes directly)
        doc_info = (
            "JSON Print Job",  # Arbitrary document name
            None,              # No output file: print straight to printer
            "RAW"              # DataType = RAW → print bytes as-is
        )

        try:
            job_id = win32print.StartDocPrinter(hPrinter, 1, doc_info)
            win32print.StartPagePrinter(hPrinter)

            # Send JSON bytes
            win32print.WritePrinter(hPrinter, json_text.encode("utf-8"))

            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            print(f"[Printer] Print job #{job_id} completed successfully on '{printer_to_open}'.")
        except Exception as e:
            print(f"[Printer][Error] Failed during printing to '{printer_to_open}': {e}")
        finally:
            win32print.ClosePrinter(hPrinter)


    elif system in ("Linux", "Darwin"):
        # ---------------------
        # Linux / macOS (silent, using lpr)
        # ---------------------
        # We pipe the JSON text directly into lpr’s stdin. No temp file needed.
        cmd = ["lpr"]
        if printer_name:
            cmd += ["-P", printer_name]

        # Before running lpr, let's check if 'lpr' exists in PATH
        from shutil import which
        if which("lpr") is None:
            print("[Printer][Error] 'lpr' command not found.")
            print("[Printer][Error] On Linux/macOS, install CUPS / lpr utilities.")
            print("  • Ubuntu/Debian: sudo apt install cups lpr")
            print("  • Fedora/CentOS: sudo dnf install cups lpr")
            print("  • macOS: ensure CUPS is enabled in System Preferences → Printers & Scanners")
            return

        # Determine target printer name for status message
        target = printer_name or "<default>"
        print(f"[Printer] Sending job to {target} (via 'lpr').")

        try:
            # Pipe JSON text into lpr
            proc = subprocess.run(
                cmd,
                input=json_text.encode("utf-8"),
                check=True,
                capture_output=True
            )
            print(f"[Printer] Job sent to printer {target} successfully.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
            print(f"[Printer][Error] lpr failed with exit code {e.returncode}.")
            if stderr:
                print(f"[Printer][Error] lpr stderr: {stderr.strip()}")
            else:
                print("[Printer][Error] No additional error output from lpr.")
        except Exception as exc:
            print(f"[Printer][Error] Unexpected error while calling lpr: {exc}")

    else:
        print(f"[Printer][Error] Unsupported OS for silent printing: {system}")


def draw_wheel(surf, wheel_center, outer_radius, mid_radius, inner_radius,
               num_segments, outer_segment_colors, mid_segment_colors,
               labels_kjq, labels_suits, current_ang):
    """
    Draw the spinning wheel with outer K/J/Q icons and mid‐level suits,
    preserving segment count and original TABLE_BG background.
    """
    pygame.gfxdraw.filled_circle(surf, wheel_center[0], wheel_center[1], outer_radius, TABLE_BG)
    pygame.gfxdraw.aacircle(surf, wheel_center[0], wheel_center[1], outer_radius, GRID)

    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments + current_ang)
        end   = start + math.radians(360 / num_segments)
        pts   = [wheel_center]
        steps = 60
        for s in range(steps + 1):
            a = start + (end - start) * (s / steps)
            x = wheel_center[0] + outer_radius * math.cos(a)
            y = wheel_center[1] + outer_radius * math.sin(a)
            pts.append((int(x), int(y)))
        pygame.gfxdraw.filled_polygon(surf, pts, outer_segment_colors[i])
        pygame.gfxdraw.aapolygon(surf, pts, (0, 0, 0))

    ranks = ['K', 'J', 'Q']
    for i in range(num_segments):
        img   = labels_kjq[ranks[i % 3]]
        angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
        pos   = (
            int(wheel_center[0] + outer_radius * 0.7 * math.cos(angle)),
            int(wheel_center[1] + outer_radius * 0.7 * math.sin(angle))
        )
        surf.blit(img, img.get_rect(center=pos))

    pygame.gfxdraw.filled_circle(surf, wheel_center[0], wheel_center[1], mid_radius, TABLE_BG)
    pygame.gfxdraw.aacircle(surf, wheel_center[0], wheel_center[1], mid_radius, GRID)

    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments + current_ang)
        end   = start + math.radians(360 / num_segments)
        pts   = [wheel_center]
        steps = 60
        for s in range(steps + 1):
            a = start + (end - start) * (s / steps)
            x = wheel_center[0] + mid_radius * math.cos(a)
            y = wheel_center[1] + mid_radius * math.sin(a)
            pts.append((int(x), int(y)))
        pygame.gfxdraw.filled_polygon(surf, pts, mid_segment_colors[i])
        pygame.gfxdraw.aapolygon(surf, pts, (0, 0, 0))

    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    for i in range(num_segments):
        img   = labels_suits[suits[i % 4]]
        angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
        pos   = (
            int(wheel_center[0] + mid_radius * 0.85 * math.cos(angle)),
            int(wheel_center[1] + mid_radius * 0.85 * math.sin(angle))
        )
        surf.blit(img, img.get_rect(center=pos))

    pygame.gfxdraw.filled_circle(surf, wheel_center[0], wheel_center[1], inner_radius, WHITE)
    pygame.gfxdraw.aacircle(surf, wheel_center[0], wheel_center[1], inner_radius, (0, 0, 0))


def update_spin(current_time, spin_start, total_rotation):
    """
    Returns (angle_deg % 360, spinning_flag) based on a 4‐second animation:
     - first 3s: linear from 0 to 75% of total_rotation
     - last 1s: ease‐out from 75% to 100% of total_rotation
    """
    duration = 4.0
    elapsed  = min(current_time - spin_start, duration)

    if elapsed <= 3.0:
        t = elapsed / 3.0
        ang = (total_rotation * 0.75) * t
        spinning = True
    else:
        u     = (elapsed - 3.0) / 1.0
        eased = 1 - (1 - u) * (1 - u)
        ang   = (total_rotation * 0.75) + (total_rotation * 0.25) * eased
        spinning = elapsed < duration

    return ang % 360, spinning


def draw_left_table(
    surf,
    now_ts,
    labels_kjq,
    labels_suits,
    x0,
    y0,
    label_size,
    suit_size,
    small_font,
    rows=4,
    cols=5
):
    """
    Draws:
      1) A table of blue cells (rows × cols) with a “Withdraw time” header row
         (suit icons) and a rank column (K/Q/J).
      2) A tray of chips below the table.
      3) Any chips that have been placed on the blue cells, showing their total amount.
      4) A visible text displaying the current total bet.
      5) A “Bet” button to submit placed bets via POST.

    SIDE EFFECTS (globals):
      - chip_rects: list of pygame.Rect for each chip in the tray
      - cell_rects: dict mapping (ridx, cidx) → pygame.Rect of each blue cell
      - rank_icon_rects: dict mapping ridx → pygame.Rect of each rank icon
      - suit_icon_rects: dict mapping cidx → pygame.Rect of each suit icon
      - bet_button_rect: pygame.Rect defining the “Bet” button area
    """
    global chip_rects, cell_rects, rank_icon_rects, suit_icon_rects, bet_button_rect
    chip_rects       = []
    cell_rects       = {}
    rank_icon_rects  = {}
    suit_icon_rects  = {}
    bet_button_rect  = None

    sw, sh    = surf.get_size()
    table_w   = int(sw * 0.48)
    table_h   = int(sh * 0.60)
    cell_h    = table_h // rows
    col_w     = table_w // cols
    radius    = 8

    # 1) Draw table background & grid lines
    table_rect = pygame.Rect(x0, y0, table_w, table_h)
    pygame.draw.rect(surf, TABLE_BG, table_rect)

    for i in range(cols + 1):
        x = x0 + i * col_w
        pygame.draw.line(surf, WHITE, (x, y0), (x, y0 + table_h), 2)
    for j in range(rows + 1):
        y = y0 + j * cell_h
        pygame.draw.line(surf, WHITE, (x0, y), (x0 + table_w, y), 2)

    # 2) Header row: “Withdraw time” + live clock + suit icons
    time_str = datetime.fromtimestamp(now_ts).strftime("%H:%M:%S")
    surf.blit(small_font.render("Withdraw time:", True, WHITE), (x0 + 10, y0 + 5))
    surf.blit(small_font.render(globals.Withdraw_time, True, WHITE), (x0 + 10, y0 + 25))

    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    for i, suit in enumerate(suits, start=1):
        cell = pygame.Rect(x0 + col_w * i, y0, col_w, cell_h)
        img  = pygame.transform.smoothscale(labels_suits[suit], (suit_size, suit_size))
        surf.blit(img, img.get_rect(center=cell.center))
        suit_icon_rects[i] = cell

    # 3) Draw rank‐column and each blue “play” cell
    ribbon_font = pygame.font.Font(None, max(8, int(small_font.get_height() * 0.8)))
    ranks = ['K', 'Q', 'J']

    for ridx, rank in enumerate(ranks, start=1):
        cell_rank = pygame.Rect(x0, y0 + ridx * cell_h, col_w, cell_h)
        img_rank  = pygame.transform.smoothscale(labels_kjq[rank], (label_size, label_size))
        surf.blit(img_rank, img_rank.get_rect(center=cell_rank.center))
        rank_icon_rects[ridx] = cell_rank

        for cidx, suit in enumerate(suits, start=1):
            cell = pygame.Rect(
                x0 + col_w * cidx,
                y0 + ridx * cell_h,
                col_w,
                cell_h
            )
            box_w = col_w * 0.7
            box_h = cell_h * 0.9
            inset_x = cell.left + (col_w - box_w) / 2
            inset_y = cell.top  + (cell_h - box_h) / 2
            blue_box = pygame.Rect(int(inset_x), int(inset_y), int(box_w), int(box_h))

            cell_rects[(ridx, cidx)] = blue_box

            pygame.draw.rect(surf, BLUE_BG, blue_box, border_radius=radius)
            pygame.draw.rect(surf, WHITE, blue_box, 2, border_radius=radius)

            total_w = label_size + suit_size + 8
            yc = blue_box.centery
            surf.blit(
                img_rank,
                img_rank.get_rect(
                    center=(int(blue_box.centerx - total_w/2 + label_size/2), yc)
                )
            )
            img_s = pygame.transform.smoothscale(labels_suits[suit], (suit_size, suit_size))
            surf.blit(
                img_s,
                img_s.get_rect(
                    center=(int(blue_box.centerx - total_w/2 + label_size + 8 + suit_size/2), yc)
                )
            )

            ribbon_h = box_h * 0.2
            ribbon_w = box_w * 1.05
            ribbon_x = blue_box.left - (ribbon_w - box_w) / 2
            ribbon_y = blue_box.bottom - ribbon_h
            ribbon_rect = pygame.Rect(int(ribbon_x), int(ribbon_y), int(ribbon_w), int(ribbon_h))

            pygame.gfxdraw.filled_polygon(
                surf,
                [ribbon_rect.topleft, ribbon_rect.topright,
                 ribbon_rect.bottomright, ribbon_rect.bottomleft],
                RED
            )
            pygame.gfxdraw.aapolygon(
                surf,
                [ribbon_rect.topleft, ribbon_rect.topright,
                 ribbon_rect.bottomright, ribbon_rect.bottomleft],
                WHITE
            )

            play_surf = ribbon_font.render("Play", True, WHITE)
            surf.blit(
                play_surf,
                (
                    ribbon_rect.left + (ribbon_w - play_surf.get_width()) / 2,
                    ribbon_rect.top  + (ribbon_h - play_surf.get_height()) / 2
                )
            )

    # 4) Draw all placed chips on the table
    for (ridx, cidx), total_amt in placed_chips.items():
        if (ridx, cidx) in cell_rects:
            center_x = cell_rects[(ridx, cidx)].centerx
            center_y = cell_rects[(ridx, cidx)].centery
            chip_radius = min(cell_h, col_w) // 6
            pygame.gfxdraw.filled_circle(surf, center_x, center_y, chip_radius, chip_defs[0]['color'])
            pygame.gfxdraw.aacircle(surf, center_x, center_y, chip_radius, WHITE)
            amt_surf = small_font.render(str(total_amt), True, WHITE)
            surf.blit(amt_surf, amt_surf.get_rect(center=(center_x, center_y)))

    # 5) Draw chip “tray” below the table
    chip_radius = min(cell_h, col_w) // 6
    chip_dia    = chip_radius * 2
    chip_spacing= chip_dia + 10
    start_x     = x0 + 10
    chips_y     = y0 + table_h + chip_radius + 20

    angle = (now_ts * 360) % 360

    for idx, chip in enumerate(chip_defs):
        cx = start_x + idx * chip_spacing
        cy = chips_y

        base_chip_surf = pygame.Surface((chip_dia, chip_dia), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(base_chip_surf, chip_radius, chip_radius, chip_radius, chip['color'])
        pygame.gfxdraw.aacircle(base_chip_surf, chip_radius, chip_radius, chip_radius, WHITE)
        amt_surf = small_font.render(str(chip['amount']), True, WHITE)
        base_chip_surf.blit(amt_surf, amt_surf.get_rect(center=(chip_radius, chip_radius)))

        if selected_chip == idx:
            rotated_surf = pygame.transform.rotate(base_chip_surf, angle)
            rotated_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
            surf.blit(rotated_surf, rotated_rect)
            chip_rects.append(pygame.Rect(int(cx - chip_radius), int(cy - chip_radius), chip_dia, chip_dia))
        else:
            surf.blit(base_chip_surf, base_chip_surf.get_rect(center=(int(cx), int(cy))))
            chip_rects.append(pygame.Rect(int(cx - chip_radius), int(cy - chip_radius), chip_dia, chip_dia))

    # 6) Draw “Current Bet” text
    total_bet = sum(placed_chips.values())
    bet_text = small_font.render(f"Current Bet: {total_bet}", True, WHITE)
    surf.blit(bet_text, (x0 + 10, chips_y + chip_dia + 10))
    text_h = small_font.get_height()

    # 7) Draw “Bet” button below the text
    btn_w, btn_h = 100, 30
    btn_x = x0 + 10
    btn_y = chips_y + chip_dia + 10 + text_h + 10
    bet_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surf, BUTTON_BG, bet_button_rect, border_radius=4)
    pygame.draw.rect(surf, BUTTON_BORDER, bet_button_rect, 2, border_radius=4)
    btn_txt = small_font.render("Bet", True, WHITE)
    surf.blit(btn_txt, btn_txt.get_rect(center=bet_button_rect.center))


def handle_click(mouse_pos):
    """
    Must be called from your main loop on MOUSEBUTTONDOWN.

    1) If the user clicks on a tray‐chip, that becomes selected.
    2) If the user clicks on the “Bet” button, send placed_chips as JSON via POST:
       • Endpoint: http://spintofortune.in/api/app_place_bet.php
       • JSON body: { "bets": { "r_c": amount, ... } }
       • Print the JSON response from the API.
    3) If a chip is selected and the user clicks on:
       • A rank icon (K/Q/J) → add amount to each cell in that row.
       • A suit icon    → add amount to each cell in that column.
       • Any individual blue cell → add amount there.
       Selection remains after placing.
    4) Click elsewhere → deselect.
    """
    global selected_chip, placed_chips

    # 1) Bet button
    if bet_button_rect and bet_button_rect.collidepoint(mouse_pos):
        payload = {
            "bets": {f"{r}_{c}": amt for (r, c), amt in placed_chips.items()},
            "Withdraw_time": globals.Withdraw_time,
            "User_id": globals.User_id
        }
        print("→ Sending payload:", json.dumps(payload, indent=2))

        resp = requests.post(
            "https://spintofortune.in/api/app_place_bet.php",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("← Status:", resp.status_code)
        print("← Raw response text:", resp.text)
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, indent=2))
        print_json_silent(data)

        # --- clear all placed bets ---
        placed_chips.clear()
        selected_chip = None
        return

    # 2) Tray‐chip selection
    for idx, rect in enumerate(chip_rects):
        if rect.collidepoint(mouse_pos):
            selected_chip = idx
            return

    # 3) Place bets if a chip is selected
    if selected_chip is not None:
        # Rank row
        for ridx, rect in rank_icon_rects.items():
            if rect.collidepoint(mouse_pos):
                for (r, c) in cell_rects:
                    if r == ridx:
                        placed_chips[(r, c)] = placed_chips.get((r, c), 0) + chip_defs[selected_chip]['amount']
                return
        # Suit column
        for cidx, rect in suit_icon_rects.items():
            if rect.collidepoint(mouse_pos):
                for (r, c) in cell_rects:
                    if c == cidx:
                        placed_chips[(r, c)] = placed_chips.get((r, c), 0) + chip_defs[selected_chip]['amount']
                return
        # Individual cell
        for (ridx, cidx), rect in cell_rects.items():
            if rect.collidepoint(mouse_pos):
                placed_chips[(ridx, cidx)] = placed_chips.get((ridx, cidx), 0) + chip_defs[selected_chip]['amount']
                return

    # 4) Elsewhere: deselect
    selected_chip = None