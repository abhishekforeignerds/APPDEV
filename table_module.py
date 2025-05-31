import pygame

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



