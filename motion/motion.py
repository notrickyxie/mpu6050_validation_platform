import gpiod
from time import sleep, time

PWM_PERIOD_S = 0.020      # 20 ms period = 50 Hz
MIN_PULSE_S = 0.00075
MAX_PULSE_S = 0.00225

GPIO_CHIP = "/dev/gpiochip0"
SERVO_GPIO = 18


def angle_to_pulse(angle_deg):
    if angle_deg < 0:
        angle_deg = 0
    if angle_deg > 180:
        angle_deg = 180

    pulse_range = MAX_PULSE_S - MIN_PULSE_S
    pulse_width = MIN_PULSE_S + (angle_deg / 180.0) * pulse_range
    return pulse_width


def send_servo_pulse(servo_req, angle_deg):
    pulse_width = angle_to_pulse(angle_deg)

    servo_req.set_value(SERVO_GPIO, gpiod.line.Value.ACTIVE)
    sleep(pulse_width)

    servo_req.set_value(SERVO_GPIO, gpiod.line.Value.INACTIVE)
    sleep(PWM_PERIOD_S - pulse_width)


def hold_angle(servo_req, angle_deg, hold_time_s):
    start_time = time()
    while time() - start_time < hold_time_s:
        send_servo_pulse(servo_req, angle_deg)


SYNC_PULSE = [
    (0, 2.0),
    (180, 0.5),
    (0, 0.5),
    (180, 0.5),
    (0, 2.0),
]

TC2_STATIC_REST = [(0, 10)]

TC3_SERVO_STEP = [
    (0, 3),
    (30, 3),
    (60, 3),
    (90, 3),
    (120, 3),
    (150, 3),
    (180, 3),
    (150, 3),
    (120, 3),
    (90, 3),
    (60, 3),
    (30, 3),
    (0, 3),
]

TC4_SLOW_SWEEP = (
    [(angle, 0.25) for angle in range(0, 181, 5)] +
    [(angle, 0.25) for angle in range(175, -1, -5)]
)

TC5_FAST_SWEEP = (
    [(angle, 0.10) for angle in range(0, 181, 10)] +
    [(angle, 0.10) for angle in range(170, -1, -10)]
)

TC6_REPEATED_CYCLE = []
for _ in range(5):
    TC6_REPEATED_CYCLE.extend([
        (0, 1),
        (90, 1),
        (180, 1),
        (90, 1),
    ])

profiles = {
    "TC2_STATIC_REST": TC2_STATIC_REST,
    "TC3_SERVO_STEP": TC3_SERVO_STEP,
    "TC4_SLOW_SWEEP": TC4_SLOW_SWEEP,
    "TC5_FAST_SWEEP": TC5_FAST_SWEEP,
    "TC6_REPEATED_CYCLE": TC6_REPEATED_CYCLE,
}


def run_profile(servo_req, profile, name):
    print(f"\nRunning sync pulse for {name}")
    for angle, hold_time in SYNC_PULSE:
        print(f"[SYNC] Moving to {angle} degrees for {hold_time} seconds")
        hold_angle(servo_req, angle, hold_time)

    print(f"\nStarting {name}")
    for angle, hold_time in profile:
        print(f"Moving to {angle} degrees for {hold_time} seconds")
        hold_angle(servo_req, angle, hold_time)
    print(f"Finished {name}")


def main():
    chip = gpiod.Chip(GPIO_CHIP)

    servo_req = chip.request_lines(
        consumer="motion-servo",
        config={
            SERVO_GPIO: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT
            )
        },
        output_values={
            SERVO_GPIO: gpiod.line.Value.ACTIVE
        }
    )

    try:
        for test_name, profile in profiles.items():
            run_profile(servo_req, profile, test_name)

    finally:
        hold_angle(servo_req, 0, 0.5)
        servo_req.set_value(SERVO_GPIO, gpiod.line.Value.INACTIVE)
        servo_req.release()
        chip.close()


if __name__ == "__main__":
    main()