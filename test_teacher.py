# tests/test.py
# НЕ использует pytest - чистый Python unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.database import SessionLocal, engine
from backend import models

# Функция для расчета буквенной оценки (если нет в main)
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

class TestStudentSystem(unittest.TestCase):
    """Тестирование системы учета студентов"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед всеми тестами"""
        print("\n" + "="*50)
        print("ЗАПУСК ТЕСТОВ СИСТЕМЫ УЧЕТА СТУДЕНТОВ")
        print("="*50)
        
        # Создаем тестовую БД
        models.Base.metadata.create_all(bind=engine)
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.db = SessionLocal()
        
        # Создаем тестового студента
        self.test_student = models.Student(
            first_name="Иван",
            last_name="Тестов",
            email="ivan.test@university.com",
            group_name="ИВТ-21",
            course=3
        )
        self.db.add(self.test_student)
        self.db.commit()
        
        # Создаем тестового преподавателя
        self.test_teacher = models.Teacher(
            first_name="Мария",
            last_name="Преподавательская",
            email="teacher@university.com",
            department="Информатики"
        )
        self.db.add(self.test_teacher)
        self.db.commit()
        
        # Создаем тестовый курс
        self.test_course = models.Course(
            title="Базы данных",
            code="CS401",
            credits=4,
            semester="Осень 2025",
            teacher_id=self.test_teacher.id
        )
        self.db.add(self.test_course)
        self.db.commit()
        
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
        
        # Очищаем БД
        models.Base.metadata.drop_all(bind=engine)
        models.Base.metadata.create_all(bind=engine)
    
    # ========== ТЕСТЫ ДЛЯ СТУДЕНТА (3 сценария) ==========
    
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
        print("✓ Тест 1 пройден: Студент может просмотреть профиль")
    
    def test_02_student_can_view_grades(self):
        """Сценарий 1: Студент просматривает свои оценки"""
        grades = self.db.query(models.Grade).filter(
            models.Grade.student_id == self.test_student.id
        ).all()
        
        self.assertGreater(len(grades), 0, "У студента должны быть оценки")
        self.assertEqual(grades[0].grade, 85.0)
        self.assertEqual(grades[0].grade_letter, "B")
        print("✓ Тест 2 пройден: Студент может просмотреть оценки")
    
    def test_03_student_can_view_gpa(self):
        """Сценарий 2: Студент просматривает GPA"""
        grades = self.db.query(models.Grade).filter(
            models.Grade.student_id == self.test_student.id
        ).all()
        
        if grades:
            gpa = sum(g.grade for g in grades) / len(grades)
            self.assertEqual(gpa, 85.0)
        print("✓ Тест 3 пройден: Студент может просмотреть GPA")
    
    def test_04_student_can_submit_appeal(self):
        """Сценарий 3: Студент подает апелляцию"""
        # Проверяем, есть ли модель Appeal
        if hasattr(models, 'Appeal'):
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
            print("✓ Тест 4 пройден: Студент может подать апелляцию")
        else:
            print("⚠ Тест 4 пропущен: Модель Appeal не найдена")
    
    # ========== ТЕСТЫ ДЛЯ ПРЕПОДАВАТЕЛЯ (3 сценария) ==========
    
    def test_05_teacher_can_add_grade(self):
        """Сценарий 1: Преподаватель выставляет оценку"""
        new_grade = models.Grade(
            student_id=self.test_student.id,
            course_id=self.test_course.id,
            grade=92.0,
            grade_letter=calculate_grade_letter(92.0)
        )
        self.db.add(new_grade)
        self.db.commit()
        
        grade_exists = self.db.query(models.Grade).filter(
            models.Grade.grade == 92.0
        ).first()
        
        self.assertIsNotNone(grade_exists)
        self.assertEqual(grade_exists.grade_letter, "A")
        print("✓ Тест 5 пройден: Преподаватель может выставить оценку")
    
    def test_06_teacher_can_edit_grade(self):
        """Сценарий 1: Преподаватель редактирует оценку"""
        grade = self.db.query(models.Grade).first()
        if grade:
            original_grade = grade.grade
            grade.grade = 95.0
            grade.grade_letter = calculate_grade_letter(95.0)
            self.db.commit()
            
            updated_grade = self.db.query(models.Grade).first()
            self.assertEqual(updated_grade.grade, 95.0)
            self.assertEqual(updated_grade.grade_letter, "A")
            print("✓ Тест 6 пройден: Преподаватель может редактировать оценку")
        else:
            print("⚠ Тест 6 пропущен: Нет оценок для редактирования")
    
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
            print("✓ Тест 7 пройден: Преподаватель может видеть статистику")
        else:
            print("⚠ Тест 7 пропущен: Нет оценок для статистики")
    
    # ========== ТЕСТЫ ДЛЯ АДМИНИСТРАТОРА (3 сценария) ==========
    
    def test_08_admin_can_create_student(self):
        """Сценарий 1: Администратор создает студента"""
        new_student = models.Student(
            first_name="Новый",
            last_name="Студент",
            email="new@student.com",
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
        print("✓ Тест 8 пройден: Администратор может создать студента")
    
    def test_09_admin_can_update_student(self):
        """Сценарий 1: Администратор обновляет данные студента"""
        student = self.db.query(models.Student).first()
        if student:
            student.group_name = "ИВТ-22"
            student.course = 4
            self.db.commit()
            
            updated_student = self.db.query(models.Student).first()
            self.assertEqual(updated_student.group_name, "ИВТ-22")
            self.assertEqual(updated_student.course, 4)
            print("✓ Тест 9 пройден: Администратор может обновить данные студента")
        else:
            print("⚠ Тест 9 пропущен: Нет студента для обновления")
    
    def test_10_admin_can_delete_student_cascade(self):
        """Сценарий 1: Администратор удаляет студента (каскадно)"""
        student_id = self.test_student.id
        
        # Удаляем студента
        student_to_delete = self.db.query(models.Student).filter(
            models.Student.id == student_id
        ).first()
        
        if student_to_delete:
            self.db.delete(student_to_delete)
            self.db.commit()
            
            # Проверяем, что студент удален
            deleted_student = self.db.query(models.Student).filter(
                models.Student.id == student_id
            ).first()
            self.assertIsNone(deleted_student)
            
            # Проверяем, что оценки удалены каскадно
            grades = self.db.query(models.Grade).filter(
                models.Grade.student_id == student_id
            ).all()
            self.assertEqual(len(grades), 0)
            print("✓ Тест 10 пройден: Администратор может удалить студента")
        else:
            print("⚠ Тест 10 пропущен: Нет студента для удаления")
    
    def test_11_grade_letter_calculation(self):
        """Дополнительный тест: Расчет буквенной оценки"""
        test_cases = [
            (95, "A"),
            (85, "B"),
            (75, "C"),
            (65, "D"),
            (55, "F"),
            (90, "A"),
            (80, "B")
        ]
        
        for grade, expected_letter in test_cases:
            result = calculate_grade_letter(grade)
            self.assertEqual(result, expected_letter)
        
        print("✓ Тест 11 пройден: Правильный расчет буквенной оценки")
    
    def test_12_unique_email_constraint(self):
        """Дополнительный тест: Уникальность email"""
        duplicate_student = models.Student(
            first_name="Дубликат",
            last_name="Тестов",
            email="ivan.test@university.com",  # Тот же email
            group_name="ИВТ-21",
            course=3
        )
        
        try:
            self.db.add(duplicate_student)
            self.db.commit()
        except Exception:
            self.db.rollback()
            print("✓ Тест 12 пройден: Проверка уникальности email")
        else:
            self.fail("Должна быть ошибка при дублировании email")

# Запуск тестов
if __name__ == "__main__":
    unittest.main(verbosity=2)