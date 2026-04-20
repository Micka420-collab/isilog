from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher


class LearningService:
    """Local continuous-improvement helper.

    It does not retrain Gemma. It injects high-signal few-shot examples and
    category priors from validated tickets, fully local.
    """

    @staticmethod
    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def build_learning_context(self, transcript: str, feedback_rows: list[dict], top_k: int = 3) -> str:
        if not feedback_rows:
            return "Aucun exemple validé disponible."

        scored = sorted(
            feedback_rows,
            key=lambda row: self.similarity(transcript, row.get("transcript", "")),
            reverse=True,
        )[:top_k]

        category_counter = Counter(row.get("category_code", "autre_incident") for row in feedback_rows)
        common_categories = ", ".join(f"{k}:{v}" for k, v in category_counter.most_common(5))

        lines = [
            "Statistiques de catégories validées (historique local): " + common_categories,
            "Exemples validés proches:",
        ]

        for idx, row in enumerate(scored, start=1):
            ticket = row.get("ticket", {})
            lines.append(
                (
                    f"Exemple {idx} | categorie_code={row.get('category_code')} | "
                    f"objet={ticket.get('objet', '')} | resume_interne={ticket.get('resume_interne', '')}"
                )
            )

        return "\n".join(lines)
