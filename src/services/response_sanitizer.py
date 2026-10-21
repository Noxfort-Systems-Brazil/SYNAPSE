# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import List, Optional, Callable
from src.interfaces.prompts import IResponseSanitizer


class ResponseSanitizer(IResponseSanitizer):
    """
    Sanitizer and post-processing service for LLM responses.
    
    Responsibilities (SRP):
    - Strip Chain-of-Thought reasoning tags (<think>...</think>).
    - Safely handle unclosed or truncated reasoning tags.
    - Apply custom post-processing filter pipelines.
    """

    def clean(self, response: str, cleaners: Optional[List[Callable[[str], str]]] = None) -> str:
        """
        Cleans and sanitizes LLM output text.
        
        Args:
            response: Raw LLM output string.
            cleaners: Optional list of post-processing filter functions: f(text) -> text.
            
        Returns:
            Cleaned response string.
        """
        if not response:
            return ""

        # Remove complete think blocks
        cleaned = re.sub(r'(?s)<think>.*?</think>', '', response).strip()

        # Handle unclosed think tags (e.g. truncated LLM generation)
        if '<think>' in cleaned:
            parts = cleaned.split('</think>', 1)
            if len(parts) > 1:
                cleaned = parts[1].strip()
            else:
                cleaned = cleaned.replace('<think>', '').strip()

        if cleaners:
            for cleaner in cleaners:
                cleaned = cleaner(cleaned)

        return cleaned
