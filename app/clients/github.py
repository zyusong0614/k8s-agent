import logging

from app.config import Settings
from app.schemas import AgentDecision, IncidentPayload, PullRequest

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def open_pull_request(self, issue_key: str, incident: IncidentPayload, decision: AgentDecision) -> PullRequest:
        branch = f"ai-fix/{issue_key.lower()}"
        title = f"[{issue_key}] {incident.workload_name}: {decision.incident_type} recommendation"
        if self.settings.dry_run or not self.settings.github_token:
            logger.info("dry_run.github open_pull_request branch=%s title=%s", branch, title)
            return PullRequest(title=title, branch=branch, url=f"dry-run://github/pr/{branch}")
        logger.info("github adapter is configured but V1 real PR creation is deferred to integration setup")
        repo = f"{self.settings.github_owner}/{self.settings.github_repo}".strip("/")
        return PullRequest(title=title, branch=branch, url=f"https://github.com/{repo}/pull/dry-run")

