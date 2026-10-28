# Program Course Finder: Coding Rules

This is a student project. Students must be able to read and understand every file. **Keep it simple.** Always follow these rules when writing code.

---

## 1. Core Rules

1. **Simple first.** Pick the most basic solution that works. No clever tricks.
2. **Readable.** Someone new to Django should understand it in one read.
3. **Reusable.** Write logic once and reuse it. Never copy and paste the same code.
4. **Clean.** No unused code, no leftover debug prints, no commented-out blocks.
5. **Small pieces.** One function does one thing. Keep functions short (about 20 lines).

## 2. What to Avoid (Do Not Overcomplicate)

- No advanced patterns (metaclasses, decorators you write yourself, complex mixins, signals unless needed).
- No extra libraries when Django already does the job.
- No premature optimization. Make it work and make it clear first.
- No deep nesting. If you have more than 2 levels of `if` or `for`, split it into a function.
- No one-line "smart" code that is hard to read. Write it in plain steps.

## 3. Python and Django Style

- **Naming:** clear full words. `get_verified_courses`, not `gvc`. Classes in `PascalCase`, functions and variables in `snake_case`.
- **Views:** prefer simple function-based views. Use Django's built-in generic views only when they make the code shorter and clear.
- **Forms:** use Django `ModelForm` so validation is written once.
- **Models:** keep logic that belongs to the data inside the model (for example, a `average_rating` method on `Course`).
- **Queries:** use the Django ORM only, no raw SQL.
- **Comments:** one short line above each function or tricky step saying **why**, in plain English. Do not comment obvious lines.
- **Imports:** standard library first, then Django, then our own apps. Remove unused imports.
- **Secrets:** read keys from `.env`, never hard-code them.

Example of the style we want:

```python
def verified_courses(max_tuition=None):
    """Return courses from approved organizations, optionally under a tuition limit."""
    courses = Course.objects.filter(organization__status="approved")
    if max_tuition:
        courses = courses.filter(yearly_tuition__lte=max_tuition)
    return courses
```

## 4. Reusable Logic

Put shared code in one place and import it.

| What | Where |
|---|---|
| Base page layout (navbar, footer) | `templates/base.html` |
| Repeated UI pieces (course card, button, review card, form field) | `templates/components/` and use `{% include %}` |
| Shared helper functions (distance, formatting) | `utils.py` in the app that owns them |
| Role checks (is user, is organization) | one small decorator or helper in `accounts`, used by every view |
| Search and filter logic | one function in `courses`, used by search and compare |

Rule of thumb: **if you write something a second time, move it to a shared place.**

## 5. Tailwind CSS

All styling uses **Tailwind CSS**. Follow the look in [Program_Course_Finder_Design.md](Program_Course_Finder_Design.md).

- Use Tailwind utility classes directly in the templates. No custom CSS files unless absolutely needed.
- Put the design colors, font, and radius in the Tailwind config once (primary, accent, text, background) so every page uses the same values.
- Build mobile first: write the base classes for phones, then add `md:` and `lg:` for bigger screens.
- Do not repeat long class lists. Turn repeated UI into an include template (for example, `components/button.html`) so the classes live in one place.
- Keep class lists readable: layout first, then spacing, then colors, then effects.

Example:

```html
<a href="{{ url }}"
   class="inline-block rounded-full bg-primary px-6 py-3 font-semibold text-white hover:bg-primary-dark">
  {{ label }}
</a>
```

## 6. Project Structure

Each Django app has the same simple layout:

```text
app_name/
  models.py      data
  forms.py       forms
  views.py       page logic
  urls.py        routes
  utils.py       shared helpers (only if needed)
  templates/app_name/   pages for this app
```

## 7. Before Finishing Any Task

- [ ] Code is simple and a beginner can follow it.
- [ ] No duplicated logic; shared code is reused.
- [ ] Names are clear and comments explain the why.
- [ ] Styled with Tailwind, mobile first, matches the design guide.
- [ ] `python manage.py check` passes and the page works.
- [ ] No unused imports, debug prints, or commented-out code.
