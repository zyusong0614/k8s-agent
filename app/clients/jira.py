import logging
from uuid import uuid4

import httpx

from app.config import Settings
from app.schemas import AgentDecision, IncidentPayload, JiraIssue

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        if self.settings.jira_user_email and self.settings.jira_api_token:
            self.auth = (self.settings.jira_user_email, self.settings.jira_api_token)
        else:
            self.auth = None
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def create_issue(self, incident: IncidentPayload, decision: AgentDecision) -> JiraIssue:
        if self.settings.dry_run or not self.auth:
            key = f"DRYRUN-{str(uuid4())[:8].upper()}"
            logger.info("dry_run.jira create_issue key=%s summary=%s", key, decision.summary)
            return JiraIssue(key=key, url=f"dry-run://jira/{key}")
        
        url = f"{self.settings.jira_base_url}/rest/api/2/issue"
        payload = {
            "fields": {
                "project": {"key": self.settings.jira_project_key},
                "summary": decision.summary[:255],
                "description": f"Incident: {incident.alert_name}\nReason: {incident.reason}\n\nDiagnosis:\n{decision.llm_diagnosis}\n\nEvidence:\n" + "\n".join(decision.evidence),
                "issuetype": {"name": "Task"}
            }
        }
        try:
            response = httpx.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return JiraIssue(key=data["key"], url=f"{self.settings.jira_base_url}/browse/{data['key']}")
        except httpx.HTTPError as e:
            logger.error("Failed to create Jira issue: %s. Response: %s", e, e.response.text if hasattr(e, "response") and e.response else "No response")
            key = f"{self.settings.jira_project_key}-ERROR"
            return JiraIssue(key=key, url=f"{self.settings.jira_base_url}/browse/{key}")

    def add_comment(self, issue: JiraIssue, comment: str) -> None:
        if self.settings.dry_run or not self.auth or issue.key.startswith("DRYRUN") or issue.key.endswith("-ERROR"):
            logger.info("dry_run.jira add_comment key=%s comment=%s", issue.key, comment.replace("\n", " ")[:500])
            return
        
        url = f"{self.settings.jira_base_url}/rest/api/2/issue/{issue.key}/comment"
        payload = {"body": comment}
        try:
            response = httpx.post(url, json=payload, auth=self.auth, headers=self.headers, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Failed to add Jira comment: %s", e)

