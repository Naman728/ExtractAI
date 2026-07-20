"""AI Understanding Engine — post-extraction analysis layer.

Runs AFTER the extraction pipeline. Never scrapes; only interprets
normalized structured data into summaries, entities, and knowledge graphs.
"""

from app.ai.services.understanding_service import UnderstandingService

__all__ = ["UnderstandingService"]
