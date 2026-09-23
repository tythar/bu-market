# Installation Guide — BU-MARKET MVP

This guide explains how to install, configure, and troubleshoot the BU-MARKET application for local development and production.

---

## 💻 Local Installation

### 1. Requirements
Ensure you have the following installed:
- Python 3.12+
- pip (Python package manager)
- PostgreSQL / Supabase account

### 2. Step-by-Step Setup
1. Clone the codebase and enter the directory:
   ```bash
   git clone <repo_url>
   cd bu-market
   ```
2. Create and launch virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables:
   Create a `.env` file in the root directory (alongside `manage.py`) and enter the following settings:
   ```env
   DEBUG=True
   SECRET_KEY=your-django-secret-key-goes-here
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgresql://user:password@host:port/dbname
   SUPABASE_URL=https://<your-project-id>.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
   SUPABASE_STORAGE_BUCKET=media
   ```
5. Build the local database:
   ```bash
   python manage.py migrate
   ```
6. Seed default pricing plans, university categories, and the default admin account:
   ```bash
   python manage.py seed_db
   ```
7. Start the development server:
   ```bash
   python manage.py runserver
   ```
8. Navigate to `http://127.0.0.1:8000/` to log in using:
   - **Username**: `admin`
   - **Password**: `admin123`

---

## 🚀 Production Deployment (Gunicorn / Whitenoise)

The project includes production-ready configurations:
- **Gunicorn**: Configured in requirements, launchable using `gunicorn bu_market.wsgi:application`.
- **Whitenoise**: Embedded in `settings.py` middleware to serve compressed static assets in production automatically.

To test production assets compilation:
```bash
python manage.py collectstatic --noinput
```
