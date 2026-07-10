# BloodLink — Blood Donor Management and Tracking System

A full-stack web application for managing blood donors, tracking donations, handling blood requests, and generating reports.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, Bootstrap 5, Vanilla CSS, Chart.js |
| Backend | Python Flask (blueprints) |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (JWT) |

---

## Setup Instructions

### 1. Clone / Open the Project

```bash
cd "blood donor management and tracking system"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate       # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Edit `.env` and fill in your Supabase credentials:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SECRET_KEY=your-random-flask-secret
```

> ⚠️ Never commit `.env` to version control.

### 5. Set Up the Database

1. Go to your **Supabase Dashboard → SQL Editor**
2. Copy and paste the contents of `supabase_schema.sql`
3. Click **Run** — this creates all tables, RLS policies, triggers, and seed data

### 6. Run the App

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Creating the First Admin User

1. Register through the UI at `/auth/register` (creates a `donor` role by default)
2. In Supabase SQL Editor, promote yourself to admin:
   ```sql
   UPDATE public.profiles
   SET role = 'admin'
   WHERE email = 'your@email.com';
   ```
3. Log out and log back in — admin features will appear

---

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Supabase client
│   ├── decorators.py        # Auth decorators
│   ├── auth/                # Login, Register, Logout
│   ├── dashboard/           # Dashboard & stats
│   ├── donors/              # Donor CRUD
│   ├── donations/           # Donation tracking
│   ├── requests/            # Blood requests
│   ├── reports/             # Analytics & CSV export
│   ├── admin/               # Admin panel
│   └── templates/           # Jinja2 HTML templates
├── static/
│   ├── css/custom.css       # Design system
│   └── js/main.js           # Frontend JS
├── supabase_schema.sql      # Database schema
├── requirements.txt
├── run.py                   # Entry point
└── .env                     # Environment variables (not committed)
```
🌐 Live Demo

🚀 Live Website

👉 https://blood-donor-management-and-tracking.onrender.com/

---

## Features

- 🔐 **Auth** — Supabase JWT-based login/register with role-based access
- 👥 **Donor Management** — Add, edit, delete, search donors; eligibility tracking (56-day rule)
- 💉 **Donation Tracking** — Record donations; auto-updates donor stats and blood inventory
- 🔔 **Blood Requests** — Submit requests with urgency levels; admin status management
- 📊 **Reports** — Chart.js analytics (monthly trend, blood group pie), CSV export
- 🛡️ **Admin Panel** — User role management, blood inventory adjustments
- 🌙 **Dark Theme** — Crimson-accented dark UI with glassmorphism sidebar
