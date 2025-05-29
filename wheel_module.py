# wheel_module.py
import pygame
import math
import time

# Wheel drawing and spin logic

def draw_wheel(surf, wheel_center, outer_radius, mid_radius, inner_radius,
               num_segments, outer_segment_colors, mid_segment_colors,
               labels_kjq, labels_suits, current_ang):
    """
    Draw the spinning wheel with outer K/J/Q icons and mid-level suits.
    """
    # Draw outer ring
    for i in range(num_segments):
        start_angle = math.radians(i * 360 / num_segments + current_ang)
        end_angle   = start_angle + math.radians(360 / num_segments)
        pts = [wheel_center]
        for step in range(31):
            a = start_angle + (end_angle - start_angle) * (step / 30)
            x = wheel_center[0] + outer_radius * math.cos(a)
            y = wheel_center[1] + outer_radius * math.sin(a)
            pts.append((x, y))
        pygame.draw.polygon(surf, outer_segment_colors[i], pts)
        pygame.draw.polygon(surf, (0,0,0), pts, 2)

    # Draw K/J/Q labels
    ranks = ['K', 'J', 'Q']
    for i in range(num_segments):
        img = labels_kjq[ranks[i % 3]]
        angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
        pos = (
            wheel_center[0] + (outer_radius * 0.7) * math.cos(angle),
            wheel_center[1] + (outer_radius * 0.7) * math.sin(angle)
        )
        surf.blit(img, img.get_rect(center=pos))

    # Draw mid-circle segments
    for i in range(num_segments):
        start = math.radians(i * 360 / num_segments + current_ang)
        end   = start + math.radians(360 / num_segments)
        pts   = [wheel_center]
        for step in range(31):
            a = start + (end - start) * (step / 30)
            pts.append((wheel_center[0] + mid_radius * math.cos(a),
                        wheel_center[1] + mid_radius * math.sin(a)))
        pygame.draw.polygon(surf, mid_segment_colors[i], pts)
        pygame.draw.polygon(surf, (0,0,0), pts, 2)

    # Draw suits
    suit_list = ['Spades', 'Diamond', 'Clubs', 'Hearts']
    for i in range(num_segments):
        img = labels_suits[suit_list[i % 4]]
        angle = math.radians((i + 0.5) * 360 / num_segments + current_ang)
        pos = (
            wheel_center[0] + (mid_radius * 0.85) * math.cos(angle),
            wheel_center[1] + (mid_radius * 0.85) * math.sin(angle)
        )
        surf.blit(img, img.get_rect(center=pos))

    # Draw inner circle
    pygame.draw.circle(surf, (255,255,255), wheel_center, inner_radius)
    pygame.draw.circle(surf, (0,0,0), wheel_center, inner_radius, 2)

def draw_left_table(surf, now_ts, labels_kjq, labels_suits,
                    x0, y0, label_size, suit_size, small_font):
    opts = {
        'col_widths': [200,75,75,75,75],
        'cell_height': 50,
        'rows': 4
    }
    col_widths = opts['col_widths']
    cell_h = opts['cell_height']
    rows = opts['rows']
    # Draw grid
    x = x0
    for w in col_widths:
        pygame.draw.line(surf, (255,255,255), (x, y0), (x, y0+rows*cell_h), 2)
        x += w
    pygame.draw.line(surf, (255,255,255), (x, y0), (x, y0+rows*cell_h), 2)
    y = y0
    for _ in range(rows+1):
        pygame.draw.line(surf, (255,255,255), (x0, y), (x0+sum(col_widths), y), 2)
        y += cell_h
    # Header row
    time_str = datetime.fromtimestamp(now_ts).strftime("%H:%M:%S")
    txt = f"Withdraw time: {time_str}"
    rect = pygame.Rect(x0, y0, col_widths[0], cell_h)
    surf.blit(small_font.render(txt, True, (255,255,255)), (rect.x+10, rect.y+10))
    # Suit icons
    suits = ['Spades','Diamond','Clubs','Hearts']
    for i, suit in enumerate(suits,1):
        img = labels_suits[suit]
        cell = pygame.Rect(x0+sum(col_widths[:i]), y0, col_widths[i], cell_h)
        surf.blit(img, img.get_rect(center=cell.center))
    # Rank rows
    ranks = ['K','Q','J']
    for ridx, rank in enumerate(ranks,1):
        img_rank = labels_kjq[rank]
        # rank column
        cell = pygame.Rect(x0, y0+ridx*cell_h, col_widths[0], cell_h)
        surf.blit(img_rank, img_rank.get_rect(center=cell.center))
        # rank+suit cells
        for cidx, suit in enumerate(suits,1):
            cell = pygame.Rect(x0+sum(col_widths[:cidx]), y0+ridx*cell_h,
                               col_widths[cidx], cell_h)
            # position icons with small gap
            total_w = label_size + suit_size + 10
            start_x = cell.centerx - total_w/2
            yc = cell.centery
            surf.blit(img_rank, img_rank.get_rect(center=(start_x+label_size/2, yc)))
            img_s = labels_suits[suit]
            surf.blit(img_s, img_s.get_rect(center=(start_x+label_size+10+suit_size/2, yc)))
def update_spin(current_time, spin_start, total_rotation):
    """
    Return updated angle and spinning flag based on elapsed time.
    """
    duration = 4.0
    elapsed = min(current_time - spin_start, duration)
    if elapsed <= 3.0:
        t = elapsed / 3.0
        ang = (total_rotation * 0.75) * t
        spinning = True
    else:
        u = (elapsed - 3.0) / 1.0
        eased = 1 - (1 - u) * (1 - u)
        ang = (total_rotation * 0.75) + (total_rotation * 0.25) * eased
        spinning = elapsed < duration
    return ang % 360, spinning
