import csv
import io

from django.db import transaction

from .forms import CourseForm

CSV_COLUMNS = ['name', 'description', 'yearly_tuition', 'term_tuition']
REQUIRED_COLUMNS = {'name', 'yearly_tuition'}
MAX_ROWS = 200
SAMPLE_ROWS = [
    ['BS Information Technology', 'Programming, networks, and databases.', '40000', '20000'],
    ['BS Nursing', 'Four-year nursing program with hospital duty.', '65000', ''],
]


def template_csv():
    """The sample file colleges download and fill in."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)
    writer.writerows(SAMPLE_ROWS)
    return output.getvalue()


def row_error(line_number, form):
    """'Row 3: yearly_tuition: Enter a number.' for the first problem of each field."""
    problems = [f'{field}: {errors[0]}' for field, errors in form.errors.items()]
    return f'Row {line_number}: ' + '; '.join(problems)


def read_course_rows(uploaded_file):
    """Check every row of the CSV with CourseForm (the same rules as the Add course page).
    Returns (valid forms, list of error messages)."""
    try:
        text = uploaded_file.read().decode('utf-8-sig')  # utf-8-sig also handles Excel's hidden BOM
    except UnicodeDecodeError:
        return [], ['The file must be saved as CSV UTF-8.']

    rows = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(rows.fieldnames or [])
    if missing:
        return [], [f'Missing column(s): {", ".join(sorted(missing))}. Use the template.']

    forms, errors = [], []
    for line_number, row in enumerate(rows, start=2):  # row 1 is the header
        if line_number - 1 > MAX_ROWS:
            return [], [f'Upload at most {MAX_ROWS} courses at a time.']
        form = CourseForm(row)
        if form.is_valid():
            forms.append(form)
        else:
            errors.append(row_error(line_number, form))
    if not forms and not errors:
        errors.append('The file has no course rows.')
    return forms, errors


def save_courses(forms, organization):
    """Save every course at once: if one fails, none are saved."""
    with transaction.atomic():
        for form in forms:
            course = form.save(commit=False)
            course.organization = organization
            course.save()
