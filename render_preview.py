"""Export the shared board as SVG for README images without a display server.

The native Entry/Button/Listbox controls are illustrated separately. This is
an app-rendered preview, not a captured Windows or macOS screenshot.
"""
import argparse
from html import escape
from pathlib import Path
import sys
import textwrap

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from between.game import Game
from between.theme import draw_board, PANEL_ALT, EDGE, TEXT, MUTED, SAND, BG, ERROR


class SVGCanvas:
    def __init__(self):self.items=[]
    def delete(self,tag):self.items=[]
    def tag_lower(self,tag):pass
    def create_rectangle(self,x,y,x2,y2,**kw):
        self.items.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="{kw.get("fill","none")}" stroke="{kw.get("outline") or "none"}"/>')
    def create_line(self,x,y,x2,y2,**kw):
        self.items.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{kw.get("fill",EDGE)}" stroke-width="{kw.get("width",1)}" stroke-linecap="round"/>')
    def create_polygon(self,points,**kw):
        pairs=list(zip(points[::2],points[1::2]))
        if kw.get("smooth"):
            mids=[((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b in zip(pairs,pairs[1:]+pairs[:1])]
            commands=[f'M {mids[-1][0]} {mids[-1][1]}']
            commands += [f'Q {point[0]} {point[1]} {mid[0]} {mid[1]}' for point,mid in zip(pairs,mids)]
            path=" ".join(commands)+" Z"
            self.items.append(f'<path d="{path}" fill="{kw.get("fill","none")}" stroke="{kw.get("outline") or "none"}"/>')
        else:
            coords=" ".join(f'{x},{y}' for x,y in pairs)
            self.items.append(f'<polygon points="{coords}" fill="{kw.get("fill","none")}"/>')
    def create_text(self,x,y,**kw):
        family,size,weight=kw.get("font",("Arial",14,"normal"));size=abs(size)
        anchor={"nw":"start","n":"middle","ne":"end"}.get(kw.get("anchor","nw"),"start")
        lines=[]
        for line in str(kw.get("text","")).split("\n"):
            lines.extend(textwrap.wrap(line,width=max(1,int(kw["width"]/(size*.49)))) if "width" in kw else [line])
        fill=kw.get("fill",TEXT)
        for n,line in enumerate(lines):
            yy=y+size*.83+n*(size*1.22+kw.get("spacing",0))
            self.items.append(f'<text x="{x}" y="{yy}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(line)}</text>')
    def svg(self):return '<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="790">'+"".join(self.items)+'</svg>'


def render(game,title,message,animated_range=None,flash=0,error=""):
    c=SVGCanvas()
    record={"wins":1 if game.state=="won" else 0,"played":1 if game.state!="playing" else 0,
            "best":game.attempts if game.state=="won" else None}
    draw_board(c,game,record,title,message,animated_range=animated_range,flash=flash)
    def control(x,y,w,h,label,primary=False,size=14):
        c.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{SAND if primary else PANEL_ALT}" stroke="{EDGE}"/>')
        c.create_text(x+w/2,y+(h-size)/2,text=label,fill=BG if primary else TEXT,font=("Arial",size,"bold" if primary else "normal"),anchor="n")
    control(43,149,208,36,game.difficulty.name+"     ▾")
    control(600,146,231,40,"How to play / Settings",size=13)
    control(850,146,148,40,"New round",size=13)
    control(68,613,360,49,"",size=23)
    control(449,613,196,49,"Make a guess" if game.state=="playing" else "Play again",True)
    if game.state=="playing":c.create_line(83,626,83,650,fill=SAND,width=1)
    for n,guess in enumerate(game.history):
        c.create_text(725,495+n*21,text=f"{n+1:02d}    {guess.number:>4}    {guess.hint}",fill=TEXT,font=("Courier New",14,"normal"),anchor="nw")
    if error:c.create_text(69,667,text=error,fill=ERROR,font=("Arial",12,"normal"),anchor="nw")
    return c.svg()


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("output",type=Path);parser.add_argument("--frames",action="store_true")
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    game=Game(secret=73)
    title,message="Every guess is a clue.","Pick a number. We’ll tell you which direction to go."
    (args.output/"start.svg").write_text(render(game,title,message),encoding="utf-8")
    counter=0
    for guess in [50,75,62,68,71,73]:
        before=(game.low,game.high);result=game.submit(str(guess))
        title,message=result.title,result.message
        if args.frames:
            for f in range(12):
                phase=min(1,f/5);ease=1-(1-phase)**3
                bounds=tuple(a+(b-a)*ease for a,b in zip(before,(game.low,game.high)))
                (args.output/f"frame-{counter:03}.svg").write_text(render(game,title,message,bounds),encoding="utf-8")
                counter+=1
        (args.output/f"guess-{guess}.svg").write_text(render(game,title,message),encoding="utf-8")
    (args.output/"win.svg").write_text(render(game,title,message),encoding="utf-8")
    print(f"Rendered shared game board into {args.output}")
