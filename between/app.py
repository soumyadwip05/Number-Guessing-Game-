"""Tkinter desktop interface. The game itself lives in game.py."""
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .game import DIFFICULTIES, Game
from .storage import Store
from . import theme as T


class BetweenApp:
    def __init__(self, root, store=None):
        self.root = root
        self.store = store if store is not None else Store()
        self.settings = self.store.data["settings"]
        self.game = Game(self.settings["difficulty"])
        self.title = "Every guess is a clue."
        self.message = "Pick a number. We’ll tell you which direction to go."
        self.width, self.height = 1040, 790
        self.range_view = (self.game.low, self.game.high)
        self.flash = 0
        self.animation_job = None
        self.resize_job = None
        self.recorded = False
        self.dialog = None
        self.font = "Arial"
        root.title("Between · Number Guessing Game")
        root.geometry("1040x790")
        root.minsize(1040, 790)
        root.configure(bg=T.BG)
        root.protocol("WM_DELETE_WINDOW", self.close)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Sand.TButton", font=(self.font,-15,"bold"), padding=(16,12),
                        background=T.SAND, foreground=T.BG, borderwidth=0, focusthickness=2, focuscolor=T.BG)
        style.map("Sand.TButton", background=[("active",T.TEXT),("disabled",T.EDGE)],
                  foreground=[("disabled",T.MUTED)])
        style.configure("Quiet.TButton", font=(self.font,-13), padding=(12,10),
                        background=T.PANEL_ALT, foreground=T.TEXT, borderwidth=1, bordercolor=T.EDGE)
        style.map("Quiet.TButton", background=[("active",T.EDGE)])
        style.configure("TCombobox", fieldbackground=T.PANEL_ALT, background=T.PANEL_ALT,
                        foreground=T.TEXT, arrowcolor=T.SAND, bordercolor=T.EDGE, padding=8)
        style.map("TCombobox", fieldbackground=[("readonly",T.PANEL_ALT)],
                  selectbackground=[("readonly",T.PANEL_ALT)], selectforeground=[("readonly",T.TEXT)])
        style.configure("TCheckbutton", background=T.PANEL, foreground=T.TEXT, font=(self.font,-14), padding=8)
        style.map("TCheckbutton", background=[("active",T.PANEL_ALT)])
        style.configure("Vertical.TScrollbar", background=T.EDGE, troughcolor=T.PANEL,
                        bordercolor=T.PANEL, arrowcolor=T.MUTED)
        root.option_add("*TCombobox*Listbox.background",T.PANEL_ALT)
        root.option_add("*TCombobox*Listbox.foreground",T.TEXT)
        root.option_add("*TCombobox*Listbox.selectBackground",T.EDGE)

        self.canvas = tk.Canvas(root,bg=T.BG,highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Configure>",self.on_resize)
        self.difficulty = tk.StringVar(value=self.game.difficulty.name)
        self.selector = ttk.Combobox(root,textvariable=self.difficulty,values=list(DIFFICULTIES),
                                     state="readonly",font=(self.font,-15),takefocus=True)
        self.selector.bind("<<ComboboxSelected>>",self.change_difficulty)
        self.new_button = ttk.Button(root,text="New round",style="Quiet.TButton",command=self.new_round)
        self.settings_button = ttk.Button(root,text="How to play / Settings",style="Quiet.TButton",command=self.show_settings)
        self.guess = tk.StringVar()
        self.entry = tk.Entry(root,textvariable=self.guess,bg="#192019",fg=T.TEXT,
                             font=(self.font,-23),insertbackground=T.SAND,relief="flat",
                             highlightthickness=2,highlightbackground=T.EDGE,highlightcolor=T.SAND,
                             selectbackground=T.SAND,selectforeground=T.BG)
        self.submit_button = ttk.Button(root,text="Make a guess",style="Sand.TButton",command=self.submit)
        self.error = tk.StringVar(value=self.store.warning)
        self.error_label = tk.Label(root,textvariable=self.error,bg=T.PANEL,fg=T.ERROR,
                                    font=(self.font,-12),anchor="w",justify="left")
        self.history = tk.Listbox(root,bg="#202620",fg=T.TEXT,font=("Courier New",-14),
                                  relief="flat",highlightthickness=0,selectbackground=T.EDGE,
                                  selectforeground=T.TEXT,activestyle="none",exportselection=False)
        self.history_scroll = ttk.Scrollbar(root,orient="vertical",command=self.history.yview)
        self.history.configure(yscrollcommand=self.history_scroll.set)
        self.entry.bind("<Return>",self.submit)
        root.bind("<Control-n>",self.new_round)
        if sys.platform == "darwin":
            root.bind("<Command-n>",self.new_round)
        root.bind("<F1>",self.show_settings)
        self.draw()
        self.entry.focus_set()

    def on_resize(self,event):
        self.width,self.height=max(1040,event.width),max(790,event.height)
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job=self.root.after(35,self.finish_resize)

    def finish_resize(self):
        self.resize_job=None
        self.draw()

    def draw(self):
        record=self.store.data["scores"][self.game.difficulty.name]
        layout=T.draw_board(self.canvas,self.game,record,self.title,self.message,
                            self.width,self.height,self.range_view,self.flash,self.font)
        end,bottom,right=layout["left_end"],layout["bottom"],layout["right"]
        self.selector.place(x=43,y=149,width=208,height=36)
        self.settings_button.place(x=self.width-440,y=146,width=231,height=40)
        self.new_button.place(x=self.width-190,y=146,width=148,height=40)
        self.entry.place(x=68,y=bottom-111,width=end-314,height=49)
        self.submit_button.place(x=end-225,y=bottom-111,width=196,height=49)
        self.error_label.configure(wraplength=end-106)
        self.error_label.place(x=69,y=bottom-59,width=end-106,height=24)
        if self.game.history:
            self.history.place(x=right+27,y=492,width=239,height=bottom-514)
            self.history_scroll.place(x=right+267,y=492,width=12,height=bottom-514)
        else:
            self.history.place_forget()
            self.history_scroll.place_forget()

    def submit(self,event=None):
        if self.game.state != "playing":
            self.new_round()
            return "break"
        previous=self.range_view
        result=self.game.submit(self.guess.get())
        if not result.accepted:
            self.error.set(result.message)
            self.entry.selection_range(0,tk.END)
            self.entry.focus_set()
            if self.settings["sound"]:
                self.root.bell()
            return "break"
        self.error.set("")
        self.title,self.message=result.title,result.message
        recent=self.game.history[-1]
        self.history.insert(tk.END,f"{self.game.attempts:02d}    {recent.number:>4}    {recent.hint}")
        self.history.see(tk.END)
        self.guess.set("")
        if self.game.state != "playing":
            if not self.recorded:
                self.store.record(self.game)
                self.recorded=True
                self.error.set(self.store.warning)
            self.entry.configure(state="disabled")
            self.submit_button.configure(text="Play again")
            self.submit_button.focus_set()
            if self.settings["sound"]:
                self.root.bell()
        else:
            self.entry.focus_set()
        self.animate(previous,(self.game.low,self.game.high))
        return "break"

    def cancel_animation(self):
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job=None

    def animate(self,start,end):
        self.cancel_animation()
        if not self.settings["animations"]:
            self.range_view=end
            self.flash=0
            self.draw()
            return
        started=time.monotonic()
        def tick():
            progress=min(1,(time.monotonic()-started)/.36)
            eased=1-(1-progress)**3
            self.range_view=tuple(a+(b-a)*eased for a,b in zip(start,end))
            self.flash=(1-progress)*.45
            self.draw()
            if progress<1:
                self.animation_job=self.root.after(16,tick)
            else:
                self.animation_job=None
        tick()

    def new_round(self,event=None,difficulty=None):
        if self.game.state=="playing" and self.game.attempts:
            if not messagebox.askyesno("Start a new round?","Your current round will end without changing your scores.",parent=self.root):
                self.difficulty.set(self.game.difficulty.name)
                return "break"
        self.cancel_animation()
        choice=difficulty or self.game.difficulty.name
        self.game=Game(choice)
        self.difficulty.set(choice)
        self.settings["difficulty"]=choice
        self.store.save()
        self.recorded=False
        self.title="Every guess is a clue."
        self.message="Pick a number. We’ll tell you which direction to go."
        self.range_view=(self.game.low,self.game.high)
        self.flash=0
        self.history.delete(0,tk.END)
        self.guess.set("")
        self.error.set(self.store.warning)
        self.entry.configure(state="normal")
        self.submit_button.configure(text="Make a guess")
        self.draw()
        self.entry.focus_set()
        return "break"

    def change_difficulty(self,event=None):
        if self.difficulty.get()!=self.game.difficulty.name:
            self.new_round(difficulty=self.difficulty.get())

    def show_settings(self,event=None):
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return "break"
        window=tk.Toplevel(self.root)
        self.dialog=window
        window.title("Between · How to play")
        window.geometry("490x430")
        window.resizable(False,False)
        window.configure(bg=T.PANEL)
        window.transient(self.root)
        tk.Label(window,text="Follow the clues.",font=(self.font,-27,"bold"),bg=T.PANEL,fg=T.TEXT).pack(anchor="w",padx=30,pady=(28,16))
        instructions=("Guess the hidden number before your turns run out.\n\n"
                      "LOW means guess higher. HIGH means guess lower.\n"
                      "The range bar remembers everything you ruled out.\n\n"
                      "Invalid, repeated, or ruled-out guesses cost no turns.\n"
                      "Try a midpoint to remove about half the possibilities.\n\n"
                      "Enter: guess   ·   Ctrl / ⌘ + N: new round   ·   F1: help")
        tk.Label(window,text=instructions,font=(self.font,-13),justify="left",bg=T.PANEL,fg=T.MUTED).pack(anchor="w",padx=30)
        motion=tk.BooleanVar(value=self.settings["animations"])
        sound=tk.BooleanVar(value=self.settings["sound"])
        def update():
            self.settings.update(animations=motion.get(),sound=sound.get())
            self.store.save()
            self.error.set(self.store.warning)
            if not motion.get():
                self.cancel_animation()
                self.range_view=(self.game.low,self.game.high)
                self.flash=0
                self.draw()
        ttk.Checkbutton(window,text="Animate range changes",variable=motion,command=update).pack(anchor="w",padx=24,pady=(16,0))
        ttk.Checkbutton(window,text="System sound on invalid input and round end",variable=sound,command=update).pack(anchor="w",padx=24)
        def dismiss(event=None):
            window.destroy()
            self.dialog=None
            self.entry.focus_set() if self.game.state=="playing" else self.submit_button.focus_set()
        ttk.Button(window,text="Back to the game",style="Sand.TButton",command=dismiss).pack(anchor="e",padx=28,pady=12)
        window.protocol("WM_DELETE_WINDOW",dismiss)
        window.bind("<Escape>",dismiss)
        window.grab_set()

    def close(self):
        self.cancel_animation()
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.root.destroy()


def main():
    try:
        root=tk.Tk()
    except tk.TclError as exc:
        print("Between needs a graphical desktop and a Python installation with Tk support.",file=sys.stderr)
        print("Check your installation with: python -m tkinter",file=sys.stderr)
        print(str(exc),file=sys.stderr)
        raise SystemExit(1) from exc
    BetweenApp(root)
    root.mainloop()
