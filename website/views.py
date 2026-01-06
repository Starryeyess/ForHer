

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Period, DailyLog 
from . import db
from datetime import datetime, timedelta, date
import json
import contentful
import io
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from sklearn.linear_model import LinearRegression

views = Blueprint('views', __name__)

from dotenv import load_dotenv


load_dotenv()




client = contentful.Client(os.getenv("SPACE_ID"), os.getenv("DELIVERY_API_TOKEN"), timeout_s=10)



PHASE_INFO = {
    'Menstrual': {
        'metaphor': 'Winter',
        'feeling': 'Relief & Rest',
        
        'bg_color': 'linear-gradient(135deg, #4b3621 0%, #800020 100%)', 
        'text_color': 'white',
        'card_color': 'rgba(255, 255, 255, 0.1)',
        'game_style': 'Zero-effort, Visual (Coloring)',
        'recipe_vibe': 'Warm, Liquid, Iron-rich',
        'wellness_feature': 'Sleep Stories / Audio Mode'
    },
    'Follicular': {
        'metaphor': 'Spring',
        'feeling': 'Energy & Clarity',
        
        'bg_color': 'radial-gradient(circle at top left, #3a6073, #16222a)', 
        'text_color': '#f0f0f0', 
        'card_color': 'rgba(58, 96, 115, 0.4)', 
        'game_style': 'Logic, Puzzle, Strategy',
        'recipe_vibe': 'Fresh, Fermented, Raw',
        'wellness_feature': 'Habit Tracker / Meal Planner'
    },
    'Ovulation': {
        'metaphor': 'Summer',
        'feeling': 'Power & Social',
        
        'bg_color': 'radial-gradient(circle at bottom right, #bf360c, #4a148c)', 
        'text_color': '#f0f0f0',
        'card_color': 'rgba(191, 54, 12, 0.4)',
        'game_style': 'Social, Competitive, Fast',
        'recipe_vibe': 'Cooling, Fancy, Shareable',
        'wellness_feature': 'HIIT Workouts / Social Forum'
    },
    'Luteal': {
        'metaphor': 'Autumn',
        'feeling': 'Nesting & Comfort',
        
        'bg_color': 'radial-gradient(circle at center, #4b6cb7, #182848)', 
        'text_color': '#e0e0e0',
        'card_color': 'rgba(75, 108, 183, 0.4)',
        'game_style': 'Organizing, Repetitive, Cozy',
        'recipe_vibe': 'Comfort Swaps, Magnesium',
        'wellness_feature': 'Mood Journal / "To-Don\'t" List'
    }
}



# --- YOUTUBE PLAYLIST CONFIGURATION ---

PHASE_PLAYLISTS = {
    # Menstrual: Gentle, Restorative (Verified: Restorative Yoga Playlist)
    'Menstrual': 'PLui6Eyny-UzxghGvVE7V_6YsZ7rh5r1Fx',
    
    # Follicular: Fresh, Energetic (Verified: Morning Yoga Playlist)
    'Follicular': 'PLui6Eyny-UzxMFVoPmxcPX1MOeLyV5uKQ',
    
    # Ovulation: High Energy, Power (Verified: Yoga for Weight Loss/Power)
    'Ovulation': 'PLui6Eyny-Uzx2jQYA8MS73ND2kUMHyII8',
    
    # Luteal: Calming, Cozy (Verified: Bedtime Yoga Playlist)
    'Luteal': 'PLui6Eyny-UzxlcWgUFYAcnNInS3SNe6Fs'
}

