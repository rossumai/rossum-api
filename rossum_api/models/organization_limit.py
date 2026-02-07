from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmailLimits:
    """Email-related limits for an organization.

    Attributes
    ----------
    count_today
        Emails sent by user today count.
    count_today_notification
        Notification emails sent today count.
    count_total
        Emails sent by user total count.
    email_per_day_limit
        Emails sent by user today limit.
    email_per_day_limit_notification
        Notification emails sent today limit.
    email_total_limit
        Emails sent by user total limit.
    last_sent_at
        Date of last sent email.
    last_sent_at_notification
        Date of last sent notification.
    """

    count_today: int
    count_today_notification: int
    count_total: int
    email_per_day_limit: int
    email_per_day_limit_notification: int
    email_total_limit: int | None = None
    last_sent_at: str | None = None
    last_sent_at_notification: str | None = None


@dataclass
class OrganizationLimit:
    """Various limits in regard to an organization."""

    email_limits: EmailLimits
