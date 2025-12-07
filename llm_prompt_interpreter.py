from recommendation_params import AIRecommendationParams
from typing import Optional
from google import genai
from google.genai import types

class LlmPromptInterpreter:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Gemini client.
        
        Args:
            api_key: Google Cloud/Gemini API key. If None, it attempts to read 
                     from the GOOGLE_API_KEY environment variable.
        """
        # If api_key is not provided, the Client will look for GOOGLE_API_KEY env var automatically
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite" 

    def interpret(self, user_prompt: str) -> AIRecommendationParams:
        """
        Analyzes the user's natural language prompt and returns a structured 
        AIRecommendationParams object using the Gemini API.
        """
        
        system_instruction = (
            "You are a music recommendation assistant. Your job is to translate a user's "
            "natural language request into specific technical audio features for a Spotify-like API.\n"
            "RULES:\n"
            "1. Analyze the user's mood, requested genre, or activity.\n"
            "2. If NO song is mentioned, you MUST select a seed song.\n"
            "3. CRITICAL: Do NOT pick the most obvious or famous song (e.g., never pick 'Weightless' for relaxing music). "
            "   Act like a 'Hipster' DJ. Dig deeper for hidden gems or less common tracks that match the vibe perfectly.\n"
            "4. Return strictly valid JSON matching the schema."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=AIRecommendationParams,
                    # temperature=2.0, # Low temperature for more consistent schema adherence
                )
            )

            # The SDK automatically validates and parses the JSON into your Pydantic model
            if response.parsed:
                return response.parsed
            else:
                # Fallback if parsed is empty (rare with structured output)
                raise ValueError("Model returned an empty response.")

        except Exception as e:
            print(f"Error interpreting prompt: {e}")
            # Return a safe default or re-raise depending on your app flow
            raise