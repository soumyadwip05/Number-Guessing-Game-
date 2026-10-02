"""The rules, independent of windows, files, and animations."""
from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Difficulty:
    name: str
    maximum: int
    limit: int


DIFFICULTIES = {
    "Easy": Difficulty("Easy", 50, 6),
    "Classic": Difficulty("Classic", 100, 7),
    "Expert": Difficulty("Expert", 1000, 10),
}


@dataclass(frozen=True)
class Guess:
    number: int
    hint: str


@dataclass(frozen=True)
class Result:
    accepted: bool
    title: str
    message: str


class Game:
    """One round. Tests may supply a fixed secret for repeatable results."""

    def __init__(self, difficulty="Classic", secret=None):
        self.difficulty = DIFFICULTIES[difficulty]
        self.secret = random.randint(1, self.difficulty.maximum) if secret is None else secret
        if type(self.secret) is not int or not 1 <= self.secret <= self.difficulty.maximum:
            raise ValueError("Secret must be an integer inside the difficulty's range.")
        self.low = 1
        self.high = self.difficulty.maximum
        self.history = []
        self.state = "playing"

    @property
    def attempts(self):
        return len(self.history)

    @property
    def remaining(self):
        return self.difficulty.limit - self.attempts

    def submit(self, text):
        """Return a message. Invalid or ruled-out numbers do not cost a turn."""
        if self.state != "playing":
            return Result(False, "Round finished", "Choose Play again for a new secret.")
        try:
            number = int(text.strip())
        except (ValueError, AttributeError):
            return Result(False, "A whole number, please", "Type a number without decimal places.")
        if not 1 <= number <= self.difficulty.maximum:
            return Result(False, "Outside the game range", f"Use a number from 1 to {self.difficulty.maximum}.")
        if any(guess.number == number for guess in self.history):
            return Result(False, "You tried that one", "Choose a new number. No turn was used.")
        if not self.low <= number <= self.high:
            return Result(False, "That number is ruled out", f"Your clues leave {self.low} to {self.high}. No turn was used.")

        if number == self.secret:
            self.history.append(Guess(number, "MATCH"))
            self.low = self.high = number
            self.state = "won"
            noun = "guess" if self.attempts == 1 else "guesses"
            return Result(True, "You found it.", f"The secret was {number}. Solved in {self.attempts} {noun}.")

        if number < self.secret:
            self.low = number + 1
            hint = "LOW"
            title = "Go a little higher."
        else:
            self.high = number - 1
            hint = "HIGH"
            title = "Try a little lower."
        self.history.append(Guess(number, hint))
        if self.remaining == 0:
            self.state = "lost"
            return Result(True, "Out of guesses.", f"The secret was {self.secret}. A new round is a fresh start.")
        return Result(True, title, f"The secret is between {self.low} and {self.high}.")
