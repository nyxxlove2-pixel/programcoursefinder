# Program Course Finder

Django project for finding colleges and courses. Read these before building:

- [Program_Course_Finder_Blueprint.md](Program_Course_Finder_Blueprint.md): what the system is.
- [Program_Course_Finder_Plan.md](Program_Course_Finder_Plan.md): features by role, build checklist, stack.
- [Program_Course_Finder_Coding_Rules.md](Program_Course_Finder_Coding_Rules.md): how to write code. Keep it simple, readable, reusable, and clean, and use Tailwind CSS. This is a student project.


## How the code is set up

- **Database:** Supabase. Our tables come from [Program_Course_Finder_Schema.sql](Program_Course_Finder_Schema.sql), so every model uses `managed = False`. To change a table, change the SQL in Supabase first, then the model.
- **Login:** our own `users` table (`accounts.User`), not Django's auth user. Use `accounts.utils`: `log_in`, `log_out`, `get_current_user`, and `@role_required('organization')`. Templates get `{{ current_user }}`.
- **Verification:** there is no admin role in the `users` table. The developer approves organizations in the super admin dashboard (`/superadmin/`, the `superadmin` app), which only a Django superuser can open (log in at `/admin/`). Status changes go through `organizations.utils.change_status()`, which also notifies the college; Django admin uses it too.
- **Reuse before writing:** form styles come from `core.forms.StyledFormMixin`; public course queries start from `courses.utils.public_courses()`; UI pieces live in `templates/components/`; form pages extend `templates/layouts/form_page.html`; money and distance use the `peso` and `km` filters (`{% load formatting %}`); ratings use `components/stars.html`; reviews on a page come from `reviews.utils.reviews_for_page()` and render with `components/review_card.html`; send notifications with `notifications.utils.notify()`; POST views that return to the previous page use `core.utils.redirect_back()`.
- **Images and settings:** photos, logos, and cover images go to Supabase Storage (bucket `profile-images`) through `core.uploads` (`new_image_url`, `delete_if_replaced`), picked with `core.forms.ImagesForm` and drawn by `components/profile_images.html`. Show them with `components/avatar.html` (`photo=`), `components/monogram.html` (`logo=`), and `components/cover_image.html`. Settings pages extend `templates/layouts/settings_page.html` (fields as rows via `components/setting_row.html`); the side menu lives in `components/settings_nav.html`. Needs `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`.
- **AI (Groq):** every call goes through `ai_assistant.groq.ask_groq()` (model in `GROQ_MODEL`, default `openai/gpt-oss-120b`), and every view that calls it first checks `ai_assistant.utils.take_ai_request()` (hourly limit `AI_REQUESTS_PER_HOUR`). The AI only gets verified data; ads are never sent to it. Summaries are saved in `review_summaries`; translations are kept in Django's cache.
- **Moderation:** reports, fake reviews, and ads are handled by the developer in Django admin, like verification. Admin status changes notify the organization.
- **Layouts by role:** public and User pages extend `base.html` (top navbar). Organization pages extend `templates/layouts/organization.html` (sidebar). `form_page.html` picks between them with `{{ base_layout }}` from `accounts/context_processors.py`. After login, `accounts.utils.redirect_home` sends users to course search and organizations to their dashboard.
- **Icons and logo:** use `components/icon.html` (SVG line icons) and `components/logo.html`. No emoji as icons.
- **Tailwind:** Play CDN in `templates/base.html`, with the design colors in its config.
- **Template comments:** `{# ... #}` must fit on one line; for longer notes use `{% comment %}...{% endcomment %}`, otherwise the text shows on the page.
- **Secrets:** `.env` (never commit it).
- **Deploy (Vercel):** `vercel.json` runs Django through `program_course_finder/wsgi.py`; WhiteNoise serves static files. Keep `templates/base.html` named as it is (Vercel does not need an `index.html`). On Vercel, `DEBUG` is off and `DJANGO_SECRET_KEY` plus the `.env` values must be set as Environment Variables. The database must use Supabase's Session pooler host. Vercel's disk is read-only, so uploaded files (verification documents) need Supabase Storage there.

Run: `.\venv\Scripts\Activate.ps1` then `python manage.py runserver`.
