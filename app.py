import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, WorkoutCompletion
from config import Config



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    AUTO_ACTIVE_EMAILS = {
        "imoren9462@gmail.com",
        "admin@campusfit.com",
    }

    def login_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            return view_func(*args, **kwargs)
        return wrapper

    def get_today_plan_info(plan):
        weekday_index = datetime.today().weekday()
        weekday_names = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        day_number = weekday_index + 1
        weekday_name = weekday_names[weekday_index]

        if day_number <= len(plan["days"]):
            today_entry = plan["days"][day_number - 1]
            workout_title = today_entry["title"]
            is_rest_day = "rest" in workout_title.lower()
        else:
            workout_title = f"Day {day_number} – Rest Day"
            is_rest_day = True

        return {
            "weekday_name": weekday_name,
            "day_number": day_number,
            "workout_title": workout_title,
            "is_rest_day": is_rest_day,
        }

    def get_today_workout_detail(plan):
        weekday_index = datetime.today().weekday()
        weekday_names = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        day_number = weekday_index + 1
        weekday_name = weekday_names[weekday_index]

        if day_number <= len(plan["days"]):
            today_entry = plan["days"][day_number - 1]
            workout_title = today_entry["title"]
            exercises = today_entry["items"]
            is_rest_day = "rest" in workout_title.lower()
        else:
            workout_title = f"Day {day_number} – Rest Day"
            exercises = []
            is_rest_day = True

        return {
            "weekday_name": weekday_name,
            "day_number": day_number,
            "workout_title": workout_title,
            "exercises": exercises,
            "is_rest_day": is_rest_day,
        }

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return redirect(url_for("register"))

            if User.query.filter_by(email=email).first():
                flash("That email is already registered. Please log in.", "warning")
                return redirect(url_for("login"))

            user = User(email=email, name=name or None)
            user.set_password(password)

            if email in AUTO_ACTIVE_EMAILS:
                user.subscription_active = True

            if email == "admin@campusfit.com":
                user.is_admin = True

            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id

            if user.subscription_active:
                flash("Account created successfully. Your subscription is active.", "success")
                return redirect(url_for("dashboard"))

            flash("Account created successfully. Please activate your subscription.", "success")
            return redirect(url_for("subscription"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                flash("Invalid email or password.", "danger")
                return redirect(url_for("login"))

            session["user_id"] = user.id
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        user = User.query.get(session["user_id"])

        selected_plan = None
        today_plan_info = None

        if user.selected_plan_slug:
            selected_plan = PLANS.get(user.selected_plan_slug)
            if selected_plan:
                today_plan_info = get_today_plan_info(selected_plan)

        return render_template(
            "dashboard.html",
            user=user,
            selected_plan=selected_plan,
            today_plan_info=today_plan_info,
        )

    @app.get("/plans")
    @login_required
    def plans():
        return render_template("plans.html")

    PLANS = {
        "muscle-builder": {
            "title": "Muscle Builder",
            "subtitle": "A 5-day split focused on building muscle, improving strength, and maintaining conditioning.",
            "goal": "Build muscle, improve strength, and maintain conditioning",
            "difficulty": "Intermediate",
            "description": "This plan is ideal for users who want a structured split with a strong muscle-building focus while still keeping some conditioning work in the week.",
            "guidance_title": "Weight Guidance",
            "guidance": "Choose a weight that is challenging but controlled. The last 1–2 reps should feel difficult while maintaining proper form. If you can easily exceed the rep range, increase the weight next session.",
            "weekly_structure": [
                "Day 1 → Back & Biceps + Abs",
                "Day 2 → Chest & Triceps + Cardio",
                "Day 3 → Legs",
                "Day 4 → Shoulders (Push Focus) + Abs",
                "Day 5 → Back (Pull Focus) + Cardio",
                "Day 6 → Rest",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Back & Biceps + Abs",
                    "items": [
                        "Lat Pulldown – 3x10",
                        "Seated Row – 3x10",
                        "Dumbbell Rows – 3x10 each arm",
                        "Barbell or Dumbbell Curl – 3x12",
                        "Hammer Curl – 3x12",
                        "Plank – 3x30–60 sec",
                        "Hanging Leg Raises – 3x10",
                    ],
                },
                {
                    "title": "Day 2 – Chest & Triceps + Cardio",
                    "items": [
                        "Bench Press – 3x8–10",
                        "Incline Dumbbell Press – 3x10",
                        "Chest Fly – 3x12",
                        "Tricep Pushdown – 3x12",
                        "Overhead Tricep Extension – 3x12",
                        "15–20 min treadmill or stairmaster (moderate pace)",
                    ],
                },
                {
                    "title": "Day 3 – Legs",
                    "items": [
                        "Squats – 3x8–10",
                        "Leg Press – 3x10",
                        "Hamstring Curl – 3x12",
                        "Leg Extension – 3x12",
                        "Calf Raises – 3x15",
                    ],
                },
                {
                    "title": "Day 4 – Shoulders (Push Focus) + Abs",
                    "items": [
                        "Shoulder Press – 3x8–10",
                        "Lateral Raises – 3x12",
                        "Front Raises – 3x12",
                        "Rear Delt Fly – 3x12",
                        "Shrugs – 3x12",
                        "Crunches – 3x15",
                        "Bicycle Kicks – 3x20",
                    ],
                },
                {
                    "title": "Day 5 – Back (Pull Focus) + Cardio",
                    "items": [
                        "Pull-Ups or Assisted Pull-Ups – 3x8",
                        "Cable Row – 3x10",
                        "Face Pulls – 3x12",
                        "Bicep Curl Variation – 3x12",
                        "15–20 min light jog or incline walk",
                    ],
                },
            ],
        },
        "fat-loss-conditioning": {
            "title": "Fat Loss & Conditioning",
            "subtitle": "A faster-paced plan designed to burn fat, improve endurance, and maintain muscle.",
            "goal": "Burn fat, improve endurance, maintain muscle",
            "difficulty": "Beginner–Intermediate",
            "description": "This plan is designed to maximize calorie burn while maintaining muscle. For best results, combine with proper nutrition and consistency.",
            "guidance_title": "Weight Guidance",
            "guidance": "Use a weight that feels challenging but allows you to keep moving. You should feel fatigued, but still able to complete all sets with good form. Rest time should be short (30–60 seconds).",
            "weekly_structure": [
                "Day 1 → Full Body Circuit",
                "Day 2 → Cardio + Core",
                "Day 3 → Upper Body Burn",
                "Day 4 → Lower Body + Cardio",
                "Day 5 → HIIT + Core",
                "Day 6 → Rest",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Full Body Circuit",
                    "items": [
                        "Perform as a circuit – repeat 3 rounds",
                        "Squats – 12 reps",
                        "Push-Ups – 10–15 reps",
                        "Dumbbell Rows – 12 reps",
                        "Lunges – 10 each leg",
                        "Shoulder Press – 12 reps",
                        "Rest 60 sec between rounds",
                    ],
                },
                {
                    "title": "Day 2 – Cardio + Core",
                    "items": [
                        "25–30 min jogging, incline walk, or bike",
                        "Plank – 3x30–60 sec",
                        "Crunches – 3x15",
                        "Leg Raises – 3x12",
                    ],
                },
                {
                    "title": "Day 3 – Upper Body Burn",
                    "items": [
                        "Bench Press or Push-Ups – 3x12",
                        "Lat Pulldown – 3x12",
                        "Shoulder Press – 3x12",
                        "Bicep Curls – 3x12",
                        "Tricep Pushdown – 3x12",
                        "Keep rest short (30–45 sec)",
                    ],
                },
                {
                    "title": "Day 4 – Lower Body + Cardio",
                    "items": [
                        "Squats – 3x12",
                        "Leg Press – 3x12",
                        "Hamstring Curl – 3x12",
                        "Calf Raises – 3x15",
                        "15–20 min incline walk or stairmaster",
                    ],
                },
                {
                    "title": "Day 5 – HIIT + Core",
                    "items": [
                        "20 min HIIT: 30 sec sprint, 60 sec walk (10 rounds)",
                        "Bicycle Kicks – 3x20",
                        "Plank – 3x45 sec",
                    ],
                },
            ],
        },
        "beginner-full-body": {
            "title": "Beginner Full Body",
            "subtitle": "A beginner-friendly plan focused on basic movements, consistency, and overall fitness.",
            "goal": "Learn basic movements, build consistency, and improve overall fitness",
            "difficulty": "Beginner",
            "description": "Focus on learning proper form before increasing weight. Consistency is more important than intensity, and rest days should be taken seriously.",
            "guidance_title": "Weight Guidance",
            "guidance": "Start with light weights to learn proper form. The last few reps should feel slightly challenging, but never painful. Focus on control and technique over heavy weight.",
            "weekly_structure": [
                "Day 1 → Full Body",
                "Day 2 → Active Recovery",
                "Day 3 → Full Body",
                "Day 4 → Active Recovery",
                "Day 5 → Full Body",
                "Day 6 → Rest",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Full Body",
                    "items": [
                        "Squats (Bodyweight or Light Weight) – 3x10",
                        "Push-Ups (or Knee Push-Ups) – 3x8–10",
                        "Dumbbell Rows – 3x10",
                        "Shoulder Press (Light) – 3x10",
                        "Plank – 3x20–30 sec",
                    ],
                },
                {
                    "title": "Day 2 – Active Recovery",
                    "items": [
                        "15–20 minutes walking, light cycling, or easy treadmill",
                        "Keep the pace light to support recovery and consistency.",
                    ],
                },
                {
                    "title": "Day 3 – Full Body",
                    "items": [
                        "Leg Press or Squats – 3x10",
                        "Dumbbell Chest Press – 3x10",
                        "Lat Pulldown – 3x10",
                        "Dumbbell Curls – 3x12",
                        "Crunches – 3x12",
                    ],
                },
                {
                    "title": "Day 4 – Active Recovery",
                    "items": [
                        "15–20 minutes walking, light cycling, or easy treadmill",
                        "Focus on moving and staying consistent without overexerting.",
                    ],
                },
                {
                    "title": "Day 5 – Full Body",
                    "items": [
                        "Lunges – 3x8 each leg",
                        "Incline Push-Ups or Bench Press – 3x10",
                        "Seated Row – 3x10",
                        "Tricep Pushdown – 3x12",
                        "Plank – 3x20–30 sec",
                    ],
                },
            ],
        },
        "home-workout": {
            "title": "Home Workout",
            "subtitle": "A no-gym plan built to improve fitness and strength using mostly bodyweight movements.",
            "goal": "Build strength, improve fitness, and stay active without a gym",
            "difficulty": "Beginner–Intermediate",
            "description": "No equipment? No problem. This plan is designed to be done anywhere using just your body weight.",
            "guidance_title": "Intensity Guidance",
            "guidance": "Focus on controlled movements and proper form. Choose a pace that challenges you while still allowing you to complete all reps. If it feels too easy, slow the movement or add more reps.",
            "weekly_structure": [
                "Day 1 → Full Body + Cardio",
                "Day 2 → Lower Body + Core",
                "Day 3 → Active Recovery",
                "Day 4 → Upper Body + Cardio",
                "Day 5 → Full Body Circuit",
                "Day 6 → Active Recovery",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Full Body + Cardio",
                    "items": [
                        "Bodyweight Squats – 3x12",
                        "Push-Ups – 3x8–12",
                        "Glute Bridges – 3x12",
                        "Plank – 3x30 sec",
                        "Jumping Jacks – 3x20",
                        "15–20 min jogging, jump rope, or brisk walking",
                    ],
                },
                {
                    "title": "Day 2 – Lower Body + Core",
                    "items": [
                        "Lunges – 3x10 each leg",
                        "Wall Sit – 3x30 sec",
                        "Step-Ups – 3x10 each leg",
                        "Leg Raises – 3x12",
                        "Bicycle Kicks – 3x20",
                    ],
                },
                {
                    "title": "Day 3 – Active Recovery",
                    "items": [
                        "15–20 min walking, light jogging, or stretching",
                    ],
                },
                {
                    "title": "Day 4 – Upper Body + Cardio",
                    "items": [
                        "Push-Ups – 3x8–12",
                        "Chair Dips – 3x10",
                        "Pike Push-Ups – 3x8",
                        "Plank Shoulder Taps – 3x20",
                        "15–20 min jump rope, jogging, or cycling",
                    ],
                },
                {
                    "title": "Day 5 – Full Body Circuit",
                    "items": [
                        "Repeat 3 rounds",
                        "Squats – 12 reps",
                        "Push-Ups – 10 reps",
                        "Lunges – 10 each leg",
                        "Plank – 30 sec",
                        "Jumping Jacks – 20 reps",
                        "Rest 60 sec between rounds",
                    ],
                },
                {
                    "title": "Day 6 – Active Recovery",
                    "items": [
                        "15–20 min walking, light cycling, or stretching",
                    ],
                },
                {
                    "title": "Day 7 – Rest",
                    "items": ["Rest day"],
                },
            ],
        },
        "strength-power": {
            "title": "Strength / Power",
            "subtitle": "A heavier, lower-rep plan focused on building strength and power in major lifts.",
            "goal": "Increase overall strength and power in major lifts",
            "difficulty": "Intermediate–Advanced",
            "description": "This plan focuses on building strength through heavier weights and lower reps. Progress gradually and prioritize proper form over heavier weight.",
            "guidance_title": "Weight Guidance",
            "guidance": "Use heavier weights with longer rest times (1.5–3 minutes). The final reps should be very challenging, with only 1–2 reps left in reserve. Focus on form and controlled movement—do not rush.",
            "weekly_structure": [
                "Day 1 → Upper Body Strength + Optional Cardio",
                "Day 2 → Lower Body Strength",
                "Day 3 → Rest / Light Activity",
                "Day 4 → Push (Power Focus)",
                "Day 5 → Pull (Power Focus) + Optional Cardio",
                "Day 6 → Rest",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Upper Body Strength + Optional Cardio",
                    "items": [
                        "Bench Press – 4x5",
                        "Barbell Row – 4x5",
                        "Overhead Press – 3x6",
                        "Pull-Ups or Lat Pulldown – 3x6",
                        "Optional cardio: 10–15 min walking or light cycling",
                    ],
                },
                {
                    "title": "Day 2 – Lower Body Strength",
                    "items": [
                        "Squats – 4x5",
                        "Deadlift – 3x5",
                        "Leg Press – 3x6",
                        "Calf Raises – 3x12",
                    ],
                },
                {
                    "title": "Day 3 – Rest / Light Activity",
                    "items": [
                        "Walking",
                        "Stretching",
                    ],
                },
                {
                    "title": "Day 4 – Push (Power Focus)",
                    "items": [
                        "Bench Press – 3x4–6",
                        "Incline Dumbbell Press – 3x6",
                        "Shoulder Press – 3x6",
                        "Tricep Dips – 3x8",
                    ],
                },
                {
                    "title": "Day 5 – Pull (Power Focus) + Optional Cardio",
                    "items": [
                        "Deadlift or Rack Pull – 3x4–6",
                        "Barbell Row – 3x6",
                        "Face Pulls – 3x10",
                        "Bicep Curls – 3x8",
                        "Optional cardio: 10–15 min walking or light incline treadmill",
                    ],
                },
            ],
        },
        "athletic-performance": {
            "title": "Athletic Performance",
            "subtitle": "A hybrid plan combining strength, endurance, conditioning, and explosive training.",
            "goal": "Improve endurance, speed, strength, and overall athletic performance",
            "difficulty": "Intermediate–Advanced",
            "description": "This plan is designed to improve overall athletic performance by combining strength, endurance, and conditioning. It is more intense than traditional workout plans and is best suited for users with prior experience.",
            "guidance_title": "Intensity Guidance",
            "guidance": "This plan combines strength, conditioning, and explosive movements. Work at a challenging pace, but maintain proper form. Rest 30–90 seconds depending on intensity.",
            "weekly_structure": [
                "Day 1 → Lower Body Power + Conditioning",
                "Day 2 → Upper Body Strength + Cardio",
                "Day 3 → Conditioning (HIIT) + Core",
                "Day 4 → Full Body Athletic Training",
                "Day 5 → Endurance + Core",
                "Day 6 → Rest",
                "Day 7 → Rest",
            ],
            "days": [
                {
                    "title": "Day 1 – Lower Body Power + Conditioning",
                    "items": [
                        "Squats – 4x6",
                        "Jump Squats – 3x8",
                        "Walking Lunges – 3x10 each leg",
                        "Box Jumps or Step Jumps – 3x8",
                        "Conditioning finisher: 3 rounds of 30 sec sprint / 60 sec walk",
                    ],
                },
                {
                    "title": "Day 2 – Upper Body Strength + Cardio",
                    "items": [
                        "Bench Press – 3x8",
                        "Pull-Ups or Lat Pulldown – 3x8",
                        "Shoulder Press – 3x10",
                        "Push-Ups – 3x12",
                        "20 min jogging or incline walk",
                    ],
                },
                {
                    "title": "Day 3 – HIIT + Core",
                    "items": [
                        "HIIT (20 minutes): 30 sec high effort / 60 sec rest",
                        "Plank – 3x45 sec",
                        "Hanging Leg Raises – 3x12",
                        "Bicycle Kicks – 3x20",
                    ],
                },
                {
                    "title": "Day 4 – Full Body Athletic Training",
                    "items": [
                        "Deadlift – 3x6",
                        "Kettlebell Swings or Dumbbell Swings – 3x12",
                        "Burpees – 3x10",
                        "Dumbbell Rows – 3x10",
                        "Farmer’s Carry – 3 rounds (30 sec)",
                    ],
                },
                {
                    "title": "Day 5 – Endurance + Core",
                    "items": [
                        "25–30 min running, cycling, or stairmaster",
                        "Crunches – 3x15",
                        "Plank – 3x45 sec",
                    ],
                },
            ],
        },
    }

    @app.get("/plan/<slug>")
    @login_required
    def plan_overview(slug):
        plan = PLANS.get(slug)
        if not plan:
            flash("That plan was not found.", "warning")
            return redirect(url_for("plans"))
        return render_template("plan_overview.html", plan=plan, slug=slug)

    @app.post("/choose-plan/<slug>")
    @login_required
    def choose_plan(slug):
        user = User.query.get(session["user_id"])
        plan = PLANS.get(slug)

        if not plan:
            flash("That plan was not found.", "warning")
            return redirect(url_for("plans"))

        user.selected_plan_slug = slug
        db.session.commit()

        flash(f"{plan['title']} has been selected as your current plan.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/workout-details")
    @login_required
    def workout_details():
        user = User.query.get(session["user_id"])

        if not user.selected_plan_slug:
            flash("Please choose a plan first.", "warning")
            return redirect(url_for("plans"))

        selected_plan = PLANS.get(user.selected_plan_slug)
        if not selected_plan:
            flash("Selected plan could not be found.", "warning")
            return redirect(url_for("plans"))

        today_workout = get_today_workout_detail(selected_plan)
        today_date = date.today().isoformat()

        saved_completions = WorkoutCompletion.query.filter_by(
            user_id=user.id,
            plan_slug=user.selected_plan_slug,
            workout_date=today_date,
            day_number=today_workout["day_number"],
            completed=True,
        ).all()

        completed_exercises = [
            item.exercise_name for item in saved_completions
        ]

        return render_template(
            "workout_detail.html",
            user=user,
            selected_plan=selected_plan,
            today_workout=today_workout,
            completed_exercises=completed_exercises,
        )

    @app.post("/toggle-exercise")
    @login_required
    def toggle_exercise():
        user = User.query.get(session["user_id"])

        exercise_name = request.form.get("exercise_name")
        completed_value = request.form.get("completed")
        day_number = request.form.get("day_number")

        if not user.selected_plan_slug or not exercise_name or day_number is None:
            return {"success": False, "error": "Missing data"}, 400

        today_date = date.today().isoformat()
        is_completed = completed_value == "true"

        existing = WorkoutCompletion.query.filter_by(
            user_id=user.id,
            plan_slug=user.selected_plan_slug,
            workout_date=today_date,
            day_number=int(day_number),
            exercise_name=exercise_name,
        ).first()

        if existing:
            existing.completed = is_completed
        else:
            existing = WorkoutCompletion(
                user_id=user.id,
                plan_slug=user.selected_plan_slug,
                workout_date=today_date,
                day_number=int(day_number),
                exercise_name=exercise_name,
                completed=is_completed,
            )
            db.session.add(existing)

        db.session.commit()

        return {"success": True}

    @app.route("/subscription", methods=["GET", "POST"])
    @login_required
    def subscription():
        user = User.query.get(session["user_id"])

        if request.method == "POST":
            user.subscription_active = True
            db.session.commit()
            flash("Subscription activated successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("subscription.html", user=user)
    
    @app.get("/management")
    def management():
        return render_template("management.html")

    @app.get("/services")
    def services():
        return render_template("services.html")

    @app.get("/faq")
    def faq():
        return render_template("faq.html")

    @app.get("/contact")
    def contact():
        return render_template("contact.html")

    @app.get("/policy")
    def policy():
        return render_template("policy.html")

    @app.route("/feedback", methods=["GET", "POST"])
    def feedback():
        if request.method == "POST":
            flash("Thank you for your feedback!", "success")
            return redirect(url_for("feedback"))
        return render_template("feedback.html")

    @app.get("/resources")
    def resources():
        return render_template("resources.html")


    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)