import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
from io import StringIO
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

DB = "dvc_tracker.db"

APP_VERSION = "3.7"

st.set_page_config(page_title="DVC True Cost Tracker", page_icon="✨", layout="wide")

# ---------------------------------------------------------
# Over-the-top Disney-vacation-inspired visual theme
# ---------------------------------------------------------
st.markdown(
    """
    <style>

    /* v2.14.1 — hide Streamlit developer/deploy chrome */
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stAppDeployButton"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* Remove the space normally reserved for Streamlit's header */
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 0.6rem !important;
    }

    :root {
      --night:#031229;
      --royal:#082d59;
      --blue:#0b4f8a;
      --sky:#dff3ff;
      --gold:#ffd65c;
      --cream:#fff8df;
      --ink:#12304f;
      --text:#12304f;
      --muted:#55708d;
    }

    /* Chrome compatibility: force the app to use the intended light palette.
       Streamlit can inherit a dark text token in Chrome even when the page
       background is light. Explicitly set the common Streamlit text surfaces. */
    html { color-scheme: light !important; }
    body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] * {
      color-scheme: light;
    }
    .stApp, .stApp p, .stApp li, .stApp label,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] li,
    .stApp [data-testid="stMarkdownContainer"] strong,
    .stApp [data-testid="stCaptionContainer"] {
      color:#12304f;
    }
    .stApp [data-testid="stMarkdownContainer"] h1,
    .stApp [data-testid="stMarkdownContainer"] h2,
    .stApp [data-testid="stMarkdownContainer"] h3,
    .stApp [data-testid="stMarkdownContainer"] h4 {
      color:#083f70 !important;
    }
    .stApp input, .stApp textarea, .stApp select {
      color:#12304f !important;
      background:#ffffff !important;
    }
    .stApp [data-baseweb="select"] *,
    .stApp [data-baseweb="input"] * {
      color:#12304f;
    }
    /* Preserve the dark hero and its light text. */
    .dvc-hero, .dvc-hero * { color:white; }
    .dvc-hero .eyebrow { color:var(--gold); }
    .dvc-hero .tagline { color:#e7f5ff; }
    .welcome-pill { color:#13345a; }
    /* Preserve dark tab text/backgrounds. */
    .stTabs [data-baseweb="tab"] { color:#e8f4ff !important; }
    .stTabs [aria-selected="true"] { color:#092e55 !important; }

    html, body, [data-testid="stAppViewContainer"] {
      background:#edf6ff;
      color:#12304f !important;
    }

    .stApp {
      background:
        radial-gradient(circle at 11% 4%, rgba(255,222,105,.30), transparent 11rem),
        radial-gradient(circle at 91% 7%, rgba(70,163,255,.28), transparent 16rem),
        linear-gradient(180deg, #021127 0px, #062a54 300px, #eaf6ff 300px, #f8fbff 100%);
    }

    .block-container {
      max-width: 1480px;
      padding-top: 1rem;
      padding-bottom: 4rem;
    }

    /* Giant vacation-magic hero */
    .dvc-hero {
      position:relative;
      overflow:hidden;
      min-height:190px;
      padding:34px 38px;
      margin:0 0 18px 0;
      border-radius:32px;
      border:2px solid rgba(255,214,92,.78);
      color:white;
      background:
        radial-gradient(circle at 18% 15%, rgba(255,217,92,.22), transparent 8rem),
        radial-gradient(circle at 76% 3%, rgba(89,177,255,.29), transparent 13rem),
        linear-gradient(128deg,#03142c 0%,#073b6c 58%,#0a568d 100%);
      box-shadow:0 22px 52px rgba(0,20,47,.34);
    }

    .dvc-hero .eyebrow {
      color:var(--gold);
      font-size:.8rem;
      font-weight:900;
      letter-spacing:.18em;
      text-transform:uppercase;
      margin-bottom:3px;
    }

    .dvc-hero h1 {
      color:white !important;
      margin:0;
      font-size:3rem;
      line-height:1.05;
      letter-spacing:.01em;
      text-shadow:0 3px 18px rgba(0,0,0,.38);
    }

    .dvc-hero .tagline {
      color:#e7f5ff;
      font-size:1.08rem;
      margin-top:9px;
      max-width:830px;
    }

    .welcome-pill {
      display:inline-block;
      margin-top:15px;
      margin-right:7px;
      padding:7px 13px;
      border-radius:999px;
      font-size:.8rem;
      font-weight:900;
      color:#13345a;
      background:linear-gradient(180deg,#ffe788,#ffd04f);
      box-shadow:0 4px 12px rgba(0,0,0,.16);
    }

    /* Decorative mouse-ear silhouettes */
    .mouse-mark {
      position:absolute;
      right:55px;
      top:31px;
      width:138px;
      height:112px;
      opacity:.32;
      filter:drop-shadow(0 7px 12px rgba(0,0,0,.22));
    }
    .mouse-mark .head {
      position:absolute;
      width:78px;height:78px;
      left:30px;top:30px;
      border-radius:50%;
      background:var(--gold);
    }
    .mouse-mark .ear {
      position:absolute;
      width:57px;height:57px;
      top:0;border-radius:50%;
      background:var(--gold);
    }
    .mouse-mark .left { left:0; }
    .mouse-mark .right { right:0; }

    /* Firework/sparkle field */
    .spark-field {
      position:absolute;
      inset:0;
      pointer-events:none;
      opacity:.65;
    }
    .spark-field:before {
      content:"✦  ✧      ✦       ✧    ✦       ✧        ✦     ✧";
      position:absolute;
      left:41%;
      top:18px;
      color:#fff1a8;
      font-size:20px;
      letter-spacing:18px;
      transform:rotate(-7deg);
    }
    .spark-field:after {
      content:"✧        ✦    ✧          ✦      ✧";
      position:absolute;
      left:32%;
      bottom:23px;
      color:white;
      font-size:13px;
      letter-spacing:20px;
      transform:rotate(4deg);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
      gap:8px;
      padding:7px;
      border-radius:22px;
      background:rgba(4,33,67,.86);
      border:1px solid rgba(255,214,92,.26);
      box-shadow:0 8px 22px rgba(0,20,45,.15);
    }
    .stTabs [data-baseweb="tab"] {
      border-radius:15px;
      padding:10px 17px;
      color:#e8f4ff;
      font-weight:800;
      background:rgba(255,255,255,.06);
    }
    .stTabs [aria-selected="true"] {
      color:#092e55 !important;
      background:linear-gradient(180deg,#ffe990,#ffd45a) !important;
    }

    /* Cards */
    [data-testid="stMetric"] {
      border-radius:22px;
      padding:18px;
      border:1px solid rgba(12,72,124,.16);
      background:
        radial-gradient(circle at 92% 10%, rgba(255,218,91,.15), transparent 5rem),
        linear-gradient(145deg,#ffffff,#edf7ff);
      box-shadow:0 9px 25px rgba(7,45,84,.09);
    }
    [data-testid="stMetricLabel"] {
      color:#55708d;
      font-weight:800;
    }
    [data-testid="stMetricValue"] {
      color:#073c6d;
      font-weight:900;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
      border-radius:22px !important;
      border:1px solid rgba(13,76,132,.16) !important;
      background:
        radial-gradient(circle at 98% 5%, rgba(255,213,87,.12), transparent 5rem),
        rgba(255,255,255,.96) !important;
      box-shadow:0 9px 24px rgba(8,46,83,.075);
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
      border-radius:999px !important;
      border:1px solid #9fc1e1 !important;
      font-weight:900 !important;
      background:linear-gradient(180deg,#ffffff,#eaf5ff) !important;
      color:#0b4475 !important;
      box-shadow:0 5px 14px rgba(11,61,107,.10);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
      border-color:#d4ac36 !important;
      box-shadow:0 7px 18px rgba(11,61,107,.16);
    }

    /* Form controls */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    textarea {
      border-radius:14px !important;
    }

    h1,h2,h3 {
      letter-spacing:.01em;
    }
    h2,h3 {
      color:#083f70;
    }

    .magic-divider {
      height:2px;
      border:0;
      background:linear-gradient(90deg,transparent,#e4bb42,#fff2a5,#e4bb42,transparent);
      margin:14px 0 20px;
    }

    .castle-strip {
      text-align:center;
      color:#1b5a8d;
      font-size:1rem;
      font-weight:800;
      margin:-3px 0 12px;
      letter-spacing:.12em;
    }
    </style>

    <div class="dvc-hero">
      <div class="spark-field"></div>
      <div class="mouse-mark">
        <div class="ear left"></div>
        <div class="ear right"></div>
        <div class="head"></div>
      </div>
      <div class="eyebrow">Disney Vacation Club • True Cost & Value</div>
      <h1>✨ My DVC Adventure ✨</h1>
      <div class="tagline">
        🏰 Welcome Home — track every point, every stay, every dollar of value,
        and just how much vacation magic your membership is really creating.
      </div>
      <span class="welcome-pill">🏰 Welcome Home</span>
      <span class="welcome-pill">✨ Point Magic</span>
      <span class="welcome-pill">🎆 Lifetime Value</span>
      <span class="welcome-pill">🏨 Resort Memories</span>
    </div>
    <div class="castle-strip">✦  🏰  ✦  •  ✦  🏨  ✦  •  ✦  🎆  ✦  •  ✦  🏰  ✦</div>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# DB helpers and migrations
# -------------------------
def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)


def table_columns(con, table):
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}


def ensure_column(con, table, name, ddl):
    if name not in table_columns(con, table):
        con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db():
    con = get_conn()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resort TEXT,
            purchase_date TEXT,
            points INTEGER,
            purchase_price REAL NOT NULL DEFAULT 0,
            closing_costs REAL NOT NULL DEFAULT 0,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS dues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY(contract_id) REFERENCES contracts(id)
        );
        CREATE TABLE IF NOT EXISTS stays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            trip_name TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            resort TEXT,
            points_used REAL NOT NULL DEFAULT 0,
            cash_room_value REAL NOT NULL DEFAULT 0,
            notes TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id)
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stay_id INTEGER,
            expense_date TEXT,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            attribution_pct REAL NOT NULL DEFAULT 100,
            notes TEXT,
            FOREIGN KEY(stay_id) REFERENCES stays(id)
        );
        """
    )
    ensure_column(con, "dues", "is_prorated", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(con, "dues", "prorated_amount", "REAL")
    ensure_column(con, "dues", "proration_note", "TEXT")
    ensure_column(con, "contracts", "contract_end_date", "TEXT")
    ensure_column(con, "dues", "published_amount", "REAL")
    ensure_column(con, "dues", "actual_cost", "REAL")
    ensure_column(con, "dues", "gift_card_used", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(con, "contracts", "contract_number", "TEXT")
    ensure_column(con, "contracts", "use_year", "TEXT")
    ensure_column(con, "contracts", "purchase_incentives", "REAL NOT NULL DEFAULT 0")
    ensure_column(con, "contracts", "magical_beginnings", "REAL NOT NULL DEFAULT 0")
    ensure_column(con, "contracts", "agreement_file", "TEXT")
    ensure_column(con, "contracts", "agreement_filename", "TEXT")
    ensure_column(con, "stays", "actual_dvc_checkout", "TEXT")
    ensure_column(con, "stays", "unused_nights", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(con, "stays", "alternate_lodging", "TEXT")
    ensure_column(con, "stays", "alternate_lodging_cost", "REAL NOT NULL DEFAULT 0")
    ensure_column(con, "stays", "realized_room_value", "REAL")
    ensure_column(con, "stays", "rate_source", "TEXT")
    ensure_column(con, "stays", "room_type", "TEXT")
    ensure_column(con, "stays", "rack_rate_total", "REAL NOT NULL DEFAULT 0")
    ensure_column(con, "stays", "rack_rate_source", "TEXT")
    ensure_column(con, "stays", "rack_rate_retrieved_at", "TEXT")
    ensure_column(con, "stays", "realistic_alt_cost", "REAL NOT NULL DEFAULT 0")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projection_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        dues_growth REAL NOT NULL DEFAULT 4.5,
        room_growth REAL NOT NULL DEFAULT 4.0,
        gift_card_discount REAL NOT NULL DEFAULT 5.0,
        annual_room_value REAL NOT NULL DEFAULT 0,
        projection_end_year INTEGER NOT NULL DEFAULT 2050,
        investment_return REAL NOT NULL DEFAULT 6.0,
        cash_discount REAL NOT NULL DEFAULT 15.0,
        dvc_rental_rate REAL NOT NULL DEFAULT 22.0,
        rental_growth REAL NOT NULL DEFAULT 3.0
    )
    """)
    cur.execute("""
    INSERT OR IGNORE INTO projection_settings
    (id, dues_growth, room_growth, gift_card_discount, annual_room_value, projection_end_year)
    VALUES (1, 4.5, 4.0, 5.0, 0, 2050)
    """)
    # v2.10 accounting model: the full DVC reservation rack value is counted as DVC value earned.
    # Alternate lodging is no longer part of the model.
    con.execute("""
        UPDATE stays
        SET realized_room_value = cash_room_value,
            alternate_lodging = '',
            alternate_lodging_cost = 0
    """)
    con.commit()
    con.close()


def query(sql, params=()):
    con = get_conn()
    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df


def execute(sql, params=()):
    con = get_conn()
    con.execute(sql, params)
    con.commit()
    con.close()


init_db()

# v2.15 — Value Resort projection assumption
try:
    execute("ALTER TABLE projection_settings ADD COLUMN value_resort_ratio REAL NOT NULL DEFAULT 0.35")
except Exception:
    pass

# v2.12 — Value Resort comparison fields
for _col, _typ in [("value_resort_benchmark","TEXT"),("value_resort_value","REAL")]:
    try:
        execute(f"ALTER TABLE stays ADD COLUMN {_col} {_typ}")
    except Exception:
        pass

# v3 financial/points model fields
for _col, _typ, _default in [
    ("cash_discount_pct","REAL","0"),
    ("discounted_cash_value","REAL","0"),
    ("rental_rate","REAL","0"),
    ("rental_cost","REAL","0"),
]:
    try:
        execute(f"ALTER TABLE stays ADD COLUMN {_col} {_typ} NOT NULL DEFAULT {_default}")
    except Exception:
        pass

# Annual point-flow ledger: makes banking, borrowing, utilization and expirations explicit.
execute("""CREATE TABLE IF NOT EXISTS point_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    use_year INTEGER NOT NULL,
    annual_points REAL NOT NULL DEFAULT 0,
    banked_points REAL NOT NULL DEFAULT 0,
    borrowed_points REAL NOT NULL DEFAULT 0,
    used_points REAL NOT NULL DEFAULT 0,
    expired_points REAL NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
)""")
# Migrate point-ledger columns using the DB helper (the init_db connection is already closed here).
try:
    execute("ALTER TABLE point_ledger ADD COLUMN banked_in REAL NOT NULL DEFAULT 0")
except Exception:
    pass
try:
    execute("ALTER TABLE point_ledger ADD COLUMN borrowed_out REAL NOT NULL DEFAULT 0")
except Exception:
    pass

# v3.7 — automatic point-source allocation for stays.
for _col, _typ, _default in [
    ("point_source", "TEXT", "'Auto'"),
    ("point_source_year", "INTEGER", "NULL"),
]:
    try:
        execute(f"ALTER TABLE stays ADD COLUMN {_col} {_typ} NOT NULL DEFAULT {_default}" if _default != "NULL" else f"ALTER TABLE stays ADD COLUMN {_col} {_typ}")
    except Exception:
        pass

execute("""CREATE TABLE IF NOT EXISTS stay_point_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stay_id INTEGER NOT NULL,
    contract_id INTEGER NOT NULL,
    source_use_year INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    points REAL NOT NULL DEFAULT 0,
    FOREIGN KEY(stay_id) REFERENCES stays(id),
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
)""")

execute("""CREATE TABLE IF NOT EXISTS historical_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resort TEXT NOT NULL,
    year INTEGER NOT NULL,
    dues_per_point REAL,
    room_rate_growth REAL,
    source TEXT,
    UNIQUE(resort, year)
)""")

# Source-backed historical dues for Polynesian (PVB), 2015-2026. These are used
# as a reference only; actual dues entered by the owner always take precedence.
_pvb_history = {
    2015: 6.02, 2016: 6.09, 2017: 6.14, 2018: 6.20, 2019: 6.76,
    2020: 6.79, 2021: 7.05, 2022: 7.39, 2023: 7.95, 2024: 8.23,
    2025: 7.93, 2026: 8.33,
}
con = get_conn()
for _y, _v in _pvb_history.items():
    con.execute("INSERT OR IGNORE INTO historical_benchmarks(resort,year,dues_per_point,source) VALUES(?,?,?,?)",
                ("Disney's Polynesian Villas & Bungalows", _y, _v, "DVCNews historical annual dues"))
con.commit(); con.close()


for _col, _typ, _default in [("investment_return","REAL","6.0"),("cash_discount","REAL","15.0"),("dvc_rental_rate","REAL","22.0"),("rental_growth","REAL","3.0")]:
    try:
        execute(f"ALTER TABLE projection_settings ADD COLUMN {_col} {_typ} NOT NULL DEFAULT {_default}")
    except Exception:
        pass

# -------------------------
# Rack-rate lookup
# -------------------------
TOURINGPLANS_RESORTS = {
    "Animal Kingdom Villas – Kidani Village": "disneys-animal-kingdom-villas",
    "Animal Kingdom Villas – Jambo House": "animal-kingdom-villas-jambo",
    "Bay Lake Tower": "bay-lake-tower-at-disneys-contemporary-resort",
    "Beach Club Villas": "disneys-beach-club-villas",
    "BoardWalk Villas": "disneys-boardwalk-villas",
    "Boulder Ridge Villas": "villas-at-disneys-wilderness-lodge",
    "Copper Creek Villas & Cabins": "copper-creek-villas-and-cabins",
    "Grand Floridian Villas": "the-villas-at-disneys-grand-floridian-resort-and-spa",
    "Old Key West Resort": "disneys-old-key-west-resort",
    "Polynesian Villas & Bungalows": "disneys-polynesian-villas-bungalows",
    "Riviera Resort": "disneys-riviera-resort",
    "Saratoga Springs Resort & Spa": "disneys-saratoga-springs-resort-spa",
}


def money_to_float(v):
    if pd.isna(v):
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", str(v).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


def fetch_rate_table(resort_name, year):
    slug = TOURINGPLANS_RESORTS[resort_name]
    url = f"https://touringplans.com/walt-disney-world/hotels/{slug}/rates/{year}"
    headers = {"User-Agent": "Mozilla/5.0 DVCTrueCostTracker/2.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    tables = pd.read_html(StringIO(r.text))
    # Pick the largest table containing a Date column.
    candidates = []
    for t in tables:
        cols = [str(c) for c in t.columns]
        if any("Date" in c for c in cols) and len(t) > 20:
            candidates.append(t)
    if not candidates:
        raise ValueError("Could not find a usable daily rate table on the source page.")
    table = max(candidates, key=lambda x: x.shape[0] * x.shape[1])
    if isinstance(table.columns, pd.MultiIndex):
        table.columns = [" - ".join([str(x) for x in c if str(x) != "nan"]).strip(" -") for c in table.columns]
    else:
        table.columns = [str(c) for c in table.columns]
    return url, table


def detect_date_col(table):
    for c in table.columns:
        if "date" in c.lower():
            return c
    return table.columns[0]


def room_columns(table):
    date_col = detect_date_col(table)
    skip = {date_col}
    return [c for c in table.columns if c not in skip and "day" not in c.lower()]


def normalize_table_dates(table, year):
    df = table.copy()
    date_col = detect_date_col(df)
    dates = []
    current_month = None
    for raw in df[date_col].astype(str):
        s = raw.strip()
        # Common TouringPlans rows are "Aug 1" or occasionally full date-like text.
        parsed = pd.to_datetime(f"{s} {year}", errors="coerce")
        if pd.isna(parsed):
            parsed = pd.to_datetime(s, errors="coerce")
            if not pd.isna(parsed):
                parsed = parsed.replace(year=year)
        dates.append(parsed.date() if not pd.isna(parsed) else None)
    df["_date"] = dates
    return df


def lookup_rack_rate(resort_name, room_type, check_in, check_out):
    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")
    nightly = []
    cur = check_in
    cache = {}
    while cur < check_out:
        if cur.year not in cache:
            url, table = fetch_rate_table(resort_name, cur.year)
            cache[cur.year] = (url, normalize_table_dates(table, cur.year))
        url, df = cache[cur.year]
        if room_type not in df.columns:
            raise ValueError(f"Room type '{room_type}' was not found for {cur.year}.")
        row = df[df["_date"] == cur]
        if row.empty:
            raise ValueError(f"No rack rate found for {cur.strftime('%b %d, %Y')}.")
        value = money_to_float(row.iloc[0][room_type])
        if value is None:
            raise ValueError(f"No numeric rate found for {cur.strftime('%b %d, %Y')}.")
        nightly.append({"date": cur, "rate": value})
        cur += timedelta(days=1)
    return nightly, cache[check_in.year][0]


# -------------------------
# Dashboard calculations
# -------------------------
def table_exists(table):
    con = get_conn()
    exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    con.close()
    return exists


def _use_year_start_month(use_year_name):
    months = {"January": 1, "February": 2, "March": 3, "April": 4, "June": 6, "August": 8, "September": 9, "October": 10, "December": 12}
    return months.get(str(use_year_name or "June"), 6)

def _dvc_use_year(check_in, use_year_name):
    dt = pd.to_datetime(check_in, errors="coerce")
    if pd.isna(dt):
        return None
    month = _use_year_start_month(use_year_name)
    return int(dt.year if dt.month >= month else dt.year - 1)

def _contract_point_start_year(crow):
    """First use year with points actually available to the owner.

    Magical Beginnings contracts begin the following calendar/use year in this
    tracker because the initial year's points were surrendered for the benefit.
    Otherwise the purchase year is the first eligible year.
    """
    purchase = pd.to_datetime(crow.get("purchase_date"), errors="coerce")
    if pd.isna(purchase):
        return None
    start = int(purchase.year)
    if float(crow.get("magical_beginnings") or 0) > 0:
        start += 1
    return start


def _stay_point_use_year(stay, crow):
    return _dvc_use_year(stay.get("check_in"), crow.get("use_year"))


def sync_point_ledger():
    """Build the point schedule from contracts and automatically allocate stays.

    The user does not enter annual points or used points.  Annual entitlement
    comes from the contract, the first eligible year respects Magical
    Beginnings, and stay points are allocated automatically.  Allocation uses
    banked points first, then the current use-year allocation, then future-year
    points (borrowing).  A stay can override this only when the owner explicitly
    chooses a source in the stay editor.
    """
    contracts = query("SELECT * FROM contracts")
    if contracts.empty:
        return

    existing = query("SELECT * FROM point_ledger")
    existing_map = {(int(r["contract_id"]), int(r["use_year"])): r for _, r in existing.iterrows()} if not existing.empty else {}

    # Create/update only years in which the contract actually has points.
    for _, c in contracts.iterrows():
        cid = int(c["id"])
        pts = float(c["points"] or 0)
        start_year = _contract_point_start_year(c)
        if start_year is None:
            continue
        end = pd.to_datetime(c.get("contract_end_date"), errors="coerce")
        end_year = int(end.year) if pd.notna(end) else max(date.today().year, start_year)
        for uy in range(start_year, end_year + 1):
            old = existing_map.get((cid, uy))
            if old is None:
                execute("""INSERT INTO point_ledger(
                    contract_id,use_year,annual_points,banked_points,borrowed_points,
                    used_points,expired_points,notes,banked_in,borrowed_out
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""", (cid, uy, pts, 0.0, 0.0, 0.0, 0.0, "", 0.0, 0.0))
            else:
                execute("UPDATE point_ledger SET annual_points=? WHERE id=?", (pts, int(old["id"])))

    # Remove stale rows from acquisition years that never had points (notably
    # a Magical Beginnings purchase year). This prevents phantom 2025 points.
    rows = query("SELECT id,contract_id,use_year FROM point_ledger")
    for _, r in rows.iterrows():
        crow_df = contracts[contracts["id"] == int(r["contract_id"])]
        if crow_df.empty:
            continue
        start_year = _contract_point_start_year(crow_df.iloc[0])
        if start_year is not None and int(r["use_year"]) < start_year:
            execute("DELETE FROM point_ledger WHERE id=?", (int(r["id"]),))

    # Rebuild stay allocations from scratch.  Manual bank/borrow/expire values
    # remain on the annual ledger; stay usage itself is always derived here.
    execute("DELETE FROM stay_point_allocations")
    execute("UPDATE point_ledger SET used_points=0, borrowed_out=0, banked_in=0")

    stays = query("SELECT * FROM stays ORDER BY check_in, id")
    if stays.empty:
        # Banked-in is deterministic from the prior year's banked-out entry.
        _sync_bank_flow_only()
        return

    # Track remaining points by source use year.  The banked amount is a
    # transfer into the following year; borrowed amounts are consumed by stays.
    led = query("SELECT * FROM point_ledger ORDER BY contract_id,use_year")
    for _, c in contracts.iterrows():
        cid = int(c["id"])
        cled = led[led["contract_id"] == cid].copy()
        if cled.empty:
            continue

        # Deterministic banked-in flow.
        for _, r in cled.iterrows():
            uy = int(r["use_year"])
            prev = cled[cled["use_year"] == uy - 1]
            banked_in = float(prev.iloc[0]["banked_points"] or 0) if not prev.empty else 0.0
            execute("UPDATE point_ledger SET banked_in=? WHERE id=?", (banked_in, int(r["id"])))

        # Source balances after explicit owner adjustments.
        balances = {}
        for _, r in cled.iterrows():
            uy = int(r["use_year"])
            annual = float(r["annual_points"] or 0)
            banked_in = float(r["banked_in"] or 0)
            banked_out = float(r["banked_points"] or 0)
            expired = float(r["expired_points"] or 0)
            balances[uy] = max(0.0, annual + banked_in - banked_out - expired)

        cstays = stays[stays["contract_id"] == cid]
        for _, stay in cstays.iterrows():
            requested = max(0.0, float(stay["points_used"] or 0))
            if requested <= 0:
                continue
            reservation_uy = _stay_point_use_year(stay, c)
            if reservation_uy is None:
                continue
            source_mode = str(stay.get("point_source") or "Auto")
            source_year_override = stay.get("point_source_year")
            allocations = []

            def take(source_year, source_type, amount):
                amount = min(float(amount), balances.get(source_year, 0.0))
                if amount > 0:
                    balances[source_year] = balances.get(source_year, 0.0) - amount
                    allocations.append((source_year, source_type, amount))
                    return amount
                return 0.0

            remaining = requested
            if source_mode == "Auto":
                # Use banked points in the reservation's use year first, then
                # that year's own annual points, then borrow from future years.
                # Since balances combine banked-in and annual points, the
                # resulting source is split only when necessary.
                banked = 0.0
                if reservation_uy in balances:
                    prev = cled[cled["use_year"] == reservation_uy - 1]
                    if not prev.empty:
                        banked = float(prev.iloc[0]["banked_points"] or 0)
                take_banked = min(remaining, banked, balances.get(reservation_uy, 0.0))
                if take_banked > 0:
                    balances[reservation_uy] -= take_banked
                    allocations.append((reservation_uy, "Banked", take_banked))
                    remaining -= take_banked
                if remaining > 0:
                    got = take(reservation_uy, "Current", remaining)
                    remaining -= got
                # Borrow only as much as needed from the next available use year.
                future_years = sorted(y for y in balances if y > reservation_uy)
                for fy in future_years:
                    if remaining <= 0:
                        break
                    got = take(fy, "Borrowed", remaining)
                    remaining -= got
            else:
                sy = None
                if pd.notna(source_year_override):
                    try:
                        sy = int(source_year_override)
                    except Exception:
                        sy = None
                if sy is None:
                    if source_mode == "Current use year":
                        sy = reservation_uy
                    elif source_mode == "Banked points":
                        sy = reservation_uy
                    elif source_mode == "Borrowed from next year":
                        sy = reservation_uy + 1
                if sy is not None:
                    source_type = "Banked" if source_mode == "Banked points" else ("Borrowed" if source_mode == "Borrowed from next year" else "Current")
                    got = take(sy, source_type, remaining)
                    remaining -= got

            # If an explicit override cannot cover the requested points, do not
            # silently invent points.  Put the unresolved amount back on the
            # stay as a warning in the UI; the stay remains intact.
            for source_year, source_type, amount in allocations:
                execute("""INSERT INTO stay_point_allocations(
                    stay_id,contract_id,source_use_year,source_type,points
                ) VALUES(?,?,?,?,?)""", (int(stay["id"]), cid, int(source_year), source_type, float(amount)))

            if remaining > 0.0001:
                execute("UPDATE stays SET notes=CASE WHEN notes IS NULL OR notes='' THEN ? ELSE notes || ? END WHERE id=?", (f"Point allocation warning: {remaining:.0f} points could not be sourced automatically.", f"\nPoint allocation warning: {remaining:.0f} points could not be sourced automatically.", int(stay["id"])))

        # Summarize allocation usage and borrowing back into the annual ledger.
        alloc = query("SELECT source_use_year, source_type, SUM(points) AS points FROM stay_point_allocations WHERE contract_id=? GROUP BY source_use_year, source_type", (cid,))
        for _, r in cled.iterrows():
            uy = int(r["use_year"])
            used = float(alloc[(alloc["source_use_year"] == uy)]["points"].sum()) if not alloc.empty else 0.0
            borrowed_out = float(alloc[(alloc["source_use_year"] == uy) & (alloc["source_type"] == "Borrowed")]["points"].sum()) if not alloc.empty else 0.0
            execute("UPDATE point_ledger SET used_points=?,borrowed_out=? WHERE contract_id=? AND use_year=?", (used, borrowed_out, cid, uy))

    _sync_bank_flow_only()


def _sync_bank_flow_only():
    """Keep banked-in values synchronized with the prior use year's banked-out."""
    rows = query("SELECT * FROM point_ledger ORDER BY contract_id,use_year")
    for _, r in rows.iterrows():
        cid, uy = int(r["contract_id"]), int(r["use_year"])
        prev = query("SELECT banked_points FROM point_ledger WHERE contract_id=? AND use_year=?", (cid, uy - 1))
        banked_in = float(prev.iloc[0]["banked_points"] or 0) if not prev.empty else 0.0
        execute("UPDATE point_ledger SET banked_in=? WHERE id=?", (banked_in, int(r["id"])))

def load_dashboard():
    contracts = query("SELECT * FROM contracts")
    dues = query("SELECT * FROM dues")
    stays = query("SELECT * FROM stays")
    expenses = query("SELECT * FROM expenses")
    ledger = query("SELECT * FROM point_ledger") if table_exists("point_ledger") else pd.DataFrame()
    if not expenses.empty:
        expenses["attributed_amount"] = expenses["amount"] * expenses["attribution_pct"] / 100.0
    return contracts, dues, stays, expenses, ledger



sync_point_ledger()
contracts, dues, stays, expenses, ledger = load_dashboard()

DVC_ROOM_TYPES = {
    "Disney's Animal Kingdom Villas - Jambo House": [
        "Deluxe Studio - Value",
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Savanna View",
        "Deluxe Studio - Club Level",
        "1 Bedroom Villa - Value",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Savanna View",
        "1 Bedroom Villa - Club Level",
        "2 Bedroom Lock-Off Villa - Value",
        "2 Bedroom Lock-Off Villa - Standard View",
        "2 Bedroom Lock-Off Villa - Savanna View",
        "2 Bedroom Lock-Off Villa - Club Level",
        "3 Bedroom Grand Villa - Savanna View",
    ],
    "Disney's Animal Kingdom Villas - Kidani Village": [
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Savanna View",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Savanna View",
        "2 Bedroom Villa - Standard View",
        "2 Bedroom Villa - Savanna View",
        "3 Bedroom Grand Villa - Standard View",
        "3 Bedroom Grand Villa - Savanna View",
    ],
    "Bay Lake Tower at Disney's Contemporary Resort": [
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Lake View",
        "Deluxe Studio - Theme Park View",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Lake View",
        "1 Bedroom Villa - Theme Park View",
        "2 Bedroom Villa - Standard View",
        "2 Bedroom Villa - Lake View",
        "2 Bedroom Villa - Theme Park View",
        "3 Bedroom Grand Villa - Lake View",
        "3 Bedroom Grand Villa - Theme Park View",
    ],
    "Boulder Ridge Villas at Disney's Wilderness Lodge": [
        "Deluxe Studio",
        "1 Bedroom Villa",
        "2 Bedroom Villa",
    ],
    "Copper Creek Villas & Cabins at Disney's Wilderness Lodge": [
        "Deluxe Studio",
        "1 Bedroom Villa",
        "2 Bedroom Villa",
        "3 Bedroom Grand Villa",
        "Cascade Cabin",
    ],
    "Disney's Beach Club Villas": [
        "Deluxe Studio",
        "1 Bedroom Villa",
        "2 Bedroom Villa",
    ],
    "Disney's BoardWalk Villas": [
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Preferred / Pool-Garden View",
        "Deluxe Studio - BoardWalk View",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Preferred / Pool-Garden View",
        "1 Bedroom Villa - BoardWalk View",
        "2 Bedroom Lock-Off Villa - Standard View",
        "2 Bedroom Lock-Off Villa - Preferred / Pool-Garden View",
        "2 Bedroom Lock-Off Villa - BoardWalk View",
        "3 Bedroom Grand Villa - BoardWalk View",
    ],
    "Disney's Old Key West Resort": [
        "Deluxe Studio",
        "1 Bedroom Villa",
        "2 Bedroom Villa",
        "3 Bedroom Grand Villa",
    ],
    "Disney's Polynesian Villas & Bungalows": [
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Preferred View",
        "Deluxe Studio - Theme Park View",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Preferred View",
        "1 Bedroom Villa - Theme Park View",
        "2 Bedroom Villa - Standard View",
        "2 Bedroom Villa - Preferred View",
        "2 Bedroom Villa - Theme Park View",
        "2 Bedroom Penthouse - Preferred View",
        "2 Bedroom Penthouse - Theme Park View",
        "Bungalow",
    ],
    "Disney's Riviera Resort": [
        "Tower Studio",
        "Deluxe Studio - Standard View",
        "Deluxe Studio - Preferred View",
        "1 Bedroom Villa - Standard View",
        "1 Bedroom Villa - Preferred View",
        "2 Bedroom Villa - Standard View",
        "2 Bedroom Villa - Preferred View",
        "3 Bedroom Grand Villa",
    ],
    "Disney's Saratoga Springs Resort & Spa": [
        "Deluxe Studio - Standard",
        "Deluxe Studio - Preferred",
        "1 Bedroom Villa - Standard",
        "1 Bedroom Villa - Preferred",
        "2 Bedroom Villa - Standard",
        "2 Bedroom Villa - Preferred",
        "3 Bedroom Grand Villa - Standard",
        "3 Bedroom Grand Villa - Preferred",
        "Treehouse Villa",
    ],
    "The Villas at Disney's Grand Floridian Resort & Spa": [
        "Deluxe Studio - Resort View",
        "Deluxe Studio - Preferred View",
        "Deluxe Studio - Theme Park View",
        "Resort Studio - Resort View",
        "Resort Studio - Preferred View",
        "Resort Studio - Theme Park View",
        "1 Bedroom Villa - Resort View",
        "1 Bedroom Villa - Preferred View",
        "1 Bedroom Villa - Theme Park View",
        "2 Bedroom Villa - Resort View",
        "2 Bedroom Villa - Preferred View",
        "2 Bedroom Villa - Theme Park View",
        "3 Bedroom Grand Villa - Lake View",
    ],
    "The Cabins at Disney's Fort Wilderness Resort": [
        "Cabin",
    ],
}


tabs = st.tabs(["🏰 Dashboard", "📜 Contracts", "💰 Annual Dues", "🛏️ Stays", "🎟️ Trip Expenses", "📊 Point Ledger", "📦 Data"])

# ============================================================
# DASHBOARD
# ============================================================
with tabs[0]:
    gross_purchase_cost = float(contracts["purchase_price"].sum() + contracts["closing_costs"].sum()) if not contracts.empty else 0
    purchase_incentives = float(contracts["purchase_incentives"].sum()) if (not contracts.empty and "purchase_incentives" in contracts.columns) else 0
    magical_beginnings = float(contracts["magical_beginnings"].sum()) if (not contracts.empty and "magical_beginnings" in contracts.columns) else 0
    purchase_cost = gross_purchase_cost - purchase_incentives - magical_beginnings

    if not dues.empty:
        if "actual_cost" in dues.columns:
            dues_effective = dues["actual_cost"].where(dues["actual_cost"].notna() & (dues["actual_cost"] > 0), dues["amount"])
        else:
            dues_effective = dues["amount"]
        dues_cost = float(dues_effective.sum())
    else:
        dues_cost = 0.0

    if not stays.empty:
        realized_value = float(stays["cash_room_value"].sum())
        value_resort_total = float(stays["value_resort_value"].fillna(0).sum()) if "value_resort_value" in stays.columns else 0.0
        points_used_total = float(stays["points_used"].sum())
    else:
        realized_value = 0.0
        points_used_total = 0.0

    driven_spend = float(expenses["attributed_amount"].sum()) if not expenses.empty and "attributed_amount" in expenses.columns else 0.0
    all_in_cost = purchase_cost + dues_cost + driven_spend

    current_year = date.today().year

    # Owner-performance metrics from the automatic annual point schedule.
    ledger_has_data = not ledger.empty
    total_used_points = float(ledger["used_points"].sum()) if ledger_has_data else (float(stays["points_used"].sum()) if not stays.empty else 0.0)
    if ledger_has_data:
        _ledger = ledger.copy()
        _ledger["use_year"] = pd.to_numeric(_ledger["use_year"], errors="coerce")
        _past = _ledger[_ledger["use_year"] <= current_year]
        lifetime_available = float((_past["annual_points"].fillna(0) + _past["banked_in"].fillna(0) - _past["banked_points"].fillna(0) - _past["expired_points"].fillna(0)).sum())
        _current = _ledger[_ledger["use_year"] == current_year]
        if not _current.empty:
            _row = _current.iloc[-1]
            current_remaining = max(0.0, float(_row["annual_points"] or 0) + float(_row["banked_in"] or 0) - float(_row["banked_points"] or 0) - float(_row["used_points"] or 0) - float(_row["expired_points"] or 0))
        else:
            current_remaining = 0.0
    else:
        lifetime_available = 0.0; current_remaining = 0.0
    unused_points = current_remaining

    utilization_pct = (total_used_points / lifetime_available * 100.0) if lifetime_available else 0.0

    stay_nights = 0
    if not stays.empty:
        _stay_days = (pd.to_datetime(stays["check_out"], errors="coerce") - pd.to_datetime(stays["check_in"], errors="coerce")).dt.days
        stay_nights = int(_stay_days.clip(lower=0).fillna(0).sum())

    total_ownership_cost = purchase_cost + dues_cost
    unrecovered_investment = max(0.0, total_ownership_cost - realized_value)
    net_value_created = realized_value - total_ownership_cost
    # This is intentionally a realized, historical metric. It includes the upfront
    # acquisition cost, so it should NOT be confused with a forward-looking DVC rate.
    net_cost_per_night = (unrecovered_investment / stay_nights) if stay_nights else 0.0
    ongoing_dues_per_night = (dues_cost / stay_nights) if stay_nights else 0.0

    assumed_rental = float(query("SELECT dvc_rental_rate FROM projection_settings WHERE id=1").iloc[0]["dvc_rental_rate"])
    unused_point_value = unused_points * assumed_rental

    # Display helpers: keep dashboard values human-readable and never let Python/NumPy
    # scientific notation leak into the UI.
    def _ui_int(value):
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            return "0"

    def _ui_currency(value):
        try:
            return f"${float(value):,.0f}"
        except (TypeError, ValueError):
            return "$0"

    # Dashboard hierarchy: ownership first, then actual performance, then owner
    # efficiency. This avoids presenting the acquisition price and vacation value as
    # if they were the same type of metric.
    st.markdown("### 💰 Ownership")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net initial investment", _ui_currency(purchase_cost))
    c2.metric("Dues paid", _ui_currency(dues_cost))
    c3.metric("Total cash invested", _ui_currency(total_ownership_cost), help="Net acquisition cost plus actual dues paid. Trip spending is intentionally excluded from ownership cost.")
    c4.metric("DVC points used", _ui_int(total_used_points))

    st.markdown("### ✨ Performance")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("DVC room value earned", _ui_currency(realized_value))
    p2.metric("Unrecovered DVC investment", _ui_currency(unrecovered_investment), help="Total ownership cost minus the lodging value already earned. A positive number means the recorded lodging value has not yet recovered the acquisition cost and dues.")
    p3.metric("Nights used", _ui_int(stay_nights))
    p4.metric("Point utilization", f"{utilization_pct:.1f}%", help=f"{_ui_int(total_used_points)} points used ÷ {_ui_int(lifetime_available)} points available through {current_year}. Banked points are treated as allocated to a future use year, not as unused points.")

    st.markdown("### 🎯 Owner efficiency")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Net cost / night", _ui_currency(net_cost_per_night) if net_cost_per_night else "—", help="Realized ownership cost after subtracting recorded DVC room value, divided by nights actually used. This includes the unrecovered upfront purchase cost, so it is a historical metric—not a forward hotel rate.")
    m2.metric("Ongoing dues / night", _ui_currency(ongoing_dues_per_night) if ongoing_dues_per_night else "—", help="Actual dues paid divided by recorded nights. This isolates the recurring ownership expense from the upfront purchase price.")
    m3.metric("Unused points", _ui_int(unused_points), help="Points that remain unspent after accounting for used, banked, borrowed and expired points in the Point Ledger. Banked points are not counted as unused because they have been intentionally carried forward.")
    m4.metric("Remaining-point value", _ui_currency(unused_point_value), help=f"Current use-year points remaining × ${assumed_rental:,.2f}/point assumed rental value.")
    st.caption(f"Point utilization: **{_ui_int(total_used_points)} used / {_ui_int(lifetime_available)} available** through {current_year} ({utilization_pct:.1f}%).")

    if driven_spend > 0:
        st.caption(f"Trip spending tracked separately: **${driven_spend:,.0}**. It is not included in DVC ownership cost because those expenses would generally exist whether the stay was owned, rented, or paid in cash.")

    # ---------------- Lifetime projection ----------------
    st.markdown("## ✨ Lifetime DVC Break-Even Journey")
    st.caption("Actual years use your recorded data. Future years are estimated all the way through the legal contract expiration.")

    settings = query("SELECT * FROM projection_settings WHERE id=1").iloc[0]

    contract_end_year = None
    if not contracts.empty and "contract_end_date" in contracts.columns:
        valid_ends = pd.to_datetime(contracts["contract_end_date"], errors="coerce").dropna()
        if not valid_ends.empty:
            contract_end_year = int(valid_ends.dt.year.max())

    # Historical evidence: actual owner-entered dues, with source-backed PVB history as a fallback reference.
    hist_dues = query("SELECT * FROM historical_benchmarks ORDER BY year")
    historical_dues_cagr = None
    if not dues.empty and "year" in dues.columns:
        _d = dues.copy()
        if "actual_cost" in _d.columns:
            _d["effective_cost"] = _d["actual_cost"].where(_d["actual_cost"].notna() & (_d["actual_cost"] > 0), _d["amount"])
        else:
            _d["effective_cost"] = _d["amount"]
        _annual = _d.groupby("year")["effective_cost"].sum().sort_index()
        if len(_annual) >= 2 and _annual.iloc[0] > 0 and _annual.iloc[-1] > 0:
            historical_dues_cagr = ((_annual.iloc[-1] / _annual.iloc[0]) ** (1 / (_annual.index[-1] - _annual.index[0])) - 1) * 100
    if historical_dues_cagr is None and not hist_dues.empty:
        _h = hist_dues[hist_dues["resort"].eq("Disney's Polynesian Villas & Bungalows") & hist_dues["dues_per_point"].notna()].sort_values("year")
        if len(_h) >= 2:
            historical_dues_cagr = ((_h.iloc[-1]["dues_per_point"] / _h.iloc[0]["dues_per_point"]) ** (1 / (_h.iloc[-1]["year"] - _h.iloc[0]["year"])) - 1) * 100

    historical_room_cagr = None
    if not stays.empty:
        _sr = stays.copy()
        _sr["year"] = pd.to_datetime(_sr["check_in"], errors="coerce").dt.year
        _rv = _sr.groupby("year")["cash_room_value"].sum().sort_index()
        _rv = _rv[_rv > 0]
        if len(_rv) >= 2:
            historical_room_cagr = ((_rv.iloc[-1] / _rv.iloc[0]) ** (1 / (_rv.index[-1] - _rv.index[0])) - 1) * 100

    # Derive a useful default future annual room value from the latest year with actual stay value.
    derived_room_value = 0.0
    actual_room_by_year = {}
    if not stays.empty:
        sproj = stays.copy()
        sproj["year"] = pd.to_datetime(sproj["check_in"], errors="coerce").dt.year
        sproj["projection_room_value"] = sproj["cash_room_value"]
        actual_room_by_year = sproj.groupby("year")["projection_room_value"].sum().to_dict()
        actual_value_by_year = sproj.groupby("year")["value_resort_value"].sum().to_dict() if "value_resort_value" in sproj.columns else {}
        positive_years = {k:v for k,v in actual_room_by_year.items() if v > 0}
        if positive_years:
            derived_room_value = float(positive_years[max(positive_years.keys())])

    saved_room = float(settings["annual_room_value"])
    default_room = saved_room if saved_room > 0 else derived_room_value

    with st.expander("⚙️ Projection assumptions", expanded=True):
        p1, p2 = st.columns(2)
        with p1:
            dues_growth = st.number_input(
                "Annual dues increase %", min_value=0.0, max_value=15.0,
                value=float(settings["dues_growth"]), step=0.1,
                help="DVC Genie uses 5% as its expected scenario. Polynesian's historical CAGR has been lower; this remains editable."
            )
            gift_discount = st.number_input(
                "Expected future gift-card discount %", min_value=0.0, max_value=25.0,
                value=float(settings["gift_card_discount"]), step=0.5,
                help="Applied to estimated future dues to model what the dues actually cost you."
            )
        with p2:
            room_growth = st.number_input(
                "Annual Disney room-rate increase %", min_value=0.0, max_value=15.0,
                value=float(settings["room_growth"]), step=0.1
            )
            annual_room_value = st.number_input(
                "Starting annual equivalent room value", min_value=0.0,
                value=float(default_room), step=250.0,
                help="The estimated cash value of the DVC lodging you expect to use in a normal future year."
            )
            value_resort_ratio_pct = st.number_input(
                "Value Resort cost as % of DVC room value",
                min_value=10.0, max_value=100.0,
                value=float(settings["value_resort_ratio"] * 100),
                step=1.0,
                help="Fallback only. Actual same-date Value Resort benchmarks override this estimate."
            )
            cash_discount_pct = st.number_input(
                "Typical Disney cash-room discount %", min_value=0.0, max_value=50.0,
                value=float(settings["cash_discount"]), step=1.0,
                help="Used for the discounted-cash alternative. This avoids assuming you always pay rack rate."
            )
        p3, p4 = st.columns(2)
        with p3:
            investment_return = st.number_input(
                "Opportunity-cost investment return %", min_value=0.0, max_value=15.0,
                value=float(settings["investment_return"]), step=0.25,
                help="Annual return assumption for money that could have remained invested instead of buying DVC."
            )
            dvc_rental_rate = st.number_input(
                "DVC rental rate $/point", min_value=0.0, max_value=50.0,
                value=float(settings["dvc_rental_rate"]), step=0.50,
                help="Benchmark for renting the same DVC points rather than owning."
            )
        with p4:
            rental_growth = st.number_input(
                "DVC rental rate growth %", min_value=0.0, max_value=10.0,
                value=float(settings["rental_growth"]), step=0.25
            )
            st.caption("Model hierarchy: actual stay benchmark → historical benchmark → editable estimate.")

        if historical_dues_cagr is not None:
            st.caption(f"📈 Historical dues CAGR: **{historical_dues_cagr:.2f}%/yr** based on available history. DVCNews notes long-run dues commonly trend around 3–5%, while actual resort history can vary materially.")
        if historical_room_cagr is not None:
            st.caption(f"🏨 Observed room-value CAGR in your recorded stays: **{historical_room_cagr:.2f}%/yr**. This is a personal-use signal, not a universal Disney room-rate index.")
        else:
            st.caption("🏨 Historical Disney room-rate data is date-specific; the tracker uses actual stay values where available and an editable forward growth assumption otherwise.")

        if contract_end_year:
            st.info(f"🏁 Projection minimum horizon: **{contract_end_year}**, based on your recorded contract end date.")
        else:
            st.warning("Add the legal Contract End Date on the Contracts tab so the lifetime graph has the correct horizon.")

        if st.button("💾 Save projection assumptions"):
            execute("""
                UPDATE projection_settings
                SET dues_growth=?, room_growth=?, gift_card_discount=?, annual_room_value=?,
                    projection_end_year=?, value_resort_ratio=?, cash_discount=?, investment_return=?,
                    dvc_rental_rate=?, rental_growth=?
                WHERE id=1
            """, (
                dues_growth, room_growth, gift_discount, annual_room_value,
                contract_end_year if contract_end_year else int(settings["projection_end_year"]),
                value_resort_ratio_pct / 100.0, cash_discount_pct, investment_return,
                dvc_rental_rate, rental_growth
            ))
            st.success("Projection assumptions saved.")
            st.rerun()

    if contracts.empty:
        st.info("Add your DVC contract to build a lifetime projection.")
    elif contract_end_year is None:
        st.info("Once you add the contract end date, this graph will run through that year automatically.")
    else:
        purchase_year = int(pd.to_datetime(contracts["purchase_date"], errors="coerce").dt.year.min())

        # Actual dues by year and future baseline from latest NON-prorated full year.
        actual_dues_by_year = {}
        baseline_year = None
        baseline_actual_cost = 0.0
        baseline_published = 0.0

        if not dues.empty:
            dproj = dues.copy()
            if "actual_cost" in dproj.columns:
                dproj["effective_cost"] = dproj["actual_cost"].where(
                    dproj["actual_cost"].notna() & (dproj["actual_cost"] > 0),
                    dproj["amount"]
                )
            else:
                dproj["effective_cost"] = dproj["amount"]

            actual_dues_by_year = dproj.groupby("year")["effective_cost"].sum().to_dict()

            if "is_prorated" in dproj.columns:
                full = dproj[dproj["is_prorated"].fillna(0) == 0].copy()
            else:
                full = dproj.copy()

            if not full.empty:
                baseline_year = int(full["year"].max())
                baseline_actual_cost = float(full.loc[full["year"] == baseline_year, "effective_cost"].sum())
                if "published_amount" in full.columns:
                    pubs = full.loc[full["year"] == baseline_year, "published_amount"].fillna(0)
                    baseline_published = float(pubs.sum())

        # If published dues are known, grow those and then apply future gift-card discount.
        # Otherwise grow actual out-of-pocket cost; don't apply the discount twice.
        use_published_baseline = baseline_published > 0

        # Value Resort comparison: actual same-trip prices win; otherwise use the
        # editable percentage of the DVC room value.
        actual_value_by_year = {}
        if not stays.empty and "value_resort_value" in stays.columns:
            svalue = stays.copy()
            svalue["year"] = pd.to_datetime(svalue["check_in"], errors="coerce").dt.year
            actual_value_by_year = svalue.groupby("year")["value_resort_value"].sum().to_dict()
        value_resort_ratio = float(value_resort_ratio_pct) / 100.0

        rows = []
        cumulative_cost = purchase_cost
        cumulative_room = 0.0
        cumulative_value_alt = 0.0
        cumulative_discounted_cash = 0.0
        cumulative_rental = 0.0
        portfolio_if_not_bought = purchase_cost
        cumulative_opportunity_gap = 0.0
        annual_points_by_year = {}
        if not ledger.empty:
            annual_points_by_year = ledger.groupby("use_year")["used_points"].sum().to_dict()

        for y in range(purchase_year, contract_end_year + 1):
            # Dues
            if y in actual_dues_by_year:
                year_dues = float(actual_dues_by_year[y])
                dues_status = "Actual"
            elif baseline_year is not None and y > baseline_year:
                years_after = y - baseline_year
                if use_published_baseline:
                    gross_est = baseline_published * ((1 + dues_growth / 100.0) ** years_after)
                    year_dues = gross_est * (1 - gift_discount / 100.0)
                else:
                    year_dues = baseline_actual_cost * ((1 + dues_growth / 100.0) ** years_after)
                dues_status = "Estimated"
            else:
                year_dues = 0.0
                dues_status = "Pending baseline"

            cumulative_cost += year_dues

            # Room value
            if y in actual_room_by_year and float(actual_room_by_year[y]) > 0:
                year_room = float(actual_room_by_year[y])
                room_status = "Actual"
            elif y > current_year and annual_room_value > 0:
                year_room = annual_room_value * ((1 + room_growth / 100.0) ** (y - current_year))
                room_status = "Estimated"
            elif y == current_year and annual_room_value > 0 and y not in actual_room_by_year:
                year_room = annual_room_value
                room_status = "Estimated"
            else:
                year_room = float(actual_room_by_year.get(y, 0.0))
                room_status = "Actual" if year_room > 0 else "Pending"

            cumulative_room += year_room

            actual_value = float(actual_value_by_year.get(y, 0) or 0)
            if actual_value > 0:
                year_value_alt = actual_value
                value_alt_status = "Actual"
            elif year_room > 0:
                year_value_alt = year_room * value_resort_ratio
                value_alt_status = "Estimated"
            else:
                year_value_alt = 0.0
                value_alt_status = "Pending"
            cumulative_value_alt += year_value_alt

            # Discounted cash alternative: same DVC room value, but assume the user
            # normally buys Disney cash rooms at a configurable discount to rack.
            year_discounted_cash = year_room * (1 - cash_discount_pct / 100.0)
            cumulative_discounted_cash += year_discounted_cash

            # DVC rental alternative: actual points used when known, otherwise annual allocation.
            points_for_rental = float(annual_points_by_year.get(y, 0) or 0)
            if points_for_rental <= 0 and y >= purchase_year:
                # Default future rental comparison to the contract's annual allocation.
                # This is derived here so the projection never depends on a variable
                # defined later in the script.
                annual_entitlement = float(contracts["points"].fillna(0).sum()) if not contracts.empty and "points" in contracts.columns else 0.0
                points_for_rental = annual_entitlement
            years_since_current = max(0, y - current_year)
            year_rental_rate = dvc_rental_rate * ((1 + rental_growth / 100.0) ** years_since_current)
            year_rental = points_for_rental * year_rental_rate if points_for_rental > 0 else 0.0
            cumulative_rental += year_rental

            # Opportunity-cost scenario: invest the acquisition cash instead, and
            # compare the resulting portfolio to the DVC ownership path.
            if y == purchase_year:
                portfolio_if_not_bought = purchase_cost * (1 + investment_return / 100.0)
            else:
                portfolio_if_not_bought *= (1 + investment_return / 100.0)
            annual_savings_vs_cash = year_discounted_cash - year_dues
            portfolio_if_not_bought += annual_savings_vs_cash
            cumulative_opportunity_gap = portfolio_if_not_bought - cumulative_cost

            rows.append({
                "Year": y,
                "Cumulative DVC Cost": round(cumulative_cost, 2),
                "Equivalent Cash Room Cost": round(cumulative_room, 2),
                "Cumulative Value Resort Cost": round(cumulative_value_alt, 2),
                "Discounted Cash Cost": round(cumulative_discounted_cash, 2),
                "DVC Rental Cost": round(cumulative_rental, 2),
                "Invest & Pay Cash Advantage": round(cumulative_opportunity_gap, 2),
                "Annual Dues Cost": round(year_dues, 2),
                "Annual Room Value": round(year_room, 2),
                "Annual Value Resort Cost": round(year_value_alt, 2),
                "Dues": dues_status,
                "Room Value": room_status,
                "Value Resort": value_alt_status
            })

        proj = pd.DataFrame(rows)

        fig_life = go.Figure()
        fig_life.add_trace(go.Scatter(
            x=proj["Year"], y=proj["Cumulative DVC Cost"],
            mode="lines", name="Cumulative DVC cost"
        ))
        fig_life.add_trace(go.Scatter(
            x=proj["Year"], y=proj["Equivalent Cash Room Cost"],
            mode="lines", name="Equivalent cash room cost"
        ))
        fig_life.add_trace(go.Scatter(
            x=proj["Year"], y=proj["Cumulative Value Resort Cost"],
            mode="lines", name=f"Value Resort alternative ({value_resort_ratio_pct:.0f}% fallback)"
        ))
        fig_life.add_trace(go.Scatter(
            x=proj["Year"], y=proj["Discounted Cash Cost"],
            mode="lines", name=f"Discounted cash ({cash_discount_pct:.0f}% off)"
        ))
        fig_life.add_trace(go.Scatter(
            x=proj["Year"], y=proj["DVC Rental Cost"],
            mode="lines", name=f"DVC rental (${dvc_rental_rate:.0f}/pt)"
        ))
        fig_life.update_layout(
            title=f"Lifetime projection through {contract_end_year}",
            xaxis_title="Year", yaxis_title="Dollars",
            height=500, legend_title_text="",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_life, use_container_width=True)

        be_deluxe = proj[proj["Equivalent Cash Room Cost"] >= proj["Cumulative DVC Cost"]]
        be_value = proj[proj["Cumulative Value Resort Cost"] >= proj["Cumulative DVC Cost"]]
        be_discounted = proj[proj["Discounted Cash Cost"] >= proj["Cumulative DVC Cost"]]
        be_rental = proj[proj["DVC Rental Cost"] >= proj["Cumulative DVC Cost"]]

        if not be_deluxe.empty:
            break_even_deluxe = int(be_deluxe.iloc[0]["Year"])
            st.success(f"🎆 DVC vs. Deluxe break-even: **{break_even_deluxe}**")
        else:
            st.info(f"DVC vs. Deluxe break-even is not reached before the contract ends in **{contract_end_year}**.")

        if not be_value.empty:
            break_even_value = int(be_value.iloc[0]["Year"])
            st.success(f"🏨 DVC vs. Value Resort break-even: **{break_even_value}**")
        else:
            st.info(f"DVC vs. Value Resort break-even is not reached before the contract ends in **{contract_end_year}**.")

        if not be_discounted.empty:
            st.success(f"💸 DVC vs. discounted cash break-even: **{int(be_discounted.iloc[0]['Year'])}**")
        else:
            st.info(f"DVC vs. discounted cash break-even is not reached before the contract ends in **{contract_end_year}**.")
        if not be_rental.empty:
            st.success(f"🔑 DVC vs. rental break-even: **{int(be_rental.iloc[0]['Year'])}**")
        else:
            st.info(f"DVC vs. rental break-even is not reached before the contract ends in **{contract_end_year}**.")

        ending = proj.iloc[-1]
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Projected DVC cost at expiration", f"${ending['Cumulative DVC Cost']:,.0f}")
        e2.metric("Projected Deluxe room value", f"${ending['Equivalent Cash Room Cost']:,.0f}")
        e3.metric("Projected Value Resort cost", f"${ending['Cumulative Value Resort Cost']:,.0f}")
        e4.metric("Value Resort advantage", f"${ending['Cumulative Value Resort Cost'] - ending['Cumulative DVC Cost']:,.0f}")
        e5, e6, e7 = st.columns(3)
        e5.metric("Discounted cash alternative", f"${ending['Discounted Cash Cost']:,.0f}")
        e6.metric("DVC rental alternative", f"${ending['DVC Rental Cost']:,.0f}")
        e7.metric("Opportunity-cost advantage", f"${ending['Invest & Pay Cash Advantage']:,.0f}", help="Positive means the invest-and-pay-cash scenario has more modeled financial value than the DVC ownership path under the selected assumptions.")

        with st.expander("📅 Year-by-year comparison", expanded=True):
            st.caption(
                "Actual values are shown in dark blue. Estimated values are shown in gold. "
                "Cumulative projected values remain gold until actual data takes over."
            )

            # Purchase price is shown once in the acquisition year. `purchase_cost`
            # is already the net acquisition cost used by the lifetime model.
            _table_rows = []
            _running_dvc_cost = 0.0
            _running_room_value = 0.0

            # Value Resort actuals by year, where the user has entered them.
            _value_by_year = {}
            if not stays.empty and "value_resort_value" in stays.columns:
                _sv = stays.copy()
                _sv["_year"] = pd.to_datetime(_sv["check_in"], errors="coerce").dt.year
                _value_by_year = _sv.groupby("_year")["value_resort_value"].sum().to_dict()

            _running_value_alt = 0.0
            _value_ratio_pct = float(value_resort_ratio_pct)
            _value_ratio = value_resort_ratio

            for _, _pr in proj.iterrows():
                _year = int(_pr["Year"])
                _purchase = purchase_cost if _year == purchase_year else 0.0
                _fees = float(_pr["Annual Dues Cost"] or 0)
                _room = float(_pr["Annual Room Value"] or 0)

                # Cumulative DVC cost: purchase + annual fees.
                _running_dvc_cost += _purchase + _fees
                _running_room_value += _room

                # Value Resort alternative:
                # actual same-year benchmark if entered; otherwise estimate directly
                # from that year's DVC room value so every projected usage year has a comparison.
                _value_alt_actual = float(_value_by_year.get(_year, 0) or 0)
                if _value_alt_actual > 0:
                    _value_alt = _value_alt_actual
                    _value_est = False
                elif _room > 0:
                    _value_alt = _room * _value_ratio
                    _value_est = True
                else:
                    _value_alt = 0.0
                    _value_est = True

                _running_value_alt += _value_alt

                _fees_est = str(_pr["Dues"]) != "Actual"
                _room_est = str(_pr["Room Value"]) != "Actual"

                def _fmt(v):
                    return "—" if not v else f"${float(v):,.0f}"

                def _span(v, estimated=False):
                    if not v:
                        return "—"
                    cls = "projected-value" if estimated else "actual-value"
                    return f'<span class="{cls}">{_fmt(v)}</span>'

                _table_rows.append(
                    "<tr>"
                    f"<td class='yr'>{_year}</td>"
                    f"<td>{_span(_purchase, False)}</td>"
                    f"<td>{_span(_fees, _fees_est)}</td>"
                    f"<td class='cum'>{_span(_running_dvc_cost, _fees_est)}</td>"
                    f"<td>{_span(_room, _room_est)}</td>"
                    f"<td class='cum'>{_span(_running_room_value, _room_est)}</td>"
                    f"<td>{_span(_value_alt, _value_est)}</td>"
                    f"<td class='cum'>{_span(_running_value_alt, _value_est)}</td>"
                    "</tr>"
                )

            _year_table = """
            <style>
              .yearly-wrap {
                overflow-x:auto;
                border:1px solid rgba(12,72,124,.18);
                border-radius:20px;
                background:white;
                box-shadow:0 8px 22px rgba(7,45,84,.08);
                margin-top:10px;
              }
              .yearly-table {
                width:100%;
                min-width:1050px;
                border-collapse:collapse;
                font-size:.88rem;
              }
              .yearly-table th, .yearly-table td {
                padding:9px 11px;
                border-bottom:1px solid #e8f0f6;
                text-align:right;
              }
              .yearly-table td.yr { text-align:center; font-weight:900; color:#0b4b7c; }
              .yearly-table .group th {
                text-align:center;
                color:white;
                font-size:.95rem;
                letter-spacing:.05em;
                border-bottom:0;
              }
              .yearly-table .dvc-group { background:#073b6c; }
              .yearly-table .usage-group { background:#0b5680; }
              .yearly-table .year-group { background:#042a50; }
              .yearly-table .sub th {
                background:#eef6fd;
                color:#173f64;
              }
              .actual-value { color:#173f64; font-weight:750; }
              .projected-value { color:#b87900; font-weight:900; }
              .cum { font-weight:900; background:#f7fbff; }
              .cum .actual-value { color:#073d6c; }
              .cum .projected-value { color:#b87900; }
              .yearly-table tbody tr:hover td { background:#f2f8fd; }
              .projection-legend { margin:4px 0 10px 2px; font-size:.84rem; color:#5a7085; }
              .projection-legend .projected-value { margin-left:16px; }
            </style>
            <div class="projection-legend">
              <span class="actual-value">● Actual</span>
              <span class="projected-value">● Estimated</span>
            </div>
            <div class="yearly-wrap">
              <table class="yearly-table">
                <thead>
                  <tr class="group">
                    <th class="year-group" rowspan="2">Year</th>
                    <th class="dvc-group" colspan="3">🏰 DVC</th>
                    <th class="usage-group" colspan="7">✨ USAGE / CASH COMPARISON</th>
                  </tr>
                  <tr class="sub">
                    <th>Purchase Price</th>
                    <th>Annual Fees</th>
                    <th>Cumulative Cost</th>
                    <th>DVC Room Rate</th>
                    <th>Cumulative DVC Room Value</th>
                    <th>Value Resort Alternative</th>
                    <th>Cumulative Value Alternative</th>
                    <th>Cumulative Discounted Cash</th>
                    <th>Cumulative DVC Rental</th>
                  </tr>
                </thead>
                <tbody>
            """ + "".join(_table_rows) + """
                </tbody>
              </table>
            </div>
            """
            st.markdown(_year_table, unsafe_allow_html=True)
            st.caption(
                f"Gold Value Resort amounts are estimated at {_value_ratio_pct:.0f}% of each year's DVC room value "
                "unless you enter an actual same-date Value Resort benchmark for that year. Discounted cash and rental are modeled alternatives."
            )

        if baseline_year is None:
            st.warning("You do not yet have a full, non-prorated dues year entered. Add your 2026 full-year dues to make future dues estimates meaningful.")

    # ---------------- DVC Financial Health ----------------
    st.markdown("## 🏰 DVC Financial Health")
    # Score rewards high utilization, positive modeled savings and long remaining life;
    # it is a diagnostic, not a statement of guaranteed investment performance.
    remaining_years = max(0, contract_end_year - current_year) if contract_end_year else 0
    score_util = min(30, utilization_pct * 0.30)
    score_value = 25 if net_value_created >= 0 else max(0, 25 * (1 + net_value_created / max(1, total_ownership_cost)))
    score_life = min(20, remaining_years / 2.0)
    score_eff = 25 if stay_nights > 0 and utilization_pct >= 80 else 18 if stay_nights > 0 else 8
    health_score = int(max(0, min(100, round(score_util + score_value + score_life + score_eff))))
    health_label = "Excellent" if health_score >= 85 else "Strong" if health_score >= 70 else "Watch" if health_score >= 50 else "Needs attention"
    h1,h2,h3 = st.columns([1,2,2])
    h1.metric("Financial Health", f"{health_score}/100")
    h2.metric("Status", health_label)
    h3.metric("Net value created", f"${net_value_created:,.0f}", help="Recorded DVC lodging value minus net acquisition cost and dues paid. This is the same gap used to determine whether the recorded lodging has recovered ownership cost.")
    st.caption("Health score is a dashboard diagnostic based on utilization, realized lodging value, remaining contract life and usage. It is not an investment rating.")

    # Historical methodology panel
    with st.expander("📚 Historical data & methodology", expanded=False):
        st.markdown("**Dues:** The app can use your actual annual dues first, then a resort-specific historical baseline, then your editable growth assumption. Historical reference: DVCNews annual-dues history (2015–2026 for Polynesian). DVCNews publishes annual dues histories by resort; DVC Genie currently uses 5% as its expected forward scenario. Historical dues are therefore treated as data, not a universal 5% rule.")
        st.markdown("**Room rates:** Actual stay cash values take priority. If no actual future benchmark exists, the app uses the latest actual annual DVC room-value baseline and your editable room-growth assumption. Disney cash-room pricing is highly date-dependent, so a single historical rate series should not overwrite actual stay data.")
        st.markdown("**Cash discounts:** The discounted-cash line applies your selected typical discount to the DVC room value rather than assuming rack rate every time.")
        st.markdown("**Value Resort:** Same-date entered benchmarks override the fallback percentage. The default 35% is an estimate, not a Disney-published conversion factor.")
        st.markdown("**Opportunity cost:** The model compounds the acquisition amount at your selected investment return and credits the modeled annual difference versus discounted cash lodging. Change the return assumption to stress-test the result.")
        st.markdown("**DVC rental:** Rental cost uses points × the selected rental rate, grown at the selected rental inflation assumption. It is a benchmark, not a guaranteed market quote.")
        if not hist_dues.empty:
            st.markdown("**Loaded historical dues benchmark:** Polynesian 2015–2026 is preloaded from DVCNews; owner-entered actual dues override it in all financial calculations.")
            _hshow = hist_dues[hist_dues["resort"].eq("Disney's Polynesian Villas & Bungalows")][["year","dues_per_point"]].copy()
            _hshow.columns = ["Year", "Polynesian dues / point"]
            st.dataframe(_hshow.sort_values("Year", ascending=False), use_container_width=True, hide_index=True)

    # Other dashboard charts
    st.subheader("Dues over time")
    if dues.empty:
        st.info("Add annual dues to unlock this chart.")
    else:
        dchart = dues.copy()
        if "actual_cost" in dchart.columns:
            dchart["effective"] = dchart["actual_cost"].where(
                dchart["actual_cost"].notna() & (dchart["actual_cost"] > 0), dchart["amount"]
            )
        else:
            dchart["effective"] = dchart["amount"]
        annual = dchart.groupby("year", as_index=False)["effective"].sum().sort_values("year")
        fig3 = px.line(annual, x="year", y="effective", markers=True, title="Actual out-of-pocket annual dues")
        fig3.update_layout(height=380, yaxis_title="Dollars", xaxis_title="Year",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Trip-by-trip lodging value")
    if stays.empty:
        st.info("Add stays to unlock this chart.")
    else:
        schart = stays.copy()
        schart["value"] = schart["cash_room_value"]
        fig4 = px.bar(
            schart, x="trip_name", y="value", text_auto="$.2s",
            title="DVC room value earned by stay"
        )
        fig4.update_layout(height=400, xaxis_title="", yaxis_title="Dollars",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("🏆✨ Point Magic — Value per Point")
    if stays.empty:
        st.info("Add stays to compare value per point.")
    else:
        vp = stays.copy()
        vp["realized_value"] = vp["cash_room_value"]

        vp = vp[(vp["points_used"] > 0) & (vp["realized_value"] > 0)].copy()
        if vp.empty:
            st.info("Enter points used for your stays to unlock value-per-point analysis.")
        else:
            vp["value_per_point"] = vp["realized_value"] / vp["points_used"]
            best = vp.loc[vp["value_per_point"].idxmax()]
            overall_vpp = vp["realized_value"].sum() / vp["points_used"].sum()

            v1, v2 = st.columns(2)
            v1.metric(
                "Best stay value / point",
                f"${best['value_per_point']:,.2f}",
                help=f"{best['trip_name']} — {best['resort']}"
            )
            v2.metric(
                "Overall DVC rack value / point",
                f"${overall_vpp:,.2f}",
                help="Total DVC rack value divided by total DVC points used."
            )

            vp = vp.sort_values("value_per_point", ascending=False)
            fig_vpp = px.bar(
                vp, x="trip_name", y="value_per_point", text_auto=".2f",
                title="DVC lodging value per point"
            )
            fig_vpp.update_layout(
                height=420, xaxis_title="", yaxis_title="Dollars per point",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_vpp, use_container_width=True)


# ============================================================
# CONTRACTS
# ============================================================
with tabs[1]:
    st.header("🏰✨ My Disney Vacation Club Contracts")
    st.caption("Your existing contracts come first. Add or edit only when you need to.")

    agreements_dir = Path("purchase_agreements")
    agreements_dir.mkdir(exist_ok=True)

    contract_rows = query("SELECT * FROM contracts ORDER BY purchase_date")

    # Existing records first
    st.markdown("### 🏠 My Contracts")
    if contract_rows.empty:
        st.info("No DVC contracts added yet.")
    else:
        for _, r in contract_rows.iterrows():
            with st.container(border=True):
                cols = st.columns([2.2, 1, 1, 1.2, 0.7])
                cols[0].markdown(f"**{r['resort']}**")
                cols[1].markdown(f"**{int(r['points'] or 0)} pts**")
                cols[2].markdown(f"Use Year: **{r['use_year'] or '—'}**")
                cols[3].markdown(f"Ends: **{r['contract_end_date'] or '—'}**")
                if cols[4].button("✏️ Edit", key=f"edit_contract_btn_{int(r['id'])}"):
                    st.session_state["edit_contract_id"] = int(r["id"])

                net = float(r["purchase_price"] or 0) + float(r["closing_costs"] or 0) - float(r["purchase_incentives"] or 0) - float(r["magical_beginnings"] or 0)
                st.caption(
                    f"Purchase ${float(r['purchase_price'] or 0):,.2f}  •  "
                    f"Closing ${float(r['closing_costs'] or 0):,.2f}  •  "
                    f"Incentives ${float(r['purchase_incentives'] or 0):,.2f}  •  "
                    f"Magical Beginnings ${float(r['magical_beginnings'] or 0):,.2f}  •  "
                    f"Net investment ${net:,.2f}"
                )

    # Edit selected row inline
    if st.session_state.get("edit_contract_id"):
        edit_id = st.session_state["edit_contract_id"]
        erows = contract_rows.loc[contract_rows["id"] == edit_id]
        if not erows.empty:
            r = erows.iloc[0]
            st.markdown("### ✏️ Edit Contract")

            purchase_dt = pd.to_datetime(r["purchase_date"], errors="coerce")
            purchase_dt = purchase_dt.date() if not pd.isna(purchase_dt) else date.today()
            end_dt = pd.to_datetime(r["contract_end_date"], errors="coerce")
            end_dt = end_dt.date() if not pd.isna(end_dt) else date(2070,1,31)
            uy_options = ["February","March","April","June","August","September","October","December"]
            uy = r["use_year"] if r["use_year"] in uy_options else "June"

            with st.form(f"edit_contract_form_{edit_id}"):
                e1,e2 = st.columns(2)
                with e1:
                    e_resort = st.text_input("🏨 Home Resort", value=r["resort"] or "")
                    e_contract = st.text_input("📜 Contract Number", value=r["contract_number"] or "")
                    e_use_year = st.selectbox("🗓️ Use Year", uy_options, index=uy_options.index(uy))
                    e_points = st.number_input("✨ Annual Points", min_value=0, value=int(r["points"] or 0), step=1)
                with e2:
                    e_purchase = st.date_input("🎉 Purchase Date", value=purchase_dt)
                    e_end = st.date_input("🏁 Contract End Date", value=end_dt)

                ec1,ec2 = st.columns(2)
                with ec1:
                    e_price = st.number_input("Original Purchase Price", min_value=0.0, value=float(r["purchase_price"] or 0), step=100.0)
                    e_incentives = st.number_input("Disney Incentives / Developer Credits", min_value=0.0, value=float(r["purchase_incentives"] or 0), step=100.0)
                with ec2:
                    e_closing = st.number_input("Closing Costs", min_value=0.0, value=float(r["closing_costs"] or 0), step=100.0)
                    e_mb = st.number_input("✨ Magical Beginnings Proceeds", min_value=0.0, value=float(r["magical_beginnings"] or 0), step=100.0)

                e_notes = st.text_area("📝 Notes", value=r["notes"] or "")
                st.info(f"Net initial investment: **${e_price + e_closing - e_incentives - e_mb:,.2f}**")

                b1,b2 = st.columns(2)
                save = b1.form_submit_button("💾 Save Changes")
                cancel = b2.form_submit_button("Cancel")
                if save:
                    auto_name = f"{e_resort} • {int(e_points)} pts • {e_purchase.year}"
                    execute("""
                        UPDATE contracts
                        SET name=?,resort=?,contract_number=?,use_year=?,purchase_date=?,
                            contract_end_date=?,points=?,purchase_price=?,closing_costs=?,
                            purchase_incentives=?,magical_beginnings=?,notes=?
                        WHERE id=?
                    """,(auto_name,e_resort,e_contract,e_use_year,e_purchase.isoformat(),e_end.isoformat(),
                         int(e_points),e_price,e_closing,e_incentives,e_mb,e_notes,edit_id))
                    st.session_state.pop("edit_contract_id",None)
                    st.success("Contract updated.")
                    st.rerun()
                if cancel:
                    st.session_state.pop("edit_contract_id",None)
                    st.rerun()

    st.markdown("#### 🏨 Cash-stay comparison")
    _cv1,_cv2 = st.columns(2)
    _cv1.metric("DVC villa rack value received", f"${realized_value:,.0f}")
    _cv2.metric("Value Resort alternative", f"${value_resort_total:,.0f}")
    st.divider()
    if st.button("➕ Add Contract", key="btn_toggle_add_contract"):
        st.session_state["show_add_contract"] = not st.session_state.get("show_add_contract", False)

    if st.session_state.get("show_add_contract", False):
        st.markdown("### ✨ Add a DVC Contract")
        with st.form("add_contract"):
            c1,c2 = st.columns(2)
            with c1:
                resort = st.text_input("🏨 Home Resort")
                contract_number = st.text_input("📜 Contract Number")
                use_year = st.selectbox("🗓️ Use Year", ["February","March","April","June","August","September","October","December"])
                points = st.number_input("✨ Annual Points", min_value=0, step=1)
            with c2:
                purchase_date = st.date_input("🎉 Purchase Date", value=date.today())
                contract_end_date = st.date_input("🏁 Contract End Date", value=date(2070,1,31))

            f1,f2 = st.columns(2)
            with f1:
                purchase_price = st.number_input("Original Purchase Price", min_value=0.0, step=100.0)
                purchase_incentives = st.number_input("Disney Incentives / Developer Credits", min_value=0.0, step=100.0)
            with f2:
                closing_costs = st.number_input("Closing Costs", min_value=0.0, step=100.0)
                magical_beginnings = st.number_input("✨ Magical Beginnings Proceeds", min_value=0.0, step=100.0)

            agreement = st.file_uploader("Purchase Agreement / Closing Document", type=["pdf"])
            notes = st.text_area("📝 Notes")
            st.info(f"Net initial investment: **${purchase_price + closing_costs - purchase_incentives - magical_beginnings:,.2f}**")

            a1,a2 = st.columns(2)
            add = a1.form_submit_button("✨ Add Contract")
            close = a2.form_submit_button("Cancel")
            if add:
                if not resort:
                    st.error("Home Resort is required.")
                else:
                    auto_name = f"{resort} • {int(points)} pts • {purchase_date.year}"
                    execute("""
                        INSERT INTO contracts(
                            name,resort,purchase_date,points,purchase_price,closing_costs,notes,
                            purchase_incentives,magical_beginnings,agreement_file,agreement_filename,
                            contract_number,use_year,contract_end_date
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,(auto_name,resort,purchase_date.isoformat(),points,purchase_price,closing_costs,notes,
                         purchase_incentives,magical_beginnings,None,agreement.name if agreement else None,
                         contract_number,use_year,contract_end_date.isoformat()))
                    new_id = int(query("SELECT MAX(id) AS id FROM contracts").iloc[0]["id"])
                    if agreement:
                        safe_name = re.sub(r"[^A-Za-z0-9._-]+","_",agreement.name)
                        saved_path = agreements_dir / f"contract_{new_id}_{safe_name}"
                        saved_path.write_bytes(agreement.getbuffer())
                        execute("UPDATE contracts SET agreement_file=? WHERE id=?",(str(saved_path),new_id))
                    st.session_state["show_add_contract"] = False
                    st.success("Contract added.")
                    st.rerun()
            if close:
                st.session_state["show_add_contract"] = False
                st.rerun()

with tabs[2]:
    st.header("💳✨ Membership Magic — Annual Dues")
    st.caption("Your dues history comes first. Add or edit only when needed.")

    dues_rows = query("""
        SELECT d.*, c.resort
        FROM dues d JOIN contracts c ON d.contract_id=c.id
        ORDER BY d.year DESC, d.id DESC
    """)

    st.markdown("### 💰 Dues History")
    if dues_rows.empty:
        st.info("No annual dues entered yet.")
    else:
        for _, r in dues_rows.iterrows():
            billed = float(r["prorated_amount"] or 0) if int(r["is_prorated"] or 0)==1 else float(r["published_amount"] or r["amount"] or 0)
            actual = float(r["actual_cost"] or r["amount"] or 0)
            with st.container(border=True):
                cols = st.columns([1.2,2,1.3,1.3,0.7])
                cols[0].markdown(f"**{int(r['year'])}**")
                cols[1].markdown(f"**{r['resort']}**")
                cols[2].markdown(f"Billed **${billed:,.2f}**")
                cols[3].markdown(f"Actual **${actual:,.2f}**")
                if cols[4].button("✏️ Edit", key=f"edit_dues_btn_{int(r['id'])}"):
                    st.session_state["edit_dues_id"] = int(r["id"])
                extra = []
                if int(r["is_prorated"] or 0)==1: extra.append("Prorated")
                if int(r["gift_card_used"] or 0)==1: extra.append("Gift cards")
                if extra:
                    st.caption(" • ".join(extra))

    if st.session_state.get("edit_dues_id"):
        did = st.session_state["edit_dues_id"]
        rr = dues_rows.loc[dues_rows["id"] == did]
        if not rr.empty:
            r = rr.iloc[0]
            st.markdown("### ✏️ Edit Dues")
            contracts_dues = query("SELECT id,resort FROM contracts ORDER BY resort")
            contract_ids = list(contracts_dues["id"])
            labels = [f"{x['resort']} (Contract {int(x['id'])})" for _,x in contracts_dues.iterrows()]
            current_idx = contract_ids.index(int(r["contract_id"])) if int(r["contract_id"]) in contract_ids else 0

            with st.form(f"edit_dues_form_{did}"):
                contract_label = st.selectbox("🏰 Contract", labels, index=current_idx)
                contract_id = contract_ids[labels.index(contract_label)]
                year = st.number_input("Year", min_value=1991, max_value=2100, value=int(r["year"]), step=1)
                is_prorated = st.checkbox("This was a prorated dues year", value=bool(r["is_prorated"]))

                d1,d2 = st.columns(2)
                with d1:
                    published = st.number_input("Full-Year Published Dues (optional)", min_value=0.0, value=float(r["published_amount"] or 0), step=50.0)
                    partial = st.number_input("Dues Actually Billed for This Partial Year", min_value=0.0, value=float(r["prorated_amount"] or 0), step=50.0, disabled=not is_prorated)
                with d2:
                    used_gc = st.checkbox("🎁 Paid with discounted Disney Gift Cards", value=bool(r["gift_card_used"]))
                    actual = st.number_input("What I Actually Paid", min_value=0.0, value=float(r["actual_cost"] or r["amount"] or 0), step=50.0)

                note = st.text_input("Proration details", value=r["proration_note"] or "", disabled=not is_prorated)
                applicable = partial if is_prorated and partial > 0 else published

                b1,b2 = st.columns(2)
                save = b1.form_submit_button("💾 Save Changes")
                cancel = b2.form_submit_button("Cancel")
                if save:
                    effective = actual if actual > 0 else applicable
                    execute("""
                        UPDATE dues SET contract_id=?,year=?,amount=?,published_amount=?,actual_cost=?,
                            gift_card_used=?,is_prorated=?,prorated_amount=?,proration_note=?
                        WHERE id=?
                    """,(contract_id,year,effective,published,effective,1 if used_gc else 0,
                         1 if is_prorated else 0,partial if is_prorated else None,
                         note if is_prorated else None,did))
                    st.session_state.pop("edit_dues_id",None)
                    st.success("Dues updated.")
                    st.rerun()
                if cancel:
                    st.session_state.pop("edit_dues_id",None)
                    st.rerun()

    st.divider()
    if st.button("➕ Add Annual Dues", key="btn_toggle_add_dues"):
        st.session_state["show_add_dues"] = not st.session_state.get("show_add_dues", False)

    if st.session_state.get("show_add_dues", False):
        contracts_dues = query("SELECT id,resort FROM contracts ORDER BY resort")
        if contracts_dues.empty:
            st.warning("Add a contract first.")
        else:
            labels = {f"{r['resort']} (Contract {int(r['id'])})":int(r["id"]) for _,r in contracts_dues.iterrows()}
            with st.form("add_dues"):
                contract_label = st.selectbox("🏰 Contract", list(labels))
                year = st.number_input("Year", min_value=1991, max_value=2100, value=date.today().year, step=1)
                is_prorated = st.checkbox("This was a prorated dues year")
                d1,d2 = st.columns(2)
                with d1:
                    published = st.number_input("Full-Year Published Dues (optional)", min_value=0.0, step=50.0)
                    partial = st.number_input("Dues Actually Billed for This Partial Year", min_value=0.0, step=50.0, disabled=not is_prorated)
                with d2:
                    used_gc = st.checkbox("🎁 Paid with discounted Disney Gift Cards")
                    actual = st.number_input("What I Actually Paid", min_value=0.0, step=50.0)
                note = st.text_input("Proration details", disabled=not is_prorated)
                applicable = partial if is_prorated and partial > 0 else published

                a1,a2 = st.columns(2)
                add = a1.form_submit_button("✨ Add Annual Dues")
                close = a2.form_submit_button("Cancel")
                if add:
                    if applicable <= 0:
                        st.error("Enter the amount Disney actually billed.")
                    else:
                        effective = actual if actual > 0 else applicable
                        execute("""
                            INSERT INTO dues(contract_id,year,amount,published_amount,actual_cost,gift_card_used,
                                             is_prorated,prorated_amount,proration_note)
                            VALUES(?,?,?,?,?,?,?,?,?)
                        """,(labels[contract_label],year,effective,published,effective,1 if used_gc else 0,
                             1 if is_prorated else 0,partial if is_prorated else None,
                             note if is_prorated else None))
                        st.session_state["show_add_dues"] = False
                        st.success("Dues added.")
                        st.rerun()
                if close:
                    st.session_state["show_add_dues"] = False
                    st.rerun()

with tabs[3]:
    st.header("🏰✨ DVC Stays & Resort Magic")
    with st.expander("🏨 Value Resort comparison"):
        st.markdown("**Default: Pop Century Standard Room.** Enter the tax-included cash rack cost for the same trip dates. This lets the lifetime graph compare DVC against both the villa you received and a cheaper Disney Value alternative.")

    st.caption("Your actual stays come first. Add or edit from the record itself.")

    stay_rows = query("SELECT * FROM stays ORDER BY check_in DESC, id DESC")

    st.markdown("### 🏨 My Vacation Memories")
    if stay_rows.empty:
        st.info("No DVC stays entered yet.")
    else:
        for _, r in stay_rows.iterrows():
            realized = float(r["cash_room_value"] or 0)
            with st.container(border=True):
                cols = st.columns([2.3,1.4,1.3,1.2,0.7])
                cols[0].markdown(f"**{r['trip_name']}**")
                cols[1].markdown(f"{r['check_in']} → {r['check_out']}")
                pts = float(r["points_used"] or 0)
                vpp = realized / pts if pts > 0 else 0
                cols[2].markdown(f"**{pts:,.0f} pts**")
                cols[3].markdown(f"Value **${realized:,.0f}**")
                if cols[4].button("✏️ Edit", key=f"edit_stay_btn_{int(r['id'])}"):
                    st.session_state["edit_stay_id"] = int(r["id"])
                if pts > 0:
                    alloc = query("SELECT source_type, source_use_year, SUM(points) AS points FROM stay_point_allocations WHERE stay_id=? GROUP BY source_type, source_use_year ORDER BY source_use_year", (int(r['id']),)) if table_exists("stay_point_allocations") else pd.DataFrame()
                    if not alloc.empty:
                        source_text = " + ".join(f"{int(a['points']):,} {a['source_type'].lower()} ({int(a['source_use_year'])})" for _, a in alloc.iterrows())
                        source_text = f" • Points from: **{source_text}**"
                    else:
                        source_text = ""
                    st.caption(
                        f"{r['resort']} • {r['room_type'] or 'Room type not set'} • "
                        f"**${vpp:,.2f} DVC value/point** • "
                        f"🏨 Value alternative **${float(r['value_resort_value'] or 0):,.0f}**" + source_text
                    )
                else:
                    st.caption(f"{r['resort']} • {r['room_type'] or 'Room type not set'} • Points not entered")

    if st.session_state.get("edit_stay_id"):
        sid = st.session_state["edit_stay_id"]
        rr = stay_rows.loc[stay_rows["id"] == sid]
        if not rr.empty:
            r = rr.iloc[0]
            st.markdown("### ✏️ Edit Stay")

            ci = pd.to_datetime(r["check_in"], errors="coerce"); ci = ci.date() if not pd.isna(ci) else date.today()
            co = pd.to_datetime(r["check_out"], errors="coerce"); co = co.date() if not pd.isna(co) else date.today()
            ac = pd.to_datetime(r["actual_dvc_checkout"], errors="coerce"); ac = ac.date() if not pd.isna(ac) else co

            with st.form(f"edit_stay_form_{sid}"):
                s1,s2 = st.columns(2)
                with s1:
                    trip = st.text_input("Trip name", value=r["trip_name"] or "")
                    resort_options = list(DVC_ROOM_TYPES.keys())
                    current_resort = r["resort"] if r["resort"] in resort_options else None
                    if current_resort:
                        resort_idx = resort_options.index(current_resort)
                        resort = st.selectbox("🏰 DVC Resort", resort_options, index=resort_idx, key=f"edit_resort_{sid}")
                    else:
                        resort = st.selectbox("🏰 DVC Resort", resort_options + ["Other / Custom"], index=len(resort_options), key=f"edit_resort_{sid}")
                        if resort == "Other / Custom":
                            resort = st.text_input("Custom resort name", value=r["resort"] or "", key=f"edit_custom_resort_{sid}")

                    room_options = DVC_ROOM_TYPES.get(resort, [])
                    current_room = r["room_type"] or ""
                    if room_options:
                        room_choices = room_options + (["Other / Custom"] if current_room not in room_options else [])
                        room_idx = room_choices.index(current_room) if current_room in room_choices else len(room_choices)-1
                        room_choice = st.selectbox("🛏️ Room Type / View", room_choices, index=room_idx, key=f"edit_room_{sid}")
                        if room_choice == "Other / Custom":
                            room = st.text_input("Custom room type", value=current_room, key=f"edit_custom_room_{sid}")
                        else:
                            room = room_choice
                    else:
                        room = st.text_input("🛏️ Room Type / View", value=current_room, key=f"edit_room_text_{sid}")

                    points = st.number_input("✨ DVC Points Used", min_value=0.0, value=float(r["points_used"] or 0), step=1.0)
                    source_options = ["Auto", "Current use year", "Banked points", "Borrowed from next year"]
                    current_source = r.get("point_source") or "Auto"
                    if current_source not in source_options:
                        current_source = "Auto"
                    point_source = st.selectbox(
                        "Point source (optional override)", source_options,
                        index=source_options.index(current_source),
                        help="Leave this on Auto. The tracker will determine whether the stay used current, banked, or borrowed points. Override only when you know Disney applied a specific source."
                    )
                with s2:
                    check_in = st.date_input("Reserved check-in", value=ci)
                    check_out = st.date_input("Reserved check-out", value=co)
                    actual_checkout = st.date_input("Last morning after an actually-used DVC night", value=ac)

                cash_value = st.number_input(
                    "Full DVC Rack Value", min_value=0.0,
                    value=float(r["cash_room_value"] or 0), step=50.0,
                    help="The full cash rack value of the DVC reservation. This is treated as DVC value earned."
                )
                realized_value = cash_value

                rate_source = st.text_input("Rate source", value=r["rate_source"] or "")

                st.markdown("#### 🏨 Value Resort Alternative")
                vb1, vb2 = st.columns(2)
                with vb1:
                    _opts = ["Pop Century - Standard Room","All-Star Movies - Standard Room","All-Star Sports - Standard Room","Custom"]
                    _cur = r["value_resort_benchmark"] or "Pop Century - Standard Room"
                    if _cur not in _opts: _opts.append(_cur)
                    value_benchmark = st.selectbox("Value Resort Benchmark", _opts, index=_opts.index(_cur), key=f"edit_vb_{sid}")
                with vb2:
                    value_resort_value = st.number_input("Equivalent Value Resort Cost", min_value=0.0, value=float(r["value_resort_value"] or 0), step=25.0)

                notes = st.text_area("Notes", value=r["notes"] or "")

                b1,b2 = st.columns(2)
                save = b1.form_submit_button("💾 Save Changes")
                cancel = b2.form_submit_button("Cancel")
                if save:
                    unused = max(0,(check_out-actual_checkout).days)
                    execute("""
                        UPDATE stays SET trip_name=?,check_in=?,check_out=?,resort=?,room_type=?,points_used=?,
                            actual_dvc_checkout=?,unused_nights=?,alternate_lodging=?,alternate_lodging_cost=?,
                            cash_room_value=?,realized_room_value=?,rate_source=?,value_resort_benchmark=?,value_resort_value=?,point_source=?,point_source_year=?,notes=?
                        WHERE id=?
                    """,(trip,check_in.isoformat(),check_out.isoformat(),resort,room,points,
                         actual_checkout.isoformat(),unused,"",0.0,cash_value,cash_value,
                         rate_source,value_benchmark,value_resort_value,point_source,None,notes,sid))
                    st.session_state.pop("edit_stay_id",None)
                    st.success("Stay updated.")
                    st.rerun()
                if cancel:
                    st.session_state.pop("edit_stay_id",None)
                    st.rerun()

    st.divider()
    if st.button("➕ Add Stay", key="btn_toggle_add_stay"):
        st.session_state["show_add_stay"] = not st.session_state.get("show_add_stay", False)

    if st.session_state.get("show_add_stay", False):
        contracts_stays = query("SELECT id,resort FROM contracts ORDER BY resort")
        if contracts_stays.empty:
            st.warning("Add a contract first.")
        else:
            contract_labels = {f"{r['resort']} (Contract {int(r['id'])})":int(r["id"]) for _,r in contracts_stays.iterrows()}
            with st.form("add_stay"):
                contract_label = st.selectbox("🏰 Contract", list(contract_labels))
                trip = st.text_input("Trip name")
                a1,a2 = st.columns(2)
                with a1:
                    check_in = st.date_input("Reserved check-in", value=date.today())
                with a2:
                    check_out = st.date_input("Reserved check-out", value=date.today())

                resort_choice = st.selectbox(
                    "🏰 DVC Resort",
                    list(DVC_ROOM_TYPES.keys()) + ["Other / Custom"]
                )
                if resort_choice == "Other / Custom":
                    resort = st.text_input("Custom resort name")
                    room = st.text_input("Custom room type / view")
                else:
                    resort = resort_choice
                    room = st.selectbox("🛏️ Villa / Room Type", DVC_ROOM_TYPES[resort_choice])

                points = st.number_input("✨ DVC Points Used", min_value=0.0, step=1.0)
                point_source = st.selectbox(
                    "Point source (optional override)",
                    ["Auto", "Current use year", "Banked points", "Borrowed from next year"],
                    help="Leave this on Auto. The tracker will determine the source from your point balances. Override only if you know Disney used a specific source."
                )
                actual_checkout = st.date_input("Last morning after an actually-used DVC night", value=check_out)
                cash_value = st.number_input(
                    "Full DVC Rack Value", min_value=0.0, step=50.0,
                    help="The full cash rack value of the reservation. The tracker treats this entire amount as DVC value earned."
                )
                rate_source = st.text_input("Rate source")

                st.markdown("#### 🏨 Value Resort Alternative")
                vb1, vb2 = st.columns(2)
                with vb1:
                    value_benchmark = st.selectbox("Value Resort Benchmark", ["Pop Century - Standard Room","All-Star Movies - Standard Room","All-Star Sports - Standard Room","Custom"])
                with vb2:
                    value_resort_value = st.number_input("Equivalent Value Resort Cost", min_value=0.0, step=25.0)

                notes = st.text_area("Notes")

                b1,b2 = st.columns(2)
                add = b1.form_submit_button("✨ Add Stay")
                close = b2.form_submit_button("Cancel")
                if add:
                    unused = max(0,(check_out-actual_checkout).days)
                    execute("""
                        INSERT INTO stays(
                            contract_id,trip_name,check_in,check_out,resort,points_used,cash_room_value,
                            notes,room_type,actual_dvc_checkout,unused_nights,alternate_lodging,
                            alternate_lodging_cost,realized_room_value,rate_source,value_resort_benchmark,value_resort_value,point_source,point_source_year
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,(contract_labels[contract_label],trip,check_in.isoformat(),check_out.isoformat(),
                         resort,points,cash_value,notes,room,actual_checkout.isoformat(),unused,
                         "",0.0,cash_value,rate_source,value_benchmark,value_resort_value,point_source,None))
                    st.session_state["show_add_stay"] = False
                    st.success("Stay added.")
                    st.rerun()
                if close:
                    st.session_state["show_add_stay"] = False
                    st.rerun()


    st.markdown("### 🏆✨ Best Point-Magic Stays")
    st.caption(
        "Ranked by the cash rack value you received for each DVC point. "
        "The Value Resort comparison shows how much additional lodging value the DVC stay delivered."
    )

    ranked = stay_rows.copy()
    if not ranked.empty:
        ranked = ranked[
            (ranked["points_used"].fillna(0) > 0)
            & (ranked["cash_room_value"].fillna(0) > 0)
        ].copy()

    if ranked.empty:
        st.caption("Enter both DVC points used and the DVC rack value to rank your stays.")
    else:
        ranked["DVC $ / Point"] = ranked["cash_room_value"] / ranked["points_used"]

        # Use entered Value Resort benchmark when available.
        # If none is entered, leave it blank here rather than mixing a projection into
        # the historical best-stay ranking.
        ranked["Value Resort Alternative"] = ranked["value_resort_value"].fillna(0)

        ranked["Extra DVC Lodging Value"] = (
            ranked["cash_room_value"] - ranked["Value Resort Alternative"]
        ).where(ranked["Value Resort Alternative"] > 0)

        ranked["Extra Value / Point"] = (
            ranked["Extra DVC Lodging Value"] / ranked["points_used"]
        )

        ranked = ranked.sort_values("DVC $ / Point", ascending=False)

        # Summary cards
        best = ranked.iloc[0]
        overall_vpp = ranked["cash_room_value"].sum() / ranked["points_used"].sum()

        b1, b2, b3 = st.columns(3)
        b1.metric(
            "🏆 Best Stay",
            f"${best['DVC $ / Point']:,.2f}/pt",
            help=str(best["trip_name"])
        )
        b2.metric(
            "✨ Overall DVC Value",
            f"${overall_vpp:,.2f}/pt",
            help="Total DVC rack value divided by total points used."
        )

        with_value = ranked[ranked["Value Resort Alternative"] > 0]
        if not with_value.empty:
            extra_per_point = (
                with_value["cash_room_value"].sum()
                - with_value["Value Resort Alternative"].sum()
            ) / with_value["points_used"].sum()
            b3.metric(
                "🏨 Extra vs Value Resort",
                f"${extra_per_point:,.2f}/pt",
                help="Additional lodging value per point above your entered Value Resort alternatives."
            )
        else:
            b3.metric("🏨 Extra vs Value Resort", "—", help="Add same-date Value Resort costs to unlock this metric.")

        display = ranked[[
            "trip_name",
            "resort",
            "room_type",
            "points_used",
            "cash_room_value",
            "DVC $ / Point",
            "Value Resort Alternative",
            "Extra DVC Lodging Value",
            "Extra Value / Point",
        ]].copy()

        display.columns = [
            "Trip",
            "Resort",
            "Room Type",
            "Points",
            "DVC Rack Value",
            "DVC $ / Point",
            "Value Resort Alternative",
            "Extra DVC Value",
            "Extra Value / Point",
        ]

        display["DVC $ / Point"] = display["DVC $ / Point"].round(2)
        display["Extra Value / Point"] = display["Extra Value / Point"].round(2)

        # Don't show $0 for a missing benchmark; blank is clearer.
        display["Value Resort Alternative"] = display["Value Resort Alternative"].replace(0, pd.NA)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Points": st.column_config.NumberColumn(format="%.0f"),
                "DVC Rack Value": st.column_config.NumberColumn(format="$%.0f"),
                "DVC $ / Point": st.column_config.NumberColumn(format="$%.2f"),
                "Value Resort Alternative": st.column_config.NumberColumn(format="$%.0f"),
                "Extra DVC Value": st.column_config.NumberColumn(format="$%.0f"),
                "Extra Value / Point": st.column_config.NumberColumn(format="$%.2f"),
            }
        )

        st.markdown("#### ✨ Value per Point")
        chart_df = ranked[["trip_name", "DVC $ / Point"]].copy()
        fig_best = px.bar(
            chart_df,
            x="trip_name",
            y="DVC $ / Point",
            text_auto=".2f",
            title="DVC rack value received per point"
        )
        fig_best.update_layout(
            height=390,
            xaxis_title="",
            yaxis_title="Dollars of DVC room value per point",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_best, use_container_width=True)


with tabs[4]:
    st.header("🎟️ Trip Expenses")
    stay_rows = query("SELECT id,trip_name,check_in FROM stays ORDER BY check_in DESC")
    opts = {"Not tied to one stay": None}
    for _,r in stay_rows.iterrows():
        opts[f"{r['trip_name']} ({r['check_in']})"] = int(r["id"])

    with st.form("add_expense"):
        stay_label = st.selectbox("Related stay", list(opts))
        expense_date = st.date_input("Expense date", value=date.today())
        category = st.selectbox("Category", [
            "Annual Pass / Tickets","Food & Dining","Merchandise","Transportation",
            "Airfare","Parking / Tolls","Special Events","Lightning Lane","Rental Car","Other"
        ])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=10.0)
        attribution_pct = st.slider("How much was caused by DVC ownership?", 0, 100, 100, 10)
        notes = st.text_area("Notes")
        if st.form_submit_button("✨ Add Expense"):
            execute("""
                INSERT INTO expenses(stay_id,expense_date,category,description,amount,attribution_pct,notes)
                VALUES(?,?,?,?,?,?,?)
            """, (opts[stay_label],expense_date.isoformat(),category,description,amount,attribution_pct,notes))
            st.success("Expense added.")
            st.rerun()

    exp_view = query("""
        SELECT e.id,COALESCE(s.trip_name,'—') AS "Trip",e.expense_date AS "Date",
               e.category AS "Category",e.description AS "Description",e.amount AS "Amount",
               e.attribution_pct AS "DVC Attribution %",
               ROUND(e.amount*e.attribution_pct/100.0,2) AS "DVC-Attributed Amount"
        FROM expenses e LEFT JOIN stays s ON e.stay_id=s.id
        ORDER BY e.expense_date DESC,e.id DESC
    """)
    st.dataframe(exp_view, use_container_width=True, hide_index=True)


# ============================================================
# ============================================================
# POINT LEDGER
# ============================================================
with tabs[5]:
    st.markdown("## 📊 Point Ledger — Automatic Use-Year Schedule")
    st.caption("Your contract tells the tracker how many points you receive every year. Your Stays tell it how many points you used. You only enter banking, borrowing and forfeiture adjustments.")
    if contracts.empty:
        st.info("Add a contract first.")
    else:
        contract_options = {f"{r['resort']} — {int(r['points'] or 0)} pts • Use Year: {r['use_year'] or 'June'}": int(r['id']) for _, r in contracts.iterrows()}
        sel = st.selectbox("Contract", list(contract_options))
        cid = contract_options[sel]
        crow = contracts[contracts["id"] == cid].iloc[0]
        purchase_ts = pd.to_datetime(crow["purchase_date"], errors="coerce")
        purchase_y = int(purchase_ts.year) if pd.notna(purchase_ts) else date.today().year
        end_ts = pd.to_datetime(crow["contract_end_date"], errors="coerce")
        end_y = int(end_ts.year) if pd.notna(end_ts) else current_year
        led = query("SELECT * FROM point_ledger WHERE contract_id=? ORDER BY use_year", (cid,))
        st.markdown("### 🧮 Automatic calculation")
        st.markdown("**Annual Points** = contract allocation  ·  **Used** = points from Stays assigned to that use year  ·  **Banked In** = prior year banked out  ·  **Borrowed Out** = current points borrowed by the prior year  ·  **Remaining** = all available points minus used and forfeited points.")
        if not led.empty:
            display=led.copy()
            display["Available"]=(display["annual_points"]+display["banked_in"]-display["banked_points"]-display["expired_points"]).clip(lower=0)
            display["Remaining"]=(display["Available"]-display["used_points"]).clip(lower=0)
            display["Utilization"]=(display["used_points"]/display["Available"].replace(0,pd.NA)*100).round(1)
            display["Status"]=display["use_year"].apply(lambda y:"Current" if int(y)==current_year else ("Past" if int(y)<current_year else "Future"))
            display=display[["use_year","Status","annual_points","banked_in","banked_points","borrowed_out","used_points","expired_points","Available","Remaining","Utilization"]]
            display.columns=["Use Year","Status","Annual Points","Banked In","Banked Out","Borrowed by Earlier Stays","Used (from Stays)","Expired / Forfeited","Available","Remaining","Utilization"]
            st.dataframe(display,use_container_width=True,hide_index=True,column_config={
                "Annual Points":st.column_config.NumberColumn(format="%.0f"),"Banked In":st.column_config.NumberColumn(format="%.0f"),"Banked Out":st.column_config.NumberColumn(format="%.0f"),"Borrowed by Earlier Stays":st.column_config.NumberColumn(format="%.0f"),"Used (from Stays)":st.column_config.NumberColumn(format="%.0f"),"Expired / Forfeited":st.column_config.NumberColumn(format="%.0f"),"Available":st.column_config.NumberColumn(format="%.0f"),"Remaining":st.column_config.NumberColumn(format="%.0f"),"Utilization":st.column_config.NumberColumn(format="%.1f%%")})
            # Show where the current points actually sit.
            cur_rows = display[display["Status"] == "Current"]
            if not cur_rows.empty:
                rr = cur_rows.iloc[0]
                st.info(f"**{int(rr['Use Year'])} use year:** {int(rr['Annual Points'])} annual + {int(rr['Banked In'])} banked in − {int(rr['Banked Out'])} banked out − {int(rr['Used (from Stays)'])} used − {int(rr['Expired / Forfeited'])} forfeited = **{int(rr['Remaining'])} points currently available**. Points borrowed by an earlier stay are already included in that use year's used total.")

            st.caption("Stays default to **Auto**. The tracker uses the points that actually exist: banked points first when available, then the current use-year allocation, then future-year points only when the reservation needs borrowing. If Disney applied a different source, edit that stay and choose the appropriate override.")

            st.markdown("### ✏️ Record point adjustments")
            st.caption("Do not enter Annual Points, Used, or Borrowed In. Those are automatic. Enter only points you intentionally bank or forfeit. Borrowing is derived from the stays that require future-year points.")
            adj_years=sorted(int(y) for y in led["use_year"].tolist())
            with st.form("point_adjustments"):
                a,b,c,d=st.columns(4)
                with a: ly=st.selectbox("Use Year",adj_years,index=adj_years.index(current_year) if current_year in adj_years else 0)
                existing=led[led["use_year"]==ly]; er=existing.iloc[0] if not existing.empty else None
                with b: banked_out=st.number_input("Banked Out",min_value=0.0,value=float(er["banked_points"] or 0) if er is not None else 0.0,step=1.0)
                with c: expired=st.number_input("Expired / Forfeited",min_value=0.0,value=float(er["expired_points"] or 0) if er is not None else 0.0,step=1.0)
                with d: notes=st.text_input("Notes",value=str(er["notes"] or "") if er is not None else "")
                if st.form_submit_button("💾 Save Adjustments"):
                    if er is None:
                        execute("INSERT INTO point_ledger(contract_id,use_year,annual_points,banked_points,borrowed_points,used_points,expired_points,notes,banked_in,borrowed_out) VALUES(?,?,?,?,?,?,?,?,?,?)",(cid,ly,float(crow["points"] or 0),banked_out,0.0,0.0,expired,notes,0.0,0.0))
                    else:
                        execute("UPDATE point_ledger SET banked_points=?,expired_points=?,notes=? WHERE id=?",(banked_out,expired,notes,int(er["id"])))
                    sync_point_ledger(); st.success("Saved. Used points and borrowing are calculated from Stays."); st.rerun()
            cur=display[display["Status"]=="Current"]
            if not cur.empty:
                rr=cur.iloc[0]
                st.success(f"**{int(rr['Use Year'])} use year:** {int(rr['Remaining'])} points remaining · {int(rr['Used (from Stays)'])} points used automatically from your Stays. Borrowing is shown automatically when needed.")
        else:
            st.info("The schedule is generated automatically from the contract. Add Stays to populate used points.")

# DATA
# ============================================================
with tabs[6]:
    st.header("📦 Data / Export")
    for title, table in [("Contracts","contracts"),("Annual Dues","dues"),("Stays","stays"),("Expenses","expenses"),("Point Ledger","point_ledger"),("Historical Benchmarks","historical_benchmarks")]:
        st.subheader(title)
        df = query(f"SELECT * FROM {table}")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            f"Download {title} CSV", df.to_csv(index=False).encode("utf-8"),
            file_name=f"{table}.csv", mime="text/csv", key=f"dl_{table}"
        )
