# Air — AI Reservations: Platform Guide

---

## What's Been Built

### Core Platform
- **User authentication** — signup, login, logout via Firebase Auth
- **Password reset** — forgot password flow sends email via Firebase
- **Session management** — Flask sessions, login-required route protection
- **Host role** — separate permissions for hosts vs guests

### Listings
- **Homes** — create, edit, publish, view; amenities, bedrooms, bathrooms, location, images
- **Experiences** — create, edit, publish, view; duration, group size, category
- **Events/Parties** — create, edit, publish, view; ticket price, capacity, date/time
- **Hotels** — search via Google Places API (New); photos, ratings, address pulled live
- **Listing detail pages** — full info, image gallery, booking form, reviews section, AI voice widget

### Bookings & Payments
- **Stripe Checkout** — guests pay a flat $9.99 Air service fee per booking
- **Booking records** — stored in Firestore with guest, listing, dates, status
- **Booking cancellation** — guests can cancel from their bookings page
- **My Bookings page** — guests see all past and upcoming bookings

### Reviews & Ratings
- **Star rating system** (1–5) — guests leave a rating + written review
- **Duplicate prevention** — one review per guest per listing
- **Live average** — listing's rating average updates after every new review
- **Reviews displayed** on listing detail pages with reviewer name and date

### AI Voice Agent (Retell AI)
- **Auto-agent creation** — when a host enables the AI toggle, an agent is created automatically via Retell API
- **Voice widget** — "Start Voice Chat" button on listing detail pages (appears only if AI is enabled)
- **Context-aware** — agent is pre-loaded with the listing's title, location, price, and description
- **Browser SDK** — uses `retell-client-js-sdk` to connect the voice call in-browser

### Design & UI
- **Inter font** across the whole app
- **Redesigned hero** — deep navy gradient, glow blobs, wave divider, stats bar
- **Card hover effects** — listings lift on hover with blue shadow
- **Category pills** — Homes, Experiences, Events, Hotels on homepage
- **Host CTA banner** — bottom of homepage
- **Responsive** — works on mobile and desktop
- **Flash messages** — animated success/error toasts
- **Footer** — links to Terms, Privacy, listing categories

### Legal & Trust
- **Terms of Service** page (`/terms`)
- **Privacy Policy** page (`/privacy`)
- **CSRF protection** — all POST forms protected via Flask-WTF

---

## What Still Needs to Be Done

### Before Launch (required)

| # | Task | Why |
|---|------|-----|
| 1 | **Email notifications** | Guests expect a booking confirmation email. Use SendGrid or Mailgun (both free tiers available). Send on booking creation and cancellation. |
| 2 | **Production deployment** | The app only runs on your local machine. No one else can access it yet. See deployment section below. |
| 3 | **Retell AI full setup** | The code is wired up, but you still need to configure your Retell account. See the Retell AI setup section below. |
| 4 | **Test the booking flow end-to-end** | Run through a full booking with Stripe test cards before going live. |

### After Launch (nice to have)

| # | Task | Why |
|---|------|-----|
| 5 | **Pagination** | All listings currently load at once. Add page limits (e.g. 12 per page) before you have large data. |
| 6 | **Login rate limiting** | Prevents brute-force attacks. Add `flask-limiter` with ~5 attempts per minute on `/auth/login`. |
| 7 | **Image optimization** | Uploaded images aren't compressed. Large images slow down the site. Consider resizing on upload. |
| 8 | **Admin dashboard** | No way to moderate listings or ban users currently. Build a simple `/admin` panel. |
| 9 | **SEO meta tags** | Each listing page needs a unique `<title>` and `<meta description>` for Google indexing. |
| 10 | **Sitemap** | Submit a `sitemap.xml` to Google Search Console after launch. |

---

## Retell AI — Full Setup Guide

### Step 1: Create a Retell Account
1. Go to [retellai.com](https://retellai.com) and sign up
2. In the dashboard, go to **API Keys** and copy your API key
3. Add it to your `.env` file:
   ```
   RETELL_API_KEY=key_xxxxxxxxxxxxxxxxxxxx
   ```

### Step 2: Connect an LLM (required by Retell)
Retell needs an LLM to power the agent's responses. In your Retell dashboard:
1. Go to **LLM** → **Create LLM**
2. Choose **OpenAI GPT-4** (recommended) or GPT-3.5-turbo
3. Add your OpenAI API key in Retell's LLM settings
4. Note the **LLM ID** Retell gives you

Then update `app/services/ai_service.py` — add `llm_websocket_url` or `llm_id` to the agent creation payload (check Retell's current API docs for the exact field name, as it may have changed):
```python
payload = {
    'agent_name': f'air_{listing_type}_{listing_id}',
    'language': 'en',
    'system_prompt': prompt,
    'llm_model': 'gpt-4',
    # Add this if Retell requires it:
    # 'llm_id': 'your_llm_id_here',
}
```

### Step 3: Configure a Phone Number (optional)
If you want guests to be able to call a real phone number (not just the in-browser widget):
1. In Retell dashboard → **Phone Numbers** → **Buy Number**
2. Assign it to an agent

For the web widget (what's built), no phone number is needed.

### Step 4: Test the Voice Widget
1. Create a listing and enable the AI Voice Agent toggle
2. After creating the listing, check Firestore — the listing should have:
   ```json
   "aiConfig": {
     "enabled": true,
     "agentId": "agent_xxxxxxxxxx"
   }
   ```
3. Go to the listing's detail page — you should see the blue AI Voice Agent card
4. Click **Start Voice Chat** — your browser will ask for microphone permission
5. Speak to the agent — it should answer questions about the listing

### Step 5: Verify the API Version
Retell updates their API regularly. The current code calls:
- `POST /v1/create-agent` — creates an agent
- `POST /v1/create-call-token` — gets a browser session token

If these return 404, check [Retell's API docs](https://docs.retellai.com) for the current endpoint paths and update `app/services/ai_service.py` accordingly.

---

## How the Database Works

Air uses **Google Firebase Firestore** — a NoSQL cloud database. There are no SQL tables. Instead, data is stored as **collections of documents**.

### Structure

```
Firestore
├── users/
│   └── {userId}/               ← one doc per user
│       ├── email
│       ├── displayName
│       ├── role                 ← "guest" or "host"
│       └── createdAt
│
├── homes/
│   └── {homeId}/               ← one doc per listing
│       ├── title
│       ├── description
│       ├── price
│       ├── hostId              ← references users/{userId}
│       ├── location: { city, country, address }
│       ├── images: [url1, url2, ...]
│       ├── amenities: [...]
│       ├── status              ← "draft" or "published"
│       ├── aiConfig: { enabled: true, agentId: "..." }
│       └── ratings: { average: 4.5, count: 12 }
│
├── experiences/                ← same pattern as homes
├── parties/                    ← same pattern as homes
│
├── bookings/
│   └── {bookingId}/
│       ├── guestId
│       ├── listingId
│       ├── listingType         ← "home", "experience", or "party"
│       ├── listingTitle
│       ├── checkIn
│       ├── checkOut
│       ├── guests
│       ├── totalPrice
│       ├── status              ← "confirmed" or "cancelled"
│       ├── stripeSessionId
│       └── createdAt
│
└── reviews/
    └── {reviewId}/
        ├── listingId
        ├── guestId
        ├── guestName
        ├── rating              ← 1–5
        ├── comment
        └── createdAt
```

### Key Concepts

**No joins** — unlike SQL, Firestore doesn't join collections. When you need data from two collections (e.g. a booking + the listing it refers to), the code fetches them separately.

**Document references** — `hostId` in a home doc is just a string ID. To get the host's name you'd fetch `users/{hostId}` separately.

**Firestore rules** — currently the app uses Firebase Admin SDK (server-side), which bypasses all security rules. This is fine for now but means your server is the gatekeeper — never expose Admin SDK credentials client-side.

**Images** — listing photos are uploaded to **Firebase Storage** (separate from Firestore) and the download URLs are stored in the `images` array of the Firestore document.

**Viewing the database** — go to [console.firebase.google.com](https://console.firebase.google.com) → your project → **Firestore Database**. You can browse, edit, and delete documents directly from there.

---

## Testing Guide

### 1. Authentication Testing

| Test | Steps | Expected |
|------|-------|----------|
| Register | Go to `/auth/register`, fill form | Redirected to home, logged in |
| Login with wrong password | Go to `/auth/login`, enter bad password | Error flash message shown |
| Forgot password | Click "Forgot password", enter email | "Check your email" confirmation |
| Access protected page logged out | Go to `/homes/create` while logged out | Redirected to login |

### 2. Listing Creation Testing

| Test | Steps | Expected |
|------|-------|----------|
| Create home (host) | Log in as host, go to `/homes/create`, fill form | Listing created, redirected to detail page |
| Create listing (guest) | Log in as guest (no host role), visit `/homes/create` | Redirected away (host_required) |
| AI toggle | On create form, flip AI toggle | Info box appears below toggle |
| Create with AI enabled | Enable AI toggle, submit | Check Firestore — `aiConfig.agentId` should be populated |

### 3. Booking & Payment Testing (Stripe)

Use Stripe's test card: **4242 4242 4242 4242** — any future expiry, any CVC.

| Test | Steps | Expected |
|------|-------|----------|
| Book a listing | Go to listing, fill dates/guests, click Book | Redirected to Stripe Checkout |
| Complete payment | Use test card on Stripe | Redirected to `/bookings/success`, booking saved in Firestore |
| Cancel booking | Go to `/bookings/my-bookings`, click Cancel | Booking status changes to "cancelled" |
| Declined card | Use test card `4000 0000 0000 0002` | Stripe shows decline message |

Check your [Stripe dashboard](https://dashboard.stripe.com/test/payments) to confirm test payments appear.

### 4. Reviews Testing

| Test | Steps | Expected |
|------|-------|----------|
| Leave review | Go to any listing, scroll to reviews section, submit stars + comment | Review appears, rating average updates |
| Review again | Try to submit a second review on same listing | Form should not appear (already reviewed) |

### 5. Hotel Search Testing

| Test | Steps | Expected |
|------|-------|----------|
| Search hotels | Go to `/hotels/`, type a city name, click Search | List of hotels with photos and ratings |
| View hotel detail | Click any hotel | Detail page with address, rating, photos |
| No results | Search for gibberish | Empty state message |

If hotels return no results, check that `GOOGLE_PLACES_API_KEY` is set in `.env` and the **Places API (New)** is enabled in Google Cloud Console.

### 6. AI Voice Agent Testing

| Test | Steps | Expected |
|------|-------|----------|
| Widget appears | View a listing with AI enabled | Blue "Air AI Voice Agent" card is visible |
| Widget hidden | View a listing with AI disabled | No AI card shown |
| Start call | Click "Start Voice Chat" | Browser requests mic permission, then "Connected — speak now" |
| Call ends | Hang up | "Call ended" status, button re-enables |

If the call doesn't connect, check:
- `RETELL_API_KEY` is set in `.env`
- The listing's `aiConfig.agentId` is not empty in Firestore
- Browser console for errors

### 7. Quick Smoke Test (run through this before every deployment)

1. Register a new account
2. Create a home listing with AI enabled
3. Publish the listing
4. Log out, log back in as a different user
5. Find the listing, book it with the Stripe test card
6. Confirm booking appears in My Bookings
7. Leave a review
8. Cancel the booking
9. Search for hotels
10. Check Firestore — all records should be present

---

## Deployment (when you're ready)

**Recommended: Railway** (free tier, deploys from GitHub in ~5 minutes)

1. Push your code to a **private** GitHub repo (never push `.env` — it has secrets)
2. Go to [railway.app](https://railway.app), sign up, click **New Project → Deploy from GitHub**
3. Select your repo
4. In Railway's dashboard → **Variables**, add all your `.env` values:
   - `SECRET_KEY`
   - `FIREBASE_WEB_API_KEY`
   - `GOOGLE_PLACES_API_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `RETELL_API_KEY`
   - `FIREBASE_KEY_JSON` (paste the entire contents of your `firebase-key.json`)
5. Add a `Procfile` to your project root:
   ```
   web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT
   ```
6. Add `gunicorn` to `requirements.txt`
7. Push — Railway auto-deploys on every push to main

**After deploying:** Update your Stripe webhook URL in the Stripe dashboard to point to your Railway URL.
