from fastapi import FastAPI, HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
app=FastAPI()
tasks=[
   {
      "id":1,
      "title":"learn python",
      "done":False

   },
   {
      "id":2,
      "title":"Build API",
      "done":False
   },
   {
      "id":3,
      "title":"Test API",
      "done":True
   }
]
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
   return tasks
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
      if task["id"]==task_id:
         return task
    
    raise HTTPException(
       status_code=404,
       detail=f"Task{task_id} not found"
    )
@app.post("/tasks")
def create_task(task:TaskCreate):
   #check for empty title 
    if not task.title.strip():
      return JSONResponse(
         status_code=400,
         content={"error":"Title cannot be empty"}
      )
   #Generate next ID 
    new_id=max(
       [task["id"] for task in tasks],
        default=0
    ) + 1
     #Create new task
    new_task={
        "id":new_id,
        "title":task.title,
        "done":False
    } 
    #Add task to list
    tasks.append(new_task)
            #Return created task
    return JSONResponse(
        status_code=201,
        content=new_task
    )

class TaskUpdate(BaseModel):
    title:str|None=None
    done:bool|None=None
@app.put("/tasks/{task_id}")
def update_task(task_id:int,task_update:TaskUpdate):
    if task_update.title is None and task_update.done is None:
        return JSONResponse(
            status_code=400,
            content={"error":"At least one field is required"}
        )
    if task_update.title is not None and not task_update.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error":"Title cannot be empty"}
        )
    for task in tasks:
        if task["id"]==task_id:
            if task_update.title is not None:
                task["title"]=task_update.title
            if task_update.done is not None:
                task["done"]=task_update.done
            return task
    raise HTTPException(
        status_code=404,
        detail=f"Task{task_id} not found"
    )
@app.delete("/tasks/{task_id}",
            status_code=204)
def delete_task(task_id:int):
    for index,task in enumerate(tasks):
        if task["id"]==task_id:
            tasks.pop(index)
            return
    raise HTTPException(
        status_code=404,
        detail=f"Task{task_id} not found"
    )     