from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "exam_anxiety_reducer_secret"


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # STUDENTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            course TEXT,
            year TEXT
        )
    """)

    # QUESTIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    """)

    # TESTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            date TEXT
        )
    """)

    # ANSWERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER,
            question_id INTEGER,
            student_answer TEXT,
            time_taken INTEGER,
            is_correct INTEGER
        )
    """)

    # SAMPLE QUESTIONS
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]

    if count == 0:

        questions = [
            (
                "Python",
                "Loops",
                "Which keyword is used to create a loop in Python?",
                "if",
                "for",
                "def",
                "class",
                "B"
            ),

            (
                "Python",
                "Loops",
                "Which loop is used when the number of iterations is known?",
                "for loop",
                "while loop",
                "do while loop",
                "nested loop",
                "A"
            ),

            (
                "Python",
                "Loops",
                "Which statement is used to stop a loop?",
                "continue",
                "pass",
                "break",
                "return",
                "C"
            ),

            (
                "Python",
                "Functions",
                "Which keyword is used to define a function?",
                "function",
                "def",
                "fun",
                "define",
                "B"
            ),

            (
                "Python",
                "Functions",
                "What keyword is used to send a value back from a function?",
                "send",
                "return",
                "output",
                "break",
                "B"
            )
        ]

        cursor.executemany("""
            INSERT INTO questions
            (
                subject,
                topic,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()
# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        course = request.form["course"]
        year = request.form["year"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO students
                (name, email, password, course, year)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, password, course, year))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered!"

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM students
            WHERE email = ? AND password = ?
        """, (email, password))

        student = cursor.fetchone()

        conn.close()

        if student:

            session["student_id"] = student[0]
            session["student_name"] = student[1]

            return redirect("/dashboard")

        else:

            return "Invalid email or password!"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["student_name"]
    )


# ---------------- PROFILE ----------------

@app.route("/profile")
def profile():

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM students
        WHERE student_id = ?
    """, (session["student_id"],))

    student = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        student=student
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
#------------------Practice Test--------------
@app.route("/practice-test", methods=["GET", "POST"])
def practice_test():

    if "student_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        subject = request.form["subject"]
        topic = request.form["topic"]

        return redirect(
            f"/start-test?subject={subject}&topic={topic}"
        )

    return render_template("practice_test.html")
#------------Start Test Route--------------------  
    
@app.route("/start-test")
def start_test():

    if "student_id" not in session:
        return redirect("/login")

    subject = request.args.get("subject")
    topic = request.args.get("topic")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM questions
        WHERE subject = ? AND topic = ?
    """, (subject, topic))

    questions = cursor.fetchall()

    conn.close()

    return render_template(
        "test.html",
        questions=questions,
        subject=subject,
        topic=topic
    )
#---------------Submit Test Route-----------------
@app.route("/submit-test", methods=["POST"])
def submit_test():

    if "student_id" not in session:
        return redirect("/login")

    subject = request.form["subject"]
    topic = request.form["topic"]

    question_ids = request.form.getlist("question_id")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    score = 0

    results = []

    for qid in question_ids:

        answer = request.form.get("answer_" + qid)

        time_taken = request.form.get(
            "time_" + qid,
            0
        )

        cursor.execute("""
            SELECT correct_answer
            FROM questions
            WHERE question_id = ?
        """, (qid,))

        correct = cursor.fetchone()[0]

        is_correct = 1 if answer == correct else 0

        if is_correct:
            score += 1

        results.append({
            "question_id": qid,
            "answer": answer,
            "correct": correct,
            "time": time_taken,
            "is_correct": is_correct
        })

    cursor.execute("""
        INSERT INTO tests
        (student_id, subject, topic,
         score, total_questions, date)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (
        session["student_id"],
        subject,
        topic,
        score,
        len(question_ids)
    ))

    test_id = cursor.lastrowid

    for result in results:

        cursor.execute("""
            INSERT INTO answers
            (test_id, question_id,
             student_answer, time_taken,
             is_correct)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_id,
            result["question_id"],
            result["answer"],
            result["time"],
            result["is_correct"]
        ))

    conn.commit()
    conn.close()

    return redirect(f"/analysis/{test_id}")
