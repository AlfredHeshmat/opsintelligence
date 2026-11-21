"""Local operator provision of additional login identities (no public registration)."""
import getpass
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import create_database_engine
from app.models.identity import User
from app.security.passwords import hash_password


def main():
    email=input('New user email: ').strip().lower()
    if len(email) > 254 or '@' not in email:
        raise ValueError('Valid email required')
    pwd=getpass.getpass('Password (min 12 characters): ')
    verify=getpass.getpass('Confirm password: ')
    if pwd != verify:raise ValueError('Passwords do not match')
    hashed=hash_password(pwd)
    engine=create_database_engine(get_settings())
    try:
        with Session(engine) as db, db.begin():
            if db.scalar(select(User).where(User.email==email)):
                raise ValueError('Account already exists')
            db.add(User(email=email,password_hash=hashed,failed_logins=0))
        print('User created. Organisation admin may add this existing user as a member.')
    finally:
        engine.dispose()


if __name__ == '__main__':main()
