# Amiyo Module 2 — SM-2 Algorithm and Complete In-App Test Guide

> ## Important: current implementation update
>
> The scheduler is now **opt-in**. Opening a completed guide records a guide-view analytics event only; it does **not** add the guide to the review schedule. To schedule a guide, go to **Study guides** and click **Add to scheduler** on a completed guide's card. The button becomes **Added to scheduler**. Deleting a review schedule entry does not delete the guide; the student can add it again later.
>
> The current rating intervals below replace every older interval example later in this document:
>
> | Rating | First rating | Second rating | Third and later ratings |
> |---|---:|---:|---|
> | Again (`0`) | 2 days; reset successful count | 2 days; reset successful count | 2 days; reset successful count |
> | Hard (`2`) | 3 days | 5 days | `interval × ease × 0.8` |
> | Good (`4`) | 4 days | 8 days | `interval × ease` |
> | Easy (`5`) | 6 days | 12 days | `interval × ease × 1.3` |
>
> A newly scheduled guide starts **due today**, with ease factor `2.5`, interval `0`, and review count `0`. The standard ease calculation is still used: Again lowers ease most, Hard lowers it slightly, Good keeps it stable, and Easy increases it.

## Current in-app test path

```text
1. Log in.
2. Open Study guides from the sidebar.
3. Find a completed guide and click Add to scheduler.
4. Confirm the button says Added to scheduler.
5. Open Review schedule → Due now: the topic appears once with ease 2.50.
6. Click Again, Hard, Good, or Easy and check it moves to Upcoming with its matching first interval above.
7. Rate the same upcoming topic again for the matching second interval above.
8. Click Remove: the schedule entry disappears, but the guide remains under Study guides.
9. Return to Study guides and click Add to scheduler again: it creates a fresh due-today entry.
```

The detailed notes below were written before this opt-in and rating-interval update. Use this update section for the actual app behavior and viva answers; the remaining sections still explain the shared concepts, endpoints, database fields, email reminders, and SM-2 ease formula.

## What this feature does

Your Module 2 feature is a personal spaced-repetition review schedule.

```text
Open completed study guide
→ create one review entry for its topic
→ topic is due today
→ student rates recall: Again / Hard / Good / Easy
→ SM-2 calculates ease, interval, review count, and next due date
→ review moves between Due now and Upcoming
→ due reviews can receive one Resend email reminder per day
```

---

# Part 1 — SM-2 algorithm used in this project

## 1. What SM-2 is

SM-2 is a spaced-repetition algorithm. Instead of asking a student to review every topic every day, it increases the time before the next review when the student remembers well, and brings the topic back sooner when they struggle.

Each review entry stores these values:

| Field | Meaning |
|---|---|
| `ease_factor` | How easy this topic is for the student. Starts at `2.5`; higher means intervals grow faster. |
| `interval_days` | Number of days until the next review. |
| `review_count` | Number of successful reviews in the current learning streak. |
| `next_review_date` | Calendar date when the topic becomes due. |

Your code is in [review_schedule_service.py](F:\chhaya\chhaya-backend\app\services\review_schedule_service.py:15).

## 2. Rating buttons and quality values

The UI uses four readable buttons, mapped to normal SM-2 quality values from 0–5:

| Button | Quality value | Student meaning |
|---|---:|---|
| Again | `0` | “I could not recall this.” |
| Hard | `2` | “I recalled it poorly / with difficulty.” |
| Good | `4` | “I recalled it correctly.” |
| Easy | `5` | “I recalled it very easily.” |

The mapping is defined in [ReviewSchedulePage.jsx](F:\chhaya\chhaya-frontend\src\pages\reviews\ReviewSchedulePage.jsx:20).

## 3. Ease-factor formula

For every rating, the code calculates a new ease factor:

```text
new ease = max(1.3,
  old ease + 0.1 - (5 - quality) × (0.08 + (5 - quality) × 0.02)
)
```

This is the standard SM-2 adjustment formula. The `max(1.3, ...)` rule prevents ease from becoming too low.

The exact code is:

```python
new_ease_factor = max(
    1.3,
    ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
)
```

Source: [review_schedule_service.py](F:\chhaya\chhaya-backend\app\services\review_schedule_service.py:18).

## 4. What happens for Again and Hard

In this project, a quality below `3` means the student did not recall the topic well enough. That includes:

```text
Again = 0
Hard  = 2
```

The implementation resets the successful-review streak:

```python
if quality < 3:
    return new_ease_factor, 2, 0
```

Source: [review_schedule_service.py](F:\chhaya\chhaya-backend\app\services\review_schedule_service.py:24).

Result:

| Value | Result |
|---|---|
| `interval_days` | `2` — topic is due in two days. |
| `review_count` | `0` — successful streak restarts. |
| `ease_factor` | Drops; Again drops more than Hard. |

## 5. What happens for Good and Easy

For a successful rating (`Good = 4`, `Easy = 5`), the interval grows in simple stages:

