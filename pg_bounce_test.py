import psycopg2
import time
import threading

DB_CONFIG_POOL = {
    "host": "localhost",
    "port": 6432,
    "user": "myuser",
    "password": "mypass",
    "dbname": "mydb"
}

TOTAL_REQUESTS = 20000
CONCURRENT_THREADS = 20


def hit_db_reuse(conn, results, index):
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_sleep(0.01);")
        cur.fetchone()
        results[index] = "OK"
    except Exception as e:
        results[index] = str(e)


def run_test(config, label):
    print(f"\n🚀 Running test: {label}")
    start = time.time()

    # ✅ Create reusable connections
    connections = [psycopg2.connect(**config) for _ in range(CONCURRENT_THREADS)]

    threads = []
    results = [None] * TOTAL_REQUESTS

    for i in range(TOTAL_REQUESTS):
        conn = connections[i % CONCURRENT_THREADS]  # reuse connection

        t = threading.Thread(target=hit_db_reuse, args=(conn, results, i))
        threads.append(t)
        t.start()

        if len(threads) >= CONCURRENT_THREADS:
            for t in threads:
                t.join()
            threads = []

    for t in threads:
        t.join()

    # close connections
    for conn in connections:
        conn.close()

    end = time.time()

    success = results.count("OK")
    failed = TOTAL_REQUESTS - success

    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"⏱ Time Taken: {round(end - start, 2)} sec")


if __name__ == "__main__":
    run_test(DB_CONFIG_POOL, "WITH PgBouncer")
    run_test({**DB_CONFIG_POOL, "port": 5433}, "WITHOUT PgBouncer")