import pytest
from pydantic import ValidationError
import copy
from data_class.recommendation_params import AIRecommendationParams, NUMBER_OF_RECOMMENDATIONS

# ==============================================================================
# TEST DATA SETUP
# ==============================================================================

# Base data that is valid for the AI input model
BASE_VALID_DATA = {
    'seeds': {'track_name': 'Townie', 'artist_name': 'Mitski'},
    'energy': 0.8,
    'valence': 0.5,
    'featureWeight': 3.0,
    'acousticness': 0.1
}

# Data needed for a valid ReccoRecommendationParams
RECCO_REQUEST_DATA = {
    **BASE_VALID_DATA,
    'seeds': ['ID12345'],
    'size': NUMBER_OF_RECOMMENDATIONS 
}

# ==============================================================================
# TESTS FOR AIRecommendationParams (Input Validation)
# ==============================================================================

def test_ai_params_valid_creation():
    """Tests successful creation with base data and checks nested dict access."""
    params = AIRecommendationParams(**BASE_VALID_DATA)
    assert params.energy == 0.8
    assert params.seeds['artist_name'] == 'Mitski'

@pytest.mark.parametrize("field, invalid_value", [
    ("energy", 1.01),      # Must be <= 1.0
    ("acousticness", -0.01), # Must be >= 0.0
    ("popularity", 101),    # Must be <= 100
    ("featureWeight", 0.9),  # Must be >= 1.0
    ("tempo", 250.1),       # Must be <= 250
])
def test_ai_params_value_constraints(field, invalid_value):
    """Tests that Pydantic enforces the field constraints (le/ge)."""
    invalid_data = copy.deepcopy(BASE_VALID_DATA)
    invalid_data[field] = invalid_value
    
    with pytest.raises(ValidationError):
        AIRecommendationParams(**invalid_data)

def test_ai_params_missing_required_field():
    """Tests that the model requires the nested seed track dictionary."""
    data = copy.deepcopy(BASE_VALID_DATA)
    del data['seeds']
    
    with pytest.raises(ValidationError):
        AIRecommendationParams(**data)

def test_ai_params_coercion():
    """Tests that Pydantic correctly converts string representations to float/int."""
    data_str = {
        'seeds': {'track_name': 'Title', 'artist_name': 'Artist'},
        'energy': "0.85",
        'popularity': "70",
    }
    params = AIRecommendationParams(**data_str)
    
    assert isinstance(params.energy, float)
    assert params.energy == 0.85
    assert isinstance(params.popularity, int)
    assert params.popularity == 70