# --- SYMPTOM ANALYSIS ENGINE ---
# Maps symptoms to biological causes based on the cycle phase
SYMPTOM_INSIGHTS = {
    'Headache': {
        'Menstrual': 'Low estrogen or iron deficiency.',
        'Luteal': 'Progesterone withdrawal often triggers migraines.',
        'Follicular': 'Dehydration or caffeine withdrawal.',
        'Ovulation': 'Hormonal surge (estrogen peak).'
    },
    'Acne': {
        'Luteal': 'High progesterone increases oil production.',
        'Menstrual': 'Hormones are resetting.'
    },
    'Bloating': {
        'Luteal': 'Water retention due to rising progesterone.',
        'Menstrual': 'Prostaglandins causing inflammation.'
    },
    'Cramps': {
        'Menstrual': 'Prostaglandins causing uterine contractions.'
    },
    'Breast Tenderness': {
        'Luteal': 'Swelling of milk glands due to high progesterone.'
    },
    'Cravings: Sweets/Chocolate': {
        'Luteal': 'Drop in serotonin levels; body seeks dopamine.'
    }
}

def get_current_phase_name(user_id):
    # Fetch latest period
    periods = Period.query.filter_by(user_id=user_id).order_by(Period.start_date).all()
    if not periods:
        return "Follicular"
        
    last_period = periods[-1]
    
    if len(periods) >= 2:
        cycles = [(periods[i+1].start_date - periods[i].start_date).days for i in range(len(periods)-1)]
        avg_cycle = sum(cycles) // len(cycles)
    else:
        avg_cycle = 28

    today = date.today()
    days_since_start = (today - last_period.start_date).days + 1
    ovulation_day = avg_cycle - 14 
    
    if days_since_start <= last_period.duration:
        return 'Menstrual'
    elif days_since_start < (ovulation_day - 2):
        return 'Follicular'
    elif days_since_start <= (ovulation_day + 2):
        return 'Ovulation'
    else:
        return 'Luteal'


@views.route('/')
def landing():
    # If user is already logged in, send them straight to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return render_template("landing.html", user=current_user)


