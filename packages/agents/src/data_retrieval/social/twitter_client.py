"""Twitter API client for mention tracking"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import httpx

from ..social_types import SocialMention, CommunitySentiment


logger = logging.getLogger(__name__)


class TwitterClient:
    """
    Twitter API v2 client for tracking Zcash mentions.
    
    Requires Twitter API v2 access with bearer token.
    """
    
    def __init__(
        self,
        bearer_token: str,
        timeout: float = 30.0
    ):
        """
        Initialize Twitter client.
        
        Args:
            bearer_token: Twitter API bearer token
            timeout: Request timeout in seconds
        """
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("Initialized Twitter client")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None
    ) -> dict:
        """
        Make Twitter API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Twitter API request failed: {e}")
            raise
    
    async def search_mentions(
        self,
        query: str = "zcash OR $ZEC",
        max_results: int = 100,
        hours_back: int = 24
    ) -> List[SocialMention]:
        """
        Search for Zcash mentions on Twitter.
        
        Args:
            query: Search query
            max_results: Maximum results to return (10-100)
            hours_back: How many hours back to search
            
        Returns:
            List of social mentions
        """
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "start_time": start_time.isoformat() + "Z",
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username"
        }
        
        try:
            data = await self._request("GET", "/tweets/search/recent", params)
            
            mentions = []
            
            # Build user lookup
            users = {}
            if "includes" in data and "users" in data["includes"]:
                for user in data["includes"]["users"]:
                    users[user["id"]] = user["username"]
            
            # Process tweets
            for tweet in data.get("data", []):
                author_id = tweet.get("author_id", "unknown")
                username = users.get(author_id, "unknown")
                
                metrics = tweet.get("public_metrics", {})
                engagement = (
                    metrics.get("like_count", 0) +
                    metrics.get("retweet_count", 0) +
                    metrics.get("reply_count", 0)
                )
                
                mentions.append(SocialMention(
                    platform="twitter",
                    post_id=tweet["id"],
                    author=username,
                    content=tweet["text"],
                    timestamp=datetime.fromisoformat(
                        tweet["created_at"].replace("Z", "+00:00")
                    ),
                    engagement=engagement,
                    sentiment=None,  # Would need sentiment analysis
                    url=f"https://twitter.com/{username}/status/{tweet['id']}"
                ))
            
            logger.info(f"Found {len(mentions)} Twitter mentions")
            return mentions
            
        except Exception as e:
            logger.error(f"Failed to search Twitter mentions: {e}")
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
                platform="twitter",
                timestamp=datetime.utcnow(),
                mention_count=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                average_sentiment=0.0,
                engagement_total=0
            )
        
        # Simple sentiment analysis based on keywords
        # In production, use a proper sentiment model
        positive_keywords = ["bullish", "moon", "great", "amazing", "love", "buy"]
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
            platform="twitter",
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
        logger.info("Closed Twitter client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
