"""Small, local-only score file with validation and atomic replacement."""
import json
import os
from pathlib import Path
import sys
import tempfile

from .game import DIFFICULTIES


def data_path():
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "Between" / "progress.json"


def defaults():
    return {
        "version": 1,
        "settings": {"animations": True, "sound": False, "difficulty": "Classic"},
        "scores": {name: {"played": 0, "wins": 0, "best": None} for name in DIFFICULTIES},
    }


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else data_path()
        self.data = defaults()
        self.warning = ""
        self.load()

    def load(self):
        if not self.path.exists():
            return
        try:
            if self.path.stat().st_size > 100_000:
                raise ValueError("Score file is unexpectedly large")
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("version") != 1:
                raise ValueError("Unsupported score file")
            settings = raw.get("settings", {})
            if not isinstance(settings, dict):
                raise ValueError("Invalid settings")
            for key in ("animations", "sound"):
                if type(settings.get(key)) is bool:
                    self.data["settings"][key] = settings[key]
            if settings.get("difficulty") in DIFFICULTIES:
                self.data["settings"]["difficulty"] = settings["difficulty"]
            scores = raw.get("scores", {})
            if not isinstance(scores, dict):
                raise ValueError("Invalid scores")
            for name, difficulty in DIFFICULTIES.items():
                record = scores.get(name, {})
                if not isinstance(record, dict):
                    continue
                played, wins, best = record.get("played", 0), record.get("wins", 0), record.get("best")
                if type(played) is not int or type(wins) is not int or not 0 <= wins <= played:
                    continue
                if best is not None and (type(best) is not int or not 1 <= best <= difficulty.limit):
                    continue
                if (wins == 0 and best is not None) or (wins > 0 and best is None):
                    continue
                self.data["scores"][name] = {"played": played, "wins": wins, "best": best}
        except (OSError, ValueError, TypeError):
            self.data = defaults()
            self.warning = "Saved progress could not be read. This session starts with fresh scores."

    def save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=".progress-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(self.data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            self.warning = ""
            return True
        except OSError:
            self.warning = "Could not save progress. You can keep playing in this session."
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def record(self, game):
        if game.state not in ("won", "lost"):
            raise ValueError("Only finished rounds can be recorded")
        record = self.data["scores"][game.difficulty.name]
        record["played"] += 1
        if game.state == "won":
            record["wins"] += 1
            record["best"] = game.attempts if record["best"] is None else min(record["best"], game.attempts)
        return self.save()
