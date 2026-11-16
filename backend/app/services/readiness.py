from sqlalchemy import Engine, text


def check_database(engine: Engine) -> None:
    """Raise an error if the database cannot answer a simple query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
