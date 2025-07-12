import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
import googleapiclient.discovery


# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class RecommenderError(Exception):
    """Custom exception for Recommender errors."""
    pass

class SkillRecommender:
    """A class to recommend learning resources for skills using the YouTube API."""
    
    def __init__(self, api_key: str):
        """Initialize the SkillRecommender with YouTube API key."""
        self.api_key = api_key
        if not self.api_key:
            raise RecommenderError("YouTube API key not found in environment variables.")
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=self.api_key)

    def fetch_youtube_resources(self, skill: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch the most relevant and high-quality YouTube resources for learning a specific skill.
        
        Args:
            skill (str): The skill to search for (e.g., 'deep learning').
            max_results (int): Maximum number of results to return.
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing resource information.
        """
        search_terms = [
            f"{skill} tutorial",
            f"learn {skill}",
            f"{skill} for beginners",
            f"{skill} course",
            f"advanced {skill}"
        ]
        
        all_resources = []
        
        for term in search_terms:
            try:
                search_response = self.youtube.search().list(
                    q=term,
                    part="snippet",
                    maxResults=10,
                    type="video",
                    relevanceLanguage="en",
                    order="relevance",
                    safeSearch="strict",
                    videoDefinition="high"
                ).execute()
                
                for item in search_response.get("items", []):
                    video_id = item["id"]["videoId"]
                    
                    video_response = self.youtube.videos().list(
                        part="snippet,contentDetails,statistics",
                        id=video_id
                    ).execute()
                    
                    if not video_response.get("items"):
                        continue
                        
                    video_info = video_response["items"][0]
                    
                    title = video_info["snippet"]["title"]
                    channel_title = video_info["snippet"]["channelTitle"]
                    published_at = video_info["snippet"]["publishedAt"]
                    description = video_info["snippet"]["description"]
                    view_count = int(video_info["statistics"].get("viewCount", 0))
                    like_count = int(video_info["statistics"].get("likeCount", 0))
                    comment_count = int(video_info["statistics"].get("commentCount", 0))
                    duration = video_info["contentDetails"]["duration"]
                    
                    duration_minutes = self.convert_duration_to_minutes(duration)
                    
                    relevance_score = self.calculate_relevance_score(
                        title, description, view_count, like_count, 
                        comment_count, duration_minutes, skill
                    )
                    
                    link = f"https://www.youtube.com/watch?v={video_id}&search={skill.replace(' ', '+')}"
                    
                    all_resources.append({
                        "platform": "YouTube",
                        "title": title,
                        "channel": channel_title,
                        "link": link,
                        "published_at": published_at,
                        "duration_minutes": duration_minutes,
                        "view_count": view_count,
                        "like_count": like_count,
                        "relevance_score": relevance_score
                    })
            except Exception as e:
                continue
        
        # Remove duplicates
        unique_resources = []
        video_ids_added = set()
        
        for resource in all_resources:
            video_id = resource["link"].split("v=")[1].split("&")[0]
            if video_id not in video_ids_added:
                unique_resources.append(resource)
                video_ids_added.add(video_id)
        
        # Sort by relevance score
        sorted_resources = sorted(
            unique_resources, 
            key=lambda x: x["relevance_score"], 
            reverse=True
        )
        
        return sorted_resources[:max_results]

    @staticmethod
    def convert_duration_to_minutes(duration: str) -> float:
        """Convert ISO 8601 duration format to minutes."""
        match = re.search(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
        
        hours = 0
        minutes = 0
        seconds = 0
        
        if match:
            hour_match = match.group(1)
            if hour_match:
                hours = int(hour_match[:-1])
                
            minute_match = match.group(2)
            if minute_match:
                minutes = int(minute_match[:-1])
                
            second_match = match.group(3)
            if second_match:
                seconds = int(second_match[:-1])
        
        total_minutes = hours * 60 + minutes + seconds / 60
        return round(total_minutes, 1)

    @staticmethod
    def calculate_relevance_score(title: str, description: str, views: int, likes: int, 
                                comments: int, duration: float, skill: str) -> int:
        """
        Calculate a relevance score for a video based on various factors.
        
        Args:
            title (str): Video title.
            description (str): Video description.
            views (int): Number of views.
            likes (int): Number of likes.
            comments (int): Number of comments.
            duration (float): Duration in minutes.
            skill (str): Skill being evaluated.
            
        Returns:
            int: Relevance score.
        """
        score = 0
        
        if skill.lower() in title.lower():
            score += 30
        
        if skill.lower() in description.lower():
            score += 10
        
        if views > 1000000:
            score += 25
        elif views > 100000:
            score += 20
        elif views > 10000:
            score += 15
        elif views > 1000:
            score += 5
        
        if views > 0:
            like_ratio = (likes / views) * 100
            if like_ratio > 5:
                score += 25
            elif like_ratio > 3:
                score += 20
            elif like_ratio > 1:
                score += 15
        
        if comments > 1000:
            score += 10
        elif comments > 100:
            score += 5
        
        if 10 <= duration <= 30:
            score += 15
        elif 30 < duration <= 60:
            score += 10
        elif duration > 60:
            score += 5
        
        return score

    def get_missing_skills_resources(self, missing_skill: str, max_results: int = 5) -> Dict[str, List[str]]:
        """
        Get YouTube course links for each missing technical skill from missing_skills.txt.
        
        Args:
            missing_skills_file (str): missing skill
            max_results (int): Maximum number of resources per skill.
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping each missing technical skill to a list of YouTube course links.
        """
        
        resources = self.fetch_youtube_resources(missing_skill, max_results)
        # Extract only the links from the resources
        links = [resource["link"] for resource in resources]
        
        return links
