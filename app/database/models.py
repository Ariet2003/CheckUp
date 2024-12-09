from typing import List
from sqlalchemy import (
    BigInteger, Integer, String, Boolean, ForeignKey, TIMESTAMP, Time, Enum, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os
from dotenv import load_dotenv
from enum import Enum as PyEnum

# Загрузка переменных окружения
load_dotenv()
engine = create_async_engine(url=os.getenv('SQLITE_URL'))
async_session = async_sessionmaker(engine)

# Базовый класс
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Enum для роли пользователя
class UserRole(PyEnum):
    SUPERADMIN = 'superadmin'
    ADMIN = "admin"
    TEACHER = "teacher"

# Enum для дней недели
class WeekDay(PyEnum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

# Таблица пользователей
class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    login: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

# Таблица факультетов
class Faculty(Base):
    __tablename__ = 'faculties'

    faculty_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

# Таблица кафедр
class Department(Base):
    __tablename__ = 'departments'

    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey('faculties.faculty_id'), nullable=False)

# Таблица курсов
class Course(Base):
    __tablename__ = 'courses'

    course_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.department_id'), nullable=False)

# Таблица групп
class Group(Base):
    __tablename__ = 'groups'

    group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey('courses.course_id'), nullable=False)

# Таблица студентов
class Student(Base):
    __tablename__ = 'students'

    student_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.group_id'), nullable=False)
    parent_contact: Mapped[str] = mapped_column(String(255), nullable=False)

# Таблица расписания
class Schedule(Base):
    __tablename__ = 'schedule'

    schedule_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.group_id'), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    day_of_week: Mapped[WeekDay] = mapped_column(Enum(WeekDay), nullable=False)
    time_start: Mapped[Time] = mapped_column(Time, nullable=False)
    time_end: Mapped[Time] = mapped_column(Time, nullable=False)

# Таблица истории посещаемости
class AttendanceHistory(Base):
    __tablename__ = 'attendance_history'

    history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), nullable=False)
    date_time: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    attendance_history_student_id: Mapped[int] = mapped_column(ForeignKey('attendance_history_students.id'), nullable=False)

# Таблица для связи истории посещаемости и студентов
class AttendanceHistoryStudent(Base):
    __tablename__ = 'attendance_history_students'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    history_id: Mapped[int] = mapped_column(ForeignKey('attendance_history.history_id'), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.student_id'), nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

