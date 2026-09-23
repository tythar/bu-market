https://bu-market-amber.vercel.app/
# BU-MARKET MVP

BU-MARKET is a mobile-first campus marketplace designed for the Bugema University community. It enables students and verified campus sellers to list items (electronics, books, hostel utilities, clothing) and services, while allowing buyers to securely browse, search, and purchase items.

---

##  Getting Started

Follow these steps to set up and run the project locally on your machine.

### Prerequisites
- Python 3.12 or newer installed
- Git installed

### Installation & Launch

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd bu-market
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Seed Default Data & Create Superuser:**
   Initialize categories, subscription plans, and the default admin user by running the custom database seeding command:
   ```bash
   python manage.py seed_db
   ```
   *Note: This automatically creates a default superuser account for local testing:*
   - **Username**: `admin`
   - **Password**: `admin123`

6. **Create a custom superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

Open your browser and navigate to `http://127.0.0.1:8000/` to view the application!

---

## 🛠️ Project Structure & Ownership

This project is organized into modular Django apps to allow concurrent team development:

- `accounts/` — User accounts, role definitions, and registration forms.
- `marketplace/` — Categories, listing models, views, and server-side limit validations.
- `subscriptions/` — Pricing plans, receipt uploads for seller subscription packages.
- `payments/` — Buyer memberships and transaction history tracking.
- `moderation/` — Listing review queues for moderators to approve/reject postings.
- `dashboard/` — Portal screens tailored to each role (Seller, Buyer, Accountant, Moderator, Admin).
- `core/` — Public homepage, listing details, profile screens, search, and query filters.
- `templates/` — HTML layouts using Bootstrap 5 with responsive mobile bottom navigation.
