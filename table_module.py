import pygame

def draw_table(surf, cols, rows, title,
               font_titles, font_cells, sw,
               labels_kjq=None, labels_suits=None,
               m=20,
               TABLE_BG=(0x35,0x0b,0x2d),
               GRID=(80,80,80),
               WHITE=(255,255,255),
               YELLOW=(200,200,0),
               ORANGE=(255,152,0),
               STRIPE1=(50, 50, 50),
               STRIPE2=(65, 65, 65),
               row_height=50,
               header_height=50):

    if not hasattr(draw_table, "scroll_offset"):
        draw_table.scroll_offset = 0
    for ev in pygame.event.get(pygame.MOUSEWHEEL):
        draw_table.scroll_offset = max(0, draw_table.scroll_offset - ev.y)

    tw = sw - 2*m
    cw = tw // len(cols)
    surf_h = surf.get_height()
    available = surf_h - (m + header_height*2 + m)
    max_visible = available // row_height
    max_offset = max(0, len(rows) - max_visible)
    draw_table.scroll_offset = min(draw_table.scroll_offset, max_offset)

    surf.fill(TABLE_BG)
    txt = font_titles.render(title, True, ORANGE)
    surf.blit(txt, (sw//2 - txt.get_width()//2, m))

    for i, h in enumerate(cols):
        display = "Marker Card" if h.lower() == "card_type" else h
        x = m + i*cw
        pygame.draw.rect(surf, YELLOW, (x, m+header_height, cw, header_height))
        surf.blit(font_cells.render(display, True, WHITE),
                  (x+5, m+header_height + (header_height-font_cells.get_height())//2))

    start_y = m + header_height*2
    for r in range(max_visible+1):
        y = start_y + r*row_height
        pygame.draw.line(surf, GRID, (m, y), (m+tw, y))
    for c in range(len(cols)+1):
        x = m + c*cw
        pygame.draw.line(surf, GRID, (x, start_y), (x, start_y + max_visible*row_height))

    for idx in range(max_visible):
        ridx = draw_table.scroll_offset + idx
        if ridx >= len(rows):
            break
        row_y = start_y + idx*row_height
        bg = STRIPE1 if idx % 2 == 0 else STRIPE2
        pygame.draw.rect(surf, bg, (m, row_y, tw, row_height))
        row = rows[ridx]

        cp_raw = row.get('claim_point')
        up_raw = row.get('unclaim_point')
        try:
            cp_val = float(cp_raw) if cp_raw not in (None, '', 'NA') else None
        except:
            cp_val = None
        try:
            up_val = float(up_raw) if up_raw not in (None, '', 'NA') else None
        except:
            up_val = None
        if cp_val is None and up_val is None:
            status = "Bet Placed"
        elif cp_val == 0 and up_val == 0:
            status = "Loose"
        elif (cp_val is not None and cp_val > 0) or (up_val is not None and up_val > 0):
            status = "WIN"
        else:
            status = "Loose"

        for cidx, key in enumerate(cols):
            cell_x = m + cidx*cw
            kl = key.lower()
            if kl == "card_type" and labels_kjq and labels_suits:
                if status == "Bet Placed":
                    txt_val = "NA"
                    surf.blit(
                        font_cells.render(txt_val, True, WHITE),
                        (cell_x + 5, row_y + (row_height-font_cells.get_height())//2)
                    )
                else:
                    gr = row.get('game_result', {})
                    num = None
                    if gr.get('winning_number') is not None:
                        num = gr.get('winning_number')
                    elif gr.get('lose_number') is not None:
                        num = gr.get('lose_number')
                    try:
                        ct = int(num)
                    except:
                        ct = None
                    if ct is None:
                        txt_val = "NA"
                        surf.blit(
                            font_cells.render(txt_val, True, WHITE),
                            (cell_x + 5, row_y + (row_height-font_cells.get_height())//2)
                        )
                    else:
                        face = 'K' if ct < 4 else 'Q' if ct < 8 else 'J'
                        suit_map = ['Spades','Diamond','Clubs','Hearts']
                        suit = suit_map[ct % 4]
                        img1, img2 = labels_kjq[face], labels_suits[suit]
                        h_img = row_height - 16
                        w1 = img1.get_width() * h_img // img1.get_height()
                        w2 = img2.get_width() * h_img // img2.get_height()
                        img1_s = pygame.transform.smoothscale(img1, (w1, h_img))
                        img2_s = pygame.transform.smoothscale(img2, (w2, h_img))
                        total_w = w1 + 4 + w2
                        x0 = cell_x + (cw - total_w)//2
                        y0 = row_y + (row_height - h_img)//2
                        surf.blit(img1_s, (x0, y0))
                        surf.blit(img2_s, (x0 + w1 + 4, y0))
            elif kl == "win_point":
                if cp_val is None and up_val is None:
                    txt_val = "NA"
                elif cp_val == 0 and up_val == 0:
                    txt_val = "0"
                elif cp_val is not None and cp_val > 0:
                    txt_val = str(int(cp_val) if hasattr(cp_val, "is_integer") and cp_val.is_integer() else str(cp_val))
                elif up_val is not None and up_val > 0:
                    txt_val = str(int(up_val) if hasattr(up_val, "is_integer") and up_val.is_integer() else str(up_val))
                else:
                    txt_val = "0"
                surf.blit(
                    font_cells.render(txt_val, True, WHITE),
                    (cell_x + 5, row_y + (row_height-font_cells.get_height())//2)
                )
            elif kl == "status":
                surf.blit(
                    font_cells.render(status, True, WHITE),
                    (cell_x + 5, row_y + (row_height-font_cells.get_height())//2)
                )
            else:
                txt = ''
                if kl in row:
                    txt = str(row.get(kl, ''))
                surf.blit(
                    font_cells.render(txt, True, WHITE),
                    (cell_x + 5, row_y + (row_height-font_cells.get_height())//2)
                )
