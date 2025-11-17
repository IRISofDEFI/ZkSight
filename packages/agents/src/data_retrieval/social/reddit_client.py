"""Reddit API client for community sentiment"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import httpx

from ..social_types import SocialMention, CommunitySentiment


logger = logging.getLogger(__name__)


class RedditClient:
    """
    Reddit API client for tracking Zcash community sentiment.
    
    Uses Reddit's OAuth2 API.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = "ChimeraAnalytics/1.0",
        timeout: float = 30.0
    ):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string
            timeout: Request timeout in seconds
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.base_url = "https://oauth.reddit.com"
        self.auth_url = "https://www.reddit.com/api/v1/access_token"
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": user_agent}
        )
        
        self.access_token: Optional[str] = None
        
        logger.info("Initialized Reddit client")
    
    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token.
        
        Returns:
            Access token
        """
        if self.access_token:
            return self.access_token
        
        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        
        response = await self.client.post(
            self.auth_url,
            auth=auth,
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        
        logger.info("Obtained Reddit access token")
        return self.access_token
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None
    ) -> dict:
        """
        Make Reddit API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON
        """
        token = await self._get_access_token()
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.user_agent
        }
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Reddit API request failed: {e}")
            raise
    
    async def search_subreddit(
        self,
        subreddit: str = "zec",
        query: str = "",
        limit: int = 100,
        time_filter: str = "day"
    ) -> List[SocialMention]:
        """
        Search posts in a subreddit.
        
        Args:
            subreddit: Subreddit name
            query: Search query (empty for all posts)
            limit: Maximum results
            time_filter: Time filter (hour, day, week, month, year, all)
            
        Returns:
            List of social mentions
        """
        endpoint = f"/r/{subreddit}/search" if query else f"/r/{subreddit}/new"
        
        params = {
            "limit": min(limit, 100),
            "t": time_filter
        }
        
        if query:
            params["q"] = query
            params["restrict_sr"] = "true"
        
        try:
            data = await self._request("GET", endpoint, params)
            
            mentions = []
            
            for post in data.get("data", {}).get("children", []):
                post_data = post["data"]
                
                # Calculate engagement (upvotes + comments)
                engagement = post_data.get("ups", 0) + post_data.get("num_comments", 0)
                
                mentions.append(SocialMention(
                    platform="reddit",
                    post_id=post_data["id"],
                    author=post_data.get("author", "unknown"),
                    content=f"{post_data.get('title', '')} {post_data.get('selftext', '')}",
                    timestamp=datetime.fromtimestamp(post_data["created_utc"]),
                    engagement=engagement,
                    sentiment=None,  # Would need sentiment analysis
                    url=f"https://reddit.com{post_data.get('permalink', '')}"
                ))
            
            logger.info(f"Found {len(mentions)} Reddit posts in r/{subreddit}")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to search Reddit: {e}")
            return []
    
    async def get_hot_posts(
        self,
        subreddit: str = "zec",
        limit: int = 25
    ) -> List[SocialMention]:
        """
        Get hot posts from subreddit.
        
        Args:
            subreddit: Subreddit name
            limit: Maximum results
            
        Returns:
            List of social mentions
        """
        params = {"limit": min(limit, 100)}
        
        try:
            data = await self._request("GET", f"/r/{subreddit}/hot", params)
            
            mentions = []
            
            for post in data.get("data", {}).get("children", []):
                post_data = post["data"]
                
                engagement = post_data.get("ups", 0) + post_data.get("num_comments", 0)
                
                mentions.append(SocialMention(
                    platform="reddit",
                    post_id=post_data["id"],
                    author=post_data.get("author", "unknown"),
                    content=f"{post_data.get('title', '')} {post_data.get('selftext', '')}",
                    timestamp=datetime.fromtimestamp(post_data["created_utc"]),
                    engagement=engagement,
                    sentiment=None,
                    url=f"https://reddit.com{post_data.get('permalink', '')}"
                ))
            
            logger.info(f"Found {len(mentions)} hot posts in r/{subreddit}")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to get hot posts: {e}")
            return []
    
    async def get_sentiment_summary(
        self,
        mentions: List[SocialMention]
    ) -> CommunitySentiment:
        """
        Calculate sentiment summary from mentions.
        
        Args:
            mentions: List of social mentions
            
        Returns:
            Aggregated sentiment data
        """
        if not mentions:
            return CommunitySentiment(
                platform="reddit",
                timestamp=datetime.utcnow(),
                mention_count=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                average_sentiment=0.0,
                engagement_total=0
            )
        
        # Simple sentiment analysis
        positive_keywords = ["bullish", "great", "amazing", "love", "buy", "hodl"]
        negative_keywords = ["bearish", "dump", "crash", "scam", "sell", "bad"]
        
        positive = 0
        negative = 0
        neutral = 0
        total_engagement = 0
        
        for mention in mentions:
            content_lower = mention.content.lower()
            total_engagement += mention.engagement
            
            has_positive = any(kw in content_lower for kw in positive_keywords)
            has_negative = any(kw in content_lower for kw in negative_keywords)
            
            if has_positive and not has_negative:
                positive += 1
            elif has_negative and not has_positive:
                negative += 1
            else:
                neutral += 1
        
        total = len(mentions)
        avg_sentiment = (positive - negative) / total if total > 0 else 0.0
        
        return CommunitySentiment(
            platform="reddit",
            timestamp=datetime.utcnow(),
            mention_count=total,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            average_sentiment=avg_sentiment,
            engagement_total=total_engagement
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("Closed Reddit client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
