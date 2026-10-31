from main import (
    engine, SessionLocal, Base,
    Student, Program, Activity, Registration, Requirement
)
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ---------- CLEAR EXISTING DATA ----------
db.query(Registration).delete()
db.query(Requirement).delete()
db.query(Activity).delete()
db.query(Program).delete()
db.query(Student).delete()
db.commit()

# ---------- STUDENTS ----------
students = [
    Student(roll_no="22CS101", name="Rahul Sharma", department="CSE"),
    Student(roll_no="22CS102", name="Priya Patel", department="IT"),
    Student(roll_no="22CS103", name="Amit Kumar", department="ECE"),
]
db.add_all(students)
db.commit()

# ---------- PROGRAMS ----------
p1 = Program(title="Annual Sports Day 2026", description="Annual inter-class sports meet", start_date="2026-03-15", end_date="2026-03-16", status="Published")
p2 = Program(title="Campus Science & Tech Expo", description="Student science and robotics exhibition", start_date="2026-03-20", end_date="2026-03-20", status="Published")
db.add_all([p1, p2])
db.commit()

# ---------- ACTIVITIES ----------
a1 = Activity(program_id=p1.id, title="100m Sprint", category="Sports", venue="Track A", start_time="2026-03-15T10:00:00", end_time="2026-03-15T11:00:00", participation_type="Individual", participant_instructions="Wear sports shoes. Report 15 minutes early.", metadata_json=None, status="Published")
a2 = Activity(program_id=p1.id, title="Relay Race", category="Sports", venue="Main Track", start_time="2026-03-15T14:00:00", end_time="2026-03-15T15:30:00", participation_type="Team", participant_instructions="4 members per team. Bring water bottle. Report 20 minutes early.", metadata_json='{"team_size": 4}', status="Published")
a3 = Activity(program_id=p2.id, title="Robotics Showcase", category="Science", venue="Main Hall", start_time="2026-03-20T11:00:00", end_time="2026-03-20T13:00:00", participation_type="Team", participant_instructions="Bring your own laptop and charger. Power outlets provided.", metadata_json='{"needs_power": true}', status="Published")
db.add_all([a1, a2, a3])
db.commit()

# ---------- REQUIREMENTS ----------
reqs = [
    Requirement(activity_id=a1.id, item_name="Stopwatches", quantity=5, assigned_to="Coach Rao", status="Arranged"),
    Requirement(activity_id=a1.id, item_name="Cones", quantity=4, assigned_to="Coach Rao", status="Pending"),
    Requirement(activity_id=a2.id, item_name="Relay Batons", quantity=4, assigned_to="Coach Rao", status="Pending"),
    Requirement(activity_id=a2.id, item_name="PA Mic System", quantity=1, assigned_to="A/V Team", status="Arranged"),
    Requirement(activity_id=a3.id, item_name="Display Tables", quantity=6, assigned_to="Facilities", status="Arranged"),
    Requirement(activity_id=a3.id, item_name="Power Strips", quantity=10, assigned_to="Facilities", status="Pending"),
]
db.add_all(reqs)
db.commit()

# ---------- REGISTRATIONS ----------
regs = [
    Registration(activity_id=a1.id, student_name="Rahul Sharma", student_roll_no="22CS101", team_name=None, team_members=None, checked_in=False, created_at=datetime.now().isoformat()),
    Registration(activity_id=a2.id, student_name="Priya Patel", student_roll_no="22CS102", team_name="Team Lightning", team_members="22CS102, 22CS103, 22CS104, 22CS105", checked_in=False, created_at=datetime.now().isoformat()),
]
db.add_all(regs)
db.commit()

print(f"Seeded {db.query(Program).count()} programs, {db.query(Student).count()} students, {db.query(Activity).count()} activities, {db.query(Registration).count()} registrations, {db.query(Requirement).count()} requirements.")
db.close()