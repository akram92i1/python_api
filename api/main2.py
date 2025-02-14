from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
#Libary..  
from ortools.sat.python import cp_model
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

@app.post("/schedule", response_model=List[Schedule])
def optimize_schedule(input_data: SchedulerInput):
    model = cp_model.CpModel()
    max_time = input_data.max_time
    tasks = input_data.tasks

    # Decision variables
    start_vars = {}
    end_vars = {}
    slack_vars = {}
    
    for task in tasks:
        start_vars[task.id] = model.NewIntVar(0, max_time, f'start_{task.id}')
        end_vars[task.id] = model.NewIntVar(0, max_time, f'end_{task.id}')
        slack_vars[task.id] = model.NewIntVar(0, max_time, f'slack_{task.id}')
        
        model.Add(end_vars[task.id] == start_vars[task.id] + task.duration)
        model.Add(end_vars[task.id] <= task.deadline + slack_vars[task.id])  # Relax deadline with slack

    # Non-overlapping constraint
    intervals = []
    for task in tasks:
        intervals.append(model.NewIntervalVar(start_vars[task.id], task.duration, end_vars[task.id], f'interval_{task.id}'))

    model.AddNoOverlap(intervals)

    # Objective: Minimize makespan
    makespan = model.NewIntVar(0, max_time, 'makespan')
    model.AddMaxEquality(makespan, [end_vars[task.id] for task in tasks])
    model.Minimize(makespan)

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = [
            Schedule(task_id=task.id, start_time=solver.Value(start_vars[task.id]), end_time=solver.Value(end_vars[task.id]))
            for task in tasks
        ]
        return schedule
    else:
        raise HTTPException(status_code=400, detail="No feasible schedule found.")


# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Task Scheduling Optimizer API is running!"} 