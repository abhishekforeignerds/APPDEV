import os
import platform
import json
import subprocess
import sys
import io
import requests
import math
import pygame
import pygame.gfxdraw

from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

import app_globals
new_withdraw_time = None

def print_withdraw_time():
    # This will only run when you explicitly call it, so by then main_app.py has set it
    print("Withdraw_time (from wheel_module):", app_globals.Withdraw_time)
    new_withdraw_time = app_globals.Withdraw_time

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
clear_button_rect = None  # Will hold pygame.Rect for the "Bet" button
double_button_rect = None  # Will hold pygame.Rect for the "Bet" button
repeat_button_rect = None  # Will hold pygame.Rect for the "Bet" button

# --------------------------------------------------
# CHIP DEFINITIONS (color + amount)
# --------------------------------------------------
chip_defs = [
    {'color': (200, 0, 0),   'amount': 5},
    {'color': (200, 0, 0),   'amount': 10},
    {'color': (200, 0, 0),   'amount': 20},
    {'color': (0, 150, 0),   'amount': 50},
    {'color': (0, 0, 200),   'amount': 100},
    {'color': (0, 0, 200),   'amount': 200},
    {'color': (200, 200, 0), 'amount': 500},
]


# --------------------------------------------------
# DRAW FUNCTIONS
# --------------------------------------------------

import platform
import json
import subprocess

try:
    import win32api
    import win32print
except ImportError:
    win32api = None
    win32print = None


def print_json_silent(data_dict, printer_name=None):
    ticket_block = data_dict.get("data", {}).get("ticket", {})
    if not ticket_block:
        print("[Printer][Error] No 'ticket' block found in data_dict.")
        return

    ticket_id       = ticket_block.get("id", "")
    serial_number   = ticket_block.get("serial_number", "")
    user_id         = ticket_block.get("user_id", "")
    amount          = ticket_block.get("amount", "")
    withdraw_time   = ticket_block.get("created_at", "")

    game_name = "Poker Roulette 12 Cards"
    game_id   = "5678425"

    now = datetime.now()
    print_date = now.strftime("%Y-%m-%d")
    print_time = now.strftime("%H:%M:%S")

    print(f"[Printer][Info] Preparing ticket data:")
    print(f"  Ticket ID     : {ticket_id}")
    print(f"  Serial Number : {serial_number}")
    print(f"  Terminal Name : {user_id}")
    print(f"  Amount        : {amount}")
    print(f"  Withdraw Time : {withdraw_time}")
    print(f"  Print Date    : {print_date}")
    print(f"  Print Time    : {print_time}")

    base_pdf_name = f"ticket_{serial_number}"
    pdf_filename = base_pdf_name + ".pdf"
    print(f"[Printer][Info] Generating PDF: {pdf_filename}")

    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    y = height - 50

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "For Amusement Only")
    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, f"Ticket ID: {ticket_id}")
    y -= 25

    lines = [
        f"Game Name        : {game_name}",
        f"Terminal Name    : {user_id}",
        f"Game ID          : {game_id}",
        f"Withdraw Time    : {withdraw_time}",
        f"Print Date       : {print_date}",
        f"Print Time       : {print_time}",
        f"Serial Number    : {serial_number}",
        f"Amount           : {amount}",
    ]

    c.setFont("Helvetica", 12)
    for line in lines:
        print(f"[Printer][Info] Adding to PDF: {line}")
        c.drawString(50, y, line)
        y -= 20

    if serial_number:
        try:
            print(f"[Printer][Info] Generating barcode for: {serial_number}")
            barcode_obj = code128.Code128(
                serial_number,
                barHeight=20 * mm,
                barWidth=0.5 * mm
            )
            barcode_width = barcode_obj.width
            x_barcode = (width - barcode_width) / 2
            barcode_obj.drawOn(c, x_barcode, y - (20 * mm))
            y -= (20 * mm + 30)

            c.setFont("Helvetica", 10)
            print(f"[Printer][Info] Embedded barcode and serial text.")
        except Exception as e:
            print(f"[Printer][Warning] Could not generate/embed barcode: {e}")
            y -= 30
    else:
        print(f"[Printer][Warning] No serial number to generate barcode.")
        y -= 30

    footer_text = "Not For Sale"
    print(f"[Printer][Info] Adding footer to PDF: {footer_text}")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, footer_text)

    c.showPage()
    c.save()
    print(f"[Printer][Info] PDF saved: {pdf_filename}")

    system_name = platform.system()
    print(f"[Printer] Detected OS: {system_name}")

    if system_name == "Windows":
        if win32api is None or win32print is None:
            print("[Printer][Error] On Windows, silent printing requires 'pywin32'.")
            print("[Printer][Error] Install it via: pip install pywin32")
            return

        try:
            if printer_name:
                target_printer = printer_name
            else:
                target_printer = win32print.GetDefaultPrinter()
        except Exception as e:
            print(f"[Printer][Error] Could not retrieve default printer: {e}")
            return

        if not target_printer:
            print("[Printer][Error] No default printer found on Windows.")
            return

        print(f"[Printer] Using Windows printer: '{target_printer}'")

        try:
            win32api.ShellExecute(
                0,
                "printto",
                pdf_filename,
                f'"{target_printer}"',
                ".",
                0
            )
            print(f"[Printer][Info] ShellExecute 'printto' issued for '{pdf_filename}'.")
        except Exception as e:
            print(f"[Printer][Error] Failed to ShellExecute print: {e}")

    elif system_name in ("Linux", "Darwin"):
        from shutil import which
        if which("lpr") is None:
            print("[Printer][Error] 'lpr' command not found.")
            print("[Printer][Error] Install CUPS / lpr utilities.")
            return

        cmd = ["lpr", pdf_filename]
        if printer_name:
            cmd = ["lpr", "-P", printer_name, pdf_filename]

        target = printer_name or "<default>"
        print(f"[Printer] Sending PDF to {target} (via 'lpr').")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            print(f"[Printer][Info] PDF sent to printer '{target}' successfully (exit code {result.returncode}).")
        except subprocess.CalledProcessError as e:
            stderr_out = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
            print(f"[Printer][Error] lpr failed (code {e.returncode}).")
            if stderr_out:
                print(f"[Printer][Error] lpr stderr: {stderr_out.strip()}")
        except Exception as exc:
            print(f"[Printer][Error] Unexpected error calling lpr: {exc}")

    else:
        print(f"[Printer][Error] Unsupported OS for printing: {system_name}")

