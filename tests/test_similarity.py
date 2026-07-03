import pytest
from pydantic import ValidationError
from core.config import Settings
from core.similarity import RapidFuzzSimilarityEngine

def test_rapid_fuzz_similarity_engine_calculation():
    # Use exact weights
    engine = RapidFuzzSimilarityEngine(
        weight_ratio=0.25,
        weight_partial_ratio=0.25,
        weight_token_sort_ratio=0.25,
        weight_token_set_ratio=0.25
    )
    
    # Calculate score manually/automatically and assert it's between 0 and 100
    score = engine.score("hola nova", "hola nova")
    assert pytest.approx(score, 1e-6) == 100.0
    
    score_unrelated = engine.score("dibuja un dinosaurio azul", "hola nova")
    assert score_unrelated < 40.0

def test_settings_weights_validation():
    # Valid sum should not raise error
    settings = Settings(
        weight_ratio=0.25,
        weight_partial_ratio=0.25,
        weight_token_sort_ratio=0.25,
        weight_token_set_ratio=0.25
    )
    assert settings.weight_ratio == 0.25
    
    # Invalid sum must raise ValidationError
    with pytest.raises(ValidationError):
        Settings(
            weight_ratio=0.1,
            weight_partial_ratio=0.2,
            weight_token_sort_ratio=0.3,
            weight_token_set_ratio=0.3
        )