#-------Analysis---------------
@app.route("/analysis/<int:test_id>")
def analysis(test_id):

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get test information
    cursor.execute("""
        SELECT test_id, subject, topic, score, total_questions, date
        FROM tests
        WHERE test_id = ? AND student_id = ?
    """, (test_id, session["student_id"]))

    test = cursor.fetchone()

    if not test:
        conn.close()
        return "Test not found!"

    # Get answer details
    cursor.execute("""
        SELECT
            a.question_id,
            a.student_answer,
            a.time_taken,
            a.is_correct,
            q.correct_answer,
            q.topic
        FROM answers a
        JOIN questions q
        ON a.question_id = q.question_id
        WHERE a.test_id = ?
    """, (test_id,))

    answers = cursor.fetchall()

    conn.close()
    

    # ---------------- ANALYSIS ----------------

    score = test[3]
    total = test[4]

    percentage = (score / total * 100) if total > 0 else 0

    wrong_answers = sum(
        1 for answer in answers
        if answer[3] == 0
    )

    correct_answers = sum(
        1 for answer in answers
        if answer[3] == 1
    )

    total_time = sum(
        int(answer[2] or 0)
        for answer in answers
    )

    average_time = (
        total_time / len(answers)
        if answers else 0
    )

    # Count mistakes by topic
    topic_mistakes = {}

    for answer in answers:

        topic = answer[5]

        if answer[3] == 0:

            topic_mistakes[topic] = (
                topic_mistakes.get(topic, 0) + 1
            )

    # Find topic with maximum mistakes
    weak_topic = None

    if topic_mistakes:

        weak_topic = max(
            topic_mistakes,
            key=topic_mistakes.get
        )
        
        
        

    # ---------------- REASON DETECTION ----------------

    if wrong_answers == 0:

        reason = "Excellent Performance"

        message = (
            "You answered all questions correctly. "
            "Keep practicing to maintain your performance."
        )

    elif weak_topic and topic_mistakes[weak_topic] >= 2:

        reason = "Possible Conceptual Gap"

        message = (
            f"You made repeated mistakes in {weak_topic}. "
            "Revise the topic and practice similar questions."
        )

    elif average_time > 60 and wrong_answers > 0:

        reason = "Possible Time Pressure"

        message = (
            "Your average response time is high and "
            "you made some mistakes. Practice timed questions "
            "to improve your speed."
        )

    elif average_time > 45:

        reason = "Time Management Needs Improvement"

        message = (
            "You are spending considerable time on questions. "
            "Try improving your time-management strategy."
        )

    else:

        reason = "Normal Mistakes"

        message = (
            "Your mistakes do not show a strong repeated pattern. "
            "Continue practicing and reviewing incorrect answers."
        )

    return render_template(
        "analysis.html",
        test=test,
        answers=answers,
        percentage=round(percentage, 1),
        correct_answers=correct_answers,
        wrong_answers=wrong_answers,
        average_time=round(average_time, 1),
        weak_topic=weak_topic,
        reason=reason,
        message=message
    )    


@app.route("/recommendations/<int:test_id>")
def recommendations(test_id):

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get test details
    cursor.execute("""
        SELECT test_id, subject, topic, score, total_questions
        FROM tests
        WHERE test_id = ? AND student_id = ?
    """, (test_id, session["student_id"]))

    test = cursor.fetchone()

    if not test:
        conn.close()
        return "Test not found!"

    # Get answers
    cursor.execute("""
        SELECT
            a.question_id,
            a.student_answer,
            a.time_taken,
            a.is_correct,
            q.correct_answer,
            q.topic
        FROM answers a
        JOIN questions q
        ON a.question_id = q.question_id
        WHERE a.test_id = ?
    """, (test_id,))

    answers = cursor.fetchall()

    conn.close()

    # ---------------- ANALYSIS ----------------

    wrong_answers = 0
    total_time = 0
    topic_mistakes = {}

    for answer in answers:

        time_taken = int(answer[2] or 0)

        total_time += time_taken

        if answer[3] == 0:

            wrong_answers += 1

            topic = answer[5]

            topic_mistakes[topic] = (
                topic_mistakes.get(topic, 0) + 1
            )

    average_time = (
        total_time / len(answers)
        if answers else 0
    )

    # Find weak topic
    weak_topic = None

    if topic_mistakes:

        weak_topic = max(
            topic_mistakes,
            key=topic_mistakes.get
        )

    # ---------------- RECOMMENDATION ----------------

    if (
        weak_topic
        and topic_mistakes[weak_topic] >= 2
    ):

        reason = "Conceptual Gap"

        recommendations = [
            f"Revise the topic: {weak_topic}",
            "Review the basic concepts again",
            "Practice similar questions",
            "Take another test after revision"
        ]

    elif average_time > 60 and wrong_answers > 0:

        reason = "Time Pressure"

        recommendations = [
            "Practice timed questions",
            "Improve your question-solving speed",
            "Avoid spending too much time on one question",
            "Practice mock tests with a timer"
        ]

    elif average_time > 45:

        reason = "Time Management"

        recommendations = [
            "Practice questions within a fixed time",
            "Read questions carefully before answering",
            "Move to the next question if one is taking too long",
            "Practice speed and accuracy together"
        ]

    else:

        reason = "General Improvement"

        recommendations = [
            "Continue regular practice",
            "Review incorrect answers",
            "Practice different types of questions",
            "Take regular mock tests"
        ]

    return render_template(
        "recommendations.html",
        test=test,
        reason=reason,
        recommendations=recommendations,
        weak_topic=weak_topic
    )
    
