# Program Course Finder

**AI-Powered College & Course Finder**

System Blueprint (Updated) · College · October 2026

## 1. Purpose

Program Course Finder helps users make informed, well-aligned decisions about colleges and courses by giving them reliable, verified, and easy-to-compare information.

> **Guiding principle**
> Program Course Finder informs; it does not decide. The system recommends and compares options based on the user's interests, budget, and location, but the final choice always belongs to the user. Program Course Finder never labels one college "the best" for everyone. "Best" means best fit for that specific user.

## 2. Account Roles

The system has two account roles only.

| Role | Description |
|---|---|
| **User** | A person looking for a college or course. Includes freshmen and shifters/transferees. Searches, compares, reviews, and uses the AI assistant. |
| **Organization** | A college or university. Manages its verified profile, offerings, tuition, and replies to reviews. |

## 3. Organization Profile & Mandatory Verification

### 3.1 Required profile information

- **Official contact:** phone number, official email, and complete campus address with map pin.
- **Official links:** website and social media pages (Facebook, Instagram, TikTok, YouTube, etc.).
- **Offerings:** course/program, description, yearly and per-term tuition, images, and video.
- **Bulk upload:** CSV template for adding many offerings at once.

### 3.2 Verification documents (required)

An organization cannot publish its profile or offerings until it uploads proof that it is a legitimate institution and the proof is verified.

| Document | Purpose |
|---|---|
| **Government recognition / permit** | CHED or TESDA recognition (College/Tech-Voc). |
| **Business / SEC registration** | Confirms the organization is a legally registered entity. |
| **Authorization letter** | Signed by the school head, naming the person managing the Program Course Finder account. |
| **Valid ID of representative** | Confirms the identity of the account manager. |
| **Proof of official channels** | Shows the listed phone, email, and social pages are owned by the school (e.g., a code posted on the official page). |

### 3.3 Verification workflow

- **Submit:** organization registers and uploads all required documents.
- **Decision:** Approved (Verified badge shown), Needs Changes (reason given), or Rejected.
- **Renewal:** documents are re-checked yearly; expired documents remove the badge until updated.
- **Reporting:** users can report false information; repeated issues lead to suspension.

> **Open question:** with no administrator role, who reviews the documents and decides? This must be settled before development (see Section 8).

## 4. User Features

- **Profile:** interests/hobbies, short bio, hometown, current address, map pin (location shared only with consent).
- **Search & filter:** by course, tuition range, distance, and verified status.
- **Compare:** view two to three colleges or programs side by side (tuition, distance, rating, offerings).
- **Reviews:** star ratings and comments per program, threaded replies from colleges, like/dislike, and one-click AI translation to English.

## 5. AI Features

> **Goal of the AI**
> The AI is a personal assistant for the user. It helps users understand their options and make their own decision, using verified Program Course Finder data only.

### 5.1 AI Assistant for Users

The assistant answers each user request or question using three things:

- **Reviews per course:** what other users say about each course or program (ratings, comments, replies).
- **Distance:** how far each campus is from the user's pinned location.
- **Convenience:** how practical the college is, such as travel distance, tuition and budget fit, schedule, and facilities listed in the profile.

Example: "Which IT course near me has good reviews and fits my ₱40,000 yearly budget?" The assistant compares verified courses and shows the review highlights, distance, and cost. The user decides.

- **Grounded answers:** uses only verified Program Course Finder data (RAG), names the source of each answer, and says it does not know when data is missing.

### 5.2 AI Summary for Organizations

- **Review and rating summary per course:** the AI summarizes all reviews and ratings for each course of the organization, monthly and yearly.
- **What it shows:** average rating, main praises, main complaints, and changes since the last period.
- **Who sees it:** shown in the organization dashboard, so colleges can see what to improve.

### 5.3 Out of Scope

- Elementary and high school levels.
- The AI does not analyze videos, images, or banners. They are shown to users as uploaded and are not used for recommendations or summaries.

## 6. Organization Dashboard

- Overall rating, unread reviews, and total likes/dislikes.
- Rating and reaction breakdown per offering.
- Notifications for new reviews, rating changes, and verification status.

## 7. Trust, Safety & Privacy

- Verification documents are stored securely and visible only to the organization that uploaded them and to whoever is assigned to verify them.
- Tuition and program details show a "last updated" date; outdated listings are flagged.
- Colleges can reply to reviews but cannot delete them.
- User data follows the Data Privacy Act of 2012 (RA 10173).
- Paid ads and promoted listings are clearly labeled and never affect AI recommendations.

## 8. Honest System Review

What is strong, and what will hurt the project if it is not fixed.

### Strengths

- Clear, real problem: college and course information is scattered and hard to compare.
- Mandatory verification is the system's strongest feature and a real advantage over social media pages.
- Grounding the AI only in database content is the right call; it limits made-up answers.
- Focusing on college only and two account roles makes the scope much more realistic.

### Weaknesses and risks

| Issue | Why it matters |
|---|---|
| **No one to verify or moderate** | Removing the administrator role leaves nobody to approve organizations, handle reports, or remove fake reviews. Verification is the core feature, so this needs a clear answer (for example, a developer-managed process outside the app, or automated checks). |
| **Scope is still large** | AI, analytics, CSV, and video in one release is a lot for a student project. Expect delays. |
| **Data accuracy** | If tuition and offerings are outdated, users stop trusting Program Course Finder no matter how good the AI is. |
| **Empty platform problem** | Users need colleges listed; colleges need users. No plan yet for getting the first colleges onboard. |
| **Fake or biased reviews** | Anyone can post. Without limits (one review per user, report button), ratings can be manipulated. |
| **Conflict of interest** | Paid ads plus "smart recommendations" will look biased unless clearly separated. |
| **No technical design** | Section on architecture is still empty. Database, stack, and AI provider must be decided before development. |
| **AI depends on reviews** | Answers based on reviews are only as good as the reviews. Courses with few or no reviews need a clear "not enough reviews yet" message, not a guess. |

> **Bottom line**
> Program Course Finder's biggest challenge is trust, not AI. Build a reliable, verified college directory with good search and comparison first. Add AI only where it clearly helps users decide.

## 9. Recommended Roadmap

| Phase | Deliverables |
|---|---|
| **1. MVP** | User and organization accounts, organization profile with contacts and links, verification document upload, offerings with tuition, search and filters, distance, comparison. |
| **2. Engagement** | Reviews, ratings, replies, likes/dislikes, reporting, organization dashboard, notifications. |
| **3. AI** | Grounded AI assistant (course reviews, distance, convenience), review summaries, translation. |
| **4. Scale** | CSV bulk upload, video ads and banners, advanced analytics. |

## 10. Success Measures

- At least 90% of listed colleges are verified.
- Tuition and offerings updated within the last 12 months.
- Users can find and compare matching colleges in under 5 minutes.
- AI answers are correct and sourced in test checks.

*Pending: technical architecture (stack, database schema, AI provider, hosting) to be added once finalized.*
