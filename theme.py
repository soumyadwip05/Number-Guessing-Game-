"""Shared neutral palette and a small scene renderer for the game board."""
BG = "#171B19"
PANEL = "#222923"
PANEL_ALT = "#29322B"
EDGE = "#465247"
TEXT = "#F1EEE4"
MUTED = "#B4BFB0"
FAINT = "#899786"
SAND = "#D5C5A5"
SAGE = "#BAC9B1"
ERROR = "#E0BCA8"


def blend(a, b, fraction):
    fraction = max(0, min(1, fraction))
    rgb = [round(int(a[i:i + 2], 16) * (1 - fraction) + int(b[i:i + 2], 16) * fraction)
           for i in (1, 3, 5)]
    return "#" + "".join(f"{v:02x}" for v in rgb)


def draw_board(canvas, game, record, title, message, width=1040, height=790,
               animated_range=None, flash=0, font="Arial"):
    """Draw the exact same board to a Tk Canvas or the documentation renderer."""
    canvas.delete("board")
    right = width - 342
    left_end = right - 24
    bottom = height - 66

    def rect(x, y, w, h, fill, outline="", radius=0):
        # Rectangles form the actual game interface, including its live range meter.
        if radius:
            points = [x+radius,y,x+w-radius,y,x+w,y,x+w,y+radius,x+w,y+h-radius,
                      x+w,y+h,x+w-radius,y+h,x+radius,y+h,x,y+h,x,y+h-radius,x,y+radius,x,y]
            return canvas.create_polygon(points, smooth=True, splinesteps=24, fill=fill,
                                         outline=outline, width=1, tags="board")
        return canvas.create_rectangle(x,y,x+w,y+h,fill=fill,outline=outline,tags="board")

    def text(x,y,value,size=14,fill=TEXT,bold=False,anchor="nw",**kwargs):
        return canvas.create_text(x,y,text=value,fill=fill,font=(font,-size,"bold" if bold else "normal"),
                                  anchor=anchor,tags="board",**kwargs)

    def line(x,y,x2,y2,fill=EDGE,width=1):
        return canvas.create_line(x,y,x2,y2,fill=fill,width=width,tags="board")

    # A subtle material gradient gives depth without bright glows.
    for y in range(0,height,4):
        rect(0,y,width,4,blend(BG,"#222923",y/height*.6))
    text(40,29,"between.",32,bold=True)
    text(43,78,"A number game about getting closer.",12,MUTED)
    text(width-42,41,"NUMBER GUESSING / PYTHON",10,FAINT,anchor="ne")
    line(40,110,width-40,110)
    text(44,128,"DIFFICULTY",9,FAINT,bold=True)
    text(276,154,f"1–{game.difficulty.maximum}   /   {game.difficulty.limit} guesses",12,MUTED)
    rect(40,200,left_end-40,bottom-200,PANEL,EDGE,22)
    rect(right,200,302,bottom-200,"#202620",EDGE,22)
    state = {"playing":"FIND THE HIDDEN NUMBER", "won":"ROUND COMPLETE", "lost":"NEXT ROUND, NEW CHANCE"}[game.state]
    text(67,225,state,10,SAND,bold=True)
    range_label = str(game.secret) if game.state != "playing" else f"{game.low} – {game.high}"
    text(64,265,range_label,52,bold=True)
    count = game.high-game.low+1
    caption = "the secret number" if game.state != "playing" else f"{count} possible number{'s' if count != 1 else ''} remaining"
    text(68,342,caption,12,MUTED)
    bar_left, bar_right = 69, left_end-30
    lo,hi = animated_range or (game.low,game.high)
    pos=lambda n: bar_left+(n-1)/(game.difficulty.maximum-1)*(bar_right-bar_left)
    line(bar_left,396,bar_right,396,EDGE,5)
    line(pos(lo),396,max(pos(lo)+2,pos(hi)),396,blend(SAND,TEXT,flash),7)
    for number in [1, game.difficulty.maximum]:
        text(pos(number),411,str(number),10,FAINT,anchor="n")
    text(68,453,title,22,blend(TEXT,SAND,flash),bold=True,width=left_end-94)
    text(69,495,message,12,MUTED,width=left_end-104)
    text(68,bottom-137,"YOUR GUESS" if game.state=="playing" else "READY FOR ANOTHER ROUND?",9,FAINT,bold=True)
    text(68,bottom-33,"Enter to guess     /     Ctrl or ⌘ + N for a new round",10,FAINT)
    text(right+25,225,"THIS ROUND",10,SAND,bold=True)
    text(right+23,268,str(game.attempts).zfill(2),47,bold=True)
    text(right+113,296,f"/ {game.difficulty.limit} guesses",12,MUTED)
    line(right+26,340,width-67,340)
    best="—" if record["best"] is None else str(record["best"])
    text(right+27,359,"PERSONAL BEST",9,FAINT,bold=True)
    text(width-70,353,best,19,SAND,bold=True,anchor="ne")
    text(right+27,392,f"{record['wins']} won  /  {record['played']} completed",11,MUTED)
    line(right+26,431,width-67,431)
    text(right+27,451,"GUESS HISTORY",10,SAND,bold=True)
    if not game.history:
        text(right+27,500,"Your first move goes here.\nTry the middle of the range.",12,FAINT,spacing=8)
    text(42,height-40,"SOUMYADWIP DAS",9,FAINT,bold=True)
    text(width-42,height-40,"Local scores. No account needed.",10,FAINT,anchor="ne")
    canvas.tag_lower("board")
    return {"right":right,"left_end":left_end,"bottom":bottom}