@views.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        duration = int(request.form.get('duration'))
        
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        
        existing_period = Period.query.filter_by(user_id=current_user.id, start_date=start_date_obj).first()
        
        if existing_period:
            flash('A period log for this date already exists!', category='error')
        else:
            new_period = Period(start_date=start_date_obj, duration=duration, user_id=current_user.id)
            db.session.add(new_period)
            db.session.commit()
            flash('Period added!', category='success')

   
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date).all()
    
    calendar_events = []
    days_left = "Unknown"
    current_phase_data = None
    phase_name = "Tracking Needed"

    health_alerts = []
    # --- POPULATE CALENDAR WITH PAST EVENTS ---
    for period in periods:
        end_date = period.start_date + timedelta(days=period.duration)
        calendar_events.append({
            'title': 'Period',
            'start': period.start_date.isoformat(),
            'end': end_date.isoformat(),
            'color': '#ff6b6b',
            'display': 'background' 
        })

    if len(periods) > 0:
        last_period = periods[-1]
        
        if len(periods) >= 2:
            # Calculate all cycle lengths in history
            cycles = []
            for i in range(len(periods) - 1):
                cycle_len = (periods[i+1].start_date - periods[i].start_date).days
                cycles.append(cycle_len)
            
            # 1. Check Most Recent Cycle
            last_cycle_len = cycles[-1]
            if last_cycle_len < 21:
                health_alerts.append({
                    'title': 'Short Cycle Detected',
                    'desc': f'Your last cycle was only {last_cycle_len} days. Cycles under 21 days can indicate hormonal imbalance.',
                    'type': 'warning'
                })
            elif last_cycle_len > 35:
                health_alerts.append({
                    'title': 'Long Cycle Detected',
                    'desc': f'Your last cycle was {last_cycle_len} days. Cycles over 35 days may be linked to PCOS or stress.',
                    'type': 'warning'
                })

            # 2. Check Irregularity (Variance)
            if len(cycles) >= 3:
                cycle_variation = max(cycles) - min(cycles)
                if cycle_variation > 9:
                    health_alerts.append({
                        'title': 'Irregular Cycles',
                        'desc': f'Your cycle length varies by {cycle_variation} days. This irregularity might make predictions less accurate.',
                        'type': 'info'
                    })

        # --- AI PREDICTION LOGIC (Linear Regression) ---
        # We need at least 2 periods to calculate a cycle, and preferably 3+ for AI to be useful.
        if len(periods) >= 3:
            # 1. Prepare Data
            # X = Cycle Number (1, 2, 3...), y = Days in that cycle
            X = []
            y = []
            
            for i in range(len(periods) - 1):
                cycle_len = (periods[i+1].start_date - periods[i].start_date).days
                X.append([i + 1]) # Sklearn expects a 2D array for inputs
                y.append(cycle_len)
            
            # 2. Train the Model
            model = LinearRegression()
            model.fit(X, y)
            
            # 3. Predict the NEXT cycle length
            next_cycle_index = len(periods) # The next number in the sequence
            predicted_cycle_length = model.predict([[next_cycle_index]])[0]
            
            # Round it to the nearest whole day
            avg_cycle = int(round(predicted_cycle_length))
            
            # Sanity Check: If AI predicts something crazy (like 5 days or 100 days), fall back to standard
            if avg_cycle < 21 or avg_cycle > 35:
                avg_cycle = 28
                
        elif len(periods) == 2:
            # Fallback to simple math if only 2 logs exist
            avg_cycle = (periods[1].start_date - periods[0].start_date).days
        else:
            # Default standard if new user
            avg_cycle = 28

        # Average Duration (Simple average is fine for duration)
        avg_duration = sum([p.duration for p in periods]) // len(periods)

        # --- END AI LOGIC ---

        # 2. Calculate Next Dates based on AI Result
        next_date = last_period.start_date + timedelta(days=avg_cycle)
        predicted_end = next_date + timedelta(days=avg_duration)
        today = date.today()
        
        # 3. Determine Current Phase
        days_since_start = (today - last_period.start_date).days + 1 
        ovulation_day = avg_cycle - 14 
        
        if days_since_start <= last_period.duration:
            phase_name = 'Menstrual'
        elif days_since_start < (ovulation_day - 2):
            phase_name = 'Follicular'
        elif days_since_start <= (ovulation_day + 2):
            phase_name = 'Ovulation'
        else:
            phase_name = 'Luteal'
            if days_since_start > avg_cycle:
                days_left = f"{days_since_start - avg_cycle} days late"
            else:
                days_left = f"{(next_date - today).days} Days"

        if "late" not in str(days_left):
             days_left = f"{(next_date - today).days} Days"

        # Load Theme Data
        current_phase_data = PHASE_INFO.get(phase_name)
        if current_phase_data:
            current_phase_data['name'] = phase_name

        # Add Prediction to Calendar
        calendar_events.append({
            'title': 'Predicted',
            'start': next_date.isoformat(),
            'end': predicted_end.isoformat(),
            'color': '#fcc2c2',
            'textColor': 'black',
            'display': 'background'
        })
    else:
        
        current_phase_data = PHASE_INFO['Follicular'] 
        current_phase_data['name'] = "Welcome"

    # Added 'alerts=health_alerts' at the end
    return render_template("home.html", user=current_user, events=calendar_events, days_left=days_left, phase=current_phase_data, alerts=health_alerts)

@views.route('/blogs', methods=['GET'])
def blogs():
    # 1. Get Filters from URL (e.g., /blogs?phase=Menstrual&category=Lifestyle)
    phase_filter = request.args.get('phase')
    category_filter = request.args.get('category')

    # 2. Build Query
    # NOTE: Replace 'article' with the actual ID of your Content Model in Contentful
    query = {'content_type': 'article'} 

    if phase_filter and phase_filter != 'All':
        query['fields.phaseTag'] = phase_filter
    
    if category_filter and category_filter != 'All':
        query['fields.category'] = category_filter

    # 3. Fetch Data
    try:
        posts = client.entries(query)
    except Exception as e:
        print(f"Contentful Error: {e}")
        posts = []

    return render_template("blogs.html", user=current_user, posts=posts, 
                           current_phase=phase_filter, current_category=category_filter)

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # A. Identity
        dob_str = request.form.get('dob')
        if dob_str:
            current_user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        # B. Cycle Baseline
        current_user.avg_cycle_length = int(request.form.get('avg_cycle_length') or 28)
        current_user.avg_period_length = int(request.form.get('avg_period_length') or 5)
        current_user.luteal_phase_length = int(request.form.get('luteal_phase_length') or 14)
        
        # C. Mode
        current_user.tracking_mode = request.form.get('tracking_mode')
        
        # D. Health
        current_user.contraception_method = request.form.get('contraception_method')
        
        # Handle Checkboxes for Conditions (getlist returns a list of selected items)
        conditions = request.form.getlist('conditions')
        current_user.health_conditions = ",".join(conditions) 
        
        db.session.commit()
        flash('Profile updated successfully!', category='success')
        
    return render_template("profile.html", user=current_user)

