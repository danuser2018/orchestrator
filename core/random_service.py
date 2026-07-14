import logging
import random

logger = logging.getLogger(__name__)

class RandomService:
    def flip_coin(self) -> str:
        """
        Simulates a coin toss, returning 'Cara' or 'Cruz'.
        """
        try:
            return random.choice(["Cara", "Cruz"])
        except Exception as e:
            logger.error(f"Failed to flip coin: {e}", exc_info=True)
            raise e

    def roll_dice(self) -> int:
        """
        Simulates a classic 6-sided dice roll, returning an integer between 1 and 6.
        """
        try:
            return random.randint(1, 6)
        except Exception as e:
            logger.error(f"Failed to roll dice: {e}", exc_info=True)
            raise e

    def random_int(self, min_value: int, max_value: int) -> int:
        """
        Generates a pseudo-random integer between min_value and max_value (inclusive).
        """
        try:
            return random.randint(min_value, max_value)
        except Exception as e:
            logger.error(f"Failed to generate random integer: {e}", exc_info=True)
            raise e
