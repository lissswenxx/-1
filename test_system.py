# tests/test_system.py
import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.database import SessionLocal, engine, Base
from backend import models
from backend.main import calculate_grade_letter

class TestStudentSystem(unittest.TestCase):
    """Тестирование системы учета студентов"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        print("\n" + "="*60)
        print("ЗАПУСК ТЕСТОВ СИСТЕМЫ УЧЕТА СТУДЕНТОВ")
        print("="*60)
        
        # Создаем таблицы
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.db = SessionLocal()
        
        # Создаем тестового студента
        self.test_student = models.Student(
            first_name="Иван",
            last_name="Тестов",
            email="ivan.test@university.com",
            phone="+79991234567",
            group_name="ИВТ-21",
            course=3
        )
        self.db.add(self.test_student)
        self.db.flush()
        
        # Создаем тестового преподавателя
        self.test_teacher = models.Teacher(
            first_name="Мария",
            last_name="Преподавательская",
            email="teacher@university.com",
            department="Информатики"
        )
        self.db.add(self.test_teacher)
        self.db.flush()
        
        # Создаем тестовый курс
        self.test_course = models.Course(
            title="Базы данных",
            code="CS401",
            credits=4,
            semester="Осень 2025",
            teacher_id=self.test_teacher.id
        )
        self.db.add(self.test_course)
        self.db.flush()
        
        # Создаем тестовую оценку
        self.test_grade = models.Grade(
            student_id=self.test_student.id,
            course_id=self.test_course.id,
            grade=85.0,
            grade_letter="B",
            comment="Отлично"
        )
        self.db.add(self.test_grade)
        self.db.commit()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    # ========== ТЕСТЫ ДЛЯ СТУДЕНТА ==========
    
    def test_01_student_can_view_profile(self):
        """Сценарий 1: Студент просматривает свой профиль"""
        student = self.db.query(models.Student).filter(
            models.Student.id == self.test_student.id
        ).first()
        
        self.assertIsNotNone(student)
        self.assertEqual(student.first_name, "Иван")
        self.assertEqual(student.last_name, "Тестов")
        self.assertEqual(student.group_name, "ИВТ-21")
        self.assertEqual(student.course, 3)
        print("  ✓ Тест 1 пройден: Студент может просмотреть профиль")
    
    def test_02_student_can_view_grades(self):
        """Сценарий 1: Студент просматривает свои оценки"""
        grades = self.db.query(models.Grade).filter(
            models.Grade.student_id == self.test_student.id
        ).all()
        
        self.assertGreater(len(grades), 0, "У студента должны быть оценки")
        self.assertEqual(grades[0].grade, 85.0)
        self.assertEqual(grades[0].grade_letter, "B")
        print("  ✓ Тест 2 пройден: Студент может просмотреть оценки")
    
    def test_03_student_can_view_gpa(self):
        """Сценарий 2: Студент просматривает GPA"""
        grades = self.db.query(models.Grade).filter(
            models.Grade.student_id == self.test_student.id
        ).all()
        
        if grades:
            gpa = sum(g.grade for g in grades) / len(grades)
            self.assertEqual(gpa, 85.0)
            print(f"  ✓ Тест 3 пройден: GPA = {gpa}")
    
    def test_04_student_can_submit_appeal(self):
        """Сценарий 3: Студент подает апелляцию"""
        appeal = models.Appeal(
            student_id=self.test_student.id,
            grade_id=self.test_grade.id,
            reason="Не согласен с оценкой",
            status="pending"
        )
        self.db.add(appeal)
        self.db.commit()
        
        saved_appeal = self.db.query(models.Appeal).filter(
            models.Appeal.student_id == self.test_student.id
        ).first()
        
        self.assertIsNotNone(saved_appeal)
        self.assertEqual(saved_appeal.reason, "Не согласен с оценкой")
        self.assertEqual(saved_appeal.status, "pending")
        print("  ✓ Тест 4 пройден: Студент может подать апелляцию")
    
    # ========== ТЕСТЫ ДЛЯ ПРЕПОДАВАТЕЛЯ ==========
    
    def test_05_teacher_can_add_grade(self):
        """Сценарий 1: Преподаватель выставляет оценку"""
        new_grade = models.Grade(
            student_id=self.test_student.id,
            course_id=self.test_course.id,
            grade=92.0,
            grade_letter=calculate_grade_letter(92.0),
            comment="Отлично!"
        )
        self.db.add(new_grade)
        self.db.commit()
        
        grade_exists = self.db.query(models.Grade).filter(
            models.Grade.grade == 92.0
        ).first()
        
        self.assertIsNotNone(grade_exists)
        self.assertEqual(grade_exists.grade_letter, "A")
        print("  ✓ Тест 5 пройден: Преподаватель может выставить оценку")
    
    def test_06_teacher_can_edit_grade(self):
        """Сценарий 1: Преподаватель редактирует оценку"""
        grade = self.db.query(models.Grade).first()
        old_grade = grade.grade
        grade.grade = 95.0
        grade.grade_letter = calculate_grade_letter(95.0)
        self.db.commit()
        
        updated_grade = self.db.query(models.Grade).first()
        self.assertEqual(updated_grade.grade, 95.0)
        self.assertEqual(updated_grade.grade_letter, "A")
        print("  ✓ Тест 6 пройден: Преподаватель может редактировать оценку")
    
    def test_07_teacher_can_view_course_statistics(self):
        """Сценарий 2: Преподаватель смотрит статистику курса"""
        grades = self.db.query(models.Grade).filter(
            models.Grade.course_id == self.test_course.id
        ).all()
        
        if grades:
            grade_values = [g.grade for g in grades]
            avg_grade = sum(grade_values) / len(grade_values)
            max_grade = max(grade_values)
            min_grade = min(grade_values)
            
            self.assertEqual(avg_grade, 85.0)
            self.assertEqual(max_grade, 85.0)
            self.assertEqual(min_grade, 85.0)
            print("  ✓ Тест 7 пройден: Преподаватель может видеть статистику")
    
    # ========== ТЕСТЫ ДЛЯ АДМИНИСТРАТОРА ==========
    
    def test_08_admin_can_create_student(self):
        """Сценарий 1: Администратор создает студента"""
        new_student = models.Student(
            first_name="Новый",
            last_name="Студент",
            email="new@student.com",
            phone="+79998887766",
            group_name="ПМИ-22",
            course=1
        )
        self.db.add(new_student)
        self.db.commit()
        
        saved_student = self.db.query(models.Student).filter(
            models.Student.email == "new@student.com"
        ).first()
        
        self.assertIsNotNone(saved_student)
        self.assertEqual(saved_student.first_name, "Новый")
        print("  ✓ Тест 8 пройден: Администратор может создать студента")
    
    def test_09_admin_can_update_student(self):
        """Сценарий 1: Администратор обновляет данные студента"""
        student = self.db.query(models.Student).first()
        student.group_name = "ИВТ-22"
        student.course = 4
        self.db.commit()
        
        updated_student = self.db.query(models.Student).first()
        self.assertEqual(updated_student.group_name, "ИВТ-22")
        self.assertEqual(updated_student.course, 4)
        print("  ✓ Тест 9 пройден: Администратор может обновить данные студента")
    
    def test_10_admin_can_delete_student(self):
        """Сценарий 1: Администратор удаляет студента"""
        student_id = self.test_student.id
        
        student_to_delete = self.db.query(models.Student).filter(
            models.Student.id == student_id
        ).first()
        self.db.delete(student_to_delete)
        self.db.commit()
        
        deleted_student = self.db.query(models.Student).filter(
            models.Student.id == student_id
        ).first()
        self.assertIsNone(deleted_student)
        print("  ✓ Тест 10 пройден: Администратор может удалить студента")
    
    def test_11_grade_letter_calculation(self):
        """Дополнительный тест: Расчет буквенной оценки"""
        test_cases = [
            (95, "A"), (85, "B"), (75, "C"),
            (65, "D"), (55, "F"), (90, "A"), (80, "B")
        ]
        
        for grade, expected_letter in test_cases:
            result = calculate_grade_letter(grade)
            self.assertEqual(result, expected_letter)
        
        print("  ✓ Тест 11 пройден: Правильный расчет буквенной оценки")
    
    def test_12_unique_email_constraint(self):
        """Дополнительный тест: Уникальность email"""
        from sqlalchemy.exc import IntegrityError
        
        duplicate_student = models.Student(
            first_name="Дубликат",
            last_name="Тестов",
            email="ivan.test@university.com",
            phone="+79991112233",
            group_name="ИВТ-21",
            course=3
        )
        
        self.db.add(duplicate_student)
        
        with self.assertRaises(Exception):
            self.db.commit()
        
        self.db.rollback()
        print("  ✓ Тест 12 пройден: Проверка уникальности email")
    
    def test_13_course_teacher_relationship(self):
        """Дополнительный тест: Связь курса с преподавателем"""
        course = self.db.query(models.Course).first()
        self.assertIsNotNone(course.teacher)
        self.assertEqual(course.teacher.first_name, "Мария")
        print("  ✓ Тест 13 пройден: Связь курса с преподавателем работает")
    
    def test_14_student_grades_relationship(self):
        """Дополнительный тест: Связь студента с оценками"""
        student = self.db.query(models.Student).first()
        self.assertGreater(len(student.grades), 0)
        print("  ✓ Тест 14 пройден: Связь студента с оценками работает")


# Запуск тестов
if __name__ == "__main__":
    print("\n" + "="*60)
    print("ЗАПУСК ТЕСТОВ")
    print("="*60 + "\n")
    
    unittest.main(verbosity=2)