@app.route("/progress")
def progress():

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get all tests of logged-in student
    cursor.execute("""
        SELECT
            test_id,
            subject,
            topic,
            score,
            total_questions,
            date
        FROM tests
        WHERE student_id = ?
        ORDER BY test_id ASC
    """, (session["student_id"],))

    tests = cursor.fetchall()

    # ---------------- OVERALL STATISTICS ----------------

    total_tests = len(tests)

    total_score = 0
    total_questions = 0

    for test in tests:
        total_score += test[3]
        total_questions += test[4]

    if total_questions > 0:
        overall_percentage = (
            total_score / total_questions
        ) * 100
    else:
        overall_percentage = 0

    # ---------------- TOPIC PERFORMANCE ----------------

    cursor.execute("""
        SELECT
            q.topic,
            COUNT(a.answer_id),
            SUM(a.is_correct)
        FROM answers a
        JOIN questions q
        ON a.question_id = q.question_id
        JOIN tests t
        ON a.test_id = t.test_id
        WHERE t.student_id = ?
        GROUP BY q.topic
    """, (session["student_id"],))

    topic_data = cursor.fetchall()

    topic_performance = []

    for topic in topic_data:

        topic_name = topic[0]
        total = topic[1]
        correct = topic[2] or 0

        percentage = (
            correct / total * 100
            if total > 0 else 0
        )

        topic_performance.append({
            "topic": topic_name,
            "total": total,
            "correct": correct,
            "percentage": round(percentage, 1)
        })

    # ---------------- AVERAGE TIME ----------------

    cursor.execute("""
        SELECT AVG(a.time_taken)
        FROM answers a
        JOIN tests t
        ON a.test_id = t.test_id
        WHERE t.student_id = ?
    """, (session["student_id"],))

    average_time = cursor.fetchone()[0]

    if average_time is None:
        average_time = 0

    # ---------------- TOTAL MISTAKES ----------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM answers a
        JOIN tests t
        ON a.test_id = t.test_id
        WHERE t.student_id = ?
        AND a.is_correct = 0
    """, (session["student_id"],))

    total_mistakes = cursor.fetchone()[0]

    conn.close()

    # ---------------- FEEDBACK ----------------

    if overall_percentage >= 80:

        feedback = (
            "Your overall performance is strong. "
            "Continue regular practice and maintain "
            "your preparation."
        )

    elif overall_percentage >= 60:

        feedback = (
            "Your performance is improving. "
            "Focus on weak topics and practice regularly."
        )

    elif total_tests == 0:

        feedback = (
            "Take your first practice test to "
            "start tracking your progress."
        )

    else:

        feedback = (
            "More practice is recommended. "
            "Review your mistakes and strengthen "
            "your basic concepts."
        )

    return render_template(
        "progress.html",
        tests=tests,
        total_tests=total_tests,
        overall_percentage=round(overall_percentage, 1),
        average_time=round(average_time, 1),
        total_mistakes=total_mistakes,
        topic_performance=topic_performance,
        feedback=feedback
    )

@app.route("/analysis-history")
def analysis_history():

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT test_id, subject, topic, score,
               total_questions, date
        FROM tests
        WHERE student_id = ?
        ORDER BY test_id DESC
    """, (session["student_id"],))

    tests = cursor.fetchall()
    conn.close()

    return render_template(
        "analysis_history.html",
        tests=tests
    )

@app.route("/recommendation-history")
def recommendation_history():

    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT test_id, subject, topic, score,
               total_questions, date
        FROM tests
        WHERE student_id = ?
        ORDER BY test_id DESC
    """, (session["student_id"],))

    tests = cursor.fetchall()
    conn.close()

    return render_template(
        "recommendation_history.html",
        tests=tests
    )    
# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    #init_db()

    app.run(debug=True)
