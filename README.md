ForHer - Holistic Menstrual Health & Cycle Syncing Platform

ForHer is a comprehensive FemTech web application designed to bridge the gap between menstrual tracking and daily lifestyle management. Unlike standard period trackers that only log dates, ForHer integrates Cycle Syncing—aligning nutrition, fitness, and mental wellness with a woman's hormonal rhythm.

🚀 Features

1. Smart Cycle Tracking

AI Prediction: Uses Linear Regression (Scikit-Learn) to predict future cycle lengths based on historical data, adapting to trends (e.g., shortening cycles) better than simple averages.

Interactive Calendar: Visualizes past logs and future predictions using FullCalendar.js.

2. Proactive Health Monitoring

Anomaly Detection: Automatically flags health risks:

Short Cycles (< 21 days) -> Polymenorrhea Warning

Long Cycles (> 35 days) -> Oligomenorrhea/PCOS Warning

Irregular Variance -> Stability Alert

Medical Alerts: Immediate warnings for "Unusual Discharge" (Infection risk) or "Super Heavy Flow" (Menorrhagia).

3. Daily Log & Analysis

Quick-Tap Interface: Log symptoms (Cramps, Acne, Mood) via an intuitive, app-like modal.

Instant Insights: The system analyzes logs in real-time to explain why symptoms are occurring (e.g., "Headache likely due to progesterone withdrawal").

4. Cycle Syncing Ecosystem

Phase-Based Nutrition: Fetches curated recipes from Contentful (Headless CMS) tailored to the current hormonal phase (e.g., Magnesium-rich foods for Luteal).

Wellness Studio: Embeds phase-appropriate YouTube playlists (Restorative Yoga for Menstrual, HIIT for Ovulation).

Adaptive Gaming: Suggests cognitive games based on energy levels:

Tetris (Luteal) for organizing thoughts.

Trivia (Ovulation) for social energy.

Coloring (Menstrual) for relaxation.

5. Doctor's Report

Generates a professional PDF Report using ReportLab.

Summarizes cycle history, flags anomalies, and plots consistency graphs (Matplotlib) for medical consultation.

🛠️ Technology Stack

Backend: Python 3.13, Flask

Database: SQLite (Development), SQLAlchemy (ORM)

Authentication: Flask-Login, Werkzeug Security (SHA-256 Hashing)

Frontend: HTML5, CSS3, Bootstrap 4, Jinja2 Templating

Machine Learning: Scikit-Learn (Linear Regression), NumPy

APIs & Services:

Contentful API: Headless CMS for recipe management.

YouTube Data: Wellness video integration.

OpenTDB: Trivia game questions.

Libraries: ReportLab (PDF), Matplotlib (Graphing), FullCalendar.js (UI).

⚙️ Installation & Setup

Clone the Repository

git clone https://github.com/Starryeyess/ForHer.git
cd ForHer


Create a Virtual Environment

python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate


Install Dependencies

pip install -r requirements.txt


Configure Environment Variables
Create a .env file in the root directory (use .env.example as a template) and add your keys:

SECRET_KEY=your_secret_key
CONTENTFUL_SPACE_ID=your_space_id
CONTENTFUL_ACCESS_TOKEN=your_access_token


Run the Application

python main.py


Access the app at http://127.0.0.1:5000.

📂 Project Structure

ForHer/
├── main.py              # Entry point
├── website/
│   ├── __init__.py      # App factory & DB setup
│   ├── auth.py          # Login/Signup routes
│   ├── views.py         # Core logic (Prediction, Phases, Logging)
│   ├── models.py        # Database Schema (User, Period, DailyLog)
│   ├── static/          # CSS, JS, Images, Game Assets
│   └── templates/       # HTML Pages (Home, Profile, Games, Reports)
└── instance/
    └── database.db      # SQLite Database


🛡️ Security & Privacy

User passwords are hashed using SHA-256.

Session management prevents unauthorized access to the dashboard.

Environment variables protect API keys from being exposed in version control.