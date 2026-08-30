from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from repository import get_connection, init_db

app = FastAPI()

init_db()

class TaskCreate(BaseModel):
    title: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"}
    )

@app.get("/")
def home():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    tasks = []

    for row in rows:
        tasks.append({
            "id": row[0],
            "title": row[1],
            "done": row[2]
        })

    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.post("/tasks")
def create_task(task: TaskCreate):
    if not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, done)
        VALUES (%s, %s)
        RETURNING id
        """,
        (task.title, False)
    )

    new_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
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
    title: str | None = None
    done: bool | None = None

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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )

    row = cursor.fetchone()

    if row is None:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    new_title = (
        task_update.title
        if task_update.title is not None
        else row[1]
    )

    new_done = (
        task_update.done
        if task_update.done is not None
        else row[2]
    )

    cursor.execute(
        """
        UPDATE tasks
        SET title = %s, done = %s
        WHERE id = %s
        """,
        (new_title, new_done, task_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": task_id,
        "title": new_title,
        "done": new_done
    }

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    conn.commit()

    cursor.close()
    conn.close()

    return