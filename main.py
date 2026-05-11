# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas
from database import engine, get_db

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Management System", version="1.0.0")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== HELPER FUNCTIONS ==========
def calculate_grade_letter(grade: float) -> str:
    """Конвертация числовой оценки в буквенную"""
    if grade >= 90:
        return "A"
    elif grade >= 80:
        return "B"
    elif grade >= 70:
        return "C"
    elif grade >= 60:
        return "D"
    else:
        return "F"

# ========== STUDENT ENDPOINTS ==========
@app.post("/api/students", response_model=schemas.StudentResponse)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Student).filter(models.Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/api/students", response_model=List[schemas.StudentResponse])
def get_students(
    skip: int = 0, 
    limit: int = 100,
    group_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Student)
    if group_name:
        query = query.filter(models.Student.group_name == group_name)
    return query.offset(skip).limit(limit).all()

@app.get("/api/students/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/api/students/{student_id}", response_model=schemas.StudentResponse)
def update_student(student_id: int, student: schemas.StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if student.email != db_student.email:
        existing = db.query(models.Student).filter(models.Student.email == student.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    for key, value in student.model_dump().items():
        setattr(db_student, key, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}

# ========== TEACHER ENDPOINTS ==========
@app.post("/api/teachers", response_model=schemas.TeacherResponse)
def create_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = models.Teacher(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@app.get("/api/teachers", response_model=List[schemas.TeacherResponse])
def get_teachers(db: Session = Depends(get_db)):
    return db.query(models.Teacher).all()

# ========== COURSE ENDPOINTS ==========
@app.post("/api/courses", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/api/courses", response_model=List[schemas.CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()

# ========== GRADE ENDPOINTS ==========
@app.post("/api/grades", response_model=schemas.GradeResponse)
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == grade.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(models.Course).filter(models.Course.id == grade.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing = db.query(models.Grade).filter(
        models.Grade.student_id == grade.student_id,
        models.Grade.course_id == grade.course_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Grade already exists for this student and course")
    
    grade_letter = calculate_grade_letter(grade.grade)
    db_grade = models.Grade(**grade.model_dump(), grade_letter=grade_letter)
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

@app.put("/api/grades/{grade_id}", response_model=schemas.GradeResponse)
def update_grade(grade_id: int, grade_data: schemas.GradeCreate, db: Session = Depends(get_db)):
    db_grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not db_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    db_grade.grade = grade_data.grade
    db_grade.grade_letter = calculate_grade_letter(grade_data.grade)
    db_grade.comment = grade_data.comment
    db_grade.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_grade)
    return db_grade

@app.get("/api/students/{student_id}/grades", response_model=List[schemas.GradeResponse])
def get_student_grades(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    return grades

@app.get("/api/students/{student_id}/gpa")
def get_student_gpa(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    if not grades:
        return {"gpa": 0.0}
    
    gpa = sum(g.grade for g in grades) / len(grades)
    return {"gpa": round(gpa, 2)}

@app.get("/api/courses/{course_id}/statistics")
def get_course_statistics(course_id: int, db: Session = Depends(get_db)):
    grades = db.query(models.Grade).filter(models.Grade.course_id == course_id).all()
    if not grades:
        return {"average": 0, "max": 0, "min": 0, "count": 0}
    
    grade_values = [g.grade for g in grades]
    return {
        "average": round(sum(grade_values) / len(grade_values), 2),
        "max": max(grade_values),
        "min": min(grade_values),
        "count": len(grades)
    }

# ========== APPEAL ENDPOINTS ==========
@app.post("/api/appeals", response_model=schemas.AppealResponse)
def create_appeal(appeal: schemas.AppealCreate, db: Session = Depends(get_db)):
    db_appeal = models.Appeal(**appeal.model_dump())
    db.add(db_appeal)
    db.commit()
    db.refresh(db_appeal)
    return db_appeal

@app.get("/api/students/{student_id}/appeals", response_model=List[schemas.AppealResponse])
def get_student_appeals(student_id: int, db: Session = Depends(get_db)):
    appeals = db.query(models.Appeal).filter(models.Appeal.student_id == student_id).all()
    return appeals

@app.put("/api/appeals/{appeal_id}")
def update_appeal_status(appeal_id: int, status: str, db: Session = Depends(get_db)):
    appeal = db.query(models.Appeal).filter(models.Appeal.id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    appeal.status = status
    db.commit()
    return {"message": "Appeal status updated"}

# ========== ROOT ==========
@app.get("/")
def root():
    return {
        "message": "Student Management System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)