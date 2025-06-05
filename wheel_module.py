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

def draw_wheel(
    surf,
    wheel_center,
    outer_radius,    # Placeholder—will be recalculated
    mid_radius,      # Placeholder—will be recalculated
    inner_radius,    # Placeholder—will be recalculated
    num_segments,
    outer_segment_colors,   # If you pass None, we’ll auto‐generate a palette
    mid_segment_colors,     # If None, we’ll auto‐generate
    labels_kjq,             # dict: {'K': Surface, 'J': Surface, 'Q': Surface}
    labels_suits,           # dict: {'Spades': S, 'Diamond': S, ...}
    current_ang             # in degrees, used to rotate the wheel
):
    """
    Draws a spinning wheel with:
      1. A subtle drop shadow behind the wheel.
      2. Smooth, high‐step arcs for each segment.
      3. Automatically generated HSV palettes (unless you pass your own).
         - To avoid any “yellow”‐colored slice, you can shift the hue in
           _generate_hsv_palette as shown above.
      4. A static arrow at the inner circumference (pointing up), in violet,
         now matching the size of the outer pointer.
      5. Alternating blinking RGB “LED” dots and sharper violet arrows
         exactly on a blue ribbon.
      6. A semi‐translucent blue “ribbon” around the outer circle (fixed pos).
      7. All radii and positions scale with window size.
      8. Arrow borders are drawn in the same violet color for smooth edges.
      9. The inner circle is now divided into the smallest segments, alternating dark/light gold.
     10. Suit icons on the mid ring are scaled dynamically based on screen size.
    """

    # --------------------------------------------------
    # 1. Recalculate radii and basic parameters based on window size
    # --------------------------------------------------
    width, height = surf.get_size()
    min_dim = min(width, height)

    # Base radii multipliers
    outer_radius = int(min_dim * 0.37)
    mid_radius   = int(min_dim * 0.22)
    inner_radius = int(min_dim * 0.07)   # Smallest circle

    # Override arrow sizes so all arrows match the pointer size
    inner_arrow_height = 20
    inner_arrow_width  = 20

    ribbon_arrow_height = 20
    ribbon_arrow_width  = 20

    # Dot radius (for LED dots)
    dot_radius = max(int(min_dim * 0.01), 3)

    # Ribbon thickness (semi‐translucent)
    ribbon_thickness = max(3, int(min_dim * 0.01))

    # Convert rotation angle to radians once
    current_rad = math.radians(current_ang)

    # --------------------------------------------------
    # 2. Prepare palettes (if the user passed None)
    # --------------------------------------------------
    if outer_segment_colors is None:
        outer_segment_colors = _generate_hsv_palette(
            num_segments,
            saturation=75,
            value=100,
            alpha=255
        )
    if mid_segment_colors is None:
        mid_segment_colors = _generate_hsv_palette(
            num_segments,
            saturation=60,
            value=85,
            alpha=255
        )

    # --------------------------------------------------
    # 3. Create an offscreen surface to draw the entire wheel + shadow
    # --------------------------------------------------
    temp_size = (
        outer_radius * 2 + SHADOW_OFFSET * 2,
        outer_radius * 2 + SHADOW_OFFSET * 2
    )
    temp_surf = pygame.Surface(temp_size, flags=pygame.SRCALPHA)
    temp_center = (
        outer_radius + SHADOW_OFFSET,
        outer_radius + SHADOW_OFFSET
    )

    # --------------------------------------------------
    # 3a. Draw drop shadow (a blurred-looking, semi-transparent circle)
    # --------------------------------------------------
    pygame.gfxdraw.filled_circle(
        temp_surf,
        temp_center[0],
        temp_center[1] + SHADOW_OFFSET,
        outer_radius,
        SHADOW_COLOR
    )

    # --------------------------------------------------
    # 4. Draw the outermost wheel circle (background + segment wedges)
    # --------------------------------------------------
    pygame.gfxdraw.filled_circle(
        temp_surf,
        temp_center[0],
        temp_center[1],
        outer_radius,
        (TABLE_BG[0], TABLE_BG[1], TABLE_BG[2], 255)
    )
    pygame.gfxdraw.aacircle(
        temp_surf,
        temp_center[0],
        temp_center[1],
        outer_radius,
        (GRID[0], GRID[1], GRID[2], 255)
    )

    for i in range(num_segments):
        start_ang = math.radians(i * 360 / num_segments) + current_rad
        end_ang   = start_ang + math.radians(360 / num_segments)

        pts = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start_ang + (end_ang - start_ang) * (s / ANGLE_STEPS)
            x = temp_center[0] + outer_radius * math.cos(a)
            y = temp_center[1] + outer_radius * math.sin(a)
            pts.append((int(x), int(y)))

        color = outer_segment_colors[i]
        pygame.gfxdraw.filled_polygon(temp_surf, pts, color)
        pygame.draw.polygon(temp_surf, (0, 0, 0), pts, 1)

    # --------------------------------------------------
    # 5. Draw the K/J/Q icons on the outer ring
    # --------------------------------------------------
    ranks = ['K', 'J', 'Q']
    for i in range(num_segments):
        rank_char = ranks[i % 3]
        img = labels_kjq[rank_char]

        angle = math.radians((i + 0.5) * 360 / num_segments) + current_rad
        px = int(temp_center[0] + outer_radius * 0.70 * math.cos(angle))
        py = int(temp_center[1] + outer_radius * 0.70 * math.sin(angle))

        temp_surf.blit(img, img.get_rect(center=(px, py)))

    # --------------------------------------------------
    # 6. Draw the mid‐circle background and segments
    # --------------------------------------------------
    pygame.gfxdraw.filled_circle(
        temp_surf,
        temp_center[0],
        temp_center[1],
        mid_radius,
        (TABLE_BG[0], TABLE_BG[1], TABLE_BG[2], 255)
    )
    pygame.gfxdraw.aacircle(
        temp_surf,
        temp_center[0],
        temp_center[1],
        mid_radius,
        (GRID[0], GRID[1], GRID[2], 255)
    )

    for i in range(num_segments):
        start_ang = math.radians(i * 360 / num_segments) + current_rad
        end_ang   = start_ang + math.radians(360 / num_segments)

        pts = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start_ang + (end_ang - start_ang) * (s / ANGLE_STEPS)
            x = temp_center[0] + mid_radius * math.cos(a)
            y = temp_center[1] + mid_radius * math.sin(a)
            pts.append((int(x), int(y)))

        color = mid_segment_colors[i]
        pygame.gfxdraw.filled_polygon(temp_surf, pts, color)
        pygame.draw.polygon(temp_surf, (0, 0, 0), pts, 1)

    # --------------------------------------------------
    # 7. Draw suit icons on the mid ring (scaled for screen size)
    # --------------------------------------------------
    # Determine a dynamic size for suit icons (e.g., 30% of mid_radius)
    suit_icon_size = int(mid_radius * 0.3)

    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    for i in range(num_segments):
        suit_name = suits[i % 4]
        img = labels_suits[suit_name]
        # Scale the image to (suit_icon_size × suit_icon_size)
        scaled_img = pygame.transform.smoothscale(img, (suit_icon_size, suit_icon_size))

        angle = math.radians((i + 0.5) * 360 / num_segments) + current_rad
        px = int(temp_center[0] + mid_radius * 0.75 * math.cos(angle))
        py = int(temp_center[1] + mid_radius * 0.75 * math.sin(angle))

        temp_surf.blit(scaled_img, scaled_img.get_rect(center=(px, py)))

    # --------------------------------------------------
    # 8. Draw the inner circle as the smallest segments (alternating dark/light gold)
    # --------------------------------------------------
    DARK_GOLD  = (184, 134, 11, 255)  # dark-goldenrod
    LIGHT_GOLD = (184, 134, 30, 255)   # light gold

    for i in range(num_segments):
        start_ang = math.radians(i * 360 / num_segments)
        end_ang   = start_ang + math.radians(360 / num_segments)

        pts = [temp_center]
        for s in range(ANGLE_STEPS + 1):
            a = start_ang + (end_ang - start_ang) * (s / ANGLE_STEPS)
            x = temp_center[0] + inner_radius * math.cos(a)
            y = temp_center[1] + inner_radius * math.sin(a)
            pts.append((int(x), int(y)))

        color = DARK_GOLD if (i % 2 == 0) else LIGHT_GOLD
        pygame.gfxdraw.filled_polygon(temp_surf, pts, color)
        pygame.draw.polygon(temp_surf, (0, 0, 0), pts, 1)

    # --------------------------------------------------
    # 9. Draw a semi‐translucent blue “ribbon” around the outer edge (fixed position)
    # --------------------------------------------------
    ribbon_center_radius = outer_radius + (ribbon_thickness // 2)
    blue_with_alpha = (
        RIBBON_COLOR_RGB[0],
        RIBBON_COLOR_RGB[1],
        RIBBON_COLOR_RGB[2],
        RIBBON_ALPHA
    )
    pygame.gfxdraw.aacircle(
        temp_surf,
        temp_center[0],
        temp_center[1],
        ribbon_center_radius,
        blue_with_alpha
    )
    pygame.draw.circle(
        temp_surf,
        blue_with_alpha,
        temp_center,
        ribbon_center_radius,
        ribbon_thickness
    )

    # --------------------------------------------------
    # 10. Draw alternating blinking RGB LED dots and sharper violet arrows
    #     exactly on the ribbon circumference
    #     Arrow borders are now drawn in the same violet color for smooth edges.
    # --------------------------------------------------
    elapsed = pygame.time.get_ticks()
    phase = (elapsed // 300) % 3
    if phase == 0:
        led_color = (255, 0, 0)    # Red
    elif phase == 1:
        led_color = (0, 255, 0)    # Green
    else:
        led_color = (0, 0, 255)    # Blue

    ribbon_inner_edge = ribbon_center_radius - (ribbon_thickness // 2)

    for i in range(num_segments):
        angle = math.radians(i * 360 / num_segments)

        if i % 2 == 0:
            # Draw a blinking LED dot at ribbon_inner_edge
            dot_x = temp_center[0] + ribbon_inner_edge * math.cos(angle)
            dot_y = temp_center[1] + ribbon_inner_edge * math.sin(angle)
            pygame.gfxdraw.filled_circle(
                temp_surf,
                int(dot_x),
                int(dot_y),
                dot_radius,
                led_color + (255,)
            )
            pygame.gfxdraw.aacircle(
                temp_surf,
                int(dot_x),
                int(dot_y),
                dot_radius,
                (0, 0, 0, 255)
            )
        else:
            # Draw a sharper inward-pointing arrow fully inside ribbon band
            tip_r  = ribbon_inner_edge - ribbon_arrow_height
            base_r = ribbon_inner_edge

            tip_x = temp_center[0] + tip_r * math.cos(angle)
            tip_y = temp_center[1] + tip_r * math.sin(angle)

            base_x = temp_center[0] + base_r * math.cos(angle)
            base_y = temp_center[1] + base_r * math.sin(angle)

            perp_dx = (ribbon_arrow_width / 2) * math.sin(angle)
            perp_dy = (ribbon_arrow_width / 2) * -math.cos(angle)

            p_tip   = (int(tip_x), int(tip_y))
            p_base1 = (int(base_x + perp_dx), int(base_y + perp_dy))
            p_base2 = (int(base_x - perp_dx), int(base_y - perp_dy))

            pygame.gfxdraw.filled_polygon(
                temp_surf,
                [p_tip, p_base1, p_base2],
                ARROW_COLOR + (255,)
            )
            # No separate border draw; filled polygon with ARROW_COLOR yields smooth edges.

    # --------------------------------------------------
    # 11. Draw static arrow at the top of the inner circumference (pointing up), in violet
    #     Now matching the pointer size (20×20)
    # --------------------------------------------------
    tip_inner_r = inner_radius + inner_arrow_height
    tip_inner_x = temp_center[0]
    tip_inner_y = temp_center[1] - inner_radius
    tip_inner = (int(tip_inner_x), int(tip_inner_y - inner_arrow_height))

    base_inner_left  = (
        int(tip_inner_x - inner_arrow_width / 2),
        int(tip_inner_y)
    )
    base_inner_right = (
        int(tip_inner_x + inner_arrow_width / 2),
        int(tip_inner_y)
    )

    pygame.gfxdraw.filled_polygon(
        temp_surf,
        [tip_inner, base_inner_left, base_inner_right],
        ARROW_COLOR + (255,)
    )
    pygame.gfxdraw.aapolygon(
        temp_surf,
        [tip_inner, base_inner_left, base_inner_right],
        ARROW_COLOR + (255,)
    )

    # --------------------------------------------------
    # 12. Blit the fully drawn “temp_surf” back onto the main surface (surf)
    # --------------------------------------------------
    dest_rect = pygame.Rect(
        wheel_center[0] - temp_center[0],
        wheel_center[1] - temp_center[1],
        temp_size[0],
        temp_size[1]
    )
    surf.blit(temp_surf, dest_rect)

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


TABLE_BG       = (30, 30, 30)
WHITE          = (255, 255, 255)
BLUE_BG        = (0, 102, 204)
RED            = (200, 0, 0)
BUTTON_BG      = (50, 50, 50)
BUTTON_BORDER  = (200, 200, 200)
GOLDEN         = (255, 215, 0)
BLACK          = (0, 0, 0)
SHADOW_COLOR   = (0, 0, 0, 100)

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
      1) A table of blue “play” cells (rows × cols) with a drop shadow.
      2) Header row: first cell (“Withdraw time”) centered; columns 1–4: suit image +
         a wider, shorter golden box containing a smaller “Play” circle, with an attached
         taller label box above reading “All <SuitPlural>”.
      3) First column for rows 1–3: rank image + a wider, shorter golden box containing
         a smaller “Play” circle, with an attached taller label box above reading “All <RankPlural>”.
      4) A tray of chips below the table.
      5) Any chips placed on the blue cells, showing their total amount.
      6) A visible text displaying the current total bet.
      7) A “Bet” button to submit placed bets via POST.
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
    radius    = 12

    # 0) Draw drop shadow for table
    shadow_surf = pygame.Surface((table_w, table_h), pygame.SRCALPHA)
    shadow_surf.fill(SHADOW_COLOR)
    surf.blit(shadow_surf, (x0 + 5, y0 + 5))

    # 1) Draw table background (no rounded corners)
    table_rect = pygame.Rect(x0, y0, table_w, table_h)
    pygame.draw.rect(surf, TABLE_BG, table_rect)

    # 2) Header row: first cell (“Withdraw time”) centered
    header_cell = pygame.Rect(x0, y0, col_w, cell_h)
    time_str    = datetime.fromtimestamp(now_ts).strftime("%H:%M:%S")
    label_surf  = small_font.render("Withdraw time:", True, WHITE)
    value_surf  = small_font.render(globals.Withdraw_time, True, WHITE)
    center_x    = header_cell.centerx
    center_y    = header_cell.centery
    surf.blit(
        label_surf,
        (
            center_x - label_surf.get_width() / 2,
            center_y - label_surf.get_height()
        )
    )
    surf.blit(
        value_surf,
        (
            center_x - value_surf.get_width() / 2,
            center_y + 2
        )
    )

    # Prepare a smaller label font for attached boxes
    label_font = pygame.font.Font(None, max(6, int(small_font.get_height() * 0.6)))

    # 3) Header row columns 1–4: suit image + wider/shorter golden box w/ “Play” circle + taller label
    suits = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    for i, suit in enumerate(suits, start=1):
        cell = pygame.Rect(x0 + col_w * i, y0, col_w, cell_h)
        suit_icon_rects[i] = cell

        # Determine smaller circle radius for “Play”
        circle_radius = int(min(col_w, cell_h) * 0.18)
        circle_dia    = circle_radius * 2

        # Padding inside golden box
        box_pad_horiz = int(circle_radius * 0.5)
        box_pad_vert  = int(circle_radius * 0.5)

        # Use full suit_size for slightly bigger suit icon
        img_w = suit_size
        img_h = suit_size

        # Total width: image + padding + circle diameter, then increase by 30%
        base_w = img_w + box_pad_horiz + circle_dia
        total_w = base_w * 1.3
        # Label box height
        label_text   = f"All {suit}{'s' if suit not in ('Spades','Clubs') else ''}"
        label_surf2  = label_font.render(label_text, True, BLACK)
        label_h      = label_surf2.get_height() + 8  # 8px vertical padding
        # Total height: max(img_h, circle_dia) + padding*2, then decrease by 10%
        base_h       = max(img_h, circle_dia) + box_pad_vert * 2
        total_h      = base_h * 0.9

        # Move everything slightly up (10 pixels)
        y_offset = 10

        # Compute golden box rectangle
        box_left = cell.centerx - total_w / 2
        box_top  = cell.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), int(total_w), int(total_h))

        # Draw golden box background with rounded corners
        pygame.draw.rect(surf, GOLDEN, golden_box, border_radius=radius//2)

        # Position suit image inside golden box (left side, centered vertically)
        img = pygame.transform.smoothscale(labels_suits[suit], (img_w, img_h))
        img_rect = img.get_rect()
        img_rect.center = (
            int(box_left + img_w / 2),
            int(box_top + total_h / 2)
        )
        surf.blit(img, img_rect)

        # Position circle center (right side inside golden box)
        circle_center_x = int(box_left + img_w + box_pad_horiz + circle_radius)
        circle_center_y = int(box_top + total_h / 2)

        # Draw Play circle with black border and black text
        pygame.gfxdraw.filled_circle(
            surf,
            circle_center_x,
            circle_center_y,
            circle_radius,
            GOLDEN
        )
        pygame.gfxdraw.aacircle(
            surf,
            circle_center_x,
            circle_center_y,
            circle_radius,
            BLACK
        )

        # Draw “Play” text in black, smaller font
        play_surf = label_font.render("Play", True, BLACK)
        surf.blit(
            play_surf,
            (
                circle_center_x - play_surf.get_width() / 2,
                circle_center_y - play_surf.get_height() / 2
            )
        )

        # 3a) Draw attached label box above golden box (no border), less width and more height
        label_box_w = total_w * 0.8
        label_box_h = label_h * 1.3
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), int(label_box_w), int(label_box_h))
        pygame.draw.rect(surf, GOLDEN, label_box, border_radius=radius//2)

        # Draw label text centered in label box (black text)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # 4) First column rows 1–3: rank image + wider/shorter golden box w/ “Play” circle + taller label
    ranks = ['K', 'Q', 'J']
    rank_label_map = {'K': 'All Kings', 'Q': 'All Queens', 'J': 'All Jacks'}
    for ridx, rank in enumerate(ranks, start=1):
        cell_rank = pygame.Rect(x0, y0 + ridx * cell_h, col_w, cell_h)
        rank_icon_rects[ridx] = cell_rank

        # Determine smaller circle radius for “Play”
        circle_radius = int(min(col_w, cell_h) * 0.18)
        circle_dia    = circle_radius * 2

        # Padding for golden box
        box_pad_horiz = int(circle_radius * 0.5)
        box_pad_vert  = int(circle_radius * 0.5)

        # Use full label_size for rank icon
        img_w = label_size
        img_h = label_size

        # Total width: image + padding + circle diameter, then increase by 30%
        base_w = img_w + box_pad_horiz + circle_dia
        total_w = base_w * 1.3
        # Label box height
        label_text   = rank_label_map[rank]
        label_surf2  = label_font.render(label_text, True, BLACK)
        label_h      = label_surf2.get_height() + 8
        # Total height: max(img_h, circle_dia) + padding*2, then decrease by 10%
        base_h       = max(img_h, circle_dia) + box_pad_vert * 2
        total_h      = base_h * 0.9

        # Move everything slightly up
        y_offset = 10

        # Compute golden box rectangle
        box_left = cell_rank.centerx - total_w / 2
        box_top  = cell_rank.centery - total_h / 2 - y_offset + label_h / 2
        golden_box = pygame.Rect(int(box_left), int(box_top), int(total_w), int(total_h))

        # Draw golden box background with rounded corners
        pygame.draw.rect(surf, GOLDEN, golden_box, border_radius=radius//2)

        # Position rank image inside golden box (left side)
        img_rank = pygame.transform.smoothscale(labels_kjq[rank], (img_w, img_h))
        img_rect = img_rank.get_rect()
        img_rect.center = (
            int(box_left + img_w / 2),
            int(box_top + total_h / 2)
        )
        surf.blit(img_rank, img_rect)

        # Position circle center (right side)
        circle_center_x = int(box_left + img_w + box_pad_horiz + circle_radius)
        circle_center_y = int(box_top + total_h / 2)

        # Draw Play circle with black border and black text
        pygame.gfxdraw.filled_circle(
            surf,
            circle_center_x,
            circle_center_y,
            circle_radius,
            GOLDEN
        )
        pygame.gfxdraw.aacircle(
            surf,
            circle_center_x,
            circle_center_y,
            circle_radius,
            BLACK
        )

        # Draw “Play” text in black
        play_surf = label_font.render("Play", True, BLACK)
        surf.blit(
            play_surf,
            (
                circle_center_x - play_surf.get_width() / 2,
                circle_center_y - play_surf.get_height() / 2
            )
        )

        # 4a) Draw attached label box above golden box (no border), less width and more height
        label_box_w = total_w * 0.8
        label_box_h = label_h * 1.3
        label_box_left = box_left + (total_w - label_box_w) / 2
        label_box_top  = box_top - label_box_h
        label_box = pygame.Rect(int(label_box_left), int(label_box_top), int(label_box_w), int(label_box_h))
        pygame.draw.rect(surf, GOLDEN, label_box, border_radius=radius//2)

        # Draw label text centered in label box (black text)
        surf.blit(
            label_surf2,
            (
                label_box.centerx - label_surf2.get_width() / 2,
                label_box.centery - label_surf2.get_height() / 2
            )
        )

    # 5) Draw blue “play” cells for the interior (rows 1–3, cols 1–4)
    ribbon_font = pygame.font.Font(None, max(6, int(small_font.get_height() * 0.6)))
    for ridx, rank in enumerate(ranks, start=1):
        for cidx, suit in enumerate(suits, start=1):
            cell = pygame.Rect(
                x0 + col_w * cidx,
                y0 + ridx * cell_h,
                col_w,
                cell_h
            )
            # Inset a blue box within this cell
            box_w = col_w * 0.7
            box_h = cell_h * 0.9
            inset_x = cell.left + (col_w - box_w) / 2
            inset_y = cell.top  + (cell_h - box_h) / 2
            blue_box = pygame.Rect(int(inset_x), int(inset_y), int(box_w), int(box_h))

            cell_rects[(ridx, cidx)] = blue_box

            pygame.draw.rect(surf, BLUE_BG, blue_box, border_radius=radius//3)
            pygame.draw.rect(surf, BLACK, blue_box, 1, border_radius=radius//3)

            # Within blue box, draw rank + suit icons (use full suit_size)
            total_w = label_size + suit_size + 8
            yc      = blue_box.centery
            img_rank_scaled = pygame.transform.smoothscale(labels_kjq[rank], (label_size, label_size))
            surf.blit(
                img_rank_scaled,
                img_rank_scaled.get_rect(
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

            # Draw red “Play” ribbon at bottom of blue box
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
                BLACK
            )

            play_surf = ribbon_font.render("Play", True, BLACK)
            surf.blit(
                play_surf,
                (
                    ribbon_rect.left + (ribbon_w - play_surf.get_width()) / 2,
                    ribbon_rect.top  + (ribbon_h - play_surf.get_height()) / 2
                )
            )

    # 6) Draw any placed chips on the blue cells
    for (ridx, cidx), total_amt in placed_chips.items():
        if (ridx, cidx) in cell_rects:
            center_x = cell_rects[(ridx, cidx)].centerx
            center_y = cell_rects[(ridx, cidx)].centery
            chip_radius = min(cell_h, col_w) // 6
            pygame.gfxdraw.filled_circle(surf, center_x, center_y, chip_radius, chip_defs[0]['color'])
            pygame.gfxdraw.aacircle(surf, center_x, center_y, chip_radius, BLACK)
            amt_surf = small_font.render(str(total_amt), True, WHITE)
            surf.blit(amt_surf, amt_surf.get_rect(center=(center_x, center_y)))

    # 7) Draw chip “tray” below the table
    chip_radius  = min(cell_h, col_w) // 6
    chip_dia     = chip_radius * 2
    chip_spacing = chip_dia + 10
    start_x      = x0 + 10
    chips_y      = y0 + table_h + chip_radius + 20

    angle = (now_ts * 360) % 360

    for idx, chip in enumerate(chip_defs):
        cx = start_x + idx * chip_spacing
        cy = chips_y

        base_chip_surf = pygame.Surface((chip_dia, chip_dia), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(base_chip_surf, chip_radius, chip_radius, chip_radius, chip['color'])
        pygame.gfxdraw.aacircle(base_chip_surf, chip_radius, chip_radius, chip_radius, BLACK)
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

    # 8) Draw “Current Bet” text
    total_bet = sum(placed_chips.values())
    bet_text   = small_font.render(f"Current Bet: {total_bet}", True, WHITE)
    surf.blit(bet_text, (x0 + 10, chips_y + chip_dia + 10))
    text_h = small_font.get_height()

    # 9) Draw “Bet” button below the text
    btn_w = 100
    btn_h = 30
    btn_x = x0 + 10
    btn_y = chips_y + chip_dia + 10 + text_h + 10
    bet_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(surf, BUTTON_BG, bet_button_rect)
    pygame.draw.rect(surf, BUTTON_BORDER, bet_button_rect, 1)
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