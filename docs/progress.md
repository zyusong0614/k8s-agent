# K8s Agent Progress Summary

*Last Updated: 2026-06-06*

## Achievements & Completed Milestones

### 1. Real API Integrations (Replacing Dry-Runs)
- **Jira HTTP Client**: The agent now creates actual Jira tickets on the Atlassian board using standard REST APIs instead of printing mock output.
- **LLM HTTP Client**: Integrated the Anthropic HTTP API to perform real-time, context-aware diagnosis on Kubernetes alerts based on Robusta logs.
- **Ticket Correlation & De-duplication**: 
  - Implemented a stateful Redis store (`active_issue:{namespace}:{workload_name}`) with a 1-hour correlation window. 
  - Subsequent incidents (e.g., repeating CrashLoopBackOff loops) are now correctly appended as comments under the existing Jira ticket rather than creating new, duplicate tickets.

### 2. Infrastructure & GitOps Automation
- **ArgoCD Integration**: Evolved the local Docker Compose bootstrap process (`bootstrap.sh`) to automatically install ArgoCD within the `k3s` cluster.
- **GitOps Pipeline**: Successfully moved demo workload manifests (`oom-demo.yaml`, `crashloop-demo.yaml`) to the public GitHub repository: [zyusong0614/k8s-agent-gitops](https://github.com/zyusong0614/k8s-agent-gitops). 
- **Automated Synchronization**: Configured an ArgoCD `Application` resource with `Automated Sync`. The cluster state is now completely declarative and bound to the GitHub repository.
- **Repository Security & Open Source Readiness**: 
  - Purged all hardcoded personal configurations, secrets, and API tokens (Anthropic, Jira) from `docker-compose.yml`.
  - Enforced a strict separation of configuration, migrating all sensitive variables to a local, untracked `.env` file using the 12-Factor App methodology.
  - Successfully published the sanitized base repository to [zyusong0614/k8s-agent](https://github.com/zyusong0614/k8s-agent).

## Current Architecture State

- **Event Source**: Robusta (Running in K3s)
- **Queue/State**: Redis (Handles event deduplication and Jira ticket correlation locks)
- **Workers**: Celery Workers (Executes the Agent pipeline)
- **Agent Pipeline**: `parse -> diagnose (Anthropic) -> create/update ticket (Jira) -> (Pending GitHub PR)`
- **Deployment Strategy**: ArgoCD GitOps Pull model via GitHub.

## Next Steps (Roadmap)

1. **GitHub HTTP Client (Auto-Remediation via PRs)**: Replace the current `dry_run` GitHub adapter. When the LLM recommends a configuration change (e.g., bumping memory limits), the Agent should automatically fork/branch from `k8s-agent-gitops`, modify the YAML manifest, and open a real Pull Request.
2. **LangGraph Migration**: Restructure the linear pipeline in `app/agent.py` into a stateful LangGraph to support multi-step reasoning, self-reflection, and human-in-the-loop approvals.
3. **Kafka/Qdrant**: (Future Scalability) Introduce Kafka for high-throughput event processing and Qdrant for RAG-based historical incident retrieval.
