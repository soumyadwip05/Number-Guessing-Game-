"""Native Tk smoke test. Linux CI runs this with xvfb-run."""
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from between.app import BetweenApp
from between.game import Game
from between.storage import Store


with tempfile.TemporaryDirectory() as folder:
    root=tk.Tk()
    app=BetweenApp(root,Store(Path(folder)/"progress.json"))
    app.settings["animations"]=False
    app.game=Game(secret=73)
    root.update()
    app.guess.set("abc")
    app.submit()
    assert app.error.get() and app.game.attempts==0
    for guess in [50,75,62,68,71,73]:
        app.guess.set(str(guess))
        app.submit()
        root.update()
    assert app.game.state=="won"
    assert app.store.data["scores"]["Classic"]["played"]==1
    assert app.history.size()==6
    assert str(app.entry.cget("state"))=="disabled"
    app.new_round()
    assert app.game.state=="playing" and app.game.attempts==0
    app.guess.set("50")
    app.submit()
    with patch("between.app.messagebox.askyesno",return_value=False):
        previous=app.game
        app.new_round()
        assert app.game is previous
    with patch("between.app.messagebox.askyesno",return_value=True):
        app.new_round(difficulty="Expert")
    assert app.game.difficulty.maximum==1000
    # Exercise animation completion without depending on the random secret.
    app.settings["animations"]=True
    app.game=Game(secret=73)
    app.range_view=(1,100)
    app.guess.set("50")
    app.submit()
    root.after(600,root.quit)
    root.mainloop()
    assert app.range_view==(51,100)
    assert app.animation_job is None
    app.show_settings()
    root.update()
    assert app.dialog.winfo_exists()
    app.dialog.destroy()
    app.dialog=None
    app.close()
print("Native Tk UI smoke test passed")
