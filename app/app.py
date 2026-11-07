import os
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)

# The database path can be overridden with an environment variable.
# On the server we will point it at a folder outside the code directory.
DATABASE = os.environ.get(
    "TODO_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.db")
)


def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


init_db()


@app.get("/")
def index():
    tasks = get_db().execute(
        "SELECT id, title, done FROM tasks ORDER BY done, id DESC"
    ).fetchall()
    return render_template("index.html", tasks=tasks)


@app.post("/add")
def add():
    title = request.form.get("title", "").strip()
    if title:
        db = get_db()
        db.execute("INSERT INTO tasks (title) VALUES (?)", (title[:200],))
        db.commit()
    return redirect(url_for("index"))


@app.post("/toggle/<int:task_id>")
def toggle(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
    db.commit()
    return redirect(url_for("index"))


@app.post("/delete/<int:task_id>")
def delete(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect(url_for("index"))


@app.get("/health")
def health():
    """Simple check used later for monitoring and load balancer health checks."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Development server for local testing only. Never use debug mode on the server.
    app.run(debug=True)
