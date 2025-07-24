from flask import render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
import os
import traceback
from app import app, db, mail
from flask_mail import Message
from app.models import Lead, User  # Ensure User model is defined
from werkzeug.security import check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from functools import wraps
#from app.utils import login_required
@app.route('/create-admin')
def create_admin():
    username = request.args.get('username', 'admin')
    email = request.args.get('email', 'admin@example.com')
    password = request.args.get('password', 'admin123')

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return f"User '{username}' already exists."

    # Create new user with admin role
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password, role='admin')
    db.session.add(new_user)
    db.session.commit()

    return f"Admin user '{username}' created successfully!"

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            user_role = session.get("role")
            if not user_id:
                flash("You must be logged in to access this page.", "warning")
                return redirect(url_for("login"))
            if role and user_role != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def send_email(to, subject="EduCall Notification", body=""):
    try:
        msg = Message(subject=subject, recipients=[to])
        msg.body = body or "No message was provided."
        mail.send(msg)
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to}: {e}")
        return False
    
@app.route('/ajax-send-lead-email/<int:lead_id>', methods=['POST'])
@login_required(role='agent')
def ajax_send_lead_email(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    message = data.get("message", "").strip()
    admin_note = data.get("note_to_admin", "").strip()  # 🆕

    if not message:
        return jsonify({"success": False, "error": "Message is empty."})

    # Save the note
    if admin_note:
        lead.note_to_admin = admin_note
        db.session.commit()  # 🔥 Save to DB

    # Send email
    success = send_email(
        to=lead.email,
        subject="Message from your EduCall Agent",
        body=message
    )

    return jsonify({"success": success})


@app.route('/global-search')
@login_required(role='admin')
def global_search():
    query = request.args.get('q', '').strip()
    agents, leads, tasks = [], [], []
    if query and len(query) > 1:
        agents = User.query.filter(
            User.role == "agent",
            User.username.ilike(f"%{query}%")
        ).all()
        leads = Lead.query.filter(
            or_(
                Lead.name.ilike(f"%{query}%"),
                Lead.email.ilike(f"%{query}%"),
                Lead.phone.ilike(f"%{query}%"),
                Lead.city.ilike(f"%{query}%"),
                Lead.state.ilike(f"%{query}%"),
                Lead.course.ilike(f"%{query}%"),
                Lead.status.ilike(f"%{query}%")
            )
        ).all()
        # If you add a Task model, search it similarly
        # tasks = Task.query.filter(Task.title.ilike(f"%{query}%")).all()
    return render_template("global_search.html", query=query, agents=agents, leads=leads, tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            # Force all public registrations to agent role only
            role = "agent"

            if password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for("register"))

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists", "danger")
                return redirect(url_for("register"))

            user = User(username=username, role=role)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.session.rollback()
            print("Error in registration:", e)
            flash("Something went wrong. Try again.", "danger")

    return render_template("register.html")

@app.route("/create-user", methods=["GET", "POST"])
def create_user():
    if session.get("role") != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if role not in ["agent", "admin"]:
            flash("Invalid role.", "danger")
            return redirect(url_for("create_user"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for("create_user"))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)

        # Log who created the user
        print(f"User {username} created with role {role} by Admin ID: {session['user_id']}")

        db.session.commit()
        flash("User created successfully.", "success")
        return redirect(url_for("view_agents"))

    return render_template("create_user.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

@app.route("/agents")
def view_agents():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("login"))

    agents = User.query.filter_by(role="agent").all()
    return render_template("agents.html", agents=agents)

@app.route('/assign-leads/<int:agent_id>', methods=['GET', 'POST'])
def assign_leads(agent_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    agent = User.query.get_or_404(agent_id)

    if request.method == 'POST':
        file = request.files.get('lead_file')

        if file:
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext not in ['.csv', '.xls', '.xlsx']:
                flash('Unsupported file format. Please upload CSV or Excel.', 'danger')
                return redirect(request.url)

            try:
                # 🔍 Read the file using pandas
                if file_ext == '.csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file, engine='openpyxl')

                print("DEBUG Columns:", df.columns)

                for _, row in df.iterrows():
                    lead = Lead(
                        name=row['Name'],                # Must match column in Excel/CSV
                        phone=row['Phone'],              # Match case exactly (e.g., 'phone' vs 'Phone')
                        email=row.get('Email'),
                        city=row.get('City'),
                        state=row.get('State'),
                        course=row.get('Course'),
                        #status='Pending',
                        agent_id=agent.id
                    )
                    db.session.add(lead)

                db.session.commit()
                flash(f"{len(df)} leads assigned to {agent.username}.", "success")
                return redirect(url_for('view_agents'))

            except Exception as e:
                traceback.print_exc()  # 🐞 Print full traceback for debugging
                print("Upload error:", e)
                flash('Error processing the file. Please check the format.', 'danger')
                return redirect(request.url)

    return render_template('assign_leads.html', agent=agent)

@app.route('/update-status/<int:lead_id>', methods=['POST'])
def update_lead_status_by_id(lead_id):
    if session.get('role') != 'agent':
        flash("Unauthorized", "danger")
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    lead = Lead.query.get_or_404(lead_id)

    if lead.agent_id != session['user_id']:
        flash("Unauthorized update attempt.", "danger")
        return redirect(url_for('agent_dashboard'))

    lead.status = new_status
    db.session.commit()
    flash("Lead status updated!", "success")
    return redirect(url_for('agent_dashboard'))

@app.route('/update-lead-status', methods=['POST'])
def update_lead_status():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))

    lead_id = request.form.get('lead_id')
    status = request.form.get(f'status_{lead_id}')

    lead = Lead.query.filter_by(id=lead_id, agent_id=session['user_id']).first()
    if lead:
        lead.status = status
        db.session.commit()
        flash("Lead status updated.", "success")
    else:
        flash("Lead not found or access denied.", "danger")

    return redirect(url_for('agent_dashboard'))




