"""
Module for handling interactions with the Google Gemini API.
Provides a wrapper class for making API calls and processing responses.
"""

import google.generativeai as genai
import streamlit as st
import json
from typing import Optional, Dict, Any
from logger import get_module_logger

logger = get_module_logger(__name__)

class ModelWrapper:
    """Wrapper class for Google Gemini API interactions."""

    def __init__(self):
        """
        Initialize the ModelWrapper with API configuration from secrets.toml.
        Raises ValueError if API key is not found.
        """
        try:
            # Try to get API key from secrets.toml
            self.api_key = st.secrets["GEMINI_API_KEY"]

            if not self.api_key:
                logger.error("GEMINI_API_KEY not found in secrets.toml")
                raise ValueError("GEMINI_API_KEY is required in secrets.toml")

            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise

    def format_prompt(self, system_prompt: str, content_prompt: str) -> str:
        """Format system and content prompts into a single prompt string."""
        formatted_prompt = f"""
[INST]
{system_prompt}

Content to process:
{content_prompt}
[/INST]
"""
        return formatted_prompt

    def count_tokens(self, text: str) -> int:
        """
        A simple token counting function.
        This implementation approximates tokens by splitting the text on whitespace.
        (For more accurate counting, consider using a specialized tokenizer.)
        """
        return len(text.split())

    def analyze_html_content(self, html_content: str) -> str:
        """
        Analyze HTML content using Gemini API to provide an extremely detailed, sentence-like analysis of the website.

        Args:
            html_content (str): Cleaned HTML content to analyze

        Returns:
            str: Analysis results in natural language
        """
        system_prompt = (
            "You are an expert web developer and technical analyst with extensive knowledge in website design, "
            "web frameworks, and modern web tools. Your task is to generate an extremely detailed, sentence-like "
            "analysis of the website's HTML structure and design. Include details on design elements such as the "
            "location and styling of the brand logo, menu items (and their names if discernible), interactive effects "
            "(e.g., spinning image effects, carousels, sliding sections), layout details (e.g., divisions with two "
            "columns, grid structures), and any web frameworks or tools in use (e.g., Bootstrap, React, Angular, etc.). "
            "Focus on clarity and precision in your descriptions."
        )

        content_prompt = (
            f"Examine the following website's HTML content and provide a detailed sentence-like analysis. Your analysis "
            f"should mention specific design elements such as:\n"
            f"- The presence and location of a brand logo (for example, top left).\n"
            f"- Menu items and their names (for example, top right navigation).\n"
            f"- Any interactive visual effects (for example, a spinning image effect, carousels, sliding sections).\n"
            f"- Layout details (for example, a division with two columns, grid layout, etc.).\n"
            f"- Identification of any web frameworks, tools, or libraries in use.\n\n"
            f"Here is the website's HTML:\n{html_content}"
        )

        return self.single_shot_completion(
            system_prompt=system_prompt,
            content_prompt=content_prompt,
            temperature=0.7
        )

    def single_shot_completion(
        self,
        system_prompt: str,
        content_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Make a single API call to generate content and return response.

        Args:
            system_prompt (str): System context/instruction.
            content_prompt (str): Content/query to process.
            temperature (float): Temperature for response generation.

        Returns:
            str: Generated response text.
        """
        logger.info("=== Starting Gemini API Request ===")
        formatted_prompt = self.format_prompt(system_prompt, content_prompt)
        logger.info("Formatted Prompt:")
        logger.info("-" * 50)
        logger.info(formatted_prompt)
        logger.info("-" * 50)

        # Count and log input token count
        input_token_count = self.count_tokens(formatted_prompt)
        logger.info("Input token count: %d", input_token_count)

        try:
            response = self.model.generate_content(
                contents=formatted_prompt,
                generation_config={'temperature': temperature}
            )
            logger.info("=== Gemini API Response Received ===")
            # Log the full response object so you can inspect its attributes
            logger.info("Full Gemini API Response object: %s", repr(response))

            # Check and log response.text if available
            if hasattr(response, 'text') and response.text:
                full_response_text = response.text
                logger.info("LLM Response Content:\n%s", full_response_text)
                # Count and log output token count
                output_token_count = self.count_tokens(full_response_text)
                logger.info("Output token count: %d", output_token_count)
            else:
                logger.info("Response object does not have a 'text' attribute or it is empty.")
                full_response_text = ""

            return full_response_text

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise
