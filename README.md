# DVC Tracker v3.10

A Streamlit app for tracking the true cost and value of a Disney Vacation Club membership: contracts, annual dues, stays, trip expenses, and an automatic point ledger.

## Password Protection Rework (v3.10)
Replaced the nginx + HTTP Basic Auth sidecar with an in-app password screen — same pattern as the Hunger Hive app: one `APP_PASSWORD`, no username, checked inside Streamlit itself. The `proxy` container and `nginx/` folder are gone; `dvc-tracker` now publishes port 8501 directly. See **Password protection** below.

## Dashboard Priority Order (v3.9)
The Dashboard is now ordered around what you actually open it to check, top to bottom:
1. **Banking deadline alerts** — only shown when a deadline is actually approaching or overdue.
2. **Your Points Right Now** — remaining points per contract, current use year, and the bank-by/use-by dates. Aggregates across contracts if you have more than one.
3. **Are You Getting Your Money's Worth?** — one headline answer (broke even in `<year>` / on pace for `<year>` / not on pace), computed vs. paying cash for the same rooms.
4. Everything else — Ownership/Performance KPIs, the full lifetime break-even detail (assumptions, chart, all 4 comparison bases), the year-by-year table, and the Financial Health score — still there, just below, and the deepest/most detailed pieces (year-by-year table, Financial Health) are now collapsed by default instead of always expanded.

The headline in #3 and the detailed projection further down share the exact same calculation function, so they can't drift out of sync with each other — the headline just uses your last-saved assumptions, and the detailed section lets you tune them live.

## Automatic Point Ledger
- Annual entitlement is derived from each contract every use year through contract expiration.
- Used points are derived automatically from recorded Stays using the contract use-year month.
- Banked-out, borrowed-in, and expired/forfeited points are the only manual point adjustments.
- Banked-in and borrowed-out flows are carried to adjacent use years automatically.
- Dashboard reports current-use-year points remaining rather than inventing lifetime unused points.
- Chrome/light theme fixes from v3.4 are retained.

## Banking Deadline Reminders (v3.8)
The Dashboard now warns you before you lose points. For each contract, it checks whether the current use year still has unbanked, unused points as DVC's 8-months-from-use-year-start banking deadline approaches (e.g. a June use year must be banked by January 31):
- **45–15 days out:** a heads-up banner.
- **14 days or less:** an urgent banner.
- **Deadline already passed:** an overdue banner, with the date those points are actually forfeited (the end of the use year) if you still don't use them.

This is computed from your existing contracts/ledger data — no setup required. It only fires when you actually have unbanked points at risk; fully banked or fully used use years stay quiet.

v3.6: Fixed startup NameError from point-ledger migration by using the DB execute helper instead of an out-of-scope connection.

---

## Running locally (no Docker)

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app creates `dvc_tracker.db` (SQLite) and a `purchase_agreements/` folder in the working directory on first run.

Optional: `python seed_historical_stays.py` seeds two example historical stays into the DB (requires a contract to already exist).

---

## Deploying on Synology via Docker (Container Manager)

This repo ships a `Dockerfile` and `docker-compose.yml` so it can be built and run directly on a Synology NAS with **Container Manager** (DSM 7.2+; called Docker on older DSM versions).

### Option A — Container Manager UI (Project)

1. On the NAS, create a shared folder (e.g. `docker/dvc-tracker`) and copy this whole repo into it — either via `git clone` over SSH (see below) or by uploading the folder with File Station.
2. Open **Container Manager → Project → Create**.
3. Set **Project name**: `dvc-tracker`, **Path**: the folder from step 1.
4. Choose **Create docker-compose.yml** → **Use existing `docker-compose.yml`** (it's already in the repo).
5. Build and run. Container Manager will build the image on the NAS and start the container.
6. Browse to `http://<nas-ip>:8501`.

### Option B — SSH + docker compose

```bash
ssh <user>@<nas-ip>
sudo mkdir -p /volume1/docker/dvc-tracker
cd /volume1/docker/dvc-tracker
git clone <your-repo-url> .
sudo docker compose up -d --build
```

Before the first `docker compose up`, set your password (see **Password protection** below) if you want one — otherwise the app starts with no login at all.

Then browse to `http://<nas-ip>:8501`. If you set a password, you'll see a simple password screen first — no username, just like the Hunger Hive app.

### Password protection

Same pattern as the Hunger Hive app: a single `APP_PASSWORD`, checked inside the app itself (no separate proxy container, no username field) — just a password box, and a "Log out" button in the top-right once you're in. Leaving `APP_PASSWORD` unset/blank runs the app with no login at all, which keeps local testing frictionless.

Set it up once, on the NAS, before first starting the stack:

```bash
cd /volume1/docker/dvc-tracker   # or wherever you cloned this repo
cp .env.example .env
cat > .env << 'EOF'
APP_PASSWORD=your-password-here
EOF
```

(`nano` isn't available on stock DSM's SSH shell — the heredoc above works the same way. Swap in `vi .env` if you prefer an editor.)

`.env` is gitignored, so your real password never gets committed or pushed to GitHub — it only exists in that file on the NAS. It's read once when the container starts, so changing `.env` and running `sudo docker compose up -d` again rotates the password (no rebuild needed, just a container restart — compose picks up the new environment value automatically).

One difference from the Hunger Hive app worth knowing: that app's login persists for 30 days via a signed cookie. Streamlit's `session_state` only lasts for the current browser session (closing the tab, or the app restarting, logs you out) — there's no long-lived "remember me" here without adding an extra package. Fine for occasional use; worth flagging if it becomes annoying.

### Data persistence

`docker-compose.yml` mounts `./data` (next to the compose file, on the NAS) into the container. Your SQLite database (`dvc_tracker.db`) and any uploaded purchase-agreement PDFs live there, so they survive container rebuilds, restarts, and image upgrades. **Back up that `data/` folder** (e.g. with Synology Hyper Backup) — it's the only thing that isn't reproducible from git.

### Updating after a git push

```bash
cd /volume1/docker/dvc-tracker
git pull
sudo docker compose up -d --build
```

Or, in Container Manager's UI: open the project → **Action → Build** after pulling the latest code (Container Manager itself doesn't `git pull`; do that over SSH first, or set up a scheduled task that runs `git pull` on the NAS).

### Changing the port

If port 8501 is already in use on your NAS, edit the `ports:` line under the **`dvc-tracker`** service in `docker-compose.yml` (e.g. `"8601:8501"`), then re-run `docker compose up -d`.

### HTTPS (optional)

To serve this under a subdomain with a Synology-issued certificate, add a **Control Panel → Login Portal → Advanced → Reverse Proxy** rule pointing your desired hostname/port at `localhost:8501` (or whatever host port you chose above). The in-app password screen still applies on top of that.
