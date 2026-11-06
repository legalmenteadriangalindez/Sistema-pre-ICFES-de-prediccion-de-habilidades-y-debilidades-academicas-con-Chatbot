"""Búsqueda opcional de material educativo externo, separada de memorias."""
import logging

from googlesearch import search
from youtube_search import YoutubeSearch

logger = logging.getLogger(__name__)


class ExternalResourcesMixin:
    def get_video_youtube(self, query: str, max_results: int = 3):
        try:
            videos = YoutubeSearch(query, max_results=max_results).to_dict()
            return [
                (item["title"], "https://www.youtube.com" + item["url_suffix"])
                for item in videos
            ]
        except Exception as exc:
            logger.warning(
                "youtube_search_failed",
                extra={"component": "external_resources", "error_type": type(exc).__name__},
            )
            return []

    @staticmethod
    def google_search(query):
        try:
            url = None
            for url in search(query, num_results=5):
                pass
            return url
        except Exception as exc:
            logger.warning(
                "google_search_failed",
                extra={"component": "external_resources", "error_type": type(exc).__name__},
            )
            return None
