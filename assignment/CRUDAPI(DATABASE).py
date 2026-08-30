import sqlite3
from fastapi import FastAPI, HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
app=FastAPI()
DB_NAME="tasks.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL
            )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("learn python", 0),
                ("Build API", 0),
                ("Test API", 1)
            ]
        )
    conn.commit()
    conn.close()
init_db()
class TaskCreate(BaseModel):
   title: str
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
   request:Request,
   exc:RequestValidationError
):
   return JSONResponse(
      status_code=400,
      content={"error":"Invalid request body"}
   )
@app.get("/")
def home():
   return{
      "name":"Task API",
      "version":"1.0",
      "endpoints":["/tasks"]
   }
@app.get("/health")
def health():
   return{
      "status":"ok"
   }
@app.get("/tasks")
def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")

    rows = cursor.fetchall()

    conn.close()

    tasks = []

    for row in rows:
        tasks.append({
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        })
    return tasks
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
   def get_task(task_id: int):

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }
@app.post("/tasks")
def create_task(task:TaskCreate):
    if not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, 0)
    )

    new_id = cursor.lastrowid

    conn.commit()
    conn.close()

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    return JSONResponse(
        status_code=201,
        content=new_task
    )

class TaskUpdate(BaseModel):
    title:str|None=None
    done:bool|None=None
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):

    if task_update.title is None and task_update.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "At least one field is required"}
        )

    if task_update.title is not None and not task_update.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()

    if row is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    new_title = (
        task_update.title
        if task_update.title is not None
        else row["title"]
    )

    new_done = (
        task_update.done
        if task_update.done is not None
        else bool(row["done"])
    )

    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (new_title, int(new_done), task_id)
    )

    conn.commit()
    conn.close()

    return {
        "id": task_id,
        "title": new_title,
        "done": new_done
    }
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    if cursor.rowcount == 0:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    conn.commit()
    conn.close()

    return