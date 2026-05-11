# backend/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# ========== Student Schemas ==========
class StudentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    group_name: str = Field(..., min_length=1, max_length=20)
    course: int = Field(1, ge=1, le=6)

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== Teacher Schemas ==========
class TeacherBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department: Optional[str] = None

class TeacherCreate(TeacherBase):
    pass

class TeacherResponse(TeacherBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== Course Schemas ==========
class CourseBase(BaseModel):
    title: str
    code: str
    credits: int = 3
    semester: str
    teacher_id: int

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== Grade Schemas ==========
class GradeBase(BaseModel):
    student_id: int
    course_id: int
    grade: float = Field(..., ge=0, le=100)
    comment: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class GradeResponse(GradeBase):
    id: int
    grade_letter: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== Appeal Schemas ==========
class AppealBase(BaseModel):
    student_id: int
    grade_id: int
    reason: str

class AppealCreate(AppealBase):
    pass

class AppealResponse(AppealBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True