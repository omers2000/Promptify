import random # <--- Import this
from data_class.recommendation_params import AIRecommendationParams
from google import genai
from google.genai import types

class LlmPromptInterpreter:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite" 
        
        # Define different "personalities" for song selection
        self.selection_strategies = [
            # 1. The Hipster (Deep cuts) - 40% chance (if you list it twice, or use weights)
            "CRITICAL: Do NOT pick the most obvious song. Dig deep for hidden gems, B-sides, or underrated tracks that match the vibe perfectly.",
            
            # 2. The Pop Culture Fan (Mainstream)
            "Select the most iconic, universally recognized anthem for this specific request. Pick a song everyone knows and loves.",
            
            # 3. The Balanced DJ (Middle ground)
            "Select a song that is well-respected in the genre but not overplayed. Balance popularity with quality.",
            
            # 4. The Chaos Agent (Wildcard)
            "Pick a song that is technically correct for the genre but might be a surprising or unconventional choice."
        ]

    def interpret(self, user_prompt: str) -> AIRecommendationParams:
        
        # 1. Randomly select a strategy
        current_strategy = random.choice(self.selection_strategies)
        print(f"llm's seed song selection strategy: {current_strategy}")

        # 2. Inject it into the system instruction
        system_instruction = (
            "You are a music recommendation assistant. Your job is to translate a user's "
            "natural language request into specific technical audio features for a Spotify-like API.\n"
            "RULES:\n"
            "1. Analyze the user's mood, requested genre, or activity.\n"
            "2. If NO song is mentioned, you MUST select a seed song.\n"
            f"3. Seed song SELECTION STRATEGY: {current_strategy}\n"  # <--- Dynamic injection here
            "4. Return strictly valid JSON matching the schema."
        )

        try:
            # 3. Slightly increase temperature for variety (0.7 to 1.2 is usually the sweet spot)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=AIRecommendationParams,
                    # temperature=1.0, 
                )
            )

            if response.parsed:
                return response.parsed
            else:
                raise ValueError("Model returned an empty response.")

        except Exception as e:
            print(f"Error interpreting prompt: {e}")
            raise