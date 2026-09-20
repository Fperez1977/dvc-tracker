# DVC Tracker v3.7

A Streamlit app for tracking the true cost and value of a Disney Vacation Club membership: contracts, annual dues, stays, trip expenses, and an automatic point ledger.

## Automatic Point Ledger
- Annual entitlement is derived from each contract every use year through contract expiration.
- Used points are derived automatically from recorded Stays using the contract use-year month.
- Banked-out, borrowed-in, and expired/forfeited points are the only manual point adjustments.
- Banked-in and borrowed-out flows are carried to adjacent use years automatically.
- Dashboard reports current-use-year points remaining rather than inventing lifetime unused points.
- Chrome/light theme fixes from v3.4 are retained.

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

Before the first `docker compose up`, set your password (see **Password protection** below) — otherwise the proxy container will fail to start with a "set BASIC_AUTH_USER" error.

Then browse to `http://<nas-ip>:8501` and log in with the username/password you set.

### Password protection

The app itself has no login. Instead, an nginx reverse-proxy container sits in front of it and requires HTTP Basic Auth before any request reaches Streamlit — the `dvc-tracker` container isn't published to the host at all, only the `proxy` container is.

Set it up once, on the NAS, before first starting the stack:

```bash
cd /volume1/docker/dvc-tracker   # or wherever you cloned this repo
cp .env.example .env
nano .env   # set BASIC_AUTH_USER and BASIC_AUTH_PASSWORD to your own values
```

`.env` is gitignored, so your real username/password never get committed or pushed to GitHub — they only exist in that file on the NAS. The password is read fresh at container start each time (`docker compose up`/`restart`), so changing `.env` and running `sudo docker compose up -d` again rotates the password.

If you ever need to disable auth temporarily (e.g. local debugging), you can bypass the proxy by adding a `ports: ["8501:8501"]` entry back onto the `dvc-tracker` service in `docker-compose.yml` — just remember to remove it again afterward.

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

If port 8501 is already in use on your NAS, edit the `ports:` line under the **`proxy`** service in `docker-compose.yml` (e.g. `"8601:80"`), then re-run `docker compose up -d`.

### HTTPS (optional)

To serve this under a subdomain with a Synology-issued certificate, add a **Control Panel → Login Portal → Advanced → Reverse Proxy** rule pointing your desired hostname/port at `localhost:8501` (or whatever host port you chose above). The Basic Auth prompt from the `proxy` container still applies on top of that.
