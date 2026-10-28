import re

from django.db.models import Q

from core.templatetags.formatting import peso
from courses.utils import add_distances, public_courses

from .groq import ask_groq

MAX_COURSES = 20         # how many courses we send to the AI per question
REVIEWS_PER_COURSE = 3   # newest review comments sent per course
CITATION = re.compile(r'\[C(\d+)\]')

# Common question words that would match almost any course, so we skip them when searching
STOP_WORDS = {
    'which', 'what', 'where', 'near', 'with', 'good', 'best', 'course', 'courses', 'college',
    'colleges', 'school', 'that', 'have', 'review', 'reviews', 'budget', 'about', 'under',
    'than', 'from', 'fits', 'yearly', 'tuition', 'cheap', 'cheapest', 'there', 'would',
    'should', 'show', 'find', 'want', 'some', 'this', 'program', 'programs',
}

SYSTEM_PROMPT = """You are the Program Course Finder assistant. You help a student choose a college course.
Rules:
- Use ONLY the course data given below. Never use outside knowledge about colleges.
- After every fact, cite the course it came from, like [C12].
- If the data does not answer the question, say you do not know.
- If a course has no reviews, say "not enough reviews yet" instead of guessing how good it is.
- Never call one college "the best". Explain the trade-offs (cost, distance, reviews); the student decides.
- Answer in plain sentences or a short list. No tables, no markdown headings. Keep it under 200 words."""


def pick_courses(question, location):
    """Choose the courses to show the AI: ones matching words in the question
    (or every course if nothing matches), nearest first when we know the user's location."""
    words = [word for word in re.findall(r'[a-zA-Z]+', question.lower()) if len(word) > 3 and word not in STOP_WORDS]
    courses = public_courses().prefetch_related('reviews')
    matches = Q()
    for word in words:
        matches |= Q(name__icontains=word) | Q(organization__name__icontains=word) | Q(description__icontains=word)
    if words and courses.filter(matches).exists():
        courses = courses.filter(matches)

    courses = add_distances(courses[:MAX_COURSES * 2], location)
    courses.sort(key=lambda c: (c.distance is None, c.distance or 0))
    return courses[:MAX_COURSES]


def describe_course(course):
    """One course written out as plain text for the AI, starting with its citation tag."""
    lines = [
        f'[C{course.pk}] {course.name} at {course.organization.name}',
        f'Yearly tuition: {peso(course.yearly_tuition)}. Per term: {peso(course.term_tuition) or "not given"}.',
        f'Distance from the student: {f"{course.distance} km" if course.distance is not None else "unknown"}.',
        f'Address: {course.organization.address or "not given"}.',
    ]
    if course.review_count:
        lines.append(f'Rating: {course.average_rating:.1f} out of 5 from {course.review_count} reviews.')
    else:
        lines.append('Rating: not enough reviews yet.')
    if course.description:
        lines.append(f'Description: {course.description[:300]}')
    for review in list(course.reviews.all())[:REVIEWS_PER_COURSE]:
        if review.comment:
            lines.append(f'Review ({review.rating} stars): "{review.comment[:200]}"')
    return '\n'.join(lines)


def number_sources(answer, courses):
    """Turn the AI's [C12] tags into [1], [2]... and return (answer, cited courses in order).
    Tags for courses we did not send are dropped, so every source is real."""
    courses_by_id = {course.pk: course for course in courses}
    sources = []

    def replace(match):
        course = courses_by_id.get(int(match.group(1)))
        if course is None:
            return ''
        if course not in sources:
            sources.append(course)
        return f'[{sources.index(course) + 1}]'

    return CITATION.sub(replace, answer), sources


def answer_question(question, user, location):
    """Answer a student's question from verified data only. Returns (answer, sources)."""
    courses = pick_courses(question, location)
    if not courses:
        return 'There are no verified courses yet, so I cannot answer that.', []

    profile = getattr(user, 'profile', None)
    about_student = f'Student interests: {profile.interests}\n' if profile and profile.interests else ''
    course_data = '\n\n'.join(describe_course(course) for course in courses)
    prompt = f'{about_student}Course data:\n{course_data}\n\nStudent question: {question}'
    return number_sources(ask_groq(SYSTEM_PROMPT, prompt), courses)
