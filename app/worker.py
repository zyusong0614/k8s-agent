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

