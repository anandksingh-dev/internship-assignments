from repository import get_connection, init_db

init_db()

conn = get_connection()

print("Connected to PostgreSQL successfully!")

conn.close()