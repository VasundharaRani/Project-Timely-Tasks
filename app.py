import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.route("/register",methods=["GET","POST"])
def register():
    #User reached via post
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        hashed_password = generate_password_hash(password)

        # Ensure username is submitted
        if not username:
            return apology("Username MUST be provided", 400)
        # Ensure password is submitted
        elif not password:
            return apology("Password MUST be provided", 400)
        # Ensure confirmation is submitted
        elif not confirmation:
            return apology("MUST confirm the password", 400)
        # Ensure password and confirmation match
        elif password != confirmation:
            return apology("Passwords donot match", 400)
        try:
            rows = db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                              username, hashed_password)
        except:
            return apology("Username already exists")
        # Remember which user has registered
        session["user_id"] = rows

        return redirect("/login")

    # User reached the route via GET
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Debug prints
        print("Rows:", rows)
        print("Password hash:", rows[0]["password"] if rows else "No user found")

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
@login_required
def index():
    if request.method == "POST":
        # Handle form submission
        return redirect("/")
    return render_template("index.html")

@app.route("/tasks/professional", methods=["GET", "POST"])
def view_professional_tasks():
    user_id = session["user_id"]
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND category = ? ORDER BY due_date ASC", user_id,"professional")  # Sort by due date
    for index, task in enumerate(tasks, start=1):
        task["serial_number"] = index
    return render_template("professional.html", tasks=tasks)

@app.route("/tasks/personal", methods=["GET", "POST"])
def view_personal_tasks():
    user_id = session["user_id"]
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND category = ? ORDER BY due_date ASC", user_id, "personal")  # Sort by due date
    for index, task in enumerate(tasks, start=1):
        task["serial_number"] = index
    return render_template("personal.html", tasks=tasks)

@app.route("/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")
        category = request.form.get("category")

        user_id = session["user_id"]

        # Add tasks to the database
        db.execute("INSERT INTO tasks (user_id, title, description, due_date, priority, category) VALUES (?,?,?,?,?,?)",
                                user_id, title, description, due_date, priority, category)
        # rows = db.execute("SELECT * FROM tasks WHERE title = ?",title)
        # session["task_id"] = rows[0]["id"]

        flash("Task is added!")
        if category == "professional":
            return redirect("/tasks/professional?updated=true")
        else:
            return redirect("/tasks/personal?updated=true")
    else:
        return render_template("tasks.html")

@app.route("/tasks")
@login_required
def tasks():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC", session["user_id"])
    return render_template("tasks.html", tasks=tasks)

@app.route("/update/<int:task_id>",methods=["GET","POST"])
@login_required
def update_task(task_id):
    if request.method == "POST":
        print("Update form submitted")
        status = request.form.get("status")
        priority = request.form.get("priority")
        # Update status or priority
        if status:
            db.execute("UPDATE tasks SET status = ? WHERE id = ?", status, task_id)
        if priority:
            db.execute("UPDATE tasks SET priority = ? WHERE id = ?", priority, task_id)

        category = db.execute("SELECT category FROM tasks WHERE id =?", task_id)[0]["category"]
        if category == "professional":
            return redirect("/tasks/professional")
        else:
            return redirect("/tasks/personal")
    else:
        task = db.execute("SELECT * FROM tasks WHERE id = ?",task_id)
        if not task:
            return apology("Task not found")
        return render_template("update.html", task=task[0])

@app.route("/delete/<int:task_id>")
@login_required
def delete_task(task_id):
    task = db.execute("SELECT category FROM tasks WHERE id = ?", task_id)
    if not task:
        return apology("Task not found")
    category = task[0]["category"]
    db.execute("DELETE FROM tasks WHERE id = ?", task_id)
    flash("Task is deleted!")
    if category == "professional":
        return redirect("/tasks/professional")
    else:
        return redirect("/tasks/personal")