@views.route('/game/<game_type>')
@login_required
def game(game_type):
    # This route handles all game redirections
    if game_type == 'coloring':
        return render_template("games/coloring.html", user=current_user)
    elif game_type == 'sudoku':
        return render_template("games/sudoku.html", user=current_user)
    elif game_type == 'trivia':
        return render_template("games/trivia.html", user=current_user)
    elif game_type == 'tetris':  # Changed from 2048 to tetris
        return render_template("games/tetris.html", user=current_user)
    else:
        flash('Game not found!', category='error')
        return redirect(url_for('views.dashboard'))

@views.route('/recipes', methods=['GET'])
@login_required
def recipes():
    
    target_phase = request.args.get('phase', 'General')

    
    query = {
        'content_type': 'recipe',
        'fields.phaseTag': target_phase
    }

    # 3. Fetch Data
    try:
        recipes_list = client.entries(query)
    except Exception as e:
        print(f"Contentful Error: {e}")
        recipes_list = []

    return render_template("recipes.html", user=current_user, recipes=recipes_list, phase_name=target_phase)

@views.route('/delete-period', methods=['POST'])
@login_required
def delete_period():
    period_data = json.loads(request.data)
    periodId = period_data['periodId']
    period = Period.query.get(periodId)
    
    if period:
        if period.user_id == current_user.id:
            db.session.delete(period)
            db.session.commit()
            flash('Log deleted!', category='success')
            
    return jsonify({})

@views.route('/wellness', methods=['GET'])
@login_required
def wellness():
    # 1. Get the phase from the URL
    target_phase = request.args.get('phase', 'General')
    
    # 2. Get the corresponding Playlist ID (Default to Menstrual if not found)
    playlist_id = PHASE_PLAYLISTS.get(target_phase, 'PLui6Eyny-UzzWwB4Csj_vdOfhxJFEuv9S')

    return render_template("wellness.html", user=current_user, playlist_id=playlist_id, phase_name=target_phase)

@views.route('/daily-log', methods=['GET', 'POST'])
@login_required
def daily_log():
    # Calculate phase for analysis context
    current_phase = get_current_phase_name(current_user.id)

    if request.method == 'POST':
        # 1. Get Form Data (using .getlist for multi-selects)
        physical = request.form.getlist('physical') # Returns list ['Cramps', 'Acne']
        discharge = request.form.get('discharge')
        mood = request.form.getlist('mood')
        digestion = request.form.getlist('digestion')
        flow = request.form.get('flow')
        
        # 2. Save to DB
        new_log = DailyLog(
            date=date.today(),
            user_id=current_user.id,
            physical=",".join(physical),
            discharge=discharge,
            mood=",".join(mood),
            digestion=",".join(digestion),
            flow=flow
        )
        db.session.add(new_log)
        db.session.commit()
        
        
        
        
        if discharge and "Unusual" in discharge:
            flash('⚠️ Medical Alert: Unusual discharge may indicate an infection.', category='error')
        if flow and "Super Heavy" in flow:
            flash('⚠️ Flow Alert: "Super Heavy" flow can indicate Menorrhagia.', category='error')

        
        insight_count = 0
        for symptom in physical:
            if symptom in SYMPTOM_INSIGHTS:
                reason = SYMPTOM_INSIGHTS[symptom].get(current_phase)
                if reason:
                    flash(f'💡 Insight: Your {symptom} is likely due to {reason}', category='info')
                    insight_count += 1
        
        if insight_count == 0:
            flash('Daily log saved successfully!', category='success')

        return redirect(url_for('views.dashboard'))

    return render_template("daily_log.html", user=current_user, phase_name=current_phase)

