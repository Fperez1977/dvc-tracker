import sqlite3

DB = "dvc_tracker.db"

def ensure_column(con, table, column, definition):
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

con = sqlite3.connect(DB)

# Make this seed script self-contained by ensuring the v2.6 stay fields exist.
ensure_column(con, "stays", "room_type", "TEXT")
ensure_column(con, "stays", "actual_dvc_checkout", "TEXT")
ensure_column(con, "stays", "unused_nights", "INTEGER NOT NULL DEFAULT 0")
ensure_column(con, "stays", "alternate_lodging", "TEXT")
ensure_column(con, "stays", "alternate_lodging_cost", "REAL NOT NULL DEFAULT 0")
ensure_column(con, "stays", "realized_room_value", "REAL")
ensure_column(con, "stays", "rate_source", "TEXT")
con.commit()

cur = con.cursor()

contract = cur.execute("SELECT id FROM contracts ORDER BY id LIMIT 1").fetchone()
if not contract:
    print("Add your DVC contract first, then run this seed script.")
    con.close()
    raise SystemExit(1)

cid = contract[0]

def exists(trip, checkin):
    return cur.execute(
        "SELECT 1 FROM stays WHERE trip_name=? AND check_in=?",
        (trip, checkin)
    ).fetchone()

# Old Key West: 3/31/26-4/3/26 reserved.
# DVC nights actually used: 3/31 and 4/1.
# Night of 4/2 was replaced by a free Marriott room.
if not exists("Old Key West — Spring 2026", "2026-03-31"):
    cur.execute("""
        INSERT INTO stays(
            contract_id,trip_name,check_in,check_out,resort,points_used,
            cash_room_value,notes,room_type,actual_dvc_checkout,unused_nights,
            alternate_lodging,alternate_lodging_cost,realized_room_value,rate_source
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        cid,
        "Old Key West — Spring 2026",
        "2026-03-31",
        "2026-04-03",
        "Disney's Old Key West Resort",
        0,
        2244.0,
        "Reserved 3 nights. Night of 4/2 was not used; stayed at a Marriott for free.",
        "Deluxe Studio",
        "2026-04-02",
        1,
        "Marriott",
        0.0,
        1496.0,
        "TouringPlans 2026 historical rack rates ($748/night); seeded by tracker v2.6.1"
    ))
    print("Added Old Key West historical stay.")
else:
    print("Old Key West historical stay already exists; skipped.")

# Kidani Village: 8/7/26-8/10/26, Deluxe Studio - Savanna View.
# Exact nightly rack values are deliberately left at $0 pending verification.
if not exists("Kidani Village — August 2026", "2026-08-07"):
    cur.execute("""
        INSERT INTO stays(
            contract_id,trip_name,check_in,check_out,resort,points_used,
            cash_room_value,notes,room_type,actual_dvc_checkout,unused_nights,
            alternate_lodging,alternate_lodging_cost,realized_room_value,rate_source
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        cid,
        "Kidani Village — August 2026",
        "2026-08-07",
        "2026-08-10",
        "Disney's Animal Kingdom Villas - Kidani Village",
        0,
        0.0,
        "Historical stay; exact nightly rack value still needs verification.",
        "Deluxe Studio - Savanna View",
        "2026-08-10",
        0,
        "",
        0.0,
        0.0,
        "TouringPlans 2026 historical rack rates — exact Aug 7-9 values pending verification"
    ))
    print("Added Kidani historical stay.")
else:
    print("Kidani historical stay already exists; skipped.")

con.commit()
con.close()
print("Done.")
