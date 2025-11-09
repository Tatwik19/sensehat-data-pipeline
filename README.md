# sensehat-data-pipeline
Sense HAT → PostgreSQL → Plotly Dash: Minimal IIoT pipeline


# Repository layout

```
sensehat-pg-dash/
├─ collector/                # code that runs on the Raspberry Pi
│  ├─ Lab_12.py              # Sense HAT → PostgreSQL writer
├─ dashboard/                # code that runs on the laptop (or any host)
│  ├─ dash_app.py            # Plotly Dash UI
├─ assets/
│  ├─ psql.jpg               # DB screenshot
│  ├─ dashboard.png          # dashboard screenshot
├─ requirements.txt          # pinned Python deps for both sides
└─ README.md
```

# supporting files

## `requirements.txt`

```
dash>=2.17
plotly>=5.22
pandas>=2.2
psycopg2-binary>=2.9
sense-hat>=2.6 
python-dotenv>=1.0
```

## Overview

The Raspberry Pi reads Sense HAT measurements, writes rows into PostgreSQL, and a Dash app on a laptop visualizes recent data with live refresh. This project includes:

* Pi “collector” script that creates the table if missing and inserts rows every 5 s.
* Dash dashboard that queries the last N records and renders six time-series charts.
* Step-by-step setup for Pi and laptop, with environment variables and pinned packages.

## Architecture

Edge: Raspberry Pi 4 + Sense HAT
Database: PostgreSQL on the Pi
Visualization: Plotly Dash running on the laptop, reading the Pi’s database over LAN

## Prerequisites

### Hardware

* Raspberry Pi 4 with Sense HAT attached and working.
* Laptop on the same network as the Pi.

### Software

* Raspberry Pi OS (Bookworm or Bullseye).
* Python 3.9+ on both machines.
* PostgreSQL 14+ on the Pi.

## 1) Raspberry Pi setup (edge and database)

1. Update OS and firmware.

   ```bash
   sudo apt update && sudo apt -y full-upgrade
   sudo reboot
   ```

2. Install packages.

   ```bash
   sudo apt -y install python3-venv python3-pip python3-dev \
                       postgresql postgresql-contrib \
                       libsense-hat python3-sense-hat
   ```

3. Create PostgreSQL role and database.

   ```bash
   sudo -u postgres psql <<'SQL'
   CREATE ROLE group2 WITH LOGIN PASSWORD 'change-me';
   CREATE DATABASE iiot_lab OWNER group2;
   \q
   SQL
   ```

4. Allow LAN access to PostgreSQL.

   * Edit `/etc/postgresql/*/main/postgresql.conf`:

     ```
     listen_addresses = '*'
     ```
   * Edit `/etc/postgresql/*/main/pg_hba.conf` and add a LAN rule (replace subnet):

     ```
     host    all     all     10.234.143.0/24     md5
     ```
   * Restart:

     ```bash
     sudo systemctl restart postgresql
     ```

5. Verify you can connect locally.

   ```bash
   psql -U group2 -d iiot_lab -h localhost -W
   ```

6. Clone the repo onto the Pi and set up a venv.

   ```bash
   git clone <your-repo-url> sensehat-pg-dash
   cd sensehat-pg-dash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

7. Configure environment variables on the Pi.

   ```bash
   cp .env.example .env
   # Edit .env so PGHOST=localhost and PGPASSWORD=your password
   sed -i 's/^PGHOST=.*/PGHOST=localhost/' .env
   ```

8. Start the collector.

   ```bash
   source .venv/bin/activate
   python collector/Lab_12.py
   ```

   The script will create table `sensor_data` if missing and append a row every 5 s.

9. Optional: run the collector as a service.

   ```bash
   sudo tee /etc/systemd/system/sensehat-collector.service >/dev/null <<'UNIT'
   [Unit]
   Description=Sense HAT → PostgreSQL collector
   After=network-online.target postgresql.service
   Wants=network-online.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/sensehat-pg-dash
   EnvironmentFile=/home/pi/sensehat-pg-dash/.env
   ExecStart=/home/pi/sensehat-pg-dash/.venv/bin/python collector/Lab_12.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   UNIT
   sudo systemctl daemon-reload
   sudo systemctl enable --now sensehat-collector
   ```

## 2) Laptop setup (dashboard host)

1. Clone the same repo and make a venv.

   ```bash
   git clone <your-repo-url> sensehat-pg-dash
   cd sensehat-pg-dash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure the laptop `.env` to point to the Pi.

   ```bash
   cp .env.example .env
   # Set PGHOST to the Pi’s IP and set PGPASSWORD accordingly.
   # Optionally change DASH_PORT.
   ```

3. Test DB connectivity from the laptop.

   ```bash
   python -c "import psycopg2,os;print(psycopg2.connect(host=os.getenv('PGHOST'),database=os.getenv('PGDATABASE'),user=os.getenv('PGUSER'),password=os.getenv('PGPASSWORD')).get_dsn_parameters())"
   ```

4. Run the dashboard.

   ```bash
   source .venv/bin/activate
   python dashboard/dash_app.py
   ```

   Open `http://<laptop-ip>:8050` or `http://localhost:8050`.

## 3) Security notes

* Change the default DB password. Do not commit `.env`.
* Restrict PostgreSQL to your LAN. Prefer a firewall:

  ```bash
  sudo apt -y install ufw
  sudo ufw allow from 10.234.143.0/24 to any port 5432 proto tcp
  sudo ufw enable
  ```
* If the laptop is remote, use an SSH tunnel instead of opening 5432.

## 4) Data model

Table `sensor_data`:

```
id SERIAL PRIMARY KEY
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
temperature FLOAT
humidity FLOAT
pressure FLOAT
pitch FLOAT
roll FLOAT
yaw FLOAT
```

## 5) Operations

* List recent rows:

  ```sql
  SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;
  ```
* Purge data:

  ```sql
  DELETE FROM sensor_data;
  VACUUM;
  ```

## 6) Troubleshooting

* **Dashboard empty:** check that `PGHOST` points to the Pi and you can `psql` from the laptop. Confirm `pg_hba.conf` has your laptop subnet.
* **Collector errors:** verify Sense HAT is detected (`python -c "from sense_hat import SenseHat;print(SenseHat().get_temperature())"`).
* **Time skew:** ensure Pi and laptop use NTP (`timedatectl status`).
* **High CPU on Pi:** lower frequency by increasing `time.sleep()` in the collector.

## 7) Screenshots

See `assets/psql.jpg` for the table preview and `assets/dashboard.png` for the charts.


# Notes

* `collector/Lab_12.py` writes Sense HAT readings to PostgreSQL every 5 s and creates the table on first run.
* `dashboard/dash_app.py` polls the last ~300 rows every 5 s and renders six line charts.

