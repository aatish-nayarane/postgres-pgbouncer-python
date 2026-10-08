# PostgreSQL PgBouncer

A Python project demonstrating **PostgreSQL connection pooling with PgBouncer**, along with direct database connections and SQLAlchemy connection pooling.

The project explores how PgBouncer can manage and reuse PostgreSQL connections to improve database connection efficiency and scalability.

## Project Structure

```text
.
├── configuration.py
├── db_test.py
├── db_test_pooled.py
├── pg_bounce_test.py
├── sqlalchemy_pool_test.py
├── docker-compose.yaml
├── __pycache__/
└── README.md
```

## PgBouncer

**PgBouncer** is a lightweight connection pooler for PostgreSQL.

Instead of allowing every application request to create a new PostgreSQL connection, PgBouncer maintains a pool of database connections and reuses them.

### Without PgBouncer

```text
Application
    |
    +---- Connection ----> PostgreSQL
    |
    +---- Connection ----> PostgreSQL
    |
    +---- Connection ----> PostgreSQL
    |
    +---- Connection ----> PostgreSQL
```

A large number of application connections can create significant overhead on PostgreSQL.

### With PgBouncer

```text
             +----------------+
             |   Application  |
             +-------+--------+
                     |
                     v
             +----------------+
             |    PgBouncer   |
             | Connection Pool|
             +-------+--------+
                     |
          +----------+----------+
          |          |          |
          v          v          v
       PostgreSQL PostgreSQL PostgreSQL
```

PgBouncer manages the connections between the application and PostgreSQL.

## Connection Pooling

Connection pooling allows existing database connections to be reused instead of creating a new connection for every request.

Typical flow:

```text
Application
     |
     v
Request database connection
     |
     v
Connection Pool
     |
     +---- Existing connection available
     |             |
     |             v
     |        Use connection
     |
     +---- No connection available
                   |
                   v
              Wait / Queue
```

After the database operation completes, the connection is returned to the pool.

## Pooling Modes

PgBouncer supports different pooling modes.

### Session Pooling

A server connection is assigned to a client for the entire client session.

```text
Client
  |
  +---- Session ----> PostgreSQL Connection
```

This provides compatibility with applications that require session-level PostgreSQL features.

### Transaction Pooling

A PostgreSQL connection is assigned to a client only for the duration of a transaction.

```text
Client
  |
  +---- Transaction ----> PostgreSQL
  |
  +---- Connection returned to pool
```

This allows better connection reuse and is useful for applications with many short transactions.

### Statement Pooling

Connections are assigned for individual statements.

This provides the highest level of connection reuse but has more restrictions because session-level features cannot generally be used.

## Project Components

### `configuration.py`

Contains database and PgBouncer configuration used by the Python examples.

Typical configuration includes:

- PostgreSQL host
- PostgreSQL port
- Database name
- Username
- Password
- PgBouncer host
- PgBouncer port
- Pool configuration

Keep credentials outside the source code in production environments.

### `db_test.py`

Demonstrates direct PostgreSQL database connectivity and database operations.

This can be used as a baseline for comparing direct PostgreSQL connections with pooled connections.

### `db_test_pooled.py`

Demonstrates PostgreSQL connections using a connection pool.

The example shows how multiple database operations can reuse connections instead of creating a new connection for every operation.

### `pg_bounce_test.py`

Contains tests/examples for connecting through **PgBouncer**.

The purpose is to verify that the application can communicate with PostgreSQL through the PgBouncer connection pool.

### `sqlalchemy_pool_test.py`

Demonstrates connection pooling using **SQLAlchemy**.

This allows comparison between:

```text
Direct PostgreSQL connection
        |
        v
Application
```

and:

```text
SQLAlchemy Pool
        |
        v
PgBouncer
        |
        v
PostgreSQL
```

### `docker-compose.yaml`

Defines the containerized environment for PostgreSQL/PgBouncer testing.

Docker Compose makes it easier to start the required services consistently.

## Running with Docker Compose

Start the services:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

View PgBouncer logs:

```bash
docker compose logs pgbouncer
```

Stop the services:

```bash
docker compose down
```

To remove containers and associated volumes:

```bash
docker compose down -v
```

## Testing

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the database test:

```bash
python db_test.py
```

Run the pooled connection test:

```bash
python db_test_pooled.py
```

Run the PgBouncer test:

```bash
python pg_bounce_test.py
```

Run the SQLAlchemy pool test:

```bash
python sqlalchemy_pool_test.py
```

## PostgreSQL vs PgBouncer

| Feature | Direct PostgreSQL | PgBouncer |
|---|---|---|
| Connection management | Application | PgBouncer |
| Connection reuse | Application-dependent | Built-in pooling |
| Connection overhead | Higher with many connections | Reduced |
| Pooling | Optional | Core functionality |
| Suitable for high concurrency | Depends on application | Yes |
| Lightweight | Yes | Yes |

## Connection Flow

The project can be used to understand the following architecture:

```text
                    Application
                         |
              +----------+----------+
              |                     |
              v                     v
       Direct PostgreSQL      SQLAlchemy Pool
                                    |
                                    v
                                PgBouncer
                                    |
                                    v
                               PostgreSQL
```

This makes it possible to compare different connection-management approaches.

## Key Concepts

This project demonstrates:

- PostgreSQL connections
- Connection pooling
- PgBouncer
- Transaction pooling
- Session pooling
- SQLAlchemy connection pools
- Database connection reuse
- Docker Compose
- PostgreSQL client connections
- Database scalability
- Connection management

## Why PgBouncer?

Creating PostgreSQL connections can be expensive when an application handles a large number of concurrent requests.

PgBouncer helps by:

- Reusing database connections
- Reducing connection establishment overhead
- Limiting the number of connections reaching PostgreSQL
- Managing connection queues
- Improving database connection efficiency
- Supporting high-concurrency applications

## Example Architecture

```text
                    +------------------+
                    |    Python App    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    SQLAlchemy    |
                    |       Pool       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    PgBouncer     |
                    | Connection Pool  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   PostgreSQL     |
                    +------------------+
```

## Learning Goals

The main goals of this project are to understand:

1. PostgreSQL connection management
2. Database connection pooling
3. PgBouncer architecture
4. PgBouncer pooling modes
5. SQLAlchemy connection pooling
6. Connection reuse
7. Database concurrency
8. Docker-based PostgreSQL environments
9. Performance implications of database connections

## Future Improvements

Possible improvements include:

- Add connection pool benchmarks
- Compare PgBouncer pooling modes
- Add PostgreSQL metrics
- Add connection monitoring
- Add Prometheus metrics
- Add Grafana dashboards
- Test high-concurrency workloads
- Add async PostgreSQL support
- Compare `psycopg` and SQLAlchemy pooling
- Add automated integration tests

## License

This project is licensed under the terms specified in the `LICENSE` file.