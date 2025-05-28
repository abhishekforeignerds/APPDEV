# main_app.py

import pygame
import sys
import math
import random
import time
import requests
import os

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

def spin_animation():
    spins = random.randint(3, 6)
    final = random.uniform(0, 360)
    total = 360 * spins + final
    frames = 120
    angles = []
    for i in range(frames):
        t = i / (frames - 1)
        eased = 1 - (1 - t) ** 3
        angles.append(eased * total)
    return angles

def launch_main_app(user_data):
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    screen = pygame.display.set_mode((sw, sh))
    pygame.display.set_caption("Main App - Spinning Wheel and History")

    # Colors
    RED    = (229, 57,  53)
    DARK   = (33,  33,  33)
    WHITE  = (255, 255, 255)
    ORANGE = (255, 152,  0)
    BLACK  = (0,   0,    0)
    GRID   = (200, 200,  200)
    YELLOW = (255, 255,   0)
    TABLE_BG = (0x35, 0x0b, 0x2d)

    # Load background from bundled resource
    bg_path = resource_path("overlay-bg.jpg")
    background_img = pygame.image.load(bg_path).convert()
    background_img = pygame.transform.scale(background_img, (sw, sh))

    # Wheel configuration
    num_segments = 12
    wheel_radius = 150
    wheel_center = (sw // 2, sh // 2)
    segment_colors = [RED, DARK] * (num_segments // 2)

    # Fonts
    font      = pygame.font.SysFont("Arial", 24, bold=True)
    big_font  = pygame.font.SysFont("Arial", 32, bold=True)
    small_font= pygame.font.SysFont("Arial", 20)

    clock = pygame.time.Clock()

    # Window control & navigation buttons
    padding = 10
    icon_size = 30
    close_btn = pygame.Rect(sw - icon_size - padding, padding, icon_size, icon_size)
    min_btn   = pygame.Rect(close_btn.x - 20, padding + 5, 20, 20)

    btn_w, btn_h, pad = 140, 40, 10
    top_y = 20
    total_w = btn_w*3 + pad*2
    start_x = sw - pad - total_w
    account_btn = pygame.Rect(start_x,              top_y, btn_w, btn_h)
    history_btn = pygame.Rect(start_x + (btn_w+pad), top_y, btn_w, btn_h)
    simple_btn  = pygame.Rect(start_x + 2*(btn_w+pad), top_y, btn_w, btn_h)
    back_btn    = pygame.Rect(50, sh - 70, 100, 40)

    # State
    last_fetch    = time.time()
    last_auto_spin= time.time()
    mapped_list   = []
    show_mode     = 'wheel'
    spinning      = False
    current_ang   = 0
    spin_angles   = []
    spin_index    = 0

    def draw_text_center(surf, text, fnt, col, pos):
        txt = fnt.render(text, True, col)
        rect = txt.get_rect(center=pos)
        surf.blit(txt, rect)

    def draw_wheel(surf, angle_deg):
        for i in range(num_segments):
            start = math.radians(i * 360/num_segments + angle_deg)
            end   = start + math.radians(360/num_segments)
            pts   = [wheel_center]
            for step in range(31):
                a = start + (end - start) * (step/30)
                x = wheel_center[0] + wheel_radius * math.cos(a)
                y = wheel_center[1] + wheel_radius * math.sin(a)
                pts.append((x, y))
            pygame.draw.polygon(surf, segment_colors[i], pts)
            mid = (start + end) / 2
            tx = wheel_center[0] + 0.7*wheel_radius * math.cos(mid)
            ty = wheel_center[1] + 0.7*wheel_radius * math.sin(mid)
            draw_text_center(surf, str(i), font, WHITE, (tx, ty))

    def draw_pointer(surf):
        p = (wheel_center[0], wheel_center[1] - wheel_radius - 10)
        l = (p[0] - 10, p[1] + 20)
        r = (p[0] + 10, p[1] + 20)
        pygame.draw.polygon(surf, ORANGE, [p, l, r])

    def draw_user_info(surf):
        s = (
            f"ID:{user_data['id']}  "
            f"User:{user_data['username']}  "
            f"Name:{user_data.get('first_name','')} {user_data.get('last_name','')}  "
            f"Pts:{user_data.get('points',0)}  "
            f"Win:{user_data.get('winning_points',0)}"
        )
        draw_text_center(surf, s, font, WHITE, (200, 30))

    def draw_table(surf, cols, rows, title):
        m = 20
        tw = sw - 2*m
        cw = tw // len(cols)
        hh, rh = 40, 30
        surf.fill(TABLE_BG)
        draw_text_center(surf, title, big_font, ORANGE, (sw//2, m + hh//2))
        # headers
        for i, h in enumerate(cols):
            x = m + i*cw
            pygame.draw.rect(surf, YELLOW, (x, m, cw, hh))
            lab = small_font.render(h, True, WHITE)
            surf.blit(lab, (x+5, m + (hh-lab.get_height())//2))
        # grid & rows
        for r in range(len(rows)+1):
            y = m + hh + r*rh
            pygame.draw.line(surf, GRID, (m, y), (m+tw, y))
        for c in range(len(cols)+1):
            x = m + c*cw
            pygame.draw.line(surf, GRID, (x, m), (x, m+hh+rh*len(rows)))
        for ridx, row in enumerate(rows):
            for cidx, key in enumerate(cols):
                txt = str(row.get(key.lower(), ''))
                surf.blit(small_font.render(txt, True, WHITE),
                          (m + cidx*cw + 5, m + hh + ridx*rh + 5))
        pygame.draw.rect(surf, ORANGE, back_btn)
        draw_text_center(surf, "Close", big_font, BLACK, back_btn.center)

    while True:
        now = time.time()
        # fetch every 2s
        if now - last_fetch >= 2:
            try:
                resp = requests.post(
                    "https://spintofortune.in/api/app_dashboard_data.php",
                    data={"ID": str(user_data["id"])}
                )
                mapped_list = resp.json().get("mapped", [])
            except:
                pass
            last_fetch = now

        # auto-spin every 20s
        if show_mode=='wheel' and not spinning and now - last_auto_spin >= 20:
            spin_angles   = spin_animation()
            spin_index    = 0
            spinning      = True
            last_auto_spin= now

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if close_btn.collidepoint(ev.pos):
                    pygame.quit(); sys.exit()
                if min_btn.collidepoint(ev.pos):
                    pygame.display.iconify()
                if show_mode=='wheel':
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
            draw_user_info(screen)
            draw_wheel(screen, current_ang)
            draw_pointer(screen)
            for btn, txt in ((account_btn,"Account"),(history_btn,"History"),(simple_btn,"Card History")):
                pygame.draw.rect(screen, ORANGE, btn)
                draw_text_center(screen, txt, font, BLACK, btn.center)

        elif show_mode == 'history':
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point","status","action"]
            draw_table(screen, cols, mapped_list, "History")

        elif show_mode == 'summary':
            total_sale       = sum(float(item.get('bet_amount',0)) for item in mapped_list)
            total_win        = sum(float(item.get('claim_point',0)) for item in mapped_list)
            total_commission = total_sale * 0.03
            net_point        = total_sale - total_win - total_commission
            cols = ["Total Sale","Total Win","Total Commission","Net Point"]
            row  = {k.lower(): round(v,2) for k,v in zip(cols,[total_sale,total_win,total_commission,net_point])}
            draw_table(screen, cols, [row], "Account")

        else:  # simple/card history
            cols = ["card_type","ticket_serial","bet_amount","claim_point","unclaim_point"]
            draw_table(screen, cols, mapped_list, "Card History")

        # draw window controls
        pygame.draw.rect(screen, RED, close_btn)
        draw_text_center(screen, "X", font, WHITE, close_btn.center)
        pygame.draw.rect(screen, DARK, min_btn)
        ly = min_btn.y + min_btn.height//2
        pygame.draw.line(screen, WHITE, (min_btn.x+2, ly), (min_btn.x+min_btn.width-2, ly), 2)

        # spinning animation
        if spinning:
            if spin_index < len(spin_angles):
                current_ang = spin_angles[spin_index] % 360
                spin_index += 1
            else:
                spinning = False
                win_seg = int(((360-current_ang)%360)/(360/num_segments))
                print("Wheel stopped on segment:", win_seg)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    dummy = {"id":0,"username":"guest","first_name":"Guest","last_name":"","points":0,"winning_points":0}
    launch_main_app(dummy)
