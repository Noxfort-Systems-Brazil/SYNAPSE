import re
from src.formatters.report_number_formatter import ReportNumberFormatter
from src.formatters.report_text_sanitizer import ReportTextSanitizer


class ReportPostProcessor:
    """
    Global Facade for ABNT report post-processing, coordinating
    number formatting, text sanitization, semantic consistency, and placeholder integrity.
    """

    @classmethod
    def clean_ai_preamble(cls, text: str) -> str:
        return ReportTextSanitizer.clean_ai_preamble(text)

    @staticmethod
    def sanitize_truncated_text(text: str) -> str:
        return ReportTextSanitizer.sanitize_truncated_text(text)

    @classmethod
    def find_unresolved_placeholders(cls, text: str) -> list[str]:
        """Detects any template placeholder {variable_name} outside LaTeX math blocks."""
        if not text:
            return []
        # Strip math blocks to avoid matching LaTeX \frac{...} or _{...}
        non_math = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
        non_math = re.sub(r"\$[^\$]+?\$", "", non_math)
        # Match {word} that is not LaTeX escaped
        matches = re.findall(r"(?<![\\])\{([a-zA-Z][a-zA-Z0-9_]*)\}", non_math)
        return matches

    @classmethod
    def assert_no_unrendered_placeholders(cls, text: str) -> None:
        """Raises ValueError if any unresolved template placeholder remains in text."""
        placeholders = cls.find_unresolved_placeholders(text)
        if placeholders:
            raise ValueError(f"Unrendered template placeholder(s) detected in report: {', '.join(set(placeholders))}")

    @classmethod
    def enforce_semantic_consistency(cls, text: str) -> str:
        if not text:
            return ""

        cleaned = cls.clean_ai_preamble(text)
        cleaned = ReportNumberFormatter.normalize_percentages_in_text(cleaned)
        cleaned = cls.sanitize_truncated_text(cleaned)
        return cleaned
