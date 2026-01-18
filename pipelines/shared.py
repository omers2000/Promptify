"""
Shared utilities for both recommendation pipelines.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel
import streamlit as st

from llm.llm_prompt_interpreter import LlmPromptInterpreter

load_dotenv()


def get_gemini_interpretation(user_prompt: str, response_model: type[BaseModel]):
    """
    Interpret user prompt using Gemini AI with the specified schema.
    
    Args:
        user_prompt: User's playlist description
        response_model: Pydantic model class for the response 
                       (ReccoBeatsParams for V1, LocalSearchParams for V2)
        
    Returns:
        Parsed response object matching the response_model schema
        
    Raises:
        ValueError: If prompt is empty or GEMINI_KEY is missing
    """
    if not user_prompt.strip():
        raise ValueError("Playlist description cannot be empty.")
    
    api_key = st.secrets["GEMINI_KEY"]
    if not api_key:
        raise ValueError("GEMINI_KEY not found in environment variables.")
    
    interpreter = LlmPromptInterpreter(api_key=api_key)
    return interpreter.interpret(
        user_prompt=user_prompt,
        response_model=response_model
    )
