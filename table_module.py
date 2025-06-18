import pygame
import requests
import json

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

    # persistent scroll + button state
    if not hasattr(draw_table, "scroll_offset"):
        draw_table.scroll_offset = 0
    if not hasattr(draw_table, "buttons"):
        draw_table.buttons = []

    draw_table.buttons.clear()

    # handle scroll wheel
    for ev in pygame.event.get(pygame.MOUSEWHEEL):
        draw_table.scroll_offset = max(0, draw_table.scroll_offset - ev.y)

    # layout
    tw = sw - 2*m
    cw = tw // len(cols)
    surf_h = surf.get_height()
    visible_rows = (surf_h - (m + header_height*2 + m)) // row_height
    draw_table.scroll_offset = min(draw_table.scroll_offset,
                                   max(0, len(rows) - visible_rows))

    # background + title
    surf.fill(TABLE_BG)
    title_surf = font_titles.render(title, True, ORANGE)
    surf.blit(title_surf, (sw//2 - title_surf.get_width()//2, m))

    # header labels
    for i, h in enumerate(cols):
        display = "Marker Card" if h.lower() == "card_type" else h.title()
        x = m + i*cw
        pygame.draw.rect(surf, YELLOW, (x, m+header_height, cw, header_height))
        surf.blit(font_cells.render(display, True, WHITE),
                  (x+5, m+header_height + (header_height-font_cells.get_height())//2))

    # grid lines
    start_y = m + header_height*2
    for r in range(visible_rows+1):
        y = start_y + r*row_height
        pygame.draw.line(surf, GRID, (m, y), (m+tw, y))
    for c in range(len(cols)+1):
        x = m + c*cw
        pygame.draw.line(surf, GRID, (x, start_y),
                         (x, start_y + visible_rows*row_height))

    # draw each visible row
    for idx in range(visible_rows):
        ridx = draw_table.scroll_offset + idx
        if ridx >= len(rows):
            break
        row = rows[ridx]
        row_y = start_y + idx*row_height
        bg = STRIPE1 if idx % 2 == 0 else STRIPE2
        pygame.draw.rect(surf, bg, (m, row_y, tw, row_height))

        # parse numeric points
        def to_val(v):
            try:
                return float(v) if v not in (None, '', 'NA') else None
            except:
                return None
        cp = to_val(row.get('claim_point'))
        up = to_val(row.get('unclaim_point'))

        # status logic
        if cp is None and up is None:
            status = "Bet Placed"
        elif cp == 0 and up == 0:
            status = "Loose"
        elif (cp or 0) > 0 or (up or 0) > 0:
            status = "WIN"
        else:
            status = "Loose"

        # draw cells
        for cidx, key in enumerate(cols):
            cell_x = m + cidx*cw
            kl = key.lower()

            # Marker Card images
            if kl == "card_type" and labels_kjq and labels_suits:
                if status == "Bet Placed":
                    txt_val = "NA"
                    surf.blit(font_cells.render(txt_val, True, WHITE),
                              (cell_x+5, row_y + (row_height-font_cells.get_height())//2))
                else:
                    gr = row.get('game_result', {})
                    num = gr.get('winning_number') or gr.get('lose_number')
                    try:
                        ct = int(num)
                    except:
                        ct = None
                    if ct is None:
                        txt_val = "NA"
                        surf.blit(font_cells.render(txt_val, True, WHITE),
                                  (cell_x+5, row_y + (row_height-font_cells.get_height())//2))
                    else:
                        face = 'K' if ct < 4 else 'Q' if ct < 8 else 'J'
                        suit_map = ['Spades','Diamond','Clubs','Hearts']
                        suit = suit_map[ct % 4]
                        img1, img2 = labels_kjq[face], labels_suits[suit]
                        h_img = row_height - 16
                        w1 = img1.get_width()*h_img//img1.get_height()
                        w2 = img2.get_width()*h_img//img2.get_height()
                        i1 = pygame.transform.smoothscale(img1,(w1,h_img))
                        i2 = pygame.transform.smoothscale(img2,(w2,h_img))
                        total_w = w1 + 4 + w2
                        x0 = cell_x + (cw - total_w)//2
                        y0 = row_y + (row_height - h_img)//2
                        surf.blit(i1,(x0,y0))
                        surf.blit(i2,(x0+w1+4,y0))

            # Win_point column
            elif kl == "win_point":
                if cp is None and up is None:
                    out = "NA"
                elif cp == 0 and up == 0:
                    out = "0"
                elif cp and cp > 0:
                    out = str(int(cp)) if cp.is_integer() else str(cp)
                elif up and up > 0:
                    out = str(int(up)) if up.is_integer() else str(up)
                else:
                    out = "0"
                surf.blit(font_cells.render(out, True, WHITE),
                          (cell_x+5, row_y + (row_height-font_cells.get_height())//2))

            # Status column
            elif kl == "status":
                surf.blit(font_cells.render(status, True, WHITE),
                          (cell_x+5, row_y + (row_height-font_cells.get_height())//2))

            # Action button
            elif kl == "action":
                if (cp in (None,0)) and (up in (None,0)):
                    label, off = "Unclaimable", True
                elif up == 0 and cp and cp > 0:
                    label, off = "Claimed", True
                elif cp == 0 and up and up > 0:
                    label, off = "Claim", False
                else:
                    label, off = "Unclaimable", True

                bw, bh = cw-10, row_height-10
                bx, by = cell_x+5, row_y+5
                color = (100,100,100) if off else (0,150,0)
                pygame.draw.rect(surf, color, (bx,by,bw,bh), border_radius=6)
                txt_s = font_cells.render(label, True, WHITE)
                surf.blit(txt_s, (bx + (bw-txt_s.get_width())//2,
                                  by + (bh-txt_s.get_height())//2))

                if not off:
                    draw_table.buttons.append({
                        'rect': pygame.Rect(bx,by,bw,bh),
                        'ticket_serial': row.get('ticket_serial')
                    })

            # default text
            else:
                text = str(row.get(kl, ''))
                surf.blit(font_cells.render(text, True, WHITE),
                          (cell_x+5, row_y + (row_height-font_cells.get_height())//2))

    # cursor change: pointer over any active button
    mx, my = pygame.mouse.get_pos()
    over = any(btn['rect'].collidepoint((mx,my)) for btn in draw_table.buttons)
    if over:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


def handle_claim_click(pos):
    """Call from your main loop on left‐click to fire the Claim API."""
    if not hasattr(draw_table, "buttons"):
        return

    for btn in draw_table.buttons:
        if btn['rect'].collidepoint(pos):
            ts = btn['ticket_serial']
            payload = {"ticket_serial": ts}

            # build the request manually so we can inspect it
            url     = "https://spintofortune.in/api/app_claim_point.php"
            payload = {"ticket_serial": ts}

            # Manually serialize and set headers so we know exactly what's sent
            payload_json = json.dumps(payload)
            headers = {
                "Content-Type":   "application/json; charset=UTF-8",
                "Content-Length": str(len(payload_json))
            }

            resp = requests.post(url, data=payload_json, headers=headers)
            print(f"[DEBUG] HTTP {resp.status_code}: {resp.text!r}")

