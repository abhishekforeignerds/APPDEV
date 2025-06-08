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

def print_json_silent(data_dict, printer_name=None):
    """
    1) Extracts the relevant ticket fields from `data_dict`.
    2) Builds a formatted PDF (with header, ticket fields, generated barcode + serial text, footer).
    3) Saves that PDF to disk (for inspection).
    4) Sends the PDF to the default (or named) printer silently—no dialogs.
    
    – data_dict: the Python dict you received from the API (containing data["ticket"]).
    – printer_name (optional): a specific printer name. If omitted, uses the OS default.
    """

    # --- 1) Extract fields from data_dict ---
    ticket_block = data_dict.get("data", {}).get("ticket", {})
    if not ticket_block:
        print("[Printer][Error] No 'ticket' block found in data_dict.")
        return

    ticket_id       = ticket_block.get("id", "")
    serial_number   = ticket_block.get("serial_number", "")
    user_id         = ticket_block.get("user_id", "")
    amount          = ticket_block.get("amount", "")
    withdraw_time   = ticket_block.get("created_at", "")

    # Static or hardcoded fields (adjust if your API provides these)
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

    # --- 2) Build a formatted PDF with generated barcode ---
    base_pdf_name = f"ticket_{serial_number}"
    pdf_filename = base_pdf_name + ".pdf"
    print(f"[Printer][Info] Generating PDF: {pdf_filename}")

    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    y = height - 50

    # Header: "For Amusement Only"
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "For Amusement Only")
    y -= 30

    # Ticket ID
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, f"Ticket ID: {ticket_id}")
    y -= 25

    # Collect lines to add
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

    # Generate a Code128 barcode for the serial number
    if serial_number:
        try:
            print(f"[Printer][Info] Generating barcode for: {serial_number}")
            barcode_obj = code128.Code128(
                serial_number,
                barHeight=20 * mm,
                barWidth=0.5 * mm
            )
            # Center the barcode horizontally
            barcode_width = barcode_obj.width
            x_barcode = (width - barcode_width) / 2
            # Draw barcode
            barcode_obj.drawOn(c, x_barcode, y - (20 * mm))
            # Move y down by barcode height + some padding
            y -= (20 * mm + 30)

            # Draw the serial text below the barcode
            c.setFont("Helvetica", 10)
            # c.drawCentredString(width / 2, y + 10, serial_number)
            print(f"[Printer][Info] Embedded barcode and serial text.")
        except Exception as e:
            print(f"[Printer][Warning] Could not generate/embed barcode: {e}")
            y -= 30
    else:
        print(f"[Printer][Warning] No serial number to generate barcode.")
        y -= 30

    # Footer: "Not For Sale"
    footer_text = "Not For Sale"
    print(f"[Printer][Info] Adding footer to PDF: {footer_text}")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, footer_text)

    c.showPage()
    c.save()
    print(f"[Printer][Info] PDF saved: {pdf_filename}")

    # --- 3) Send PDF to the printer silently ---
    system = platform.system()
    print(f"[Printer] Detected OS: {system}")

    if system == "Windows":
        try:
            import win32print
        except ImportError:
            print("[Printer][Error] On Windows, silent printing requires 'pywin32'.")
            print("[Printer][Error] Install it via: pip install pywin32")
            return

        # Determine which printer to open
        try:
            if printer_name:
                target_printer = printer_name
            else:
                target_printer = win32print.GetDefaultPrinter() or ""
        except Exception as e:
            print(f"[Printer][Error] Could not retrieve default printer: {e}")
            return

        if not target_printer:
            print("[Printer][Error] No default printer found on Windows.")
            return
        else:
            print(f"[Printer] Using Windows printer: '{target_printer}'")

        try:
            hPrinter = win32print.OpenPrinter(target_printer)
        except Exception as e:
            print(f"[Printer][Error] Could not open printer '{target_printer}': {e}")
            return

        # Prepare document info: sending raw PDF bytes
        doc_info = (
            pdf_filename,  # Document name (arbitrary)
            None,          # No output file, direct to printer
            "RAW"          # DataType = RAW, so bytes go directly
        )

        try:
            print(f"[Printer][Info] Starting print job for '{pdf_filename}' on '{target_printer}'")
            job_id = win32print.StartDocPrinter(hPrinter, 1, doc_info)
            win32print.StartPagePrinter(hPrinter)

            # Read PDF bytes
            with open(pdf_filename, "rb") as f:
                pdf_bytes = f.read()
            win32print.WritePrinter(hPrinter, pdf_bytes)

            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            print(f"[Printer][Info] Print job #{job_id} completed on '{target_printer}'.")
        except Exception as e:
            print(f"[Printer][Error] Failed during printing to '{target_printer}': {e}")
        finally:
            win32print.ClosePrinter(hPrinter)

    elif system in ("Linux", "Darwin"):
        # On Linux/macOS: pipe the PDF file into `lpr`
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
        print(f"[Printer][Error] Unsupported OS for printing: {system}")


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
    highlight_index=None,
    highlight_on=False
):
    """
    Draws the spinning wheel onto `surf`. If highlight_index is not None and
    highlight_on=True, the segment at highlight_index is drawn in a brighter color
    with a yellow border. Otherwise, everything is drawn normally.
    """

    width, height = surf.get_size()
    min_dim = min(width, height)
    outer_radius = int(min_dim * 0.30)
    mid_radius   = int(min_dim * 0.18)
    inner_radius = int(min_dim * 0.08)

    # Arrow sizes
    inner_arrow_w = inner_arrow_h = 20
    ribbon_arrow_w = ribbon_arrow_h = 20

    # Ribbon thickness
    ribbon_thickness = max(6, int(min_dim * 0.015))
    current_rad = math.radians(current_ang)

    # Generate palettes for outer ring if not provided
    if outer_segment_colors is None:
        outer_segment_colors = _generate_hsv_palette(num_segments, 75, 100, 255)

    # Prepare off-screen surface for drop shadow and drawing
    temp_size = (outer_radius * 2 + SHADOW_OFFSET * 2,
                 outer_radius * 2 + SHADOW_OFFSET * 2)
    temp_surf = pygame.Surface(temp_size, pygame.SRCALPHA)
    temp_center = (outer_radius + SHADOW_OFFSET,
                   outer_radius + SHADOW_OFFSET)

    # Draw drop shadow
    gfxdraw.filled_circle(
        temp_surf,
        temp_center[0],
        temp_center[1] + SHADOW_OFFSET,
        outer_radius,
        SHADOW_COLOR
    )

    # Draw outer wheel background (white) and border
    gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1],
                          outer_radius, (*TABLE_BG, 255))
    gfxdraw.aacircle(temp_surf, temp_center[0], temp_center[1],
                     outer_radius, (*GRID, 255))

    # Draw outer wheel segments
    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments) + current_rad
        end   = start + math.radians(360 / num_segments)
        pts = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start + (end - start) * (s / ANGLE_STEPS)
            x = temp_center[0] + outer_radius * math.cos(a)
            y = temp_center[1] + outer_radius * math.sin(a)
            pts.append((int(x), int(y)))

        if i == highlight_index and highlight_on:
            # Brighten this segment's color and draw a thick yellow outline
            base_color = outer_segment_colors[i]
            r, g, b = base_color
            bright = (min(255, r + 100), min(255, g + 100), min(255, b + 100))
            gfxdraw.filled_polygon(temp_surf, pts, bright)
            pygame.draw.polygon(temp_surf, (255, 255, 0), pts, 3)
        else:
            gfxdraw.filled_polygon(temp_surf, pts, outer_segment_colors[i])
            pygame.draw.polygon(temp_surf, GRID, pts, 1)

    # Define the “K/Q/J” order in outer ring:
    ranks = ['K', 'Q', 'J']
    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']

    # Draw rank icons on each segment (outer circle)
    for i in range(num_segments):
        rank = ranks[i // 4]  # 0–3 → K, 4–7 → Q, 8–11 → J
        ang = math.radians((i + 0.5) * 360 / num_segments) + current_rad

        rank_radius = outer_radius * 0.85
        rx = int(temp_center[0] + rank_radius * math.cos(ang))
        ry = int(temp_center[1] + rank_radius * math.sin(ang))
        rank_img = labels_kjq[rank]
        temp_surf.blit(rank_img, rank_img.get_rect(center=(rx, ry)))

    # Mid ring: gradient from white → darker
    inner_grad = mid_radius - int(mid_radius * 0.3)
    for r in range(mid_radius, inner_grad, -1):
        shade = 255 - int((mid_radius - r) / (mid_radius - inner_grad) * 100)
        gfxdraw.filled_circle(temp_surf, temp_center[0], temp_center[1], r,
                              (shade, shade, shade))

    # Radial lines between mid ring and inner ring
    for i in range(num_segments):
        ang = math.radians(i * 360 / num_segments) + current_rad
        x1  = temp_center[0] + inner_radius * math.cos(ang)
        y1  = temp_center[1] + inner_radius * math.sin(ang)
        x2  = temp_center[0] + mid_radius * math.cos(ang)
        y2  = temp_center[1] + mid_radius * math.sin(ang)
        pygame.draw.aaline(temp_surf, GRID, (int(x1), int(y1)), (int(x2), int(y2)))

    # Draw suit icons in the mid ring
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

    # Inner circle segments (alternating dark/light gold)
    DARK_GOLD  = (*GOLD, 255)
    LIGHT_GOLD = (*GOLD, 254)
    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments)
        end   = start + math.radians(360 / num_segments)
        pts = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start + (end - start) * (s / ANGLE_STEPS)
            x = temp_center[0] + inner_radius * math.cos(a)
            y = temp_center[1] + inner_radius * math.sin(a)
            pts.append((int(x), int(y)))
        gfxdraw.filled_polygon(
            temp_surf, pts,
            DARK_GOLD if i % 2 == 0 else LIGHT_GOLD
        )

    # Draw ribbon (outermost border circle)
    ribbon_rad   = outer_radius + ribbon_thickness // 2
    ribbon_color = (*RIBBON_COLOR_RGB, RIBBON_ALPHA)
    gfxdraw.aacircle(
        temp_surf, temp_center[0], temp_center[1],
        ribbon_rad, ribbon_color
    )
    pygame.draw.circle(temp_surf, ribbon_color, temp_center,
                       ribbon_rad, ribbon_thickness)

    # Dots and arrows on the ribbon
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
            tip_r = inner_edge - ribbon_arrow_h
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

    # Draw the static inner arrow at 12 o'clock
    tip = (temp_center[0], temp_center[1] - inner_radius - inner_arrow_h)
    b1  = (temp_center[0] - inner_arrow_w // 2, temp_center[1] - inner_radius)
    b2  = (temp_center[0] + inner_arrow_w // 2, temp_center[1] - inner_radius)
    gfxdraw.filled_polygon(temp_surf, [tip, b1, b2], (*GOLD, 255))
    gfxdraw.aapolygon(temp_surf, [tip, b1, b2], (*GOLD, 255))

    # Blit everything onto the main surface
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


TABLE_BG       = (16, 16, 16)        # mid-gray
WHITE          = (255, 255, 255)
BLUE_BG_TOP    = (255, 255, 255)     # top of blue-cell gradient (pure white)
BLUE_BG_BOTTOM = (200, 200, 200)     # bottom of blue-cell gradient (light gray)
RED            = (200, 0, 0)
BLUE_RIBBON    = (0, 0, 200)         # ribbon color when a bet is placed (blue)
BUTTON_BG      = (50, 50, 50)
BUTTON_BORDER  = (200, 200, 200)
GOLDEN         = (255, 215, 0)
YELLOW         = (255, 255, 0)
BLACK          = (0, 0, 0)
DARK_BORDER    = (20, 20, 20)        # slightly black for outer table border

# Add a dict to store ribbon rects per cell
ribbon_rects = {}

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
      1) A table of cells with no drop shadow.
      2) Header row: first cell ("Withdraw time") centered; columns 1–4: suit image +
         a taller colored ribbon box containing a smaller "Play" circle or chip,
         with an attached taller label box above reading "All <SuitPlural>".
      3) First column rows 1–3: rank image + taller colored ribbon box containing
         a smaller "Play" circle or chip, with an attached taller label box above reading "All <RankPlural>".
      4) A tray of chips below the table.
      5) Any chips placed on the ribbons, hiding the "Play" text.
      6) A visible text displaying the current total bet.
      7) A "Bet" button to submit placed bets.
    """
    global chip_rects, cell_rects, rank_icon_rects, suit_icon_rects, bet_button_rect, ribbon_rects
    chip_rects       = []
    cell_rects       = {}
    rank_icon_rects  = {}
    suit_icon_rects  = {}
    bet_button_rect  = None
    ribbon_rects     = {}

    # Move entire table up by 60 pixels (to give more space at bottom)
    y0_adj = y0 - 60

    sw, sh    = surf.get_size()
    # Compute a normal cell height from ~55% of screen height
    base_height = int(sh * 0.55)
    cell_h    = base_height // rows
    # Add half a cell height extra to table for header‐box overflow
    extra_h   = cell_h // 2
    table_h   = cell_h * rows + extra_h
    col_w     = int((sw * 0.48) // cols)
    table_w   = col_w * cols
    radius    = 12

    # Vertical offset to center the grid of rows inside the taller table rectangle
    grid_total_h = cell_h * rows
    y_start = y0_adj + (table_h - grid_total_h) // 2

    # Helper: draw a gradient fill box with only an outer golden border
    def draw_gradient_simple_box(surf, rect, outer_radius):
        """
        - Fills interior with a vertical gradient from YELLOW (top) to GOLDEN (bottom).
        - Draws an outer border in GOLDEN (solid), with rounded corners.
        """
        grad_rect = rect.inflate(-2, -2)
        if grad_rect.width > 0 and grad_rect.height > 0:
            grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
            for yi in range(grad_rect.height):
                t = yi / max(1, grad_rect.height - 1)
                r = int(YELLOW[0] + t * (GOLDEN[0] - YELLOW[0]))
                g = int(YELLOW[1] + t * (GOLDEN[1] - YELLOW[1]))
                b = int(YELLOW[2] + t * (GOLDEN[2] - YELLOW[2]))
                pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
            surf.blit(grad_surf, (grad_rect.left, grad_rect.top))
        pygame.draw.rect(surf, GOLDEN, rect, 1, border_radius=outer_radius)

    # Helper: draw a gradient for blue play cells (white at top → light gray at bottom)
    def draw_blue_cell_gradient(surf, rect, corner_radius):
        """
        - Fills interior of rect with a vertical gradient from BLUE_BG_TOP to BLUE_BG_BOTTOM.
        - Draws a 1px BLACK border around rect with rounded corners.
        """
        grad_rect = rect.inflate(-2, -2)
        if grad_rect.width > 0 and grad_rect.height > 0:
            grad_surf = pygame.Surface((grad_rect.width, grad_rect.height))
            for yi in range(grad_rect.height):
                t = yi / max(1, grad_rect.height - 1)
                r = int(BLUE_BG_TOP[0] + t * (BLUE_BG_BOTTOM[0] - BLUE_BG_TOP[0]))
                g = int(BLUE_BG_TOP[1] + t * (BLUE_BG_BOTTOM[1] - BLUE_BG_TOP[1]))
                b = int(BLUE_BG_TOP[2] + t * (BLUE_BG_BOTTOM[2] - BLUE_BG_TOP[2]))
                pygame.draw.line(grad_surf, (r, g, b), (0, yi), (grad_rect.width, yi))
            surf.blit(grad_surf, (grad_rect.left, grad_rect.top))
        pygame.draw.rect(surf, BLACK, rect, 1, border_radius=corner_radius)

    # 1) Draw table background with rounded corners, plus outer and inner borders
    table_rect = pygame.Rect(x0, y0_adj, table_w, table_h)
    pygame.draw.rect(surf, TABLE_BG, table_rect, border_radius=radius)
    pygame.draw.rect(surf, DARK_BORDER, table_rect, 1, border_radius=radius)
    inner_rect = table_rect.inflate(-2, -2)
    pygame.draw.rect(surf, BLACK, inner_rect, 1, border_radius=max(0, radius - 1))

    # 2) Header row: first cell (“Withdraw time”) centered in top grid cell
    header_cell = pygame.Rect(x0, y_start, col_w, cell_h)
    label_surf  = small_font.render("Withdraw time:", True, WHITE)
    value_surf  = small_font.render(globals.Withdraw_time, True, WHITE)
    center_x    = header_cell.centerx
    center_y    = header_cell.centery
    surf.blit(label_surf, (center_x - label_surf.get_width() / 2, center_y - label_surf.get_height()))
    surf.blit(value_surf, (center_x - value_surf.get_width() / 2, center_y + 2))

    # Prepare a smaller label font for attached boxes
    label_font = pygame.font.Font(None, max(6, int(small_font.get_height() * 0.6)))

    # 3) Header row columns 1–4: suit image + taller labeled box + ribbon (red by default) with “Play”
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
        total_w = int(combined_w * 1.3)
        label_text   = f"All {suit}{'s' if suit not in ('Spades','Clubs') else ''}"
        label_surf2  = label_font.render(label_text, True, BLACK)
        label_h      = label_surf2.get_height() + 8
        base_h       = max(img_h, circle_dia) + box_pad_vert * 2
        total_h      = int(base_h * 1.2)

        y_offset = 10
        box_left = cell.centerx - total_w / 2
        box_top  = cell.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), total_w, total_h)
        draw_gradient_simple_box(surf, golden_box, small_radius)

        combined_left = box_left + (total_w - combined_w) / 2
        center_y_box  = box_top + total_h / 2

        img = pygame.transform.smoothscale(labels_suits[suit], (img_w, img_h))
        img_rect = img.get_rect(center=(int(combined_left + img_w / 2), int(center_y_box - total_h * 0.1)))
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

        # Attached label above
        label_box_w = int(total_w * 0.8)
        label_box_h = int(label_h * 1.5)
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), label_box_w, label_box_h)
        draw_gradient_simple_box(surf, label_box, small_radius)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # 4) First column rows 1–3: rank image + taller labeled box + ribbon (red by default) with “Play”
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
        total_w = int(combined_w * 1.3)
        label_text   = rank_label_map[rank]
        label_surf2  = label_font.render(label_text, True, BLACK)
        label_h      = label_surf2.get_height() + 8
        base_h       = max(img_h, circle_dia) + box_pad_vert * 2
        total_h      = int(base_h * 1.2)

        y_offset = 10
        box_left = cell_rank.centerx - total_w / 2
        box_top  = cell_rank.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), total_w, total_h)
        draw_gradient_simple_box(surf, golden_box, small_radius)

        combined_left = box_left + (total_w - combined_w) / 2
        center_y_box  = box_top + total_h / 2

        img_rank = pygame.transform.smoothscale(labels_kjq[rank], (img_w, img_h))
        img_rect = img_rank.get_rect(center=(int(combined_left + img_w / 2), int(center_y_box - total_h * 0.1)))
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

        # Attached label above
        label_box_w = int(total_w * 0.8)
        label_box_h = int(label_h * 1.5)
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), label_box_w, label_box_h)
        draw_gradient_simple_box(surf, label_box, small_radius)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # 5) Draw play cells (rows 1–3, cols 1–4) with white→light-gray gradient and ribbons (red by default, blue if bet placed)
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
            draw_blue_cell_gradient(surf, blue_box, radius // 3)

            # Draw rank and suit icons inside the blue cell
            total_w = int(label_size * 1 + suit_size * 1.2 + 8)
            yc      = blue_box.centery - int(box_h * 0.1)

            img_rank_scaled = pygame.transform.smoothscale(labels_kjq[rank], (label_size, label_size))
            surf.blit(
                img_rank_scaled,
                img_rank_scaled.get_rect(
                    center=(int(blue_box.centerx - total_w / 2 + label_size / 2), yc)
                )
            )

            img_s = pygame.transform.smoothscale(labels_suits[suit], (int(suit_size * 1.2), int(suit_size * 1.2)))
            surf.blit(
                img_s,
                img_s.get_rect(
                    center=(int(blue_box.centerx - total_w / 2 + label_size + 8 + (int(suit_size * 1.2)) / 2), yc)
                )
            )

            # Determine ribbon rect
            ribbon_h = int(box_h * 0.2)
            ribbon_w = int(box_w * 1.05)
            ribbon_x = int(blue_box.left - (ribbon_w - box_w) / 2)
            ribbon_y = int(blue_box.bottom - ribbon_h - int(box_h * 0.1))
            ribbon_rect = pygame.Rect(ribbon_x, ribbon_y, ribbon_w, ribbon_h)
            ribbon_rects[(ridx, cidx)] = ribbon_rect

            # Choose ribbon color: RED by default, BLUE if bet is placed here
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

            # Only draw "Play" text if no chip is placed here
            if (ridx, cidx) not in placed_chips:
                play_surf = ribbon_font.render("Play", True, BLACK)
                surf.blit(
                    play_surf,
                    (
                        ribbon_rect.left + (ribbon_w - play_surf.get_width()) / 2,
                        ribbon_rect.top  + (ribbon_h - play_surf.get_height()) / 2
                    )
                )

    # 6) Draw any placed chips on the ribbons (hiding "Play")
    for (ridx, cidx), total_amt in placed_chips.items():
        if (ridx, cidx) in ribbon_rects:
            rrect = ribbon_rects[(ridx, cidx)]
            center_x = rrect.centerx
            center_y = rrect.centery
            chip_radius = int(min(cell_h, col_w) // 6)
            pygame.gfxdraw.filled_circle(surf, center_x, center_y, chip_radius, chip_defs[0]['color'])
            pygame.gfxdraw.aacircle(surf, center_x, center_y, chip_radius, BLACK)
            amt_surf = small_font.render(str(total_amt), True, WHITE)
            surf.blit(amt_surf, amt_surf.get_rect(center=(center_x, center_y)))

    # 7) Draw chip “tray” below the table (with supersampling for smoother edges)
    chip_radius  = int(min(cell_h, col_w) // 3)
    chip_dia     = chip_radius * 2
    chip_spacing = chip_dia + 20
    start_x      = x0 + 10
    chips_y      = y0_adj + table_h + chip_radius + 20

    SS = 4  # Supersampling factor
    for idx, chip in enumerate(chip_defs):
        cx = start_x + idx * chip_spacing
        cy = chips_y

        hr_dia     = chip_dia * SS
        hr_radius  = chip_radius * SS
        chip_body_hr = pygame.Surface((hr_dia, hr_dia), pygame.SRCALPHA)

        pygame.gfxdraw.filled_circle(chip_body_hr, hr_radius, hr_radius, hr_radius, chip['color'])
        pygame.gfxdraw.aacircle(chip_body_hr, hr_radius, hr_radius, hr_radius, BLACK)

        strip_count     = 8
        strip_ang_width = 20
        outer_r_hr = hr_radius
        inner_r_hr = int(hr_radius * 0.7)
        for i in range(strip_count):
            a = i * (360 / strip_count)
            a_rad = math.radians(a)
            half_rad = math.radians(strip_ang_width / 2)

            p1 = (
                hr_radius + int((outer_r_hr - 1) * math.cos(a_rad + half_rad)),
                hr_radius + int((outer_r_hr - 1) * math.sin(a_rad + half_rad))
            )
            p2 = (
                hr_radius + int((outer_r_hr - 1) * math.cos(a_rad - half_rad)),
                hr_radius + int((outer_r_hr - 1) * math.sin(a_rad - half_rad))
            )
            p3 = (
                hr_radius + int(inner_r_hr * math.cos(a_rad - half_rad)),
                hr_radius + int(inner_r_hr * math.sin(a_rad - half_rad))
            )
            p4 = (
                hr_radius + int(inner_r_hr * math.cos(a_rad + half_rad)),
                hr_radius + int(inner_r_hr * math.sin(a_rad + half_rad))
            )
            pygame.gfxdraw.filled_polygon(chip_body_hr, [p1, p2, p3, p4], WHITE)
            pygame.gfxdraw.aapolygon(chip_body_hr, [p1, p2, p3, p4], BLACK)

        center_r_hr = int(hr_radius * 0.6)
        pygame.gfxdraw.filled_circle(chip_body_hr, hr_radius, hr_radius, center_r_hr, WHITE)
        pygame.gfxdraw.aacircle(chip_body_hr, hr_radius, hr_radius, center_r_hr, BLACK)

        chip_body = pygame.transform.smoothscale(chip_body_hr, (chip_dia, chip_dia))
        chip_body_rect = chip_body.get_rect()
        amt_surf = small_font.render(str(chip['amount']), True, BLACK)

        if selected_chip == idx:
            angle = -(now_ts * 60) % 360
            rotated_body = pygame.transform.rotate(chip_body, angle)
            rot_rect = rotated_body.get_rect(center=(int(cx), int(cy)))
            surf.blit(rotated_body, rot_rect)

            amt_pos = (rot_rect.left + rot_rect.width // 2, rot_rect.top + rot_rect.height // 2)
            surf.blit(amt_surf, amt_surf.get_rect(center=amt_pos))

            chip_rects.append(
                pygame.Rect(int(cx - chip_radius), int(cy - chip_radius), chip_dia, chip_dia)
            )
        else:
            chip_body_rect.center = (int(cx), int(cy))
            surf.blit(chip_body, chip_body_rect)
            surf.blit(amt_surf, amt_surf.get_rect(center=(int(cx), int(cy))))
            chip_rects.append(
                pygame.Rect(int(cx - chip_radius), int(cy - chip_radius), chip_dia, chip_dia)
            )

    # 8) Draw “Current Bet” text
    total_bet = sum(placed_chips.values())
    bet_text   = small_font.render(f"Current Bet: {total_bet}", True, WHITE)
    surf.blit(bet_text, (x0 + 10, y0_adj + table_h + chip_dia + 10))
    text_h = small_font.get_height()

    # 9) Draw “Bet” button below the text, with rounded corners
    btn_w = 100
    btn_h = 30
    btn_x = x0 + 10
    btn_y = y0_adj + table_h + chip_dia + 10 + text_h + 10
    bet_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surf, BUTTON_BG, bet_button_rect, border_radius=radius // 2)
    pygame.draw.rect(surf, BUTTON_BORDER, bet_button_rect, 1, border_radius=radius // 2)
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
       • A rank icon (K/Q/J) add amount to each cell in that row.
       • A suit icon    add amount to each cell in that column.
       • Any individual blue cell add amount there.
       Selection remains after placing.
    4) Click elsewhere deselect.
    """
    global selected_chip, placed_chips

    # 1) Bet button
    if bet_button_rect and bet_button_rect.collidepoint(mouse_pos):
        payload = {
            "bets": {f"{r}_{c}": amt for (r, c), amt in placed_chips.items()},
            "Withdraw_time": globals.Withdraw_time,
            "User_id": globals.User_id
        }
        print("Sending payload:", json.dumps(payload, indent=2))

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