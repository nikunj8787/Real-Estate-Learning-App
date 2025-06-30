import requests
import json
from datetime import datetime

class YouTubeContentManager:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def search_videos(self, query, max_results=10, order="relevance"):
        """Search YouTube videos"""
        
        if not self.api_key:
            # Return mock data if no API key
            return self._get_mock_videos(query, max_results)
        
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_info = {
                    "id": item['id']['videoId'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "thumbnail": item['snippet']['thumbnails']['medium']['url'],
                    "channel": item['snippet']['channelTitle'],
                    "published_at": item['snippet']['publishedAt']
                }
                
                # Get additional video details
                video_details = self._get_video_details(video_info['id'])
                video_info.update(video_details)
                
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            print(f"YouTube API Error: {str(e)}")
            return self._get_mock_videos(query, max_results)
    
    def _get_video_details(self, video_id):
        """Get additional video details"""
        
        params = {
            "part": "contentDetails,statistics",
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/videos", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                item = data['items'][0]
                return {
                    "duration": item['contentDetails']['duration'],
                    "views": item['statistics'].get('viewCount', '0'),
                    "likes": item['statistics'].get('likeCount', '0')
                }
            
        except Exception as e:
            print(f"Video details error: {str(e)}")
        
        return {
            "duration": "PT0M0S",
            "views": "0",
            "likes": "0"
        }
    
    def _get_mock_videos(self, query, max_results):
        """Return mock video data"""
        
        mock_videos = [
            {
                "id": "mock_video_1",
                "title": f"Complete Guide to {query}",
                "description": f"Comprehensive tutorial on {query} in Indian real estate context",
                "thumbnail": "https://via.placeholder.com/320x180",
                "channel": "Real Estate Expert",
                "duration": "PT15M30S",
                "views": "25000",
                "likes": "1200",
                "published_at": "2023-11-15T10:00:00Z"
            },
            {
                "id": "mock_video_2",
                "title": f"{query} - Practical Examples",
                "description": f"Real-world examples and case studies of {query}",
                "thumbnail": "https://via.placeholder.com/320x180",
                "channel": "Property Guru",
                "duration": "PT22M45S",
                "views": "18500",
                "likes": "890",
                "published_at": "2023-10-20T14:30:00Z"
            },
            {
                "id": "mock_video_3",
                "title": f"Advanced {query} Techniques",
                "description": f"Expert-level strategies for {query}",
                "thumbnail": "https://via.placeholder.com/320x180",
                "channel": "Real Estate Pro",
                "duration": "PT18M12S",
                "views": "12300",
                "likes": "654",
                "published_at": "2023-09-30T16:45:00Z"
            }
        ]
        
        return mock_videos[:max_results]
    
    def get_channel_videos(self, channel_id, max_results=20):
        """Get videos from a specific channel"""
        
        if not self.api_key:
            return self._get_mock_videos("channel content", max_results)
        
        # First get channel's upload playlist
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/channels", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                uploads_playlist = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                return self._get_playlist_videos(uploads_playlist, max_results)
            
        except Exception as e:
            print(f"Channel videos error: {str(e)}")
        
        return []
    
    def _get_playlist_videos(self, playlist_id, max_results):
        """Get videos from a playlist"""
        
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": max_results,
            "key": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/playlistItems", params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_info = {
                    "id": item['snippet']['resourceId']['videoId'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'],
                    "thumbnail": item['snippet']['thumbnails']['medium']['url'],
                    "channel": item['snippet']['channelTitle'],
                    "published_at": item['snippet']['publishedAt']
                }
                
                videos.append(video_info)
            
            return videos
            
        except Exception as e:
            print(f"Playlist videos error: {str(e)}")
            return []
    
    def curate_educational_content(self, topics):
        """Curate educational content for multiple topics"""
        
        curated_content = {}
        
        for topic in topics:
            # Search for educational videos
            videos = self.search_videos(f"{topic} real estate India tutorial", max_results=5)
            
            # Filter for educational content
            educational_videos = []
            for video in videos:
                # Simple filtering based on keywords
                if any(keyword in video['title'].lower() for keyword in ['tutorial', 'guide', 'explained', 'course', 'learn']):
                    educational_videos.append(video)
            
            curated_content[topic] = educational_videos
        
        return curated_content
    
    def format_duration(self, duration):
        """Format YouTube duration to readable format"""
        
        import re
        
        # Parse ISO 8601 duration format (PT15M30S)
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if match:
            hours, minutes, seconds = match.groups()
            
            parts = []
            if hours:
                parts.append(f"{hours}h")
            if minutes:
                parts.append(f"{minutes}m")
            if seconds:
                parts.append(f"{seconds}s")
            
            return " ".join(parts) if parts else "0s"
        
        return duration
    
    def format_view_count(self, views):
        """Format view count to readable format"""
        
        try:
            count = int(views)
            if count >= 1000000:
                return f"{count/1000000:.1f}M"
            elif count >= 1000:
                return f"{count/1000:.1f}K"
            else:
                return str(count)
        except:
            return views
