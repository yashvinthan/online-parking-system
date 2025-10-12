Online Parking Slot Booking System (Django)

Overview
- Django 4.x backend with DRF APIs
- Bootstrap 5 frontend with responsive UI
- Stripe test payments, Google Pay/Paytm/card preferences, and QR confirmation
- Vehicle-aware pricing tiers with rate management from the admin
- Admin insights dashboard (Chart.js) plus daily revenue report
- Google OAuth sign-in via django-allauth

Quick Start
1) Create venv and install deps
   - Windows: `python -m venv .venv && .venv\Scripts\python -m pip install -r requirements.txt`
2) Environment (optional; defaults provided)
   - `DJANGO_DEBUG=1`
   - `STRIPE_PUBLIC_KEY=pk_test_...`
   - `STRIPE_SECRET_KEY=sk_test_...`
   - `BOOKING_HOURLY_RATE=50`
   - `GOOGLE_CLIENT_ID=...` (OAuth client ID)
   - `GOOGLE_CLIENT_SECRET=...`
   - `DJANGO_SITE_ID=1`
3) Initialize DB
   - `.venv\Scripts\python manage.py migrate`
   - `.venv\Scripts\python manage.py createsuperuser`
4) Run server
   - `.venv\Scripts\python manage.py runserver`

Sample Data
- Migrations seed 10 parking slots and default pricing tiers (Hatchback/Sedan/SUV/EV).

Key URLs
- Home: `/`
- Auth: `/accounts/login/`, `/accounts/signup/`
- Dashboard: `/bookings/dashboard/`
- Book: `/bookings/book/`
- Admin: `/admin/`
- Admin Daily Report: `/bookings/admin/reports/daily/` (staff only)
- Admin Analytics: `/bookings/admin/dashboard/` (staff only)
- APIs (DRF): `/api/slots/`, `/api/bookings/`, `/api/users/` (admin only)

Authentication
- Username/password plus Google sign-in (`/oauth/login/google/`).
- Configure OAuth credentials in Google Cloud Console and set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`.
- Update the Django Site domain in `/admin/sites/site/` to match your callback origin.

Payments
- Uses Stripe Checkout in test mode; set keys via env vars.
- On successful payment, a QR code image is generated under `media/qr_codes/` and shown on the confirmation page.

Notes
- Custom user model `accounts.User` adds `phone` and `preferred_payment_method` fields.
- SQLite is used for local development by default.
- For production, set `DJANGO_ALLOWED_HOSTS`, secure secret key, configure HTTPS, and update the Sites domain.

Docker (optional)
- Build: `docker build -t parking-system .`
- Run: `docker run -p 8000:8000 --env STRIPE_PUBLIC_KEY=... --env STRIPE_SECRET_KEY=... parking-system`
# online-parking-system
