"""Create first local owner securely. Usage: python -m scripts.bootstrap_identity.

Password is read with getpass, not command line arguments or environment variables.
"""
import getpass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_database_engine
from app.models.identity import Membership, Organisation, User
from app.security.passwords import hash_password


def main():
    engine = create_database_engine(get_settings())
    try:
        email = input('Administrator email: ').strip().lower()
        name = input('Organisation name: ').strip()
        if not 3 <= len(email) <= 254 or '@' not in email:
            raise ValueError('Valid email required')
        if not 2 <= len(name) <= 120:
            raise ValueError('Organisation name must be 2–120 characters')
        password = getpass.getpass('Password (at least 12 characters): ')
        confirm = getpass.getpass('Confirm password: ')
        if password != confirm:
            raise ValueError('Passwords do not match')
        digest = hash_password(password)
        with Session(engine) as db:
            with db.begin():
                if db.scalar(select(User.id).limit(1)) is not None:
                    raise ValueError('Identity already initialised; refusing to create another bootstrap owner')
                user = User(email=email, password_hash=digest, failed_logins=0)
                db.add(user)
                db.flush()
                org = Organisation(name=name)
                db.add(org)
                db.flush()
                db.add(Membership(user_id=user.id, organisation_id=org.id, role='owner'))
        print('Local administrator and organisation created. Do not expose this development server publicly.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