```python
if review_count == 0:
    new_interval_days = 2
elif review_count == 1:
    new_interval_days = 6
else:
    new_interval_days = max(1, round(interval_days * new_ease_factor))

return new_ease_factor, new_interval_days, review_count + 1
```

Source: [review_schedule_service.py](F:\chhaya\chhaya-backend\app\services\review_schedule_service.py:30).

| Successful review stage | Interval result |
|---|---|
| First Good/Easy (`review_count = 0`) | 2 days |
| Second Good/Easy (`review_count = 1`) | 6 days |
| Third and later successes | previous interval × current ease factor |

## 6. Concrete SM-2 examples from a fresh topic

A newly opened completed guide creates a review with:

```text
ease factor = 2.5
interval = 0 days
review count = 0
next review date = today
```

### Again

```text
quality = 0
new ease = 2.5 + 0.1 - 5 × (0.08 + 5 × 0.02)
         = 2.5 + 0.1 - 0.9
         = 1.7
interval = 2 days
review count = 0
next date = today + 2 days
```

### Hard

```text
quality = 2
new ease = 2.5 + 0.1 - 3 × (0.08 + 3 × 0.02)
         = 2.5 + 0.1 - 0.42
         = 2.18
interval = 2 days
review count = 0
next date = today + 2 days
```

### Good

```text
quality = 4
new ease = 2.5 + 0.1 - 1 × (0.08 + 1 × 0.02)
         = 2.5
interval = 2 days
review count = 1
next date = today + 2 days
```

### Easy

```text
quality = 5
new ease = 2.5 + 0.1
         = 2.6
interval = 2 days
review count = 1
next date = today + 2 days
```

### Second Good review

Assume the topic currently has:

```text
ease = 2.5
interval = 2 days
review count = 1
```

After Good:

```text
ease = 2.5
interval = 6 days
review count = 2
next date = today + 6 days
```

### Third Good review

Assume the topic has:

```text
ease = 2.5
interval = 6 days
review count = 2
```

After Good:

```text
new interval = round(6 × 2.5) = 15 days
review count = 3
next date = today + 15 days
```

## 7. How the new date is saved

After SM-2 returns values, this code calculates the date:

```python
next_review_date=date.today() + timedelta(days=interval_days)
```

Source: [review_schedule_service.py](F:\chhaya\chhaya-backend\app\services\review_schedule_service.py:69).

Then [review_schedule_repository.py](F:\chhaya\chhaya-backend\app\repositories\review_schedule_repository.py:82) updates the review row with the new ease, interval, count, date, and `last_reviewed_on`.

---

# Part 2 — Complete in-app testing guide

## Before testing

1. Start the backend and frontend.
2. Log in with a test account.
3. Ensure you have at least one **completed** study guide. If you do not, create a study guide and wait until its page shows finished content.
4. Use different guide topics for different tests. This keeps the expected results easy to see.

## Test A — Automatic review creation

### Navigation

```text
Login
→ Study guides (sidebar)
→ open a completed guide
→ Review schedule (sidebar)
→ Due now
```

### Expected result

- The guide topic appears once in **Due now**.
- It displays a due date of today.
- It shows an ease factor of `2.50`.
- It has rating buttons: Again, Hard, Good, Easy.

### What this proves

```text
GuideDetailPage
→ POST /progress/study-guide-views
→ analytics endpoint calls create_review_from_study_guide
→ one review_schedules row exists
→ Review schedule page reads and displays it
```

## Test B — Duplicate guide opening

### Navigation

```text
Study guides
→ open the exact same completed guide again
→ refresh the guide page once
→ Review schedule
→ All reviews
```

### Expected result

The topic appears only **one time**.

### Why

The database has a unique rule for `(user_id, study_guide_id)`. Repeated guide views may record analytics views, but they do not create duplicate review schedules.

## Test C — Again rating

### Navigation

```text
Review schedule
→ Due now
→ select a fresh topic
→ click Again
→ Upcoming
```

### Expected result

- The topic leaves Due now.
- It appears in Upcoming.
- The next due date is in two days.
- The displayed interval is 2 days.
- Ease is lower than `2.50` (fresh-topic expected value: `1.70`).

## Test D — Hard rating

Use another fresh completed guide topic.

### Navigation

```text
Study guides
→ open another completed guide
→ Review schedule
→ Due now
→ click Hard
→ Upcoming
```

### Expected result

- Due in two days.
- Interval 2 days.
- Ease lower than `2.50`, but higher than Again's `1.70`.
- Fresh-topic expected ease: `2.18`.

## Test E — Good rating

Use another fresh completed guide topic.

### Navigation

```text
Study guides
→ open another completed guide
→ Review schedule
→ Due now
→ click Good
→ Upcoming
```

### Expected result

- Due in two days.
- Interval 2 days.
- Ease remains `2.50` for a fresh topic.
- The topic is now a successful first review (`review_count = 1` internally).

## Test F — Easy rating

Use another fresh completed guide topic.

### Navigation

```text
Study guides
→ open another completed guide
→ Review schedule
→ Due now
→ click Easy
→ Upcoming
```

### Expected result

- Due in two days.
- Interval 2 days.
- Ease increases from `2.50` to `2.60`.

## Test G — Second and third successful interval

The current Review Schedule UI allows a topic in **Upcoming** to be rated early. That is useful for fast demonstration/testing; in a future stricter version, ratings could be restricted to due reviews only.

### Navigation to test 6 days

```text
Review schedule
→ Upcoming
→ choose the topic you rated Good once
→ click Good again
```

### Expected result

```text
Interval becomes 6 days.
```

### Navigation to test 15 days

```text
Stay in Upcoming
→ click Good once more on the same topic
```

### Expected result

```text
Interval becomes about 15 days for ease 2.50.
```

## Test H — Filters

### Navigation

```text
Review schedule
→ click Due now
→ click Upcoming
→ click All reviews
```

### Expected result

| Tab | Shows |
|---|---|
| Due now | Reviews whose date is today or earlier. |
| Upcoming | Reviews with a date after today. |
| All reviews | Both groups. |

## Test I — Remove a review

### Navigation

```text
Review schedule
→ All reviews
→ choose a topic
→ Remove
→ confirm browser popup
```

### Expected result

- The topic disappears immediately.
- Switching between all filters does not show it again.

## Test J — Empty state

### Navigation

```text
Review schedule
→ remove all visible review topics
→ Due now / Upcoming / All reviews
```

### Expected result

The page shows a friendly empty-state message, not an error or blank page.

---

# Part 3 — Resend email reminder test

## 1. Configure Resend first

In `chhaya-backend/.env`, add real Resend settings:

```env
RESEND_API_KEY=re_your_actual_key
RESEND_FROM_EMAIL=your-verified-sender@yourdomain.com
```

Then restart the backend. The sender email must be verified in your Resend account.

For Resend testing/sandbox accounts, the recipient may also need to be your own verified email address. Use a Chhaya test account registered with an inbox you can access.

## 2. Create a due review

### Navigation

```text
Login with the account whose email you can receive
→ Study guides
→ open a completed guide you have not opened before
→ Review schedule
```

The newly created review is due today.

## 3. Trigger the reminder check in the app

When `ReviewSchedulePage` opens, it silently calls:

```text
POST /reviews/reminders/check
```

The call is made in [ReviewSchedulePage.jsx](F:\chhaya\chhaya-frontend\src\pages\reviews\ReviewSchedulePage.jsx:57).

### Navigation

```text
Any app page
→ Review schedule
→ wait a few seconds
→ check inbox and spam folder
```

### Expected email

Subject:

```text
Chhaya review due: <your topic>
```

Body:

```text
Your review for <your topic> is due today.
Open Chhaya and rate how well you recalled it to schedule the next review.
```

## 4. Test one-email-per-day protection

### Navigation

```text
Review schedule
→ leave to another sidebar page
→ return to Review schedule
→ refresh once
```

### Expected result

You should receive **no duplicate email for the same topic on the same day**.

After successful delivery, the backend saves today's date into `last_reminded_on`; future checks skip that review until another day.

## 5. Test without Resend configuration

Remove or leave blank the two Resend values and restart backend.

### Navigation

```text
Review schedule
→ open/refresh the page with a due topic
```

### Expected result

- The review page still loads normally.
- Rating, filtering, and deletion still work.
- No email is sent.
- The app does not crash.

This is intentional: the reminder feature fails safely when credentials are absent during local development.

## 6. Important implementation note for viva

The current implementation performs the reminder check when a student opens the Review Schedule page. The backend endpoint is designed to be safe to call once per day and sends at most one reminder per review per day.

For a fully unattended production system, a server scheduler/cron job can call the same endpoint daily. The current week-two implementation keeps the trigger simple and testable from within the app.

---

# Part 4 — Complete live-demo path

Use this in order during your demo:

```text
1. Log in with a test account.
2. Open a completed study guide.
3. Open Review schedule → show topic under Due now.
4. Click Good → show it moved to Upcoming with a two-day interval.
5. Click Good again in Upcoming → show six-day interval.
6. Click All reviews → show stored topic, due date, interval, and ease.
7. Open the same guide again → prove it does not create a duplicate review.
8. Remove one topic → prove Delete works.
9. With Resend configured, open Review schedule with a newly due topic → show reminder in inbox.
10. Refresh Review schedule → prove no duplicate email arrives that day.
```

## Final one-minute explanation

> Opening a completed guide creates one review schedule entry for that topic. It begins due today with ease factor 2.5. When the student rates recall, Again and Hard reset the interval to one day and reset the successful streak, while Good and Easy increase the review interval through the SM-2 stages of one day, six days, then interval times ease factor. The review dashboard separates due and upcoming topics, and Resend sends a due reminder at most once per topic per day when the reminder check runs.
