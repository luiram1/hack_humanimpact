"""User-reviewed Google Calendar drafts. No OAuth tokens or background writes."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def calendar_link(day, clock, zone, minutes, career='IT support'):
    if minutes not in (15, 30, 60):
        raise ValueError('Choose 15, 30, or 60 minutes.')
    try:
        tz = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError('Choose a valid IANA time zone, such as America/New_York.')
    naive = datetime.combine(day, clock)
    start = naive.replace(tzinfo=tz)
    if start.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != naive:
        raise ValueError('That local time does not exist because of daylight saving time. Choose another time.')
    if start.utcoffset() != naive.replace(tzinfo=tz, fold=1).utcoffset():
        raise ValueError('That time is ambiguous during a daylight saving transition. Choose another time.')
    utc = start.astimezone(timezone.utc)
    end = utc + timedelta(minutes=minutes)
    return 'https://calendar.google.com/calendar/render?' + urlencode({
        'action': 'TEMPLATE', 'text': 'LearningCurve: ' + career + ' practice',
        'dates': utc.strftime('%Y%m%dT%H%M%SZ') + '/' + end.strftime('%Y%m%dT%H%M%SZ'),
        'ctz': zone, 'details': f'{minutes} minutes of career learning and reflection. Return to LearningCurve to continue. Learning activity, not employment experience.'})
