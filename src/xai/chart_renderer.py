# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import io
import base64
import logging
from typing import Any, Dict, List, Optional
import matplotlib
import matplotlib.pyplot as plt

# Ensure matplotlib does not try to open windows (headless mode)
matplotlib.use("Agg")

logger = logging.getLogger("Synapse.XAI.ChartRenderer")


class ChartRenderer:
    """
    Renders neural feature importance horizontal bar charts using headless Matplotlib.
    Outputs images directly as bytes, base64 strings or saves to disk.
    """

    def __init__(self, target_id: str = "ALL", title: Optional[str] = None) -> None:
        self.target_id = target_id
        self.custom_title = title

    def render(self, sorted_analysis: List[Dict[str, Any]], output_path: str) -> None:
        data = self.render_to_bytes(sorted_analysis)
        with open(output_path, "wb") as f:
            f.write(data)

    def render_to_bytes(self, sorted_analysis: List[Dict[str, Any]]) -> bytes:
        plt.close("all")

        top_items = sorted_analysis[:12] if sorted_analysis else []
        names = [x.get("name", "Sensor") for x in top_items]
        values = [abs(float(x.get("importance", 0.0))) for x in top_items]

        if not names:
            names = ["Nenhum dado amostrado"]
            values = [0.0]

        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.barh(names, values, color="#2563EB", edgecolor="#1D4ED8", height=0.6)

        # Value annotations on bar tips
        for bar in bars:
            width = bar.get_width()
            if width > 0.001:
                val_str = f"{width * 100:.1f}%".replace(".", ",") if width <= 1.0 else f"{width:.1f}%".replace(".", ",")
                ax.annotate(
                    val_str,
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=8.5,
                    color="#374151"
                )

        if self.custom_title:
            title_text = self.custom_title
        elif str(self.target_id).upper() in ["ALL", "ALL_AGENTS", "TODOS", "REDE_GERAL", "GLOBAL"]:
            title_text = "Atribuição de Relevância por Gradientes Integrados — Malha Arterial"
        else:
            title_text = f"Atribuição de Relevância por Gradientes Integrados — Estação / Detector {self.target_id}"

        ax.set_xlabel("Importância Relativa (%) — Gradientes Integrados (Captum)", fontsize=9.5, labelpad=8)
        ax.set_title(title_text, fontsize=11, fontweight="bold", pad=12)
        ax.invert_yaxis()
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.set_axisbelow(True)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=160)
        plt.close(fig)
        return buf.getvalue()

    def render_to_base64(self, sorted_analysis: List[Dict[str, Any]]) -> str:
        raw_bytes = self.render_to_bytes(sorted_analysis)
        return base64.b64encode(raw_bytes).decode("utf-8")
