import json
import sys

from app.schemas import AgentDecision, IncidentPayload, IncidentType, PolicyStatus, MemoryRecommendation
from app.worker import remediate_incident

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.test_remediation_agent <JIRA_ISSUE_KEY>")
        sys.exit(1)

    issue_key = sys.argv[1]
    print(f"Testing Async Remediation Agent for Jira Issue: {issue_key}")

    # Mock an incident
    incident = IncidentPayload(
        cluster="minikube",
        namespace="k8s-agent-demo",
        workload_kind="Deployment",
        workload_name="oom-demo",
        reason="OOMKilled",
        alert_name="CrashLoopBackOff",
        logs="Terminated with exit code 137. Reason: OOMKilled",
    )

    # Mock an AI decision that requires PR
    decision = AgentDecision(
        incident_type=IncidentType.OOM_KILLED,
        confidence=0.99,
        summary="Testing auto-remediation async flow.",
        evidence=["Mock evidence for testing"],
        recommended_action="Bump memory to 50Mi",
        pr_required=True,
        policy_status=PolicyStatus.ALLOWED,
        policy_reason="Testing",
        llm_diagnosis="This is a test diagnosis from the Remediation Agent test script.",
        memory_recommendation=MemoryRecommendation(
            current_limit="10Mi",
            proposed_limit="50Mi",
            reason="Because it keeps crashing"
        )
    )

    print("Dispatching Celery task...")
    result = remediate_incident.delay(
        issue_key,
        incident.model_dump(mode="json"),
        decision.model_dump(mode="json")
    )

    print(f"Task dispatched with ID: {result.id}")
    print("Check your Celery worker logs (or run `./demo logs`) to see the progression!")

if __name__ == "__main__":
    main()