# --------------------------------------------------
# COLORS (feel free to tweak or replace)
# --------------------------------------------------
import pygame
import pygame.gfxdraw
import math

# Color and drawing constants
TABLE_BG             = (30, 30, 30)       # Wheel background
GRID                 = (200, 200, 200)    # Wheel segment borders
GOLDEN               = (255, 215, 0)      # “Golden” fill for the inner circle (no longer used for segments)
SHADOW_COLOR         = (0, 0, 0, 80)      # Semi-transparent black for drop shadow
RIBBON_COLOR_RGB     = (0, 0, 255)        # Blue ribbon color
RIBBON_ALPHA         = 200                # Out of 255, for slight translucency
SHADOW_OFFSET        = 8                  # Pixels to offset the wheel’s drop shadow
ANGLE_STEPS          = 120                # Increase for even smoother arcs
ARROW_COLOR          = (148, 0, 211)      # Violet for all arrows

def draw_pointer(screen, wheel_center, outer_radius):
    p = (wheel_center[0], wheel_center[1] - outer_radius - 10)
    l = (p[0] - 10, p[1] + 20)
    r = (p[0] + 10, p[1] + 20)
    pygame.draw.polygon(screen, (255, 165, 0), [p, l, r])  # ORANGE = (255, 165, 0)

def _generate_hsv_palette(num_segments, saturation=80, value=100, alpha=255):
    """
    Create a list of length num_segments of pygame.Color objects
    evenly spaced around the HSV color wheel. Alpha is constant.

    If you want to avoid a pure‐yellow (≈60°) segment, you can add an offset
    here. For example, add +30 to each hue so no index lands exactly at 60°.
    """
    palette = []
    for i in range(num_segments):
        hue = (i / num_segments) * 360
        c = pygame.Color(0)
        c.hsva = (hue, saturation, value, alpha)
        palette.append((c.r, c.g, c.b, alpha))
    return palette
import math
import pygame
from pygame import gfxdraw

# Constants
SHADOW_OFFSET = 5
SHADOW_COLOR = (0, 0, 0, 100)
TABLE_BG = (255, 255, 255)
GRID = (0, 0, 0)
RIBBON_COLOR_RGB = (0, 0, 0)
RIBBON_ALPHA = 200
GOLD = (255, 215, 0)

ANGLE_STEPS = 60

import math
import pygame
from pygame import gfxdraw
SHADOW_OFFSET    = 6
SHADOW_COLOR     = (0, 0, 0, 100)
TABLE_BG         = (16, 16, 16)
GRID             = (50, 50, 50)
ANGLE_STEPS      = 30
RIBBON_COLOR_RGB = (200, 0, 0)
RIBBON_ALPHA     = 200
GOLD             = (212, 175, 55)
RED_BG           = (200, 0, 0)      # Solid red inner circle background

