from django.db import models
from apps.common.models import TimeStampedModel


class SupportRequest(TimeStampedModel):
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE)
    request_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"Support #{self.id} - Booking #{self.booking.id} - {self.request_type} ({self.status})"


class SupportTimeline(TimeStampedModel):
    support_request = models.ForeignKey(SupportRequest, on_delete=models.CASCADE, related_name="timeline")
    message = models.TextField()

    def __str__(self):
        message_preview = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"Timeline #{self.id} - Support #{self.support_request.id} - {message_preview}"
