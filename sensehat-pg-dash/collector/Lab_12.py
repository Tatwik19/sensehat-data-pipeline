from sense_hat import SenseHat
import time
import psycopg2
import random

sense = SenseHat()

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="iiot_lab",
    user="group2",
    password="mfg598"
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature FLOAT,
    humidity FLOAT,
    pressure FLOAT,
    pitch FLOAT,
    roll FLOAT,
    yaw FLOAT
);
""")
conn.commit()

while True:
    t = sense.get_temperature()
    h = sense.get_humidity()
    p = sense.get_pressure()
    o = sense.get_orientation()  # dict with pitch, roll, yaw

    # Simulate small variations
    t += random.uniform(-0.3, 0.3)
    h += random.uniform(-0.5, 0.5)
    p += random.uniform(-0.2, 0.2)

    cur.execute(
        "INSERT INTO sensor_data (temperature, humidity, pressure, pitch, roll, yaw) VALUES (%s,%s,%s,%s,%s,%s)",
        (t, h, p, o['pitch'], o['roll'], o['yaw'])
    )
    conn.commit()
    time.sleep(5)
