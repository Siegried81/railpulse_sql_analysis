# SQL & DB Theory — RailPulse Study Guide

## 1. General Database Paradigms

### Q1. What's the difference between an SQL and a NoSQL database?

| | SQL (Relational) | NoSQL |
|---|---|---|
| Schema | Fixed, defined upfront (columns, types) | Flexible / schema-less |
| Data structure | Tables with rows and columns, linked by keys | Documents, key-value pairs, graphs, or wide columns |
| Consistency model | ACID transactions | Usually BASE (eventually consistent) |
| Relationships | Native support via JOINs and foreign keys | Usually denormalized; relationships handled in application code |
| Scaling | Mostly vertical (bigger server) | Mostly horizontal (more nodes) |
| Good for | Structured data with clear relationships, financial/transactional integrity | High-volume, flexible, or rapidly-changing data; specific access patterns |

Examples: PostgreSQL, MySQL, SQLite (SQL) vs. MongoDB (document), Redis (key-value), Cassandra (column), Neo4j (graph).

**RailPulse angle:** GTFS data (trips, routes, stops, stop_times, calendar) is inherently relational — a trip belongs to a route, has many stop_times, each pointing to a stop. That's exactly what SQL is built for, so a relational database was the right choice for this project.

### Q2. What other database engines exist, and how does SQLite compare?

| Engine type | Optimized for | Example |
|---|---|---|
| Graph | Traversing relationships/paths (friend-of-a-friend, shortest path) | Neo4j |
| Vector | Similarity search over embeddings (semantic search, RAG) | Pinecone, Weaviate |
| Time-Series | High-volume timestamped metrics, retention/downsampling | InfluxDB, TimescaleDB |
| Relational (SQLite) | Structured, transactional data on a single machine | SQLite |

**SQLite** is an *embedded* relational engine: the entire database lives in one file, there's no separate server process, and it's fully ACID-compliant. It's excellent for local analytics, prototypes, and single-user or low-concurrency applications — exactly the RailPulse use case. It's not designed to be a high-concurrency, multi-writer production backend the way PostgreSQL is.

### Q3. Why would 50 simultaneous scrapers break our SQLite setup, and what should we migrate to?

SQLite locks the *whole database file* for writes. In its default rollback-journal mode it allows any number of concurrent **readers**, but only **one writer at a time** — every other writer has to wait. Even in WAL (Write-Ahead Log) mode, which SQLite supports and which allows one writer to run concurrently with readers, there is still only ever a single writer.

With 50 scraper processes all trying to `INSERT` train departures at once:
- write locks queue up behind each other;
- many processes hit `database is locked` errors (SQLite retries briefly, then raises);
- overall throughput collapses because writes become effectively serial regardless of how much hardware is thrown at it.

**Migration target:** **PostgreSQL**. It uses MVCC (Multi-Version Concurrency Control), so many transactions can write concurrently without blocking each other on a single file lock, while still respecting ACID guarantees. It also runs as a proper client-server process built for concurrent access, unlike SQLite's single-file design.

---

## 2. Relational Schema & Data Modeling

### Q1. What is a data model?

A data model is the blueprint that translates a real-world domain into database structure. It defines:
- **entities** → tables (e.g. `trips`, `stops`, `routes`)
- **attributes** → columns (e.g. `trip_headsign`, `stop_lat`)
- **relationships** → how entities connect (via keys)
- **constraints** → rules that keep the data valid (NOT NULL, UNIQUE, FK)

It's the step between "what does the business need to track?" and the actual `CREATE TABLE` statements.

### Q2. One-to-one vs many-to-one vs many-to-many (Stations, Vehicles, Departures example)

- **One-to-one**: one `station` ↔ one `station_metadata` record extending it (e.g. accessibility details stored separately). Rare in practice — usually just merged into one table unless there's a good reason (optional data, security, huge column count) to split it.
- **Many-to-one**: many `departures` belong to one `station`. Each departure row has a `station_id` pointing to a single station, but a station has many departures.
  ```
  departures.station_id → stations.station_id
  ```
- **Many-to-many**: `vehicles` (trains) and `stations` — a single vehicle stops at many stations over its route, and a station is visited by many different vehicles over time. This needs a bridge/junction table to resolve, which in GTFS terms is exactly what `stop_times` does between `trips` and `stops`:
  ```
  trips ---- stop_times ---- stops
  ```

### Q3. What is normalization? Why does it matter, and is our project normalized?

Normalization is the process of structuring tables to eliminate redundant data and prevent update anomalies, typically by progressively applying normal forms:

- **1NF** — atomic values, no repeating groups (no comma-separated lists in a cell).
- **2NF** — every non-key column depends on the *whole* primary key (relevant for composite keys).
- **3NF** — no transitive dependencies (a non-key column shouldn't depend on another non-key column).

**Why it matters:** less duplicated data, fewer places for the same fact to go out of sync, cleaner inserts/updates/deletes, better integrity.

**Is RailPulse normalized?** Yes, close to 3NF. The GTFS static schema splits data into `agency`, `routes`, `trips`, `stops`, `stop_times`, `calendar`, `calendar_dates`, `transfers`, `feed_info`, and `translations` — each table owns one concept, and they're linked by foreign keys (`trips.route_id → routes.route_id`, `stop_times.trip_id → trips.trip_id`, `stop_times.stop_id → stops.stop_id`) rather than repeating route or stop details on every single stop_time row. This is inherited directly from the official GTFS spec, which is itself designed as a normalized relational model.

### Q4. Primary Key vs Foreign Key vs Unique Key — physical and logical difference

| | Primary Key | Foreign Key | Unique Key |
|---|---|---|---|
| **Logical role** | Uniquely identifies each row in *this* table | Points to a row in *another* table, enforcing referential integrity | Guarantees no duplicate values in a column, but doesn't identify the row |
| **Nullability** | Never NULL | Can be NULL (optional relationship) | Can be NULL (usually one NULL allowed, engine-dependent) |
| **Count per table** | Exactly one (can be composite) | Zero or more | Zero or more |
| **Physical implementation** | Automatically backed by a unique index | Not automatically indexed (should be indexed manually for join performance) | Backed by a unique index |

Example from the project: `trip_id` is the primary key of `trips`; `stop_times.trip_id` is a foreign key referencing it; a route's `route_short_name` could be enforced as unique even though `route_id` remains the actual primary key.

---

## 3. Analytical Modeling & Architecture

### Q1. Fact table vs. dimension table — where does `departures`/`stop_times` fall?

- **Fact table**: stores *events* or *measurements* — usually high-volume, numeric, timestamped, and mostly made of foreign keys pointing to dimensions (little descriptive text of its own).
- **Dimension table**: stores *descriptive context* used to slice and filter the facts — names, categories, calendars.

| Table | Role |
|---|---|
| `stop_times` / `departures` | **Fact table** — one row per (trip, stop) event: arrival/departure time, sequence |
| `stops`, `routes`, `agency`, `calendar` | **Dimension tables** — describe *where*, *which line*, *which operator*, *which service days* |

If RailPulse were rebuilt as a data warehouse, `stop_times` would be the fact table at the center, surrounded by `stops`, `routes`, `trips`, and `calendar` as dimensions.

### Q2. Star Schema vs Snowflake Schema

- **Star schema**: one fact table connected directly to *denormalized* dimension tables (a dimension might repeat data instead of splitting further). Fewer joins → faster, simpler queries for BI tools.
- **Snowflake schema**: dimensions are further normalized into sub-dimensions (e.g. `routes` → `agency` as a separate table rather than repeating agency name in `routes`). Less redundancy and smaller storage, but more joins to reach the final answer.

**Trade-off:** star schema favors query speed and simplicity (good for analysts and dashboards); snowflake schema favors storage efficiency and structural cleanliness (closer to a fully normalized OLTP design). RailPulse's GTFS schema is essentially snowflaked already, since `routes` references `agency` rather than embedding the operator's name directly.

---

## 4. Theoretical Frameworks & Guardrails

### Q1. The ACID framework — with a RailPulse ingestion failure example

- **Atomicity** — a transaction is all-or-nothing; if any statement fails, the whole transaction rolls back.
- **Consistency** — a transaction can only bring the database from one valid state to another (constraints, foreign keys, types are always respected).
- **Isolation** — concurrent transactions don't see each other's uncommitted changes.
- **Durability** — once a transaction commits, it survives a crash or power loss.

**RailPulse example:** `main.py`'s GTFS ingestion inserts a trip into `trips` and then all of its related rows into `stop_times`. If the process crashes halfway through inserting `stop_times` for that trip (e.g. malformed row in the CSV), wrapping the insert in a transaction means **atomicity** rolls the whole trip's insert back — we end up with either a complete trip + all its stop_times, or nothing at all, never an orphaned trip with half its stops missing.

### Q2. The CAP theorem — and the iRail outage scenario

CAP theorem states a distributed system can only guarantee two of the following three at once, in the presence of a network partition:
- **Consistency** — every read returns the most recent write.
- **Availability** — every request gets a (non-error) response.
- **Partition tolerance** — the system keeps working despite network failures between nodes.

SQLite itself is a single-file, non-distributed database, so CAP doesn't apply to it directly — it always gives a consistent, available answer as long as the local machine is up, because there's no network partition to worry about. CAP becomes relevant at the **ingestion layer**, when the pipeline talks to the external iRail API over the network:

- If the iRail API goes offline mid-scrape, the pipeline has to choose:
  - **Favor Consistency**: stop and reject new inserts until a full, fresh liveboard is available again — avoid writing partial/stale data.
  - **Favor Availability**: keep serving the last known departures (cached/stale data) instead of erroring out, accepting that the info might be outdated.

RailPulse's `live_ingest.py` effectively favors availability-of-history: it appends whatever snapshot it *can* get and simply skips a pull if the API is unreachable, rather than blocking the whole pipeline.

---

## 5. Database Objects & Query Mechanisms

### Q1. View vs Window Function vs Subquery — when to use which

- **View**: a named, saved query that behaves like a virtual table. Use it to reuse a complex query in multiple places, simplify access for other users, or hide underlying table structure.
  ```sql
  CREATE VIEW busiest_routes AS
  SELECT route_id, COUNT(*) AS trip_count
  FROM trips
  GROUP BY route_id;
  ```
- **Window function**: performs a calculation across a set of rows *related to the current row*, without collapsing them into a single output row (unlike GROUP BY). Use it for rankings, running totals, or "latest per group" queries.
  ```sql
  SELECT trip_id, stop_id, departure_time,
         ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY stop_sequence) AS rn
  FROM stop_times;
  ```
- **Subquery**: a query nested inside another (in `SELECT`, `FROM`, or `WHERE`). Use it for one-off filtering or intermediate aggregation that doesn't need to be reused or named.

**Rule of thumb:** reusable logic → View; need per-row context alongside aggregation → Window function; quick one-off nested logic → Subquery.

### Q2. Index Scan vs Index Seek — which is faster and why?

| | Index Seek | Index Scan |
|---|---|---|
| What it does | Jumps directly to the matching rows using the index's B-tree structure | Reads through a large portion (or all) of the index sequentially |
| When it happens | Highly selective predicate (e.g. `WHERE trip_id = 'X'` on an indexed column) | Low-selectivity predicate, or the predicate can't use the index efficiently |
| Cost | Low — touches only the relevant pages | Higher — touches many/most pages |

**Seek is faster** because it uses the index's tree structure to jump straight to the matching range instead of walking through every entry.

### Q3. What is a "SARGable" violation, and why does `WHERE strftime('%Y', scheduled_time) = '2026'` hurt performance?

"SARGable" = **S**earch **ARG**ument **Able** — a predicate is SARGable if the query optimizer can use an index to evaluate it directly, without having to process every row first.

Wrapping an indexed column in a function breaks this: the database can't know the function's output for a row without first *computing* it, so it has to evaluate the function on every single row (a full scan) before it can filter — the index on `scheduled_time` becomes useless.

```sql
-- Not SARGable: forces a full scan, index on scheduled_time is ignored
WHERE strftime('%Y', scheduled_time) = '2026'

-- SARGable: a plain range comparison on the raw column, index can be used
WHERE scheduled_time >= '2026-01-01' AND scheduled_time < '2027-01-01'
```

This is exactly what RailPulse's index optimization work demonstrated: `01_peak_hour.sql` originally wrapped `departure_time` in `CAST`/`SUBSTR`, defeating a plain index on that column. Only an **expression index** built on the same `SUBSTR(departure_time, 1, 2)` expression restored SARGability and eliminated the temporary B-tree the query planner was building for the `GROUP BY`.

---

## 6. Advanced Query Optimization & Performance Tuning

### The problem query

```sql
FROM orders
JOIN (
  SELECT customer_id, MAX(date)
  FROM logs
  GROUP BY customer_id
) AS sub
  ON orders.customer_id = sub.customer_id
```

**Why this can hurt performance:**
- The subquery scans and aggregates the *entire* `logs` table before the join can even start — there's no way to push the `orders` filter down into it.
- The database has to materialize this whole aggregated result (in memory, or spilled to disk if it's large) before joining.
- Grouping by `customer_id` typically requires a sort or hash step, which is memory- and CPU-intensive on a large `logs` table.
- If this pattern is repeated across several queries, the same expensive aggregation gets recomputed every time.

**Optimized alternatives:**

**1. Window function** — avoids the separate aggregated derived table entirely, letting the optimizer potentially use an index and process rows in one pass:
```sql
WITH ranked_logs AS (
  SELECT customer_id, date,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY date DESC) AS rn
  FROM logs
)
SELECT o.*, rl.date AS latest_log_date
FROM orders o
JOIN ranked_logs rl
  ON o.customer_id = rl.customer_id
WHERE rl.rn = 1;
```

**2. Temporary/materialized table** — if this "latest log per customer" result is reused by several downstream queries, compute it once, index it, and join against it repeatedly instead of recalculating it every time.

**3. Supporting index** — add a composite index on `logs(customer_id, date DESC)` so the database can seek the latest row per customer directly instead of scanning and sorting.
