import sqlalchemy as sa
import sqlalchemy.pool as pool
import time
import threading
from sqlalchemy import create_engine, text

# Same DB configs as pg_bounce_test.py
DB_CONFIG_PGBOUNCER = {
    "host": "localhost",
    "port": 6432,
    "user": "myuser",
    "password": "mypass",
    "dbname": "mydb"
}

DB_CONFIG_DIRECT = {
    "host": "localhost",
    "port": 5433,
    "user": "myuser",
    "password": "mypass",
    "dbname": "mydb"
}

# Connection string for SQLAlchemy (psycopg2 dialect)
PGBOUNCER_URL = "postgresql+psycopg2://myuser:mypass@localhost:6432/mydb"
DIRECT_URL = "postgresql+psycopg2://myuser:mypass@localhost:5433/mydb"

TOTAL_REQUESTS = 20000
CONCURRENT_THREADS = 20
POOL_SIZE = 20  # Match concurrent threads


def hit_db(engine, results, index):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT pg_sleep(0.01)"))
            conn.commit()  # Ensure transaction
            result = conn.scalar(text("SELECT 1"))
        results[index] = "OK"
    except Exception as e:
        results[index] = str(e)


def run_test(db_url, label):
    print(f"\n🚀 Running SQLAlchemy test: {label}")
    start = time.time()

    # Create engine with fixed pool size (no overflow)
    engine = create_engine(
        db_url,
        poolclass=pool.QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=0,
        pool_pre_ping=True,
        echo=False
    )

    threads = []
    results = [None] * TOTAL_REQUESTS

    def worker(index):
        hit_db(engine, results, index)

    for i in range(TOTAL_REQUESTS):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

        if len(threads) >= CONCURRENT_THREADS:
            for t in threads:
                t.join()
            threads = []

    # Join remaining
    for t in threads:
        t.join()

    # Dispose engine
    engine.dispose()

    end = time.time()

    success = results.count("OK")
    failed = TOTAL_REQUESTS - success

    print(f"✅ Success: {success}/{TOTAL_REQUESTS}")
    print(f"❌ Failed: {failed}")
    print(f"⏱ Time Taken: {round(end - start, 2)} sec")
    print(f"📊 Success Rate: {100 * success / TOTAL_REQUESTS:.1f}%")


if __name__ == "__main__":
    # Test PgBouncer (SQLAlchemy pool + PgBouncer pool)
    run_test(PGBOUNCER_URL, "WITH PgBouncer (SQLAlchemy pool_size=20)")

    # Test Direct Postgres
    run_test(DIRECT_URL, "Direct Postgres (SQLAlchemy pool_size=20)")
