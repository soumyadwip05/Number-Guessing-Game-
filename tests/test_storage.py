import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from between.game import Game
from between.storage import Store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"nested/progress.json"

    def win(self,guesses):
        game=Game(secret=73)
        for guess in guesses:
            game.submit(str(guess))
        return game

    def test_defaults_do_not_create_files(self):
        store=Store(self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(store.data["settings"]["difficulty"],"Classic")

    def test_scores_persist_and_best_only_improves(self):
        store=Store(self.path)
        for guesses in [[50,73],[73],[50,75,73]]:
            self.assertTrue(store.record(self.win(guesses)))
        record=Store(self.path).data["scores"]["Classic"]
        self.assertEqual(record,{"played":3,"wins":3,"best":1})

    def test_losses_count_without_improving_best(self):
        store=Store(self.path)
        game=Game(secret=100)
        for number in range(1,8): game.submit(str(number))
        store.record(game)
        self.assertEqual(Store(self.path).data["scores"]["Classic"],{"played":1,"wins":0,"best":None})

    def test_unfinished_round_rejected(self):
        with self.assertRaises(ValueError):Store(self.path).record(Game())

    def test_preferences_roundtrip(self):
        store=Store(self.path)
        store.data["settings"].update(animations=False,sound=True,difficulty="Expert")
        store.save()
        self.assertEqual(Store(self.path).data["settings"],store.data["settings"])

    def test_corrupt_file_recovers_with_warning(self):
        self.path.parent.mkdir()
        self.path.write_text("not json",encoding="utf-8")
        store=Store(self.path)
        self.assertTrue(store.warning)
        self.assertEqual(store.data["scores"]["Classic"]["played"],0)

    def test_wrong_schema_recovers(self):
        self.path.parent.mkdir()
        for content in [[],{"version":2},{"version":1,"settings":[]},{"version":1,"scores":[]}]:
            self.path.write_text(json.dumps(content),encoding="utf-8")
            self.assertTrue(Store(self.path).warning)

    def test_invalid_record_ignored(self):
        store=Store(self.path)
        store.data["scores"]["Classic"]={"played":1,"wins":99,"best":-3}
        store.save()
        self.assertEqual(Store(self.path).data["scores"]["Classic"]["played"],0)

    def test_failed_save_keeps_previous_file_and_cleans_temporary(self):
        store=Store(self.path)
        store.save()
        before=self.path.read_bytes()
        store.data["settings"]["sound"]=True
        with patch("between.storage.os.replace",side_effect=PermissionError):
            self.assertFalse(store.save())
        self.assertTrue(store.warning)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(list(self.path.parent.glob(".progress-*")),[])


if __name__=="__main__":unittest.main()
