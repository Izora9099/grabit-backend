from celery import shared_task


@shared_task(ignore_result=True)
def record_event(event_type, shop_id, product_id, user_id, session_key=""):
    """
    Fire-and-forget analytics write.  Always called via .delay() so a slow DB
    write never adds latency to payment or order requests.
    """
    from .models import AnalyticsEvent
    AnalyticsEvent.objects.create(
        event_type=event_type,
        shop_id=shop_id,
        product_id=product_id,
        user_id=user_id,
        session_key=session_key or "",
    )
