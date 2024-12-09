from typing import Optional, List
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, func, CompoundSelect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import async_session, User, UserRole
from sqlalchemy.exc import SQLAlchemyError
from bot_instance import bot
from sqlalchemy import select, delete
from datetime import datetime
from sqlalchemy import update
import random
from sqlalchemy import or_
from sqlalchemy.orm import aliased
import json
from openpyxl import Workbook
from sqlalchemy import select

async def check_admin(telegram_id: str) -> bool:
    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(User).where(
                        User.login == telegram_id,
                        or_(User.role == UserRole.ADMIN, User.role == UserRole.SUPERADMIN)
                    )
                )
                admin = result.scalar_one_or_none()

                if admin:
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error occurred while checking if user is admin: {e}")
        return False

async def get_name(telegram_id: str) -> Optional[str]:
    async with async_session() as session:
        result = await session.execute(
            select(User.full_name).where(telegram_id == User.login)
        )
        name = result.scalar_one_or_none()

        return name

# Add a new user
async def add_user(full_name: str, role: UserRole, login: str) -> bool:
    async with async_session() as session:
        async with session.begin():
            # Проверяем, существует ли уже пользователь с таким логином
            existing_user = await session.execute(
                select(User).where(User.login == login)
            )
            existing_user = existing_user.scalars().first()

            if existing_user:
                return False  # Пользователь с таким логином уже существует

            # Добавляем нового пользователя
            new_user = User(
                full_name=full_name,
                role=role,
                login=login
            )
            session.add(new_user)
            await session.commit()

            return True  # Возвращаем True, если пользователь был успешно добавлен

async def check_super_admin(telegram_id: str) -> bool:
    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(User).where(
                        User.login == telegram_id, User.role == UserRole.SUPERADMIN
                    )
                )
                admin = result.scalar_one_or_none()

                if admin:
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error occurred while checking if user is admin: {e}")
        return False

async def delete_admin(telegram_id: str) -> bool:
    try:
        async with async_session() as session:
            async with session.begin():
                # Проверяем, существует ли админ с таким telegram_id
                result = await session.execute(
                    select(User).where(
                        User.login == telegram_id,
                        or_(User.role == UserRole.ADMIN, User.role == UserRole.SUPERADMIN)
                    )
                )
                admin = result.scalar_one_or_none()

                # Если админ найден, удаляем его
                if admin:
                    await session.execute(
                        delete(User).where(
                            User.login == telegram_id  # Удаляем по telegram_id
                        )
                    )
                    await session.commit()
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error occurred while deleting admin: {e}")
        return False

async def delete_teacher(telegram_id: str) -> bool:
    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(User).where(
                        User.login == telegram_id, User.role == UserRole.TEACHER)
                    )
                teacher = result.scalar_one_or_none()

                if teacher:
                    await session.execute(
                        delete(User).where(
                            User.login == telegram_id  # Удаляем по telegram_id
                        )
                    )
                    await session.commit()
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error occurred while deleting admin: {e}")
        return False

async def export_users_to_excel_by_role(role: UserRole, filename: str) -> bool:
    try:
        # Открываем сессию базы данных
        async with async_session() as session:
            # Выполняем запрос на получение пользователей с указанной ролью
            if role == UserRole.TEACHER:
                result = await session.execute(
                    select(User).where(User.role == role)
                )
                users = result.scalars().all()
            else:
                result = await session.execute(
                    select(User).where(User.role != UserRole.TEACHER)
                )
                users = result.scalars().all()

            if not users:
                print("No users found for the given role.")
                return False

            # Создаём Excel файл
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = f"{role.value} Users"

            # Записываем заголовки
            headers = ["User ID", "Full Name", "Role", "Login", "Created At"]
            sheet.append(headers)

            # Заполняем данные
            for user in users:
                sheet.append([
                    user.user_id,
                    user.full_name,
                    user.role.value,
                    user.login,
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else ""
                ])

            # Сохраняем файл
            workbook.save(filename)
            return True
    except Exception as e:
        print(f"Error in export_users_to_excel_by_role: {e}")
        return False


