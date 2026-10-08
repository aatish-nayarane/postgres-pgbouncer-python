from contextlib import contextmanager
from datetime import datetime
import uuid
import time
import threading
import random
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Float,
    JSON,
    and_,
    create_engine,
    text,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from configuration import load_env

# -------------------------------
# BASE
# -------------------------------
Base = declarative_base()

# -------------------------------
# DB CONFIG - DUAL ENGINES
# -------------------------------
PGBOUNCER_URL = f"postgresql+psycopg2://myuser:mypass@localhost:6432/mydb"
DIRECT_URL = f"postgresql+psycopg2://myuser:mypass@localhost:5433/mydb"

# Enhanced pooling for high load
POOL_KWARGS = {
    "pool_size": 50,
    "max_overflow": 0,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_pre_ping": True
}

pgbouncer_engine = create_engine(PGBOUNCER_URL, **POOL_KWARGS)
direct_engine = create_engine(DIRECT_URL, **POOL_KWARGS)

# Default to PgBouncer
engine = pgbouncer_engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------------
# TABLE SETUP
# -------------------------------
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")

# -------------------------------
# SESSION MANAGER
# -------------------------------
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# -------------------------------
# MODELS (unchanged)
# -------------------------------
class FlavorModel(Base):
    __tablename__ = "machine_type"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ram = Column(Integer, nullable=False)
    disk = Column(Integer, nullable=False)
    vcpus = Column(Integer, nullable=False)
    project_id = Column(String, nullable=True, index=True)
    os_flv_ext_data_ephemeral = Column(Integer, nullable=True)
    swap = Column(Integer, nullable=True)
    rxtx_factor = Column(Float, nullable=True)
    tag = Column(String, nullable=False, index=True)
    pricing = Column(Integer, nullable=False)
    property = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ram": self.ram,
            "disk": self.disk,
            "vcpus": self.vcpus,
            "project_id": self.project_id,
            "os_flv_ext_data_ephemeral": self.os_flv_ext_data_ephemeral,
            "swap": self.swap,
            "rxtx_factor": self.rxtx_factor,
            "tag": self.tag,
            "pricing": self.pricing,
            "property": self.property,
        }

# -------------------------------
# DB CLIENT (minimal changes - engine switchable)
# -------------------------------
class PostgreSQLClient:

    def __init__(self, use_pgbouncer=True):
        global engine, SessionLocal
        if use_pgbouncer:
            engine = pgbouncer_engine
        else:
            engine = direct_engine
        SessionLocal.configure(bind=engine)
        self.test_connection()

    def close_connection(self):
        engine.dispose()

    def test_connection(self):
        with get_db() as db:
            try:
                db.execute(text("SELECT 1"))
                return True
            except Exception as e:
                print(f"Failed to establish a connection: {e}")
                return False

    # All existing methods unchanged...
    def read_table(self, table, skip=0, filtr=None, query=None, limit=100):
        with get_db() as db:
            db_query = db.query(table)
            if filtr:
                db_query = db_query.filter(table.id == filtr)
            if query:
                db_query = db_query.filter(query)
            result = db_query.offset(skip).limit(limit).all()
            return [row.to_dict() for row in result]

    def flvor_data(self, table, skip=0, filtr=None, query=None, limit=100):
        with get_db() as db:
            db_query = db_query.filter(query)
            result = db_query.offset(skip).limit(limit).all()
            return [row.to_dict() for row in result]

    def read_table_flavor(self, table, params, skip=0):
        with get_db() as db:
            db_query = db.query(table)
            filters = []
            if params:
                if params.get("project_id"):
                    filters.append(table.project_id == params.get("project_id"))
                if params.get("disk"):
                    filters.append(table.disk == params.get("disk"))
                if params.get("ram"):
                    filters.append(table.ram == params.get("ram"))
                if params.get("tag"):
                    filters.append(table.tag == params.get("tag"))
                if params.get("price"):
                    filters.append(table.pricing == params.get("price"))
            if filters:
                db_query = db_query.filter(and_(*filters))
            result = db_query.offset(skip).limit(params["limit"]).all()
            return [row.to_dict() for row in result]

    # ... other methods trimmed for brevity, copy from original

    def write_table(self, db_tables):
        with get_db() as db:
            db.add(db_tables)
            db.commit()
            db.refresh(db_tables)
            return db_tables

    def list_collection_names(self):
        with get_db() as db:
            result = db.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            return [row[0] for row in result]

# -------------------------------
# VIGOROUS LOAD TEST (40k req, 50 threads)
# -------------------------------
TEST_DATA_TEMPLATE = {
    "id": lambda: str(uuid.uuid4()),
    "name": "test-flavor",
    "ram": random.randint(1, 64),
    "disk": random.randint(10, 1000),
    "vcpus": random.randint(1, 32),
    "project_id": "test-project",
    "tag": "test-tag",
    "pricing": random.randint(10, 100),
    "os_flv_ext_data_ephemeral": 0,
    "swap": 0,
    "rxtx_factor": 1.0,
    "property": {}
}

def load_test(client, label, total_requests=40000, concurrent=50):
    print(f"\n🚀 {label} - {total_requests} requests, {concurrent} threads")
    start = time.time()
    results = [None] * total_requests
    threads = []
    
    def worker(i):
        flavor = FlavorModel(**{k: v() if callable(v) else v for k, v in TEST_DATA_TEMPLATE.items()})
        try:
            # Write
            client.write_table(flavor)
            # Read back
            flavors = client.read_table(FlavorModel, limit=1)
            results[i] = len(flavors) > 0
        except Exception as e:
            results[i] = False
    
    for i in range(total_requests):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        if len(threads) >= concurrent:
            for t in threads:
                t.join()
            threads = []
    
    for t in threads:
        t.join()
    
    end = time.time()
    success = sum(1 for r in results if r)
    print(f"✅ Success: {success}/{total_requests} ({success/total_requests*100:.1f}%)")
    print(f"⏱ {round(end-start,2)}s RPS: {total_requests/(end-start):.0f}")

# -------------------------------
# MAIN - TEST
# -------------------------------
if __name__ == "__main__":
    create_tables()
    
    # Test PgBouncer pooling
    client_pb = PostgreSQLClient(use_pgbouncer=True)
    load_test(client_pb, "PgBouncer + SQLAlchemy Pool (50)")
    
    # Test Direct
    client_direct = PostgreSQLClient(use_pgbouncer=False)
    load_test(client_direct, "Direct Postgres + SQLAlchemy Pool (50)")
    
    print("✅ All tests complete")
