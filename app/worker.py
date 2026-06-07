from celery import Celery

from app.agent import handle_incident
from app.config import get_settings

settings = get_settings()

celery_app = Celery("k8s_agent", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.update(task_track_started=True)


@celery_app.task(name="app.worker.process_incident")
def process_incident(payload: dict) -> dict:
    from redis import Redis
    s = get_settings()
    redis_client = Redis.from_url(s.redis_url, decode_responses=True)
    return handle_incident(payload, s, redis_client)


@celery_app.task(name="app.worker.remediate_incident")
def remediate_incident(issue_key: str, incident_dict: dict, decision_dict: dict) -> dict:
    import logging
    from app.clients.github import GitHubClient
    from app.clients.jira import JiraClient
    from app.schemas import AgentDecision, IncidentPayload, JiraIssue
    from app.agent import render_jira_comment

    logger = logging.getLogger(__name__)
    s = get_settings()
    jira = JiraClient(s)
    github = GitHubClient(s)

    incident = IncidentPayload(**incident_dict)
    decision = AgentDecision(**decision_dict)
    issue = JiraIssue(key=issue_key, url=f"{s.jira_base_url}/browse/{issue_key}")

    logger.info("Remediation Agent starting for issue %s", issue_key)

    # 1. Transition to In Progress
    jira.transition_issue(issue, "In Progress")

    # 2. Open Pull Request
    pr = github.open_pull_request(issue_key, incident, decision)

    # 3. Leave Comment with PR link
    comment = render_jira_comment(incident, decision, pr)
    jira.add_comment(issue, f"## 🤖 Auto-Remediation Executed\n\n{comment}")

    # 4. Transition to In Review
    jira.transition_issue(issue, "In Review")

    logger.info("Remediation Agent completed for issue %s", issue_key)
    return {"status": "success", "pr_url": pr.url if pr else None}

