"""
GitLab API Client for CodeCritique Integration
"""
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from config.gitlab_config import gitlab_config

logger = logging.getLogger(__name__)

class GitLabClient:
    """Client for interacting with GitLab API"""
    
    def __init__(self):
        self.base_url = gitlab_config.base_url
        self.headers = gitlab_config.get_api_headers()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated request to GitLab API"""
        if not gitlab_config.is_configured():
            logger.warning("GitLab not configured, skipping API request")
            return None
            
        url = f"{self.base_url}/api/v4{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GitLab API request failed: {e}")
            return None
    
    def get_merge_request(self, project_id: str, mr_iid: str) -> Optional[Dict[str, Any]]:
        """Get merge request details"""
        return self._make_request(
            'GET',
            f'/projects/{project_id}/merge_requests/{mr_iid}'
        )
    
    def get_mr_changes(self, project_id: str, mr_iid: str) -> Optional[Dict[str, Any]]:
        """Get merge request changes (files, diffs)"""
        return self._make_request(
            'GET',
            f'/projects/{project_id}/merge_requests/{mr_iid}/changes'
        )
    
    def get_mr_commits(self, project_id: str, mr_iid: str) -> Optional[List[Dict[str, Any]]]:
        """Get commits in merge request"""
        return self._make_request(
            'GET',
            f'/projects/{project_id}/merge_requests/{mr_iid}/commits'
        )
    
    def create_mr_comment(self, project_id: str, mr_iid: str, body: str, 
                         note_type: str = 'discussion') -> Optional[Dict[str, Any]]:
        """Create comment on merge request"""
        return self._make_request(
            'POST',
            f'/projects/{project_id}/merge_requests/{mr_iid}/notes',
            json={
                'body': body,
                'note_type': note_type
            }
        )
    
    def create_mr_discussion(self, project_id: str, mr_iid: str, body: str, 
                           position: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create discussion thread on merge request"""
        data = {'body': body}
        if position:
            data['position'] = position
            
        return self._make_request(
            'POST',
            f'/projects/{project_id}/merge_requests/{mr_iid}/discussions',
            json=data
        )
    
    def get_project_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        return self._make_request('GET', f'/projects/{project_id}')
    
    def get_file_content(self, project_id: str, file_path: str, 
                        ref: str = 'main') -> Optional[str]:
        """Get file content from repository"""
        response = self._make_request(
            'GET',
            f'/projects/{project_id}/repository/files/{file_path.replace("/", "%2F")}/raw',
            params={'ref': ref}
        )
        return response if isinstance(response, str) else None
    
    def analyze_mr_for_review(self, project_id: str, mr_iid: str) -> Dict[str, Any]:
        """Analyze merge request to extract review-relevant information"""
        mr_data = self.get_merge_request(project_id, mr_iid)
        if not mr_data:
            return {}
        
        changes = self.get_mr_changes(project_id, mr_iid)
        commits = self.get_mr_commits(project_id, mr_iid)
        
        # Extract relevant information for code review
        analysis = {
            'mr_info': {
                'id': mr_data.get('iid'),
                'title': mr_data.get('title'),
                'description': mr_data.get('description'),
                'source_branch': mr_data.get('source_branch'),
                'target_branch': mr_data.get('target_branch'),
                'author': mr_data.get('author', {}).get('name'),
                'author_username': mr_data.get('author', {}).get('username'),
                'created_at': mr_data.get('created_at'),
                'updated_at': mr_data.get('updated_at'),
                'state': mr_data.get('state'),
                'merge_status': mr_data.get('merge_status'),
                'url': gitlab_config.get_mr_url(project_id, mr_iid)
            },
            'changes': {
                'files_changed': len(changes.get('changes', [])) if changes else 0,
                'additions': mr_data.get('changes_count', {}).get('additions', 0),
                'deletions': mr_data.get('changes_count', {}).get('deletions', 0),
                'modified_files': [change.get('new_path') for change in changes.get('changes', [])] if changes else []
            },
            'commits': {
                'count': len(commits) if commits else 0,
                'latest': commits[0] if commits else None,
                'all': commits if commits else []
            },
            'suggested_reviewers': self._suggest_reviewers(mr_data),
            'review_categories': self._suggest_review_categories(changes)
        }
        
        return analysis
    
    def _suggest_reviewers(self, mr_data: Dict[str, Any]) -> List[str]:
        """Suggest reviewers based on MR data"""
        suggestions = []
        
        # Get assignees
        assignees = mr_data.get('assignees', [])
        for assignee in assignees:
            suggestions.append(assignee.get('username', ''))
        
        # Get author (they shouldn't review their own MR)
        author = mr_data.get('author', {})
        author_username = author.get('username', '')
        
        return [s for s in suggestions if s and s != author_username]
    
    def _suggest_review_categories(self, changes: Optional[Dict[str, Any]]) -> List[str]:
        """Suggest review categories based on changed files"""
        if not changes or 'changes' not in changes:
            return ['Architecture', 'CodeStyle', 'Testing']  # Default categories
        
        categories = set()
        file_changes = changes.get('changes', [])
        
        for change in file_changes:
            file_path = change.get('new_path', change.get('old_path', ''))
            
            # Suggest categories based on file types and paths
            if any(ext in file_path for ext in ['.js', '.ts', '.jsx', '.tsx']):
                categories.update(['CodeStyle', 'Performance', 'Testing'])
            elif any(ext in file_path for ext in ['.py', '.java', '.kt', '.swift']):
                categories.update(['CodeStyle', 'Logic', 'Error Handling'])
            elif 'test' in file_path.lower():
                categories.add('Testing')
            elif 'config' in file_path.lower():
                categories.update(['Architecture', 'Security'])
            elif any(folder in file_path for folder in ['security', 'auth', 'crypto']):
                categories.add('Security')
            elif any(folder in file_path for folder in ['api', 'service', 'controller']):
                categories.update(['API Usage', 'Architecture'])
            elif any(folder in file_path for folder in ['ui', 'view', 'component']):
                categories.add('UI/UX')
            elif any(folder in file_path for folder in ['db', 'database', 'migration']):
                categories.update(['Architecture', 'Storage'])
        
        return list(categories) if categories else ['Architecture', 'CodeStyle', 'Testing']

# Global instance
gitlab_client = GitLabClient()
