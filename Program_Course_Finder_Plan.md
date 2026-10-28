# Program Course Finder: Build Plan

Based on [Program_Course_Finder_Blueprint.md](Program_Course_Finder_Blueprint.md). College only. Two roles: **User** and **Organization**.

**Stack:**
- **Backend:** Django 6 + Python venv (already set up).
- **Database:** Supabase free tier (hosted PostgreSQL). Django connects through the `DATABASES` setting using `psycopg`.
- **AI:** Groq API (free tier) for the assistant, review summaries, and translation.
- **Secrets:** keep the Supabase and Groq keys in a `.env` file, never in code or git.

---

## 1. Features by Role

### User

| Feature | How it works |
|---|---|
| Register / log in | Sign up with email and password, choose role "User". |
| Profile | Add interests, bio, hometown, address, and map pin. Location is optional and shared only with consent. |
| Search and filter | Find courses by name, tuition range, distance, and verified status. |
| Compare | Pick 2 to 3 colleges or programs and see tuition, distance, rating, and offerings side by side. |
| Reviews | Rate a program (1 to 5 stars), comment, like/dislike others, and translate a review to English. One review per program. |
| Report | Flag false information or abusive reviews. |
| AI assistant | Ask a question in plain words. It answers from verified data (reviews, distance, cost) and cites its sources. |

### Organization

| Feature | How it works |
|---|---|
| Register / log in | Sign up with email and password, choose role "Organization". |
| Profile | Add contacts, address with map pin, website, and social links. |
| Verification | Upload the 5 required documents. Profile and offerings stay hidden until approved. |
| Offerings | Add, edit, or remove courses with description, yearly and per-term tuition, images, and video. |
| CSV bulk upload | Upload one CSV file to add many offerings at once. |
| Reply to reviews | Reply to user reviews. Cannot delete them. |
| Dashboard | See overall rating, unread reviews, likes/dislikes, and a per-course breakdown. |
| Notifications | Alerts for new reviews, rating changes, and verification status. |
| AI summary | Monthly and yearly summary per course: average rating, praises, complaints, and changes. |

### Public (not logged in)

- Browse and search verified colleges and courses.
- Cannot review, compare with saved data, or use the AI assistant.

---

## 2. What to Build (Django apps and models)

| App | Purpose | Main models |
|---|---|---|
| `accounts` | Login, roles, profiles | `User` (role: user / organization), `UserProfile` |
| `organizations` | College profile and verification | `Organization`, `VerificationDocument` |
| `courses` | Offerings, search, compare | `Course`, `CourseMedia` |
| `reviews` | Ratings, replies, reactions, reports | `Review`, `ReviewReply`, `ReviewReaction`, `Report` |
| `notifications` | Alerts for both roles | `Notification` |
| `ai_assistant` | Assistant, summaries, translation (Groq) | `ReviewSummary` (cached results) |
| `ads` | Sponsored banners and videos | `Ad` |

---

## 3. Build Checklist

Work top to bottom. Each phase should run before starting the next.

### Phase 1: MVP
- [x] Create a Supabase project and connect Django to it (`.env` + `DATABASES`)
- [x] Create the apps above and register them in settings
- [x] Custom `User` model with `role` field (before first migration)
- [x] Register, login, logout for both roles
- [x] Organization profile (contacts, address, map pin, links)
- [x] Verification document upload (5 types)
- [x] Organization status: Pending, Approved, Needs Changes, Rejected
- [x] Add, edit, delete offerings with tuition
- [x] Public search and filters (course, tuition, verified)
- [x] Distance calculation from the user's pin
- [x] Compare 2 to 3 courses

### Phase 2: Engagement
- [x] Reviews and star ratings (one per user per course)
- [x] Organization replies
- [x] Like/dislike
- [x] Report button
- [x] Organization dashboard
- [x] Notifications

### Phase 3: AI
- [x] Get a Groq API key and add it to `.env`
- [x] Assistant (Groq) answering only from verified database content
- [x] Respect Groq free-tier rate limits (cache summaries, limit requests per user)
- [x] "Not enough reviews yet" message when data is missing
- [x] Monthly and yearly review summaries
- [x] Review translation to English

### Phase 4: Scale
- [x] CSV bulk upload
- [x] Video ads and banners (clearly labeled)
- [x] Advanced analytics

---

## 4. Decisions Still Needed

1. **Who verifies organizations?** There is no administrator role. Options: you review manually (e.g., Django's built-in admin, used only by the developer), or automated checks.
2. **Map and distance:** which map service (e.g., OpenStreetMap is free, Google Maps is paid).
3. **Hosting** for the Django app (the database is on Supabase, the AI is on Groq).
4. **File storage:** verification documents, images, and video can use Supabase Storage (free tier has size limits).

---

## 5. One-Prompt Build

Copy this into Claude Code to build Phase 1 in one go:

```text
Using the Django project in this folder (program_course_finder) and the
blueprint in Program_Course_Finder_Blueprint.md, build Phase 1 (MVP):

1. Create apps: accounts, organizations, courses.
2. accounts: custom User model with role (user / organization), register,
   login, logout, and a UserProfile (interests, bio, hometown, address,
   latitude/longitude).
3. organizations: Organization profile (phone, email, address, map pin,
   website, social links, status: pending / approved / needs_changes /
   rejected) and VerificationDocument (5 types: government recognition,
   SEC registration, authorization letter, valid ID, proof of official
   channels). Only approved organizations are public.
4. courses: Course (name, description, yearly tuition, per-term tuition,
   last_updated) with add / edit / delete for the owning organization,
   public search with filters (name, tuition range, verified), distance
   from the user's pin, and a compare page for 2 to 3 courses.
5. Use Django templates, simple clean HTML/CSS, and the Django admin for
   reviewing verification documents (developer-only).
6. Use Supabase (free tier PostgreSQL) as the database: read the connection
   details from a .env file (python-dotenv), install psycopg, add .env to
   .gitignore, and update requirements.txt. I will provide the credentials.
7. Run migrations, create a superuser, add a few sample records, and
   confirm python manage.py check and the dev server both work.

Keep the code simple and commented. Do not build reviews or AI yet.
```

For Phase 3, add: "Use the Groq API (key in .env) for the assistant, summaries, and translation, answering only from database content."

For other phases, use the same format: replace the numbered list with that phase's checklist items.
