from app.tasks.celery_app import celery_app


@celery_app.task(
    name="app.tasks.opportunity_tasks.refresh_opportunities"
)
def refresh_opportunities() -> dict[str, str]:
    return {
        "status": "completed",
        "message": "Opportunity refresh task completed.",
    }