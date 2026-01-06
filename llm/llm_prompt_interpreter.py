import random
from data_class.recommendation_params import ReccoBeatsParams, LocalSearchParams
from typing import Type, Union
from google import genai
from google.genai import types
import time

class LlmPromptInterpreter:

    _BASE_SYSTEM_INSTRUCTION = (
        "You are a music recommendation assistant. Your job is to translate a user's "
        "natural language request into specific technical audio features.\n"
        "CORE CONCEPTS:\n"
        "1. **Audio Features**: acousticness, danceability, energy, tempo, valence, popularity.\n"
        "2. **Weights (0.0 to 1.0)**: You must assign a weight to each feature to indicate its importance:\n"
        "   - 1.0 = Critical constraint (Must match very well).\n"
        "   - 0.5 = Moderate preference.\n"
        "   - 0.0 = Irrelevant (Do not filter by this).\n"
        "RULES:\n"
        "1. Analyze the user's mood, requested genre, or activity.\n"
    )

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite" 


    def interpret(
        self, 
        user_prompt: str, 
        response_model: Type[Union[ReccoBeatsParams, LocalSearchParams]], 
        retries: int = 3
    ):
        
        if response_model == ReccoBeatsParams:
            self.selection_strategies = [
                "CRITICAL: Do NOT pick the most obvious songs. Dig deep for hidden gems, B-sides, or underrated tracks that match the vibe perfectly.",
                "Select the most iconic, universally recognized anthems for this specific request. Pick songs everyone knows and loves.",
                "Select songs that are well-respected in the genre but not overplayed. Balance popularity with quality."
            ]

            current_strategy = random.choice(self.selection_strategies)
            print(f"llm's seed song selection strategy: {current_strategy}")

            system_instruction = (
                f"{self._BASE_SYSTEM_INSTRUCTION}"
                "2. You MUST provide seed songs.\n"
                f"3. Seed songs SELECTION STRATEGY: {current_strategy}\n"
                "4. **Feature Weights**: Even though this is an external API, provide weights so we can re-rank the results accurately locally.\n"
                "5. Return strictly valid JSON matching the schema."
           )
            
        elif response_model == LocalSearchParams:
           system_instruction = (
                f"{self._BASE_SYSTEM_INSTRUCTION}"
                "2. Rank the importance of features (weights) based on the user's emphasis for the Vector Search.\n"
                "3. Return strictly valid JSON matching the schema."
            )

        else:
            raise ValueError("Unsupported response model type.")
        
        
        for attempt in range(retries):
            try:
                # 3. Slightly increase temperature for variety (0.7 to 1.2 is usually the sweet spot)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=response_model,
                        # temperature=1.0, 
                    )
                )

                if response.parsed:
                    return response.parsed

                print(f"Attempt {attempt + 1} failed: Model returned empty response (Check Safety Filters). Retrying...")

            except Exception as e:
                print(f"Attempt {attempt + 1} Error: {e}")
            
            if attempt < retries - 1:
                time.sleep(1)
        
        raise ValueError("Gemini failed to generate valid JSON after multiple attempts.")
