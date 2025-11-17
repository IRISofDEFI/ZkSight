"""Type definitions for social data"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SocialMention(BaseModel):
    """Social media mention data"""
    platform: str = Field(description="Platform name (twitter, reddit, etc.)")
    post_id: str = Field(description="Unique post identifier")
    author: str = Field(description="Author username")
    content: str = Field(description="Post content")
    timestamp: datetime = Field(description="Post timestamp")
    engagement: int = Field(description="Engagement count (likes, upvotes, etc.)")
    sentiment: Optional[float] = Field(default=None, description="Sentiment score (-1 to 1)")
    url: Optional[str] = Field(default=None, description="Post URL")


class CommunitySentiment(BaseModel):
    """Aggregated community sentiment"""
    platform: str = Field(description="Platform name")
    timestamp: datetime = Field(description="Analysis timestamp")
    mention_count: int = Field(description="Number of mentions")
    positive_count: int = Field(description="Positive mentions")
    negative_count: int = Field(description="Negative mentions")
    neutral_count: int = Field(description="Neutral mentions")
    average_sentiment: float = Field(description="Average sentiment score")
    engagement_total: int = Field(description="Total engagement")


class DeveloperActivity(BaseModel):
    """GitHub developer activity metrics"""
    repository: str = Field(description="Repository name")
    timestamp: datetime = Field(description="Activity timestamp")
    commits_count: int = Field(description="Number of commits")
    pull_requests_count: int = Field(description="Number of pull requests")
    issues_count: int = Field(description="Number of issues")
    contributors_count: int = Field(description="Number of active contributors")
    stars: int = Field(description="Repository stars")
    forks: int = Field(description="Repository forks")
