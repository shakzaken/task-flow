# Local Infrastructure Setup

This document explains how to run PostgreSQL, RabbitMQ, and Redis locally with Homebrew for this project.

The connection values used by the project live in the root `.env` file. Use `.env` as the source of truth if you change any host, port, user, password, or database values.

---

## Current Connection Values

From the root `.env`:

- PostgreSQL host: `localhost`
- PostgreSQL port: `5432`
- PostgreSQL database: `task_flow`
- PostgreSQL user: `yakir`
- PostgreSQL password: empty
- RabbitMQ URL: `amqp://guest:guest@localhost:5672/`
- Redis URL: `redis://localhost:6379/0`

---

## Start PostgreSQL With Brew

If you installed PostgreSQL with Homebrew, the exact formula name may be versioned, for example `postgresql@16`.

Check the installed service name:

```bash
brew services list
```

Start PostgreSQL:

```bash
brew services start <your-postgres-formula>
```

Examples:

```bash
brew services start postgresql@16
brew services start postgresql@15
```

Verify it is running:

```bash
brew services list
pg_isready -h localhost -p 5432
```

---

## Create The PostgreSQL User And Database

The root `.env` expects this database setup:

- database: `task_flow`
- user: `yakir`
- password: empty

One simple way to create them:

```bash
psql postgres
```

Then run:

```sql
CREATE DATABASE task_flow OWNER yakir;
```

Exit with:

```sql
\q
```

If you change these values, update the root `.env` file to match.

---

## Start RabbitMQ With Brew

Start RabbitMQ:

```bash
brew services start rabbitmq
```

Verify it is running:

```bash
brew services list
```

The current root `.env` expects:

- host: `localhost`
- port: `5672`
- username: `guest`
- password: `guest`

That matches the default local RabbitMQ setup in many Homebrew installs.

---

## Start Redis With Brew

Start Redis:

```bash
brew services start redis
```

Verify it is running:

```bash
brew services list
redis-cli ping
```

The current root `.env` expects:

- Redis URL: `redis://localhost:6379/0`
- host: `localhost`
- port: `6379`
- database: `0`

If `redis-cli ping` returns `PONG`, Redis is running and reachable on the expected local address.

---

## Stop Services

Stop PostgreSQL:

```bash
brew services stop <your-postgres-formula>
```

Stop RabbitMQ:

```bash
brew services stop rabbitmq
```

Stop Redis:

```bash
brew services stop redis
```

---

## Notes

- `api-service` and `worker-service` should both read their connection values from the root `.env`.
- Redis connection values should also come from the root `.env`.
- If you later move these services into separate Docker containers, keep the service-specific environment values aligned with the same connection contract.
- The shared file storage path is also configured in the root `.env` through `LOCAL_STORAGE_PATH`.
