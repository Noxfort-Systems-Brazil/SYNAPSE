# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any


class ReportNumberFormatter:
    """
    Formats numerical values for formal Brazilian ABNT standards (comma decimal, dot thousands).
    """

    @staticmethod
    def format_number(val: Any, decimal_places: int = 1) -> str:
        """Formats numbers with comma decimal and dot thousands."""
        if val is None or val == "":
            return "0,0"

        try:
            if isinstance(val, str):
                cleaned = val.replace("%", "").strip()
                if "," in cleaned and "." in cleaned:
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                elif "," in cleaned:
                    cleaned = cleaned.replace(",", ".")
                num = float(cleaned)
            else:
                num = float(val)

            fmt = f"{{:,.{decimal_places}f}}".format(num)
            return fmt.replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return str(val)

    @staticmethod
    def format_percent(val: Any, decimal_places: int = 1, is_ratio: bool = False) -> str:
        """
        Formats percentage with standard mathematical half-up rounding (ROUND_HALF_UP) and comma decimal.
        If is_ratio is True, multiplies by 100 before formatting.
        For example, 0.2945 with is_ratio=True -> '29,5%'.
        """
        if val is None or val == "":
            return "0,0%"

        try:
            from decimal import Decimal, ROUND_HALF_UP
            if isinstance(val, str):
                cleaned = val.replace("%", "").strip()
                if "," in cleaned and "." in cleaned:
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                elif "," in cleaned:
                    cleaned = cleaned.replace(",", ".")
                d = Decimal(cleaned)
            else:
                d = Decimal(str(val))

            if is_ratio:
                d = d * Decimal("100")

            target_exp = Decimal(f"1e-{decimal_places}")
            rounded = d.quantize(target_exp, rounding=ROUND_HALF_UP)
            res = f"{rounded:f}".replace(".", ",")
            return f"{res}%"
        except Exception:
            return f"{val}%"

    @staticmethod
    def normalize_percentages_in_text(text: str) -> str:
        """Replaces period decimal percentages with comma decimals (ex: 28.5% -> 28,5%)."""
        if not text:
            return ""
        return re.sub(r"(\d+)\.(\d+)%", r"\1,\2%", text)
