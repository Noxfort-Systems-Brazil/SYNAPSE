# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re


class ReportTextSanitizer:
    """
    Sanitizes LLM/SLM generated markdown text, stripping conversational preambles,
    duplicate titles, and incomplete truncated outputs.
    """

    PREAMBLE_PATTERNS = [
        re.compile(r"^(Aqui (está|segue) (o|a) (relatório|laudo|parecer|análise)|Segue abaixo)[\s\S]*?\n\n", re.IGNORECASE),
        re.compile(r"^(Com base nos dados fornecidos|Conforme solicitado|Como Engenheiro|Como Perito)[\s\S]*?:\n\n", re.IGNORECASE),
        re.compile(r"^Certamente![\s\S]*?\n\n", re.IGNORECASE),
    ]

    @classmethod
    def clean_ai_preamble(cls, text: str) -> str:
        """Removes conversational AI greetings or preambles."""
        if not text:
            return ""

        cleaned = text.strip()
        for pat in cls.PREAMBLE_PATTERNS:
            cleaned = pat.sub("", cleaned).strip()

        return cleaned

    @staticmethod
    def sanitize_truncated_text(text: str) -> str:
        """Removes trailing incomplete words or cut off sentences."""
        if not text:
            return ""

        cleaned = text.strip()
        # If text doesn't end with sentence-ending punctuation and has open sentence, trim to last punctuation
        if cleaned and cleaned[-1] not in [".", ":", "!", "?", '"', "'", "`", "]", "}", ")", "*"]:
            last_period = max(cleaned.rfind(". "), cleaned.rfind(".\n"), cleaned.rfind(".**"))
            if last_period > len(cleaned) * 0.7:
                cleaned = cleaned[: last_period + 1].strip()

        return cleaned