@views.route('/export-report')
@login_required
def export_report():
    
    periods = Period.query.filter_by(user_id=current_user.id).order_by(Period.start_date).all()
    
    
    if len(periods) < 2:
        flash('Not enough data to generate a report. Please log at least 2 cycles.', category='error')
        return redirect(url_for('views.dashboard'))

    # 2. Setup PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- HEADER ---
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Report")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Name: {current_user.first_name}")
    c.drawString(50, height - 95, f"Date Generated: {date.today().strftime('%Y-%m-%d')}")
    c.drawString(50, height - 110, f"Age/DOB: {current_user.dob if current_user.dob else 'Not Provided'}")

    # --- ANOMALY DETECTION SECTION ---
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 150, "Cycle Anomalies Detected")
    
    y_position = height - 170
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.red)
    
    anomalies_found = False
    
    # Logic (Reused from Home View)
    cycles = []
    for i in range(len(periods) - 1):
        cycle_len = (periods[i+1].start_date - periods[i].start_date).days
        cycles.append(cycle_len)
    
    if cycles:
        last_cycle = cycles[-1]
        if last_cycle < 21:
            c.drawString(70, y_position, f"• Short Cycle Flag: Last cycle was {last_cycle} days (<21).")
            y_position -= 15
            anomalies_found = True
        elif last_cycle > 35:
            c.drawString(70, y_position, f"• Long Cycle Flag: Last cycle was {last_cycle} days (>35).")
            y_position -= 15
            anomalies_found = True
            
        if len(cycles) >= 3:
            variation = max(cycles) - min(cycles)
            if variation > 9:
                c.drawString(70, y_position, f"• Irregularity Flag: Cycle variation is {variation} days.")
                y_position -= 15
                anomalies_found = True

    if not anomalies_found:
        c.setFillColor(colors.green)
        c.drawString(70, y_position, "• No significant cycle anomalies detected in recent history.")
    
    c.setFillColor(colors.black) # Reset color

    # --- PERIOD HISTORY TABLE ---
    y_position -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "Period History (Last 4 Logs)")
    
    y_position -= 25
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_position, "Start Date")
    c.drawString(150, y_position, "Duration")
    c.drawString(250, y_position, "Cycle Length (Days)")
    
    c.setFont("Helvetica", 10)
    y_position -= 5
    c.line(50, y_position, 400, y_position) # Divider line
    y_position -= 15

    # Loop through last 4 periods reversed
    recent_periods = periods[-4:]
    reversed_periods = recent_periods[::-1]
    
    for idx, p in enumerate(reversed_periods):
        # Calculate cycle length for this specific period entry
        # (We look forward in time to find the difference, or N/A for the most recent)
        cycle_val = "N/A"
        # Find index in main list to calculate difference
        original_idx = periods.index(p)
        if original_idx < len(periods) - 1:
            cycle_val = (periods[original_idx+1].start_date - p.start_date).days
        
        c.drawString(50, y_position, p.start_date.strftime('%Y-%m-%d'))
        c.drawString(150, y_position, f"{p.duration} Days")
        c.drawString(250, y_position, str(cycle_val))
        y_position -= 20

    # --- CYCLE PATTERN GRAPH ---
    # Draw Graph only if we have cycle data
    if len(cycles) >= 2:
        plt.figure(figsize=(6, 3))
        plt.plot(range(1, len(cycles) + 1), cycles, marker='o', linestyle='-', color='#ff6b6b')
        plt.title('Cycle Length Consistency')
        plt.xlabel('Cycle Number')
        plt.ylabel('Length (Days)')
        plt.grid(True)
        
        # Save plot to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        # Draw Image on PDF
        c.drawImage(io.BytesIO(img_buffer.read()), 50, y_position - 220, width=400, height=200)
        plt.close()

    # 3. Save & Return
    c.showPage()
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"ForHer_Report_{current_user.first_name}.pdf", mimetype='application/pdf')