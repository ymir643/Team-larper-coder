from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------- DATABASE SETUP ----------
DATABASE_URL = "sqlite:///./campus.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---------- MODELS ----------
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    status = Column(String, default="Draft")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    participation_type = Column(String, default="Individual")
    participant_instructions = Column(String, nullable=True)
    metadata_json = Column("metadata", String, nullable=True)
    status = Column(String, default="Draft")

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    student_name = Column(String, nullable=True)
    student_roll_no = Column(String, nullable=False)
    team_name = Column(String, nullable=True)
    team_members = Column(String, nullable=True)
    checked_in = Column(Boolean, default=False)
    created_at = Column(String, nullable=True)

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    assigned_to = Column(String, nullable=True)
    status = Column(String, default="Pending")

# ---------- PYDANTIC SCHEMAS ----------
class HostLogin(BaseModel):
    email: str
    password: str

class RequirementIn(BaseModel):
    item_name: str
    quantity: int = 1
    assigned_to: Optional[str] = None

class ActivityCreate(BaseModel):
    program_id: Optional[int] = None
    title: str
    category: Optional[str] = None
    venue: Optional[str] = None
    start_time: str
    end_time: str
    participation_type: str = "Individual"
    participant_instructions: Optional[str] = None
    metadata: Optional[str] = None
    status: str = "Draft"
    requirements: List[RequirementIn] = Field(default_factory=list)

class StatusUpdate(BaseModel):
    status: str

class RegisterIn(BaseModel):
    student_name: str
    student_roll_no: str
    team_name: Optional[str] = None
    team_members: Optional[str] = None

class CheckinUpdate(BaseModel):
    checked_in: bool

class RequirementUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None

# ---------- HOST AUTH ----------
HOSTS = {
    "coach@campus.edu": {"password": "coach123", "name": "Sports Coordinator"},
    "dean@campus.edu": {"password": "dean123", "name": "Dean"},
}

# ---------- APP ----------
app = FastAPI(title="Campus Activity Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ALGORITHMS ----------
def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def parse_dt(s):
    return datetime.fromisoformat(s)

VALID_TRANSITIONS = {
    "Draft": ["Published"],
    "Published": ["Ongoing"],
    "Ongoing": ["Completed"],
    "Completed": [],
}

def activity_student_dict(a, db):
    reqs = db.query(Requirement).filter(Requirement.activity_id == a.id).all()
    ready = sum(1 for r in reqs if r.status == "Arranged")
    return {
        "id": a.id,
        "program_id": a.program_id,
        "title": a.title,
        "category": a.category,
        "venue": a.venue,
        "start_time": a.start_time,
        "end_time": a.end_time,
        "participation_type": a.participation_type,
        "participant_instructions": a.participant_instructions,
        "status": a.status,
        "metadata": a.metadata_json,
        "requirements_ready": ready,
        "requirements_total": len(reqs),
    }

def activity_host_dict(a, db):
    d = activity_student_dict(a, db)
    reqs = db.query(Requirement).filter(Requirement.activity_id == a.id).all()
    regs = db.query(Registration).filter(Registration.activity_id == a.id).all()
    d["requirements"] = [
        {"id": r.id, "item_name": r.item_name, "quantity": r.quantity,
         "assigned_to": r.assigned_to, "status": r.status}
        for r in reqs
    ]
    d["registrations"] = [
        {"id": r.id, "student_name": r.student_name,
         "student_roll_no": r.student_roll_no, "team_name": r.team_name,
         "team_members": r.team_members, "checked_in": r.checked_in,
         "created_at": r.created_at}
        for r in regs
    ]
    return d

# ---------- ENDPOINTS ----------
@app.get("/")
def root():
    return {"message": "Campus Activity Platform API", "docs": "/docs"}

@app.post("/api/host/login")
def host_login(body: HostLogin):
    host = HOSTS.get(body.email)
    if host and host["password"] == body.password:
        return {"success": True, "name": host["name"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/programs")
def list_programs(db: Session = Depends(get_db)):
    ps = db.query(Program).all()
    return [
        {"id": p.id, "title": p.title, "description": p.description,
         "start_date": p.start_date, "end_date": p.end_date, "status": p.status}
        for p in ps
    ]

@app.get("/api/activities")
def list_activities(
    program_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Activity)
    if program_id is not None:
        q = q.filter(Activity.program_id == program_id)
    if category:
        q = q.filter(Activity.category == category)
    if status:
        q = q.filter(Activity.status == status)
    else:
        q = q.filter(Activity.status != "Draft")
    return [activity_student_dict(a, db) for a in q.all()]

@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int, view: str = "student", db: Session = Depends(get_db)):
    a = db.query(Activity).filter(Activity.id == activity_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Activity not found")
    if view == "host":
        return activity_host_dict(a, db)
    return activity_student_dict(a, db)

@app.post("/api/activities")
def create_activity(body: ActivityCreate, db: Session = Depends(get_db)):
    new_act = Activity(
        program_id=body.program_id,
        title=body.title,
        category=body.category,
        venue=body.venue,
        start_time=body.start_time,
        end_time=body.end_time,
        participation_type=body.participation_type,
        participant_instructions=body.participant_instructions,
        metadata_json=body.metadata,
        status=body.status,
    )
    db.add(new_act)
    db.flush()
    for r in body.requirements:
        db.add(Requirement(
            activity_id=new_act.id,
            item_name=r.item_name,
            quantity=r.quantity,
            assigned_to=r.assigned_to,
            status="Pending",
        ))
    db.commit()
    db.refresh(new_act)
    return activity_host_dict(new_act, db)

@app.patch("/api/activities/{activity_id}/status")
def update_status(activity_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    a = db.query(Activity).filter(Activity.id == activity_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Activity not found")
    if body.status not in VALID_TRANSITIONS.get(a.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {a.status} to {body.status}",
        )
    a.status = body.status
    db.commit()
    db.refresh(a)
    return activity_host_dict(a, db)

@app.post("/api/activities/{activity_id}/register")
def register(activity_id: int, body: RegisterIn, db: Session = Depends(get_db)):
    a = db.query(Activity).filter(Activity.id == activity_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Activity not found")
    if a.status != "Published":
        raise HTTPException(
            status_code=400,
            detail="Activity is not open for registration",
        )
    existing = db.query(Registration).filter(
        Registration.activity_id == activity_id,
        Registration.student_roll_no == body.student_roll_no,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You are already registered for this activity",
        )
    my_regs = db.query(Registration).filter(
        Registration.student_roll_no == body.student_roll_no
    ).all()
    new_start = parse_dt(a.start_time)
    new_end = parse_dt(a.end_time)
    for r in my_regs:
        other = db.query(Activity).filter(Activity.id == r.activity_id).first()
        if not other:
            continue
        if overlaps(new_start, new_end, parse_dt(other.start_time), parse_dt(other.end_time)):
            raise HTTPException(
                status_code=400,
                detail=f"Time conflict with '{other.title}'",
            )
    reg = Registration(
        activity_id=activity_id,
        student_name=body.student_name,
        student_roll_no=body.student_roll_no,
        team_name=body.team_name,
        team_members=body.team_members,
        checked_in=False,
        created_at=datetime.now().isoformat(),
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return {
        "id": reg.id, "activity_id": reg.activity_id,
        "student_name": reg.student_name,
        "student_roll_no": reg.student_roll_no,
        "team_name": reg.team_name, "team_members": reg.team_members,
        "checked_in": reg.checked_in, "created_at": reg.created_at,
    }

@app.patch("/api/registrations/{reg_id}/checkin")
def checkin(reg_id: int, body: CheckinUpdate, db: Session = Depends(get_db)):
    r = db.query(Registration).filter(Registration.id == reg_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Registration not found")
    r.checked_in = body.checked_in
    db.commit()
    db.refresh(r)
    return {"id": r.id, "checked_in": r.checked_in}

@app.patch("/api/requirements/{req_id}")
def update_requirement(req_id: int, body: RequirementUpdate, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if body.status not in ["Pending", "Arranged"]:
        raise HTTPException(status_code=400, detail="Status must be Pending or Arranged")
    r.status = body.status
    if body.assigned_to is not None:
        r.assigned_to = body.assigned_to
    db.commit()
    db.refresh(r)
    return {"id": r.id, "item_name": r.item_name, "status": r.status, "assigned_to": r.assigned_to}

@app.get("/api/students/{roll_no}")
def get_student(roll_no: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student roll number not found")
    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "department": student.department
    }

@app.get("/api/students/{roll_no}/schedule")
def schedule(roll_no: str, db: Session = Depends(get_db)):
    regs = db.query(Registration).filter(Registration.student_roll_no == roll_no).all()
    items = []
    for r in regs:
        a = db.query(Activity).filter(Activity.id == r.activity_id).first()
        if not a:
            continue
        items.append({
            "activity_id": a.id,
            "title": a.title,
            "venue": a.venue,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "team_name": r.team_name,
            "participant_instructions": a.participant_instructions,
            "checked_in": r.checked_in,
        })
    items.sort(key=lambda x: x["start_time"])
    return items

if __name__ == "__main__":
    import uvicorn
    print("Starting Campus Activity Platform backend")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)