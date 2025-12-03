import pytest
from pydantic import ValidationError
import copy
from recommendation_params import AIRecommendationParams, ReccoRecommendationParams, NUMBER_OF_RECOMMENDATIONS
from typing import List
# ==============================================================================
# TEST DATA SETUP
# ==============================================================================

# Base data that is valid for the AI input model
BASE_VALID_DATA = {
    'ai_choice_seed_track': {'track_name': 'Townie', 'artist_name': 'Mitski'},
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
    assert params.ai_choice_seed_track['artist_name'] == 'Mitski'

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
    del data['ai_choice_seed_track']
    
    with pytest.raises(ValidationError):
        AIRecommendationParams(**data)

def test_ai_params_coercion():
    """Tests that Pydantic correctly converts string representations to float/int."""
    data_str = {
        'ai_choice_seed_track': {'track_name': 'Title', 'artist_name': 'Artist'},
        'energy': "0.85",
        'popularity': "70",
    }
    params = AIRecommendationParams(**data_str)
    
    assert isinstance(params.energy, float)
    assert params.energy == 0.85
    assert isinstance(params.popularity, int)
    assert params.popularity == 70

# ==============================================================================
# TESTS FOR ReccoBeatsRequest (API Contract Validation)
# ==============================================================================

def test_reccobeats_request_valid_creation():
    """Tests successful creation of the final API model."""
    request = ReccoRecommendationParams(**RECCO_REQUEST_DATA)
    assert request.size == NUMBER_OF_RECOMMENDATIONS
    assert request.seeds == ['ID12345']
    assert request.energy == 0.8 # Check inherited field is present

@pytest.mark.parametrize("seeds_list", [
    [],                       # Fails min_length=1
    ['A', 'B', 'C', 'D', 'E', 'F'] # Fails max_length=5
])
def test_reccobeats_request_seed_length_validation(seeds_list: List[str]):
    """Tests that the strict seeds length constraint (1 <= length <= 5) is enforced."""
    invalid_data = copy.deepcopy(RECCO_REQUEST_DATA)
    invalid_data['seeds'] = seeds_list
    
    with pytest.raises(ValidationError):
        ReccoRecommendationParams(**invalid_data)

def test_to_query_params_removes_ai_choice_seed_track():
    """Tests the CRITICAL exclusion logic: the API should not see the search dict."""
    request = ReccoRecommendationParams(**RECCO_REQUEST_DATA)
    params = request.to_query_params()
    
    # CRITICAL CHECK: The intermediate search object MUST NOT be in the final API payload
    assert 'ai_choice_seed_track' not in params
    
    # Check that required API fields and one optional feature ARE present
    assert 'seeds' in params
    assert 'size' in params
    assert 'energy' in params

def test_to_query_params_removes_none_values():
    """Tests that optional fields not set (None) are correctly excluded."""
    data_small = {
        'ai_choice_seed_track': {'track_name': 'T', 'artist_name': 'A'},
        'energy': 0.7,
        'seeds': ['ID1'],
        'size': 10
        # All other optional fields are None
    }
    request = ReccoRecommendationParams(**data_small)
    params = request.to_query_params()
    
    # Expected keys: seeds, size, energy. All others excluded.
    assert 'energy' in params
    assert 'valence' not in params 
    assert len(params) == 3 

def test_inheritance_of_constraints():
    """Tests that the ReccoBeatsRequest inherits the parent's constraints (e.g., energy)."""
    invalid_data = copy.deepcopy(RECCO_REQUEST_DATA)
    invalid_data['energy'] = 1.0001 # Invalid for parent class
    
    with pytest.raises(ValidationError):
        ReccoRecommendationParams(**invalid_data)