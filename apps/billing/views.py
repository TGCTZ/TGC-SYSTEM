"""GePG inbound webhook endpoints (called by GePG, CSRF-exempt)."""

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import handle_bill_response_callback, process_payment_notification

logger = logging.getLogger(__name__)


def _xml(body: str) -> HttpResponse:
    return HttpResponse(body, content_type="application/xml", status=200)


@csrf_exempt
@require_POST
def payment_notification(request):
    """Receive a GePG payment notification and return a signed acknowledgement."""
    ack = process_payment_notification(request.body.decode("utf-8"))
    return _xml(ack)


@csrf_exempt
@require_POST
def bill_response(request):
    """Receive an async GePG control-number callback and return an acknowledgement."""
    ack = handle_bill_response_callback(request.body.decode("utf-8"))
    return _xml(ack)
