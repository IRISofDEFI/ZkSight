"""GitHub API client for developer activity metrics"""
import logging
from typing import Optional
from datetime import datetime, timedelta
import httpx

from ..social_types import DeveloperActivity


logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub API client for tracking Zcash developer activity.
    
    Uses GitHub REST API v3.
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize GitHub client.
        
        Args:
            access_token: GitHub personal access token (optional, increases rate limit)
            timeout: Request timeout in seconds
        """
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ChimeraAnalytics/1.0"
        }
        
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers
        )
        
        logger.info("Initialized GitHub client")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None
    ) -> dict:
        """
        Make GitHub API request.
        
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
            logger.error(f"GitHub API request failed: {e}")
            raise
    
    async def get_repository_info(
        self,
        owner: str,
        repo: str
    ) -> dict:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data
        """
        return await self._request("GET", f"/repos/{owner}/{repo}")
    
    async def get_commits_count(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> int:
        """
        Get commit count for a time period.
        
        Args:
            owner: Repository owner
            repo: Repository name
            since: Start date
            until: End date
            
        Returns:
            Number of commits
        """
        params = {}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        
        try:
            # Get commits (paginated, max 100 per page)
            commits = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/commits",
                params={**params, "per_page": 100}
            )
            
            # Note: This is simplified. Full implementation would handle pagination
            return len(commits)
            
        except Exception as e:
            logger.error(f"Failed to get commits count: {e}")
            return 0
    
    async def get_pull_requests_count(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        since: Optional[datetime] = None
    ) -> int:
        """
        Get pull request count.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            since: Start date
            
        Returns:
            Number of pull requests
        """
        params = {"state": state, "per_page": 100}
        
        try:
            prs = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/pulls",
                params=params
            )
            
            # Filter by date if specified
            if since:
                prs = [
                    pr for pr in prs
                    if datetime.fromisoformat(
                        pr["created_at"].replace("Z", "+00:00")
                    ) >= since
                ]
            
            return len(prs)
            
        except Exception as e:
            logger.error(f"Failed to get pull requests count: {e}")
            return 0
    
    async def get_issues_count(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        since: Optional[datetime] = None
    ) -> int:
        """
        Get issues count.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            since: Start date
            
        Returns:
            Number of issues
        """
        params = {"state": state, "per_page": 100}
        
        try:
            issues = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/issues",
                params=params
            )
            
            # Filter out pull requests (they're included in issues endpoint)
            issues = [issue for issue in issues if "pull_request" not in issue]
            
            # Filter by date if specified
            if since:
                issues = [
                    issue for issue in issues
                    if datetime.fromisoformat(
                        issue["created_at"].replace("Z", "+00:00")
                    ) >= since
                ]
            
            return len(issues)
            
        except Exception as e:
            logger.error(f"Failed to get issues count: {e}")
            return 0
    
    async def get_contributors_count(
        self,
        owner: str,
        repo: str
    ) -> int:
        """
        Get number of contributors.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Number of contributors
        """
        try:
            contributors = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/contributors",
                params={"per_page": 100}
            )
            
            return len(contributors)
            
        except Exception as e:
            logger.error(f"Failed to get contributors count: {e}")
            return 0
    
    async def get_developer_activity(
        self,
        owner: str = "zcash",
        repo: str = "zcash",
        days_back: int = 7
    ) -> DeveloperActivity:
        """
        Get comprehensive developer activity metrics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            days_back: Number of days to look back
            
        Returns:
            Developer activity metrics
        """
        since = datetime.utcnow() - timedelta(days=days_back)
        
        try:
            # Get repository info for stars and forks
            repo_info = await self.get_repository_info(owner, repo)
            
            # Get activity counts
            commits = await self.get_commits_count(owner, repo, since=since)
            prs = await self.get_pull_requests_count(owner, repo, since=since)
            issues = await self.get_issues_count(owner, repo, since=since)
            contributors = await self.get_contributors_count(owner, repo)
            
            return DeveloperActivity(
                repository=f"{owner}/{repo}",
                timestamp=datetime.utcnow(),
                commits_count=commits,
                pull_requests_count=prs,
                issues_count=issues,
                contributors_count=contributors,
                stars=repo_info.get("stargazers_count", 0),
                forks=repo_info.get("forks_count", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get developer activity: {e}")
            # Return zero values on error
            return DeveloperActivity(
                repository=f"{owner}/{repo}",
                timestamp=datetime.utcnow(),
                commits_count=0,
                pull_requests_count=0,
                issues_count=0,
                contributors_count=0,
                stars=0,
                forks=0
            )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("Closed GitHub client")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
