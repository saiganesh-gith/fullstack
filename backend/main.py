import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Student Fees Management System")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
def init_db():
    conn = sqlite3.connect("fees.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            class_name TEXT NOT NULL,
            total_fees REAL NOT NULL,
            paid_fees REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Pydantic Models
class StudentCreate(BaseModel):
    name: str
    roll_no: str
    class_name: str
    total_fees: float
    paid_fees: float

class PaymentUpdate(BaseModel):
    paid_fees: float

# Routes
@app.get("/students")
def get_students():
    conn = sqlite3.connect("fees.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.post("/students")
def add_student(student: StudentCreate):
    try:
        conn = sqlite3.connect("fees.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, roll_no, class_name, total_fees, paid_fees) VALUES (?, ?, ?, ?, ?)",
            (student.name, student.roll_no, student.class_name, student.total_fees, student.paid_fees)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Student added successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, context={"error": "Roll Number already exists"})

@app.put("/students/{student_id}/pay")
def update_payment(student_id: int, payment: PaymentUpdate):
    conn = sqlite3.connect("fees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT paid_fees, total_fees FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
        
    new_paid = row[0] + payment.paid_fees
    if new_paid > row[1]:
        conn.close()
        raise HTTPException(status_code=400, detail="Paid fees cannot exceed total fees")
        
    cursor.execute("UPDATE students SET paid_fees = ? WHERE id = ?", (new_paid, student_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Payment updated successfully"}

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    conn = sqlite3.connect("fees.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Student record deleted"}
