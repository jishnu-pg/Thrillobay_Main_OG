from django.db import models
from apps.common.models import TimeStampedModel


class SupportRequest(TimeStampedModel):
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE, help_text="Related booking")
    request_type = models.CharField(max_length=50, help_text="Type of support request")
    status = models.CharField(max_length=20, help_text="Status of the request")

    def __str__(self):
        return f"Support #{self.id} - Booking #{self.booking.id} - {self.request_type} ({self.status})"


class SupportTimeline(TimeStampedModel):
    support_request = models.ForeignKey(SupportRequest, on_delete=models.CASCADE, related_name="timeline", help_text="Related support request")
    message = models.TextField(help_text="Message content")

    def __str__(self):
        message_preview = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"Timeline #{self.id} - Support #{self.support_request.id} - {message_preview}"


class FAQ(TimeStampedModel):
    """
    Parent model for a Question.
    Example: "Which are the famous places to visit in Wayanad?"
    """
    location = models.CharField(max_length=255, help_text="e.g., Wayanad")
    question = models.CharField(
        max_length=500, 
        help_text="e.g., Which are the famous places to visit in Wayanad?"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FAQ Group"
        verbose_name_plural = "FAQ Groups"
        ordering = ["location", "question"]

    def __str__(self):
        return f"{self.location} | {self.question[:50]}..."


class FAQItem(TimeStampedModel):
    """
    Individual items/answers under a specific FAQ question.
    Example: "Edakkal Caves", "Banasura Dam"
    """
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(
        max_length=255, 
        help_text="e.g., Edakkal Caves"
    )
    description = models.TextField(
        help_text="Detailed description of the place or answer"
    )
    order = models.PositiveIntegerField(default=0, help_text="Order of display")

    class Meta:
        verbose_name = "FAQ Item"
        verbose_name_plural = "FAQ Items"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
