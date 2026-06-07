import logging

import httpx

from app.config import Settings
from app.schemas import AgentDecision, IncidentPayload

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate_diagnosis(self, incident: IncidentPayload, decision: AgentDecision) -> str:
        if self.settings.dry_run or not self.settings.llm_api_key:
            logger.info("dry_run.llm diagnosis incident=%s/%s", incident.namespace, incident.workload_name)
            return decision.summary

        headers = {
            "x-api-key": self.settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        prompt = f"Analyze this Kubernetes incident and provide a concise 1-paragraph summary:\nAlert: {incident.alert_name}\nReason: {incident.reason}\nLogs: {incident.logs}\nDescribe: {incident.describe_snapshot}"
        
        payload = {
            "model": self.settings.llm_model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = httpx.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except httpx.HTTPError as e:
            logger.error("Failed to generate LLM diagnosis: %s", e)
            return decision.summary