@app.route('/upload-leads', methods=['GET', 'POST'])
def upload_leads():
    if request.method == 'POST':
        file = request.files['file']
        agent_id = request.form.get('agent_id')

        if file and file.filename.endswith(('.csv', '.xlsx', '.xls')):
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)

            # 🚀 Ensure uploads directory exists
            upload_dir = os.path.join(app.root_path, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            # (Optional) Save filename in DB, process contents, etc.
            flash("File uploaded successfully!", "success")
            return redirect(url_for('upload_leads'))
        else:
            flash("Invalid file type.", "danger")

    agents = User.query.filter_by(role='agent').all()
    return render_template('upload_leads.html', agents=agents)






@app.route('/agent-dashboard')
def agent_dashboard():
    if session.get('role') != 'agent':
        return redirect(url_for('login'))

    # Fetch leads assigned to the currently logged-in agent
    leads = Lead.query.filter_by(agent_id=session['user_id']).order_by(Lead.created_at.desc()).all()

    return render_template('agent_dashboard.html', leads=leads)





@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("register"))

    if session["role"] == "admin":
        agents = User.query.filter_by(role="agent").all()
        leads_by_agent = {}

        for agent in agents:
            leads = Lead.query.filter_by(agent_id=agent.id).order_by(Lead.created_at.desc()).all()
            summary = {
                "leads": leads,
                "total": len(leads),
                "interested": sum(1 for lead in leads if lead.status == "Interested"),
                "not_interested": sum(1 for lead in leads if lead.status == "Not Interested"),
                "talk_later": sum(1 for lead in leads if lead.status == "Talk to Later"),
            }
            leads_by_agent[agent.username] = summary

        return render_template("admin_dashboard.html", leads_by_agent=leads_by_agent)

    # Agent view
    leads = Lead.query.filter_by(agent_id=session["user_id"]).order_by(Lead.created_at.desc()).all()
    return render_template("dashboard.html", leads=leads)


@app.route("/add-lead", methods=["GET", "POST"])
def add_lead():
    if "user_id" not in session or session["role"] != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login"))

    agents = User.query.filter_by(role="agent").all()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        city = request.form.get("city")
        state = request.form.get("state")
        course = request.form.get("course")
        status = request.form.get("status")
        agent_id = request.form.get("agent_id")

        try:
            new_lead = Lead(
                name=name,
                email=email,
                phone=phone,
                city=city,
                state=state,
                course=course,
                status=status,
                agent_id=int(agent_id) if agent_id else None
            )

            db.session.add(new_lead)
            db.session.commit()
            flash("Lead added successfully!", "success")
            return redirect(url_for("index"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template("add_lead.html", agents=agents)
