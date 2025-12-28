"""Time formatting utilities for relative time display."""

from datetime import datetime


def format_relative_time(dt: datetime, reference: datetime | None = None) -> str:
    """Format a datetime as a human-readable relative string.

    Args:
        dt: The datetime to format
        reference: Reference time (default: now)

    Returns:
        Human-readable string like "just now", "5 minutes ago", "2 days ago",
        or "Dec 14, 2025" for older dates

    Examples:
        >>> from datetime import datetime, timedelta
        >>> now = datetime.now()
        >>> format_relative_time(now - timedelta(seconds=30))
        'just now'
        >>> format_relative_time(now - timedelta(minutes=5))
        '5 minutes ago'
        >>> format_relative_time(now - timedelta(hours=3))
        '3 hours ago'
        >>> format_relative_time(now - timedelta(days=2))
        '2 days ago'
    """
    if reference is None:
        reference = datetime.now()

    delta = reference - dt
    seconds = delta.total_seconds()

    # Handle future dates
    if seconds < 0:
        return dt.strftime("%b %d, %Y")

    # Less than 60 seconds
    if seconds < 60:
        return "just now"

    # Less than 60 minutes
    minutes = int(seconds // 60)
    if minutes < 60:
        if minutes == 1:
            return "1 minute ago"
        return f"{minutes} minutes ago"

    # Less than 24 hours
    hours = int(seconds // 3600)
    if hours < 24:
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"

    # Less than 7 days
    days = int(seconds // 86400)
    if days < 7:
        if days == 1:
            return "1 day ago"
        return f"{days} days ago"

    # Less than 30 days (show as weeks)
    if days < 30:
        weeks = days // 7
        if weeks == 1:
            return "1 week ago"
        return f"{weeks} weeks ago"

    # 30 days or older - show actual date
    return dt.strftime("%b %d, %Y")
