"""Seed the two demo companies and their accounts. Safe to run repeatedly."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User, UserRole

DEMO_COMPANY = "Demo Security SA"
OTHER_COMPANY = "Other Site Security"


def _get_or_create_company(db: Session, name: str) -> Company:
    company = db.scalar(select(Company).where(Company.name == name))
    if company is None:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


def _upsert_user(db: Session, company: Company, email: str, full_name: str, role: UserRole, password: str) -> None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            company_id=company.id,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )
        db.add(user)
    else:
        user.company_id = company.id
        user.full_name = full_name
        user.role = role


def seed_users(db: Session | None = None) -> None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        demo = _get_or_create_company(db, DEMO_COMPANY)
        other = _get_or_create_company(db, OTHER_COMPANY)

        _upsert_user(
            db,
            demo,
            "admin@demo.tn",
            "Amina Ben Salah",
            UserRole.ADMIN,
            settings.seed_admin_password,
        )
        _upsert_user(
            db,
            demo,
            "operator@demo.tn",
            "Youssef Trabelsi",
            UserRole.OPERATOR,
            settings.seed_operator_password,
        )
        _upsert_user(
            db,
            other,
            "admin@other.tn",
            "Other Site Admin",
            UserRole.ADMIN,
            settings.seed_admin_password,
        )
        db.commit()
        print("Seed accounts ready:")
        print(f"  admin@demo.tn / {settings.seed_admin_password}")
        print(f"  operator@demo.tn / {settings.seed_operator_password}")
        print(f"  admin@other.tn / {settings.seed_admin_password}")
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    init_db()
    seed_users()
