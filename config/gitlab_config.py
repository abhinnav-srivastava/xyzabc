"""
GitLab Integration Configuration
"""
import os
from typing import Dict, Any, Optional

class GitLabConfig:
    """GitLab API configuration and utilities"""
    
    def __init__(self):
        self.base_url = os.environ.get('GITLAB_URL', 'https://gitlab.com')
        self.access_token = os.environ.get('GITLAB_ACCESS_TOKEN')
        self.webhook_secret = os.environ.get('GITLAB_WEBHOOK_SECRET')
        self.project_id = os.environ.get('GITLAB_PROJECT_ID')
        
    def is_configured(self) -> bool:
        """Check if GitLab integration is properly configured"""
        return bool(self.access_token and self.webhook_secret)
    
    def get_api_headers(self) -> Dict[str, str]:
        """Get headers for GitLab API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'CodeCritique/1.0'
        }
    
    def get_webhook_url(self, base_url: str) -> str:
        """Get the webhook URL for GitLab to call"""
        return f"{base_url}/webhook/gitlab"
    
    def get_mr_url(self, project_id: str, mr_iid: str) -> str:
        """Get merge request URL"""
        return f"{self.base_url}/-/project/{project_id}/-/merge_requests/{mr_iid}"
    
    def get_commit_url(self, project_id: str, commit_sha: str) -> str:
        """Get commit URL"""
        return f"{self.base_url}/-/project/{project_id}/-/commit/{commit_sha}"

# Global instance
gitlab_config = GitLabConfig()

