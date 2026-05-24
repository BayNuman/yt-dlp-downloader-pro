# core/suggester.py

class SmartFormatSuggester:
    """Heuristic Scoring Engine analyzing video metadata to predict the optimal download format."""
    
    def __init__(self):
        # Base scores for fallback categories
        self.base_scores = {
            "mp4_standard": 10,  # Base fallback level
            "mp4_vertical": 0,
            "mp3_music": 0,
            "mp3_podcast": 0
        }

        # Sets for O(1) membership queries
        self.music_keywords = {"music", "song", "official", "audio", "lyric", "album", "cover", "clip", "müzik", "şarkı", "klip"}
        self.podcast_keywords = {"podcast", "interview", "röportaj", "talk", "episode", "full length", "söyleşi", "sohbet", "ders", "lecture"}

    def analyze(self, info_dict: dict) -> str:
        """
        Analyzes metadata and outputs the highest-scoring format key.
        Keys: 'mp4_standard', 'mp4_vertical', 'mp3_music', 'mp3_podcast'
        """
        scores = self.base_scores.copy()

        # Gather data safely with defaults to avoid KeyErrors
        duration = info_dict.get("duration", 0.0) or 0.0
        width = info_dict.get("width", 1) or 1
        height = info_dict.get("height", 1) or 1
        
        title = str(info_dict.get("title", "")).lower()
        
        # Safe categories pulling
        categories = info_dict.get("categories") or []
        categories = [str(c).lower() for c in categories]
        
        # Safe tags pulling
        tags = info_dict.get("tags") or []
        tags = [str(t).lower() for t in tags]

        # Consolidate all metadata terms to analyze intersections
        text_pool = set(title.split() + categories + tags)

        # ----------------- HEURISTIC RULES -----------------
        
        # Rule 1: Aspect Ratio and Duration (Shorts/Reels detection)
        if height > width and duration < 180:
            scores["mp4_vertical"] += 60
        elif height > width:
            scores["mp4_vertical"] += 25

        # Rule 2: Official Categorizations
        if "music" in categories:
            scores["mp3_music"] += 45
        if "education" in categories or "science & technology" in categories or "news & politics" in categories:
            scores["mp3_podcast"] += 20

        # Rule 3: Title & Tags Text Intersection Queries
        music_hits = len(self.music_keywords.intersection(text_pool))
        scores["mp3_music"] += (music_hits * 15)

        podcast_hits = len(self.podcast_keywords.intersection(text_pool))
        scores["mp3_podcast"] += (podcast_hits * 20)

        # Rule 4: Duration Behavior Analysis
        # Over 45 minutes -> highly likely a podcast, tutorial, or background lecture
        if duration > 2700:
            scores["mp3_podcast"] += 35
            scores["mp4_standard"] -= 15  # Discourage large video downloads

        # Result selection
        best_format = max(scores, key=scores.get)
        print(f"[Heuristic Suggester] Engine Scores: {scores} | Winner: {best_format}")
        
        return best_format
