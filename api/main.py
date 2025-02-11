from fastapi import FastAPI , HTTPException
from pydantic import BaseModel 
from typing import List 
from fastapi.middleware.cors import CORSMiddleware 
app = FastAPI()


# Specify the allowed origin
allowed_origins = [
    "https://akramkhelilinnov.xyz"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Allow specific origin
    allow_credentials=True,        # Allow cookies if needed
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all HTTP headers
)
# Define input data models
class Task(BaseModel):
    id: int
    name: str
    priority: int
    duration: int
    deadline: int

class Schedule(BaseModel):
    task_id: int
    start_time: int
    end_time: int

class SchedulerInput(BaseModel):
    tasks: List[Task]
    max_time: int

# API Endpoint to optimize task scheduling
@app.post("/schedule", response_model=List[Schedule])
def optimize_schedule(input_data: SchedulerInput):
    tasks = sorted(input_data.tasks, key=lambda x: (-x.priority, x.deadline))
    max_time = input_data.max_time
    time = 0
    schedule = []

    for task in tasks:
        if time + task.duration <= min(task.deadline, max_time):
            schedule.append(Schedule(
                task_id=task.id,
                start_time=time,
                end_time=time + task.duration
            ))
            time += task.duration
        else:
            continue

    if not schedule:
        raise HTTPException(status_code=400, detail="No feasible schedule found.")

    return schedule



# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Task Scheduling Optimizer API is running!"}