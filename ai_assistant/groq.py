import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'


class AIUnavailable(Exception):
    """Raised when Groq cannot answer (no key, no internet, or rate limit)."""


def ask_groq(system_prompt, user_prompt, json_mode=False, max_tokens=1500):
    """Send one question to Groq and return the reply text.
    With json_mode=True, Groq is told to reply with a JSON object."""
    if not settings.GROQ_API_KEY:
        raise AIUnavailable('GROQ_API_KEY is missing from .env')

    body = {
        'model': settings.GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.2,  # low = stick closely to the data we give it
        'max_tokens': max_tokens,
        'reasoning_effort': 'low',  # short thinking keeps answers fast and inside the free tier
    }
    if json_mode:
        body['response_format'] = {'type': 'json_object'}

    request = Request(GROQ_URL, data=json.dumps(body).encode(), method='POST', headers={
        'Authorization': f'Bearer {settings.GROQ_API_KEY}',
        'Content-Type': 'application/json',
        'User-Agent': 'ProgramCourseFinder/1.0',
    })
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except (URLError, TimeoutError, ValueError) as error:
        raise AIUnavailable(str(error)) from error
    reply = (data['choices'][0]['message'].get('content') or '').strip()
    if not reply:
        raise AIUnavailable('Groq sent back an empty reply')
    return reply
