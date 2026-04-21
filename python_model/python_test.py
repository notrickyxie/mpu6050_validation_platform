from time import sleep, time
from pathlib import Path
import csv
from adafruit_mpu6050 import MPU6050

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "python_log.csv"

mpu = MPU6050("/dev/i2c-1", 0x68)

try:
    with open(LOG_FILE, "w", newline="") as f:
        f.write(f"# WHO_AM_I={mpu.device_id}\n")
        writer = csv.writer(f)
        writer.writerow([
            "timestamp_s",
            "ax", "ay", "az",
            "gx", "gy", "gz"
        ])

        print(f"0x{mpu.device_id:02X}")

        while True:
            timestamp = time()
            ax, ay, az = mpu.acceleration
            gx, gy, gz = mpu.gyro
            temp = mpu.temperature

            print(f"time : {timestamp:.3f}")
            print(f"accel: {ax:.3f}, {ay:.3f}, {az:.3f} m/s^2")
            print(f"gyro : {gx:.3f}, {gy:.3f}, {gz:.3f} rad/s")
            print()

            writer.writerow([timestamp, ax, ay, az, gx, gy, gz])
            f.flush()
            sleep(0.5)

finally:
    mpu.close()