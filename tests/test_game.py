import unittest
from unittest.mock import patch

from between.game import DIFFICULTIES, Game


class GameTests(unittest.TestCase):
    def test_story(self):
        game=Game(secret=73)
        expected=[(51,100),(51,74),(63,74),(69,74),(72,74),(73,73)]
        for guess,bounds in zip([50,75,62,68,71,73],expected):
            result=game.submit(str(guess))
            self.assertTrue(result.accepted)
            self.assertEqual((game.low,game.high),bounds)
        self.assertEqual(game.state,"won")
        self.assertEqual(game.attempts,6)
        self.assertIn("6 guesses",result.message)

    def test_invalid_inputs_do_not_cost_turns(self):
        game=Game(secret=73)
        for text in [""," ","abc","3.5","0","101","-4","1e2","9"*5000]:
            self.assertFalse(game.submit(text).accepted)
        self.assertEqual(game.attempts,0)
        self.assertEqual((game.low,game.high),(1,100))

    def test_repeated_and_ruled_out_numbers_cost_no_turns(self):
        game=Game(secret=73)
        game.submit("50")
        self.assertFalse(game.submit("50").accepted)
        self.assertFalse(game.submit("20").accepted)
        self.assertEqual(game.attempts,1)

    def test_whitespace_and_plus_sign_are_valid(self):
        game=Game(secret=73)
        self.assertTrue(game.submit("  +73  ").accepted)
        self.assertEqual(game.state,"won")

    def test_first_guess_win(self):
        game=Game(secret=73)
        result=game.submit("73")
        self.assertIn("1 guess.",result.message)
        self.assertEqual(game.remaining,6)

    def test_both_range_endpoints(self):
        for name,difficulty in DIFFICULTIES.items():
            for secret in [1,difficulty.maximum]:
                game=Game(name,secret=secret)
                self.assertTrue(game.submit(str(secret)).accepted)
                self.assertEqual(game.state,"won")

    def test_last_turn_can_win(self):
        game=Game(secret=100)
        for guess in [1,2,3,4,5,6,100]:
            game.submit(str(guess))
        self.assertEqual(game.state,"won")
        self.assertEqual(game.remaining,0)

    def test_loss_reveals_secret_and_stops(self):
        game=Game(secret=100)
        for guess in range(1,8):
            result=game.submit(str(guess))
        self.assertEqual(game.state,"lost")
        self.assertIn("100",result.message)
        self.assertFalse(game.submit("100").accepted)
        self.assertEqual(game.attempts,7)

    def test_finished_round_cannot_change(self):
        game=Game(secret=1)
        game.submit("1")
        self.assertFalse(game.submit("2").accepted)
        self.assertEqual(game.attempts,1)

    def test_secret_is_chosen_once(self):
        with patch("between.game.random.randint",return_value=73) as choose:
            game=Game()
            game.submit("50")
            game.submit("73")
        choose.assert_called_once_with(1,100)

    def test_invalid_secrets(self):
        for value in [0,101,2.5,True,"73"]:
            with self.assertRaises(ValueError):
                Game(secret=value)

    def test_midpoint_strategy_wins_for_every_secret(self):
        # Exhaustively check all 1,150 possible secrets across the three modes.
        for name,difficulty in DIFFICULTIES.items():
            for secret in range(1,difficulty.maximum+1):
                game=Game(name,secret=secret)
                while game.state=="playing":
                    result=game.submit(str((game.low+game.high)//2))
                    self.assertTrue(result.accepted)
                    self.assertLessEqual(game.low,secret)
                    self.assertGreaterEqual(game.high,secret)
                self.assertEqual(game.state,"won",(name,secret))
                self.assertLessEqual(game.attempts,difficulty.limit)


if __name__=="__main__":
    unittest.main()
