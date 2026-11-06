"""undefined"""
from youtube_search import YoutubeSearch
from googlesearch import search


class ExternalResourcesMixin:
    def get_video_youtube(self, query: str,max_results=3):
        videosSearch = YoutubeSearch(query, max_results=max_results).to_dict()
        videos= []

        for video in videosSearch:
            title = video["title"]
            url = 'https://www.youtube.com'+ video["url_suffix"]
            videos.append((title,url))
        return videos

    def google_search(query):
        url= None
        for url in search(query, num_results=5):
            url = url
        return url 




    
    


# ==========================================================CLASE USER MANAGER ==============================================================================


class UserManager:

    @staticmethod