# ─── WHEEL DRAWING ─────────────────────────────────────────────────────────────
def draw_wheel(
    surf,
    wheel_center,
    outer_radius,
    mid_radius,
    inner_radius,
    num_segments,
    outer_segment_colors,
    mid_segment_colors,
    labels_kjq,
    labels_suits,
    current_ang,
    is_spinning=False,
    anim_offset=0.0,
    result_index=None,
    highlight_index=None,
    highlight_on=False
):
    """
    Draws the spinning wheel onto `surf`.

    • highlight_index/highlight_on: if highlight_on=True, the outer segment at
      highlight_index is filled solid green and outlined in green.

    • While is_spinning=True: the inner circle is solid red, and one label
      (“1X” → “2X” → “3X” → “4X” → “N”) appears, cycling at ~5 labels/sec.

    • Once is_spinning=False and result_index is provided, that same red inner
      circle displays the winning segment’s rank+suit icons side-by-side, with a
      large “N” directly below them.
    """

    # 1) Recompute radii if surface size changed
    width, height = surf.get_size()
    min_dim = min(width, height)
    outer_radius = int(min_dim * 0.30)
    mid_radius   = int(min_dim * 0.18)
    inner_radius = int(min_dim * 0.08)

    # Arrow sizes (unchanged)
    inner_arrow_w = inner_arrow_h = 20
    ribbon_arrow_w = ribbon_arrow_h = 20

    # Ribbon thickness
    ribbon_thickness = max(6, int(min_dim * 0.015))
    current_rad = math.radians(current_ang)

    # If no palette provided, generate one
    if outer_segment_colors is None:
        outer_segment_colors = _generate_hsv_palette(num_segments, 75, 100, 255)

    # 2) Off-screen surface for drop shadow + drawing
    temp_size   = (outer_radius * 2 + SHADOW_OFFSET * 2,
                   outer_radius * 2 + SHADOW_OFFSET * 2)
    temp_surf   = pygame.Surface(temp_size, pygame.SRCALPHA)
    temp_center = (outer_radius + SHADOW_OFFSET,
                   outer_radius + SHADOW_OFFSET)

    # 3) Draw drop shadow
    gfxdraw.filled_circle(
        temp_surf,
        temp_center[0],
        temp_center[1] + SHADOW_OFFSET,
        outer_radius,
        SHADOW_COLOR
    )

    # 4) Draw outer wheel background + border
    gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1],
                          outer_radius, (*TABLE_BG, 255))
    gfxdraw.aacircle(temp_surf, temp_center[0], temp_center[1],
                     outer_radius, (*GRID, 255))

    # 5) Draw outer-ring segments
    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments) + current_rad
        end   = start + math.radians(360 / num_segments)
        pts   = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start + (end - start) * (s / ANGLE_STEPS)
            x = temp_center[0] + outer_radius * math.cos(a)
            y = temp_center[1] + outer_radius * math.sin(a)
            pts.append((int(x), int(y)))

        if i == highlight_index and highlight_on:
            # Fill this segment solid green and outline in green
            green_fill = (0, 255, 0)
            gfxdraw.filled_polygon(temp_surf, pts, green_fill)
            pygame.draw.polygon(temp_surf, green_fill, pts, 3)
        else:
            gfxdraw.filled_polygon(temp_surf, pts, outer_segment_colors[i])
            pygame.draw.polygon(temp_surf, GRID, pts, 1)

    # 6) Draw “K/Q/J” rank icons around the outer ring (no suit icons in outer ring)
    ranks = ['K', 'Q', 'J']
    for i in range(num_segments):
        rank = ranks[i // 4]  # 0–3→K, 4–7→Q, 8–11→J
        ang  = math.radians((i + 0.5) * 360 / num_segments) + current_rad
        rank_radius = outer_radius * 0.85
        rx = int(temp_center[0] + rank_radius * math.cos(ang))
        ry = int(temp_center[1] + rank_radius * math.sin(ang))
        rank_img = labels_kjq[rank]
        temp_surf.blit(rank_img, rank_img.get_rect(center=(rx, ry)))

    # 7) Mid-ring: white→darker gradient
    inner_grad = mid_radius - int(mid_radius * 0.3)
    for r in range(mid_radius, inner_grad, -1):
        shade = 255 - int((mid_radius - r) / (mid_radius - inner_grad) * 100)
        gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1], r,
                              (shade, shade, shade))

    # 8) Draw radial lines connecting mid ring → inner circle
    for i in range(num_segments):
        ang = math.radians(i * 360 / num_segments) + current_rad
        x1  = temp_center[0] + inner_radius * math.cos(ang)
        y1  = temp_center[1] + inner_radius * math.sin(ang)
        x2  = temp_center[0] + mid_radius * math.cos(ang)
        y2  = temp_center[1] + mid_radius * math.sin(ang)
        pygame.draw.aaline(temp_surf, GRID, (int(x1), int(y1)), (int(x2), int(y2)))

    # 9) Draw suit icons in the mid ring
    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    suit_size = int(mid_radius * 0.3)
    for i in range(num_segments):
        ang = math.radians((i + 0.5) * 360 / num_segments) + current_rad
        mx  = int(temp_center[0] + mid_radius * 0.75 * math.cos(ang))
        my  = int(temp_center[1] + mid_radius * 0.75 * math.sin(ang))
        suit = suits[i % 4]
        suit_img = pygame.transform.smoothscale(
            labels_suits[suit], (suit_size, suit_size)
        )
        temp_surf.blit(suit_img, suit_img.get_rect(center=(mx, my)))

    # 10) Inner circle:
    if is_spinning:
        # 10a) Solid red background + border
        gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1],
                              inner_radius, RED_BG)
        gfxdraw.aacircle(temp_surf, temp_center[0], temp_center[1],
                         inner_radius, (*GRID, 255))

        # 10b) Single scrolling label: ["1X", "2X", "3X", "4X", "N"]
        scroll_texts = ["1X", "2X", "3X", "4X", "N"]
        font_size = max(12, inner_radius // 2)
        tw_font = pygame.font.SysFont("Arial", font_size, bold=True)

        idx = int(anim_offset) % len(scroll_texts)
        txt = scroll_texts[idx]
        rendered = tw_font.render(txt, True, (255, 255, 255))
        text_w   = rendered.get_width()
        text_h   = rendered.get_height()
        x = temp_center[0] - text_w // 2
        y = temp_center[1] - text_h // 2
        temp_surf.blit(rendered, (x, y))

    else:
        # 10c) Once stopped → fill inner circle solid red + border
        gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1],
                              inner_radius, RED_BG)
        gfxdraw.aacircle(temp_surf, temp_center[0], temp_center[1],
                         inner_radius, (*GRID, 255))

        # 10d) If result_index is valid, draw its rank+suit icons side-by-side
        if isinstance(result_index, int) and 0 <= result_index < num_segments:
            ranks = ['K', 'Q', 'J']
            suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
            rank = ranks[result_index // 4]
            suit = suits[result_index % 4]

            # Icon dimensions: about 70% of inner_radius in height
            icon_h = int(inner_radius * 0.7)
            icon_w = icon_h  # square
            rank_img = pygame.transform.smoothscale(labels_kjq[rank], (icon_w, icon_h))
            suit_img = pygame.transform.smoothscale(labels_suits[suit], (icon_w, icon_h))

            # Place side-by-side, with 10px gap
            total_width = icon_w * 2 + 10
            left_x = temp_center[0] - total_width // 2
            rank_rect = rank_img.get_rect(center=(left_x + icon_w // 2, temp_center[1]))
            suit_rect = suit_img.get_rect(center=(left_x + icon_w + 10 + icon_w // 2, temp_center[1]))
            temp_surf.blit(rank_img, rank_rect)
            temp_surf.blit(suit_img, suit_rect)

            # Draw letter “N” just below the icons
            font_n = pygame.font.SysFont("Arial", max(16, inner_radius // 3), bold=True)
            text_n = font_n.render("N", True, (255, 255, 255))
            text_rect = text_n.get_rect(center=(temp_center[0], temp_center[1] + icon_h // 2 + 15))
            temp_surf.blit(text_n, text_rect)

    # 11) Draw ribbon (outermost border circle)
    ribbon_rad   = outer_radius + ribbon_thickness // 2
    ribbon_color = (*RIBBON_COLOR_RGB, RIBBON_ALPHA)
    gfxdraw.aacircle(
        temp_surf, temp_center[0], temp_center[1],
        ribbon_rad, ribbon_color
    )
    pygame.draw.circle(temp_surf, ribbon_color, temp_center,
                       ribbon_rad, ribbon_thickness)

    # 12) Dots/arrows on the ribbon (unchanged)
    inner_edge = ribbon_rad - ribbon_thickness // 2
    for i in range(num_segments):
        ang = math.radians(i * 360 / num_segments)
        if i % 2 == 0:
            px = int(temp_center[0] + inner_edge * math.cos(ang))
            py = int(temp_center[1] + inner_edge * math.sin(ang))
            gfxdraw.filled_circle(
                temp_surf, px, py,
                ribbon_thickness // 2 + 2, (*GOLD, 255)
            )
        else:
            tip_r  = inner_edge - ribbon_arrow_h
            base_r = inner_edge
            tip = (
                int(temp_center[0] + tip_r * math.cos(ang)),
                int(temp_center[1] + tip_r * math.sin(ang))
            )
            bx = temp_center[0] + base_r * math.cos(ang)
            by = temp_center[1] + base_r * math.sin(ang)
            perp_dx = (ribbon_arrow_w / 2) * math.sin(ang)
            perp_dy = (ribbon_arrow_w / 2) * -math.cos(ang)
            b1 = (int(bx + perp_dx), int(by + perp_dy))
            b2 = (int(bx - perp_dx), int(by - perp_dy))
            gfxdraw.filled_polygon(temp_surf, [tip, b1, b2], (*GOLD, 255))

    # 13) Static inner arrow at 12 o’clock (unchanged)
    tip = (temp_center[0], temp_center[1] - inner_radius - inner_arrow_h)
    b1  = (temp_center[0] - inner_arrow_w // 2, temp_center[1] - inner_radius)
    b2  = (temp_center[0] + inner_arrow_w // 2, temp_center[1] - inner_radius)
    gfxdraw.filled_polygon(temp_surf, [tip, b1, b2], (*GOLD, 255))
    gfxdraw.aapolygon(temp_surf, [tip, b1, b2], (*GOLD, 255))

    # 14) Blit onto the main surface
    dest = pygame.Rect(
        wheel_center[0] - temp_center[0],
        wheel_center[1] - temp_center[1],
        temp_size[0], temp_size[1]
    )
    surf.blit(temp_surf, dest)



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
def draw_vertical_gradient_rect(surf, rect, top_color, bottom_color, border_radius=0):
    """
    Draws a vertical gradient from top_color to bottom_color inside 'rect' on 'surf'.
    border_radius controls corner curvature.
    """
    grad_surf = pygame.Surface((rect.width, rect.height))
    for y in range(rect.height):
        t = y / (rect.height - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(grad_surf, (r, g, b), (0, y), (rect.width, y))
    grad_surf.set_alpha(255)

    # Create a rounded mask to preserve corner_radius
    rounded = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(rounded, (255, 255, 255, 255), (0, 0, rect.width, rect.height), border_radius=border_radius)
    rounded.blit(grad_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(rounded, (rect.x, rect.y))

# --------------------------------------
# Main drawing function
# --------------------------------------
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
    cols=5,
    highlight_cell=None,
    highlight_on=False
):
    """
    Draws:
      1) Table background + borders
      2) “Withdraw time” header
      3) Suit header cells (All Spades, All Diamond, etc.)
      4) Rank header cells (All Kings, All Queens, All Jacks)
      5) Play cells with ribbons
      6) Placed chips on ribbons
      7) Chip tray below
      8) “Current Bet:” text + 2×2 button grid
      9) History row under everything
    """
    global chip_rects, cell_rects, rank_icon_rects, suit_icon_rects
    global bet_button_rect, clear_button_rect, double_button_rect, repeat_button_rect, ribbon_rects

    TABLE_BG       = (16,  16,  16)
    WHITE          = (255, 255, 255)
    BLUE_BG_TOP    = (255, 255, 255)
    BLUE_BG_BOTTOM = (200, 200, 200)
    RED            = (200,   0,   0)
    BLUE_RIBBON    = (  0,   0, 200)
    BUTTON_BG      = ( 50,  50,  50)
    BUTTON_BORDER  = (200, 200, 200)
    GOLDEN         = (255, 215,   0)
    YELLOW         = (255, 255,   0)
    BLACK          = (  0,   0,   0)
    DARK_BORDER    = ( 20,  20,  20)
    GREEN          = (  0, 255,   0)

    # We'll populate these inside draw_left_table():
    chip_rects       = []
    cell_rects       = {}
    rank_icon_rects  = {}
    suit_icon_rects  = {}
    bet_button_rect  = None
    clear_button_rect   = None
    double_button_rect  = None
    repeat_button_rect  = None
    ribbon_rects     = {}

    # Move table up by 60 px
    y0_adj = y0 - 60

    sw, sh = surf.get_size()
    base_height = int(sh * 0.55)
    cell_h      = base_height // rows
    extra_h     = cell_h // 2
    table_h     = cell_h * rows + extra_h
    col_w       = int((sw * 0.48) // cols)
    table_w     = col_w * cols
    radius      = 12

    grid_total_h = cell_h * rows
    y_start      = y0_adj + (table_h - grid_total_h) // 2

    # ----------------------
    # 1) Table background
    # ----------------------
    table_rect = pygame.Rect(x0, y0_adj, table_w, table_h)
    pygame.draw.rect(surf, TABLE_BG, table_rect, border_radius=radius)
    pygame.draw.rect(surf, DARK_BORDER, table_rect, 1, border_radius=radius)
    inner_rect = table_rect.inflate(-2, -2)
    pygame.draw.rect(surf, BLACK, inner_rect, 1, border_radius=max(0, radius-1))

    # ----------------------
    # 2) “Withdraw time” header
    # ----------------------
    header_cell = pygame.Rect(x0, y_start, col_w, cell_h)
    label_surf  = small_font.render("Withdraw time:", True, WHITE)
    value_surf  = small_font.render(app_globals.Withdraw_time, True, WHITE)
    cx = header_cell.centerx
    cy = header_cell.centery
    surf.blit(label_surf, (cx - label_surf.get_width() / 2, cy - label_surf.get_height()))
    surf.blit(value_surf, (cx - value_surf.get_width() / 2, cy + 2))

    # Font for “All <Suit>” / “All <Rank>” boxes
    label_font = pygame.font.Font(None, max(6, int(small_font.get_height() * 0.6)))

    # ----------------------
    # 3) Header row columns 1–4: suits
    # ----------------------
    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    small_radius = max(4, radius // 4)
    for i, suit in enumerate(suits, start=1):
        cell = pygame.Rect(x0 + col_w * i, y_start, col_w, cell_h)
        suit_icon_rects[i] = cell

        circle_radius = int(min(col_w, cell_h) * 0.18)
        circle_dia    = circle_radius * 2
        box_pad_horiz = int(circle_radius * 0.5)
        box_pad_vert  = int(circle_radius * 0.5)

        img_w = int(suit_size * 1.2)
        img_h = int(suit_size * 1.2)

        combined_w = img_w + box_pad_horiz + circle_dia
        total_w    = int(combined_w * 1.3)
        label_text = f"All {suit}{'s' if suit not in ('Spades', 'Clubs') else ''}"
        label_surf2 = label_font.render(label_text, True, BLACK)
        label_h     = label_surf2.get_height() + 8
        base_h      = max(img_h, circle_dia) + box_pad_vert * 2
        total_h     = int(base_h * 1.2)

        y_offset = 10
        box_left = cell.centerx - total_w / 2
        box_top  = cell.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), total_w, total_h)

        # Gradient‐bordered “All <Suit>” box
        grad_rect = golden_box.inflate(-2, -2)
        if grad_rect.width > 0 and grad_rect.height > 0:
            grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
            for yi in range(grad_rect.height):
                t = yi / max(1, grad_rect.height - 1)
                r = int(YELLOW[0] + t * (GOLDEN[0] - YELLOW[0]))
                g = int(YELLOW[1] + t * (GOLDEN[1] - YELLOW[1]))
                b = int(YELLOW[2] + t * (GOLDEN[2] - YELLOW[2]))
                pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
            surf.blit(grad_surf, (grad_rect.left, grad_rect.top))
        pygame.draw.rect(surf, GOLDEN, golden_box, 1, border_radius=small_radius)

        # Suit icon + “Play” circle
        combined_left = box_left + (total_w - combined_w) / 2
        center_y_box  = box_top + total_h / 2

        img = pygame.transform.smoothscale(labels_suits[suit], (img_w, img_h))
        img_rect = img.get_rect(center=(int(combined_left + img_w/2), int(center_y_box - total_h*0.1)))
        surf.blit(img, img_rect)

        circle_center_x = int(combined_left + img_w + box_pad_horiz + circle_radius)
        circle_center_y = int(center_y_box - total_h * 0.1)
        pygame.gfxdraw.filled_circle(surf, circle_center_x, circle_center_y, circle_radius, GOLDEN)
        pygame.gfxdraw.aacircle(surf, circle_center_x, circle_center_y, circle_radius, BLACK)

        play_surf = label_font.render("Play", True, BLACK)
        surf.blit(
            play_surf,
            (
                circle_center_x - play_surf.get_width() / 2,
                circle_center_y - play_surf.get_height() / 2
            )
        )

        # Labeled box above
        label_box_w = int(total_w * 0.8)
        label_box_h = int(label_h * 1.5)
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), label_box_w, label_box_h)
        grad_rect2 = label_box.inflate(-2, -2)
        if grad_rect2.width > 0 and grad_rect2.height > 0:
            grad_surf2 = pygame.Surface((grad_rect2.width, grad_rect2.height))
            for yi in range(grad_rect2.height):
                t = yi / max(1, grad_rect2.height - 1)
                r = int(YELLOW[0] + t * (GOLDEN[0] - YELLOW[0]))
                g = int(YELLOW[1] + t * (GOLDEN[1] - YELLOW[1]))
                b = int(YELLOW[2] + t * (GOLDEN[2] - YELLOW[2]))
                pygame.draw.line(grad_surf2, (r, g, b), (0, yi), (grad_rect2.width, yi))
            surf.blit(grad_surf2, (grad_rect2.left, grad_rect2.top))
        pygame.draw.rect(surf, GOLDEN, label_box, 1, border_radius=small_radius)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # ----------------------
    # 4) First column rows 1–3: ranks
    # ----------------------
    ranks = ['K', 'Q', 'J']
    rank_label_map = {'K': 'All Kings', 'Q': 'All Queens', 'J': 'All Jacks'}
    for ridx, rank in enumerate(ranks, start=1):
        cell_rank = pygame.Rect(x0, y_start + ridx * cell_h, col_w, cell_h)
        rank_icon_rects[ridx] = cell_rank

        circle_radius = int(min(col_w, cell_h) * 0.18)
        circle_dia    = circle_radius * 2
        box_pad_horiz = int(circle_radius * 0.5)
        box_pad_vert  = int(circle_radius * 0.5)

        img_w = label_size
        img_h = label_size

        combined_w = img_w + box_pad_horiz + circle_dia
        total_w    = int(combined_w * 1.3)
        label_text = rank_label_map[rank]
        label_surf2 = label_font.render(label_text, True, BLACK)
        label_h     = label_surf2.get_height() + 8
        base_h      = max(img_h, circle_dia) + box_pad_vert * 2
        total_h     = int(base_h * 1.2)

        y_offset = 10
        box_left = cell_rank.centerx - total_w / 2
        box_top  = cell_rank.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), total_w, total_h)

        # Gradient “All <Rank>” box
        grad_rect = golden_box.inflate(-2, -2)
        if grad_rect.width > 0 and grad_rect.height > 0:
            grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
            for yi in range(grad_rect.height):
                t = yi / max(1, grad_rect.height - 1)
                r = int(YELLOW[0] + t * (GOLDEN[0] - YELLOW[0]))
                g = int(YELLOW[1] + t * (GOLDEN[1] - YELLOW[1]))
                b = int(YELLOW[2] + t * (GOLDEN[2] - YELLOW[2]))
                pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
            surf.blit(grad_surf, (grad_rect.left, grad_rect.top))
        pygame.draw.rect(surf, GOLDEN, golden_box, 1, border_radius=small_radius)

        # Rank icon + “Play” circle
        combined_left = box_left + (total_w - combined_w) / 2
        center_y_box  = box_top + total_h / 2

        img_rank = pygame.transform.smoothscale(labels_kjq[rank], (img_w, img_h))
        img_rect = img_rank.get_rect(center=(int(combined_left + img_w/2), int(center_y_box - total_h*0.1)))
        surf.blit(img_rank, img_rect)

        circle_center_x = int(combined_left + img_w + box_pad_horiz + circle_radius)
        circle_center_y = int(center_y_box - total_h * 0.1)
        pygame.gfxdraw.filled_circle(surf, circle_center_x, circle_center_y, circle_radius, GOLDEN)
        pygame.gfxdraw.aacircle(surf, circle_center_x, circle_center_y, circle_radius, BLACK)

        play_surf = label_font.render("Play", True, BLACK)
        surf.blit(
            play_surf,
            (
                circle_center_x - play_surf.get_width() / 2,
                circle_center_y - play_surf.get_height() / 2
            )
        )

        # Labeled box above
        label_box_w = int(total_w * 0.8)
        label_box_h = int(label_h * 1.5)
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), label_box_w, label_box_h)

        grad_rect2 = label_box.inflate(-2, -2)
        if grad_rect2.width > 0 and grad_rect2.height > 0:
            grad_surf2 = pygame.Surface((grad_rect2.width, grad_rect2.height))
            for yi in range(grad_rect2.height):
                t = yi / max(1, grad_rect2.height - 1)
                r = int(YELLOW[0] + t * (GOLDEN[0] - YELLOW[0]))
                g = int(YELLOW[1] + t * (GOLDEN[1] - YELLOW[1]))
                b = int(YELLOW[2] + t * (GOLDEN[2] - YELLOW[2]))
                pygame.draw.line(grad_surf2, (r, g, b), (0, yi), (grad_rect2.width, yi))
            surf.blit(grad_surf2, (grad_rect2.left, grad_rect2.top))
        pygame.draw.rect(surf, GOLDEN, label_box, 1, border_radius=small_radius)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # ----------------------
    # 5) Play cells (ribbons)
    # ----------------------
    ribbon_font = pygame.font.Font(None, max(6, int(small_font.get_height() * 0.6)))
    for ridx, rank in enumerate(ranks, start=1):
        for cidx, suit in enumerate(suits, start=1):
            cell = pygame.Rect(
                x0 + col_w * cidx,
                y_start + ridx * cell_h,
                col_w,
                cell_h
            )
            box_w = int(col_w * 0.7)
            box_h = int(cell_h * 0.9)
            inset_x = int(cell.left + (col_w - box_w) / 2)
            inset_y = int(cell.top  + (cell_h - box_h) / 2)
            blue_box = pygame.Rect(inset_x, inset_y, box_w, box_h)

            cell_rects[(ridx, cidx)] = blue_box

            # Draw blue gradient cell
            grad_rect = blue_box.inflate(-2, -2)
            if grad_rect.width > 0 and grad_rect.height > 0:
                grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
                for yi in range(grad_rect.height):
                    t = yi / max(1, grad_rect.height - 1)
                    r = int(BLUE_BG_TOP[0] + t * (BLUE_BG_BOTTOM[0] - BLUE_BG_TOP[0]))
                    g = int(BLUE_BG_TOP[1] + t * (BLUE_BG_BOTTOM[1] - BLUE_BG_TOP[1]))
                    b = int(BLUE_BG_TOP[2] + t * (BLUE_BG_BOTTOM[2] - BLUE_BG_TOP[2]))
                    pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
                surf.blit(grad_surf, (grad_rect.left, grad_rect.top))
            pygame.draw.rect(surf, BLACK, blue_box, 1, border_radius=radius//3)

            # Rank + suit icons inside
            total_w = int(label_size * 1 + suit_size * 1.2 + 8)
            yc      = blue_box.centery - int(box_h * 0.1)

            img_rank_scaled = pygame.transform.smoothscale(labels_kjq[rank], (label_size, label_size))
            surf.blit(
                img_rank_scaled,
                img_rank_scaled.get_rect(
                    center=(int(blue_box.centerx - total_w/2 + label_size/2), yc)
                )
            )

            img_s = pygame.transform.smoothscale(labels_suits[suit], (int(suit_size*1.2), int(suit_size*1.2)))
            surf.blit(
                img_s,
                img_s.get_rect(
                    center=(int(blue_box.centerx - total_w/2 + label_size + 8 + (int(suit_size*1.2))/2), yc)
                )
            )

            # Ribbon (colored rectangle at bottom of cell)
            ribbon_h = int(box_h * 0.2)
            ribbon_w = int(box_w * 1.05)
            ribbon_x = int(blue_box.left - (ribbon_w - box_w)/2)
            ribbon_y = int(blue_box.bottom - ribbon_h - int(box_h * 0.1))
            ribbon_rect = pygame.Rect(ribbon_x, ribbon_y, ribbon_w, ribbon_h)
            ribbon_rects[(ridx, cidx)] = ribbon_rect

            # Determine ribbon color
            if highlight_cell == (ridx, cidx):
                blink_color = GREEN if highlight_on else RED
                color = blink_color
            else:
                color = BLUE_RIBBON if (ridx, cidx) in placed_chips else RED

            pygame.gfxdraw.filled_polygon(
                surf,
                [ribbon_rect.topleft, ribbon_rect.topright,
                 ribbon_rect.bottomright, ribbon_rect.bottomleft],
                color
            )
            pygame.gfxdraw.aapolygon(
                surf,
                [ribbon_rect.topleft, ribbon_rect.topright,
                 ribbon_rect.bottomright, ribbon_rect.bottomleft],
                BLACK
            )

            if (ridx, cidx) not in placed_chips:
                play_surf = ribbon_font.render("Play", True, BLACK)
                surf.blit(
                    play_surf,
                    (
                        ribbon_rect.left + (ribbon_w - play_surf.get_width())/2,
                        ribbon_rect.top  + (ribbon_h - play_surf.get_height())/2
                    )
                )

    # ----------------------
    # 6) Draw placed chips on ribbons
    # ----------------------
    for (ridx, cidx), total_amt in placed_chips.items():
        if (ridx, cidx) in ribbon_rects:
            rrect = ribbon_rects[(ridx, cidx)]
            cx, cy = rrect.center
            chip_radius = int(min(cell_h, col_w) // 6)
            pygame.gfxdraw.filled_circle(surf, cx, cy, chip_radius, chip_defs[0]['color'])
            pygame.gfxdraw.aacircle(surf, cx, cy, chip_radius, BLACK)
            amt_surf = small_font.render(str(total_amt), True, WHITE)
            surf.blit(amt_surf, amt_surf.get_rect(center=(cx, cy)))

    # ----------------------
    # 7) Draw chip tray below table
    # ----------------------
    chip_radius  = int(min(cell_h, col_w) // 3)
    chip_dia     = chip_radius * 2
    chip_spacing = chip_dia + 20
    start_x      = x0 + 10
    chips_y      = y0_adj + table_h + chip_radius + 20
    SS = 4

    for idx, chip in enumerate(chip_defs):
        cx = start_x + idx * chip_spacing
        cy = chips_y

        hr_dia    = chip_dia * SS
        hr_radius = chip_radius * SS
        chip_body_hr = pygame.Surface((hr_dia, hr_dia), pygame.SRCALPHA)

        pygame.gfxdraw.filled_circle(chip_body_hr, hr_radius, hr_radius, hr_radius, chip['color'])
        pygame.gfxdraw.aacircle(chip_body_hr, hr_radius, hr_radius, hr_radius, BLACK)

        # draw stripes on the large chip
        strip_count     = 8
        strip_ang_width = 20
        outer_r_hr = hr_radius
        inner_r_hr = int(hr_radius * 0.7)
        for i in range(strip_count):
            a    = math.radians(i * (360 / strip_count))
            half = math.radians(strip_ang_width / 2)
            p1 = (hr_radius + int((outer_r_hr - 1) * math.cos(a + half)),
                  hr_radius + int((outer_r_hr - 1) * math.sin(a + half)))
            p2 = (hr_radius + int((outer_r_hr - 1) * math.cos(a - half)),
                  hr_radius + int((outer_r_hr - 1) * math.sin(a - half)))
            p3 = (hr_radius + int(inner_r_hr * math.cos(a - half)),
                  hr_radius + int(inner_r_hr * math.sin(a - half)))
            p4 = (hr_radius + int(inner_r_hr * math.cos(a + half)),
                  hr_radius + int(inner_r_hr * math.sin(a + half)))
            pygame.gfxdraw.filled_polygon(chip_body_hr, [p1, p2, p3, p4], WHITE)
            pygame.gfxdraw.aapolygon(chip_body_hr,   [p1, p2, p3, p4], BLACK)

        # center circle on the large chip
        center_r_hr = int(hr_radius * 0.6)
        pygame.gfxdraw.filled_circle(chip_body_hr, hr_radius, hr_radius, center_r_hr, WHITE)
        pygame.gfxdraw.aacircle(chip_body_hr, hr_radius, hr_radius, center_r_hr, BLACK)

        chip_body = pygame.transform.smoothscale(chip_body_hr, (chip_dia, chip_dia))
        chip_body_rect = chip_body.get_rect()
        amt_surf = small_font.render(str(chip['amount']), True, BLACK)

        if selected_chip == idx:
            angle = -(now_ts * 60) % 360
            rotated_body = pygame.transform.rotate(chip_body, angle)
            rot_rect     = rotated_body.get_rect(center=(cx, cy))
            surf.blit(rotated_body, rot_rect)
            surf.blit(amt_surf, amt_surf.get_rect(center=rot_rect.center))
            chip_rects.append(pygame.Rect(cx-chip_radius, cy-chip_radius, chip_dia, chip_dia))
        else:
            chip_body_rect.center = (cx, cy)
            surf.blit(chip_body, chip_body_rect)
            surf.blit(amt_surf, amt_surf.get_rect(center=(cx, cy)))
            chip_rects.append(pygame.Rect(cx-chip_radius, cy-chip_radius, chip_dia, chip_dia))

    # ----------------------
    # 8) “Current Bet:” text + 2×2 buttons
    # ----------------------
    total_bet   = sum(placed_chips.values())
    bet_text    = small_font.render(f"Current Bet: {total_bet}", True, WHITE)

    # Align “Current Bet:” left edge with left edge of the “Bet” button:
    btn_w        = 100
    btn_h        = 30
    btn_spacing  = 8

    # Calculate total width of two buttons + spacing
    total_btns_w = btn_w * 2 + btn_spacing
    left_shift   = 70   # push everything further left; adjust as needed
    margin       = 180

    btn_x_base   = sw - margin - total_btns_w - left_shift
    btn_y_top    = y0_adj + table_h + chip_dia + 30  # vertical position just below the chips

    # Draw “Current Bet:” so its left == btn_x_base
    surf.blit(bet_text, (btn_x_base + 30, btn_y_top - small_font.get_height() - 8))

    # Green gradient colors and corner radius
    DARK_GREEN  = (0, 100, 0)
    radius_btn  = btn_h // 2
    pad_x       = 8   # horizontal padding
    pad_y       = 4   # vertical padding

    # Top-Left: “Bet”
    bet_button_rect = pygame.Rect(btn_x_base, btn_y_top, btn_w, btn_h)
    pygame.draw.rect(surf, DARK_GREEN, bet_button_rect, border_radius=radius_btn)
    pygame.draw.rect(surf, BUTTON_BORDER, bet_button_rect, 1, border_radius=radius_btn)
    btn_txt_surf = small_font.render("Bet", True, WHITE)
    inner = bet_button_rect.inflate(-pad_x*2, -pad_y*2)
    surf.blit(btn_txt_surf, btn_txt_surf.get_rect(center=inner.center))

    # Top-Right: “Clear Bet”
    clear_button_rect = pygame.Rect(
        btn_x_base + btn_w + btn_spacing,
        btn_y_top,
        btn_w,
        btn_h
    )
    pygame.draw.rect(surf, DARK_GREEN, clear_button_rect, border_radius=radius_btn)
    pygame.draw.rect(surf, BUTTON_BORDER, clear_button_rect, 1, border_radius=radius_btn)
    clear_txt_surf = small_font.render("Clear Bet", True, WHITE)
    inner = clear_button_rect.inflate(-pad_x*2, -pad_y*2)
    surf.blit(clear_txt_surf, clear_txt_surf.get_rect(center=inner.center))

    # Second row-left: “Double Bet”
    double_button_rect = pygame.Rect(
        btn_x_base,
        btn_y_top + btn_h + btn_spacing,
        btn_w,
        btn_h
    )
    pygame.draw.rect(surf, DARK_GREEN, double_button_rect, border_radius=radius_btn)
    pygame.draw.rect(surf, BUTTON_BORDER, double_button_rect, 1, border_radius=radius_btn)
    double_txt_surf = small_font.render("Double Bet", True, WHITE)
    inner = double_button_rect.inflate(-pad_x*2, -pad_y*2)
    surf.blit(double_txt_surf, double_txt_surf.get_rect(center=inner.center))

    # Second row-right: “Repeat Bet”
    repeat_button_rect = pygame.Rect(
        btn_x_base + btn_w + btn_spacing,
        btn_y_top + btn_h + btn_spacing,
        btn_w,
        btn_h
    )
    pygame.draw.rect(surf, DARK_GREEN, repeat_button_rect, border_radius=radius_btn)
    pygame.draw.rect(surf, BUTTON_BORDER, repeat_button_rect, 1, border_radius=radius_btn)
    repeat_txt_surf = small_font.render("Repeat Bet", True, WHITE)
    inner = repeat_button_rect.inflate(-pad_x*2, -pad_y*2)
    surf.blit(repeat_txt_surf, repeat_txt_surf.get_rect(center=inner.center))


    # ----------------------
    # 9) History row (unchanged)
    # ----------------------
    history = getattr(app_globals, "history_json", [])
    if history:
        # Compute base sizes
        box_size   = int(min(col_w, cell_h) * 0.7)
        narrow_w   = box_size // 2
        spacing    = 4  # fixed gap between boxes
        text_h     = small_font.get_height()

        # Button vertical position (as defined earlier)
        btn_y_top  = y0_adj + table_h + chip_dia + 10

        # Place history just beneath the two rows of buttons
        base_y     = btn_y_top + btn_h * 2 - 14

        # Build list of widths: first box full width, others narrower
        narrow_w = int(box_size * 0.75)
        widths   = [box_size] + [narrow_w] * (len(history) - 1)
        total_width = sum(widths) + spacing * (len(history) - 1)
        start_x     = x0 + (table_w - total_width) // 2

        mapping = {
            0: ("K", "Spades"),   1: ("K", "Diamond"),
            2: ("K", "Clubs"),    3: ("K", "Hearts"),
            4: ("Q", "Spades"),   5: ("Q", "Diamond"),
            6: ("Q", "Clubs"),    7: ("Q", "Hearts"),
            8: ("J", "Spades"),   9: ("J", "Diamond"),
        10: ("J", "Clubs"),  11: ("J", "Hearts"),
        }

        blink_color_1 = (255, 255, 255)
        blink_color_2 = (  0, 255,   0)
        blink_speed   = 500
        time_ms       = pygame.time.get_ticks()
        blink_phase   = (time_ms // blink_speed) % 2
        blink_bg      = blink_color_1 if blink_phase == 0 else blink_color_2

        time_font     = pygame.font.SysFont(None, max(14, int(box_size * 0.2)))
        TIME_TEXT_COLOR = (0, 0, 0)

        x_cursor = start_x
        for idx, item in enumerate(history):
            w = widths[idx]
            bx = x_cursor
            by = base_y
            rect     = pygame.Rect(bx, by, w, box_size)
            grad_rect = rect.inflate(-2, -2)

            if idx == 0:
                pygame.draw.rect(surf, blink_bg, grad_rect, border_radius=4)
            else:
                grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
                for yi in range(grad_rect.height):
                    t = yi / max(1, grad_rect.height - 1)
                    r = int(255 * (1 - t))
                    g = int(255 * (1 - t))
                    b = int(255 * (1 - t) + 30 * t)
                    pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
                surf.blit(grad_surf, (grad_rect.left, grad_rect.top))

            pygame.draw.rect(surf, DARK_BORDER, rect, 1, border_radius=4)

            time_surf = time_font.render(item['created_time'], True, TIME_TEXT_COLOR)
            time_rect = time_surf.get_rect(midtop=(rect.centerx, rect.top + 4))
            surf.blit(time_surf, time_rect)

            rank_key, suit_key = mapping.get(item['result_number'], ("J", "Hearts"))
            icon_size = int(box_size * 0.4)
            rank_img  = pygame.transform.smoothscale(labels_kjq[rank_key], (icon_size, icon_size))
            rank_rect = rank_img.get_rect(midtop=(rect.centerx, time_rect.bottom + 2))
            surf.blit(rank_img, rank_rect)

            suit_img  = pygame.transform.smoothscale(labels_suits[suit_key], (icon_size, icon_size))
            suit_rect = suit_img.get_rect(midtop=(rect.centerx, rank_rect.bottom + 2))
            surf.blit(suit_img, suit_rect)

            # Advance cursor for next box
            x_cursor += w + spacing



# --------------------------------------
# Click-handling function
# --------------------------------------
def handle_click(mouse_pos):
    """
    Must be called in your main loop on MOUSEBUTTONDOWN.
    1) Click a tray chip → select that chip.
    2) Click “Bet” → send placed_chips via POST, then clear.
    3) Click “Clear Bet” → clear placed_chips.
    4) Click “Double Bet” → double each placed chip amount.
    5) Click “Repeat Bet” → restore last_placed_chips to placed_chips.
    6) If a chip is selected and you click a rank/suit/icon → add that chip’s amount.
    7) Click outside → deselect.
    """
    global selected_chip, placed_chips, last_placed_chips

    # — Bet button —
    if bet_button_rect and bet_button_rect.collidepoint(mouse_pos):
        total_bet_amount = sum(amt for (_, _), amt in placed_chips.items())
        payload = {
            "bets": {f"{r}_{c}": amt for (r, c), amt in placed_chips.items()},
            "Withdraw_time": app_globals.Withdraw_time,
            "User_id": app_globals.User_id
        }
        print("Sending payload:", json.dumps(payload, indent=2))
        app_globals.user_data_points -= total_bet_amount
        resp = requests.post(
            "https://spintofortune.in/api/app_place_bet.php",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("Status:", resp.status_code)
        print("Raw response text:", resp.text)
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, indent=2))
        print_json_silent(data)

        # --- clear all placed bets ---
        last_placed_chips = placed_chips.copy()
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


    # — Clear Bet button —
    if clear_button_rect and clear_button_rect.collidepoint(mouse_pos):
        placed_chips.clear()
        selected_chip = None
        return

    # — Double Bet button —
    if double_button_rect and double_button_rect.collidepoint(mouse_pos):
        for key in list(placed_chips):
            placed_chips[key] *= 2
        return

    # — Repeat Bet button —
    if repeat_button_rect and repeat_button_rect.collidepoint(mouse_pos):
        placed_chips = last_placed_chips.copy()
        return

    # — Tray-chip selection & placing logic —
    # 1) Click tray chip?
    for idx, rect in enumerate(chip_rects):
        if rect.collidepoint(mouse_pos):
            selected_chip = idx
            return

    # 2) If a chip is selected, clicking on a rank/suit/cell places a bet
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

    # 3) Click anywhere else → deselect
    selected_chip = None