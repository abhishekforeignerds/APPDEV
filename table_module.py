import pygame
from datetime import datetime

# Table drawing utilities

def draw_table(surf, cols, rows, title, font_titles, font_cells,
               sw, m=20, TABLE_BG=(0x35,0x0b,0x2d), GRID=(80,80,80),
               WHITE=(255,255,255), YELLOW=(200,200,0), ORANGE=(255,152,0)):
    tw = sw - 2 * m
    cw = tw // len(cols)
    hh, rh = 40, 30
    surf.fill(TABLE_BG)
    # Title
    txt = font_titles.render(title, True, ORANGE)
    surf.blit(txt, (sw//2 - txt.get_width()//2, m))
    # Headers
    for i, h in enumerate(cols):
        x = m + i * cw
        pygame.draw.rect(surf, YELLOW, (x, m, cw, hh))
        surf.blit(font_cells.render(h, True, WHITE), (x+5, m + (hh-font_cells.get_height())//2))
    # Grid lines
    for r in range(len(rows)+1):
        y = m + hh + r * rh
        pygame.draw.line(surf, GRID, (m, y), (m+tw, y))
    for c in range(len(cols)+1):
        x = m + c * cw
        pygame.draw.line(surf, GRID, (x, m), (x, m+hh+rh*len(rows)))
    # Rows
    for ridx, row in enumerate(rows):
        for cidx, key in enumerate(cols):
            txt = str(row.get(key.lower(), ''))
            surf.blit(font_cells.render(txt, True, WHITE),
                      (m + cidx*cw +5, m + hh + ridx*rh +5))


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