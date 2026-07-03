from abc import ABC, abstractmethod
from rapidfuzz import fuzz
from .config import settings

class SimilarityEngine(ABC):
    @abstractmethod
    def score(self, user_text: str, example_phrase: str) -> float:
        """
        Calculates the similarity score between the user text and an example phrase.
        Returns a value between 0.0 and 100.0.
        """
        pass

class RapidFuzzSimilarityEngine(SimilarityEngine):
    def __init__(
        self, 
        weight_ratio: float = settings.weight_ratio,
        weight_partial_ratio: float = settings.weight_partial_ratio,
        weight_token_sort_ratio: float = settings.weight_token_sort_ratio,
        weight_token_set_ratio: float = settings.weight_token_set_ratio
    ):
        self.weight_ratio = weight_ratio
        self.weight_partial_ratio = weight_partial_ratio
        self.weight_token_sort_ratio = weight_token_sort_ratio
        self.weight_token_set_ratio = weight_token_set_ratio

    def score(self, user_text: str, example_phrase: str) -> float:
        # RapidFuzz returns scores between 0.0 and 100.0
        score_ratio = fuzz.ratio(user_text, example_phrase)
        score_partial = fuzz.partial_ratio(user_text, example_phrase)
        score_sort = fuzz.token_sort_ratio(user_text, example_phrase)
        score_set = fuzz.token_set_ratio(user_text, example_phrase)
        
        combined_score = (
            self.weight_ratio * score_ratio +
            self.weight_partial_ratio * score_partial +
            self.weight_token_sort_ratio * score_sort +
            self.weight_token_set_ratio * score_set
        )
        return combined_score
