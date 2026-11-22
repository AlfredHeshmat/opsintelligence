"""Public synthetic portfolio demo bootstrap. Requires explicit OPS_PUBLIC_DEMO_ONLY."""
import os
import sys


def main() -> None:
    if os.environ.get('OPS_PUBLIC_DEMO_ONLY', '').lower() != 'true':
        raise SystemExit('Refusing public deployment without OPS_PUBLIC_DEMO_ONLY=true')
    if os.environ.get('OPS_ENABLE_LOCAL_SIGNUP', '').lower() == 'true':
        raise SystemExit('Public demo may not enable local company signup')
    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('DATABASE_URL must be set to a dedicated synthetic-only database')
    if not os.environ.get('CORS_ORIGINS'):
        raise SystemExit('CORS_ORIGINS must explicitly list the public frontend URL')

    # Database migrations must succeed before the API opens to the public.
    from alembic.config import Config
    from alembic import command
    command.upgrade(Config('alembic.ini'), 'head')

    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.db.session import create_database_engine
    from app.services.demo import seed_demo
    engine = create_database_engine(get_settings())
    try:
        with Session(engine) as session:
            try:
                seed_demo(session, count=240, seed=42)
                print('Seeded synthetic demo data', flush=True)
            except ValueError as error:
                if 'Orders already exist' not in str(error):
                    raise
                print('Existing synthetic demo data preserved', flush=True)
    finally:
        engine.dispose()

    import uvicorn
    uvicorn.run('app.main:create_app', factory=True, host='0.0.0.0',
                port=int(os.environ.get('PORT', '10000')), workers=1)


if __name__ == '__main__':
    main()
