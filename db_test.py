from contextlib import contextmanager
from datetime import datetime
import uuid

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
# DB CONFIG
# -------------------------------
path = load_env["path"]
username = load_env["user_name"]
password = load_env["password"]
host = load_env["host"]
port = load_env["port"]
dbname = load_env["dbname"]

DATABASE_URL = f"{path}://{username}:{password}@{host}:{port}/{dbname}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
# MODELS
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
# DB CLIENT
# -------------------------------
class PostgreSQLClient:

    def __init__(self):
        pass

    def close_connection(self):
        pass

    def test_connection(self):
        with get_db() as db:
            try:
                db.execute(text("SELECT 1"))
                return True
            except Exception as e:
                print(f"Failed to establish a connection: {e}")
                return False

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
            db_query = db.query(table)

            if filtr:
                db_query = db_query.filter(table.id == filtr)

            if query:
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

    def read_table_tag_flavor(self, table, params, skip=0):
        with get_db() as db:
            db_query = db.query(table)
            filters = []

            if params:
                if "id" in params:
                    filters.append(table.id == params["id"])
                if "tag" in params:
                    filters.append(table.tag == params["tag"])

            if filters:
                db_query = db_query.filter(and_(*filters))

            db_query = db_query.offset(skip)

            if "limit" in params:
                db_query = db_query.limit(params["limit"])

            result = db_query.all()
            return [row.to_dict() for row in result]

    def write_table(self, db_tables):
        with get_db() as db:
            db.add(db_tables)
            db.commit()
            db.refresh(db_tables)
            return db_tables

    def update_table(self, filter_query, update_data):
        with get_db() as db:
            tables = db.query(FlavorModel).filter(filter_query)
            existing_entry = tables.first()

            if not existing_entry:
                return 0

            for key, value in update_data.items():
                setattr(existing_entry, key, value)

            db.commit()
            return 1

    def list_collection_names(self):
        with get_db() as db:
            result = db.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            return [row[0] for row in result]

# -------------------------------
# WRITE FUNCTION
# -------------------------------
def write(
    user_id,
    user_name,
    project_id,
    project_name,
    tenant,
    method,
    api_path,
    services,
    start_date,
    end_date,
    request_id,
    action_status=None,
    event_metadata=None,
    is_deleted=False,
):
    data = dict(
        request_id=request_id,
        user_id=user_id,
        user_name=user_name,
        project_id=project_id,
        project_name=project_name,
        tenant=tenant,
        method=method,
        api_path=api_path,
        action_status=action_status,
        services=services,
        event_metadata=event_metadata,
        start_date=start_date,
        end_date=end_date,
        is_deleted=is_deleted,
    )

    post = PostgreSQLClient()
    post.write_tables(data)