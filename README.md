# SBVM Vinayaka Association – Ganesh Chanda Collection Management

A clean, responsive, full-stack Django application for managing Ganesh Chanda/Donation collections and payment history.

## Features

- **Dashboard**: High-level collection summaries (Total Donors, Paid/Due Counts, Amount Collected, and Pending Due Amounts) along with a recent activity feed.
- **Google Maps Integration**: Autocomplete-assisted address entry. Automatically saves formatted address strings, exact latitude/longitude coordinates, and Google Place IDs.
- **Dynamic Map Pinning**: Open a donor's precise location directly in Google Maps via dynamically generated GPS URLs in a single click.
- **Automated Notifications**: Abstraction-based invitation/receipt delivery. Sends formatted welcome and invitation emails when a donor's status changes from DUE to PAID.
- **Global Search & Filter**: Search donors by Name, Mobile, Email, or Address and filter by Status, Amount Range, or Date Ranges.
- **Robust Validation**: Indian mobile format checking and positive amount validations.
- **Admin Authentication**: Enforced login security for all dashboards, detail views, and action controllers.
- **Retry Mechanism**: Manual retry button for welcome emails in case of SMTP connection issues.
- **Clean Responsive Styling**: Modern CSS dashboard featuring side navigation (responsive for mobile viewports) with saffron and maroon accents.

---

## Technology Stack

- **Backend**: Python 3.13+, Django 5.x
- **Database**: MySQL (default) / SQLite (automatic fallback)
- **Frontend**: HTML5, Vanilla CSS3, Vanilla JavaScript (Places Autocomplete)
- **Email**: Django SMTP Mail Engine (Automatic console logging fallback for development testing)

---

## Local Setup & Installation

Follow these steps to run the application on your local machine:

### 1. Prerequisite Checklist
- **Python**: Ensure Python 3.10+ is installed (`python --version`)
- **MySQL**: A running MySQL Server instances (if running in production database mode)

### 2. Set Up Virtual Environment
Initialize a virtual environment in the project root directory:

```bash
# Create virtual environment
python -m venv env

# Activate on Windows (PowerShell)
.\env\Scripts\Activate.ps1

# Activate on macOS/Linux
source env/bin/activate
```

### 3. Install Dependencies
Install Python libraries from the requirements file:

```bash
pip install -r requirements.txt
```

### 4. Create Database
Log in to your MySQL terminal and run the SQL statement to create the database:

```sql
CREATE DATABASE chanda_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Setup Environment Configurations (`.env`)
Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in your settings:
- **`SECRET_KEY`**: A unique string for encryption.
- **`DEBUG`**: Set to `True` for local development, `False` in production.
- **MySQL Connection**: Fill in `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. *(If left blank, the app automatically falls back to an SQLite database file `db.sqlite3`)*.
- **`GOOGLE_MAPS_API_KEY`**: Insert your Google Maps API key with the **Places API** and **Maps JavaScript API** enabled in the Google Cloud Console.
- **Email/SMTP Settings**: Fill in your email account credentials (e.g. Gmail with App Passwords) for sending welcome messages. *(If left blank, emails will print to the console instead of sending over the internet)*.

---

## Database Migrations & Administration

### 1. Apply Migrations
Apply database migrations to structure the database:

```bash
python manage.py makemigrations donors
python manage.py migrate
```

### 2. Create Superuser (Admin Account)
Create an administrative login to access the system:

```bash
python manage.py createsuperuser
```
Follow the terminal prompts to input a username, email, and password.

---

## Running the Application

### 1. Start Development Server
Launch the Django built-in local development server:

```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

### 2. How to Use the Application
1. **Login**: Log in using the superuser credentials you created.
2. **Dashboard**: View collection totals.
3. **Add Donor / Collect Chanda**: Fill in donor details. Start typing in the "Search Address" field. Select an address from the Google Autocomplete suggestion list. Choose PAID or DUE and save.
4. **Mark as Paid**: Go to the **Due** list. Click **Mark Paid** on any entry. A confirmation dialog will pop up. Confirming the dialog updates the database and triggers the automated email notification.
5. **View Detail**: Click on any donor name to view their complete profile, see coordinates, click their address to open in Google Maps, and review email notification dispatch logs.
6. **Advanced Search**: Go to the **Advanced Search** tab to perform granular query searches.

---

## Running Automated Tests

Verify code correct and security logic by executing the test cases:

```bash
python manage.py test donors
```
*(All 6 unit tests should complete successfully with an `OK` result).*

---

## Production Considerations

When deploying to a production server (e.g., AWS, DigitalOcean, Heroku):
1. Change `DEBUG` in `.env` to `False`.
2. Generate a secure, randomized `SECRET_KEY`.
3. Set `ALLOWED_HOSTS` to your production domain name (e.g. `allowed_hosts=yourdomain.com`).
4. Set up a secure MySQL server with database access restrictions.
5. Configure static files collection: `python manage.py collectstatic`.
6. Use a WSGI/ASGI server like Gunicorn or Uvicorn behind a reverse proxy (Nginx).
