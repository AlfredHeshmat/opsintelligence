"""Build a safe SQLAlchemy DB URL from Docker-supplied variables, then launch app or migration."""
import os
import sys
from sqlalchemy.engine import URL


def configure_database():
    required=('POSTGRES_USER','POSTGRES_PASSWORD','POSTGRES_DB')
    absent=[x for x in required if not os.environ.get(x)]
    if absent:
        raise RuntimeError('Missing database configuration: '+', '.join(absent))
    url=URL.create('postgresql+psycopg',username=os.environ['POSTGRES_USER'],
                   password=os.environ['POSTGRES_PASSWORD'],host=os.getenv('DATABASE_HOST','db'),
                   port=int(os.getenv('DATABASE_PORT','5432')),database=os.environ['POSTGRES_DB'])
    os.environ['DATABASE_URL']=url.render_as_string(hide_password=False)


def main():
    configure_database()
    if len(sys.argv)!=2 or sys.argv[1] not in ('migrate','serve'):
        raise SystemExit('Usage: python -m scripts.container_entrypoint migrate|serve')
    if sys.argv[1]=='migrate':
        from alembic.config import Config
        from alembic import command
        command.upgrade(Config('alembic.ini'),'head')
    else:
        import uvicorn
        uvicorn.run('app.main:create_app',factory=True,host='0.0.0.0',port=8000,workers=1)

if __name__=='__main__':main()
