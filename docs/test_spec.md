# Test Specification - MPU6050 Validation Platform

## Purpose
This project is a hardware-software validation platform built around an **MPU6050 IMU** connected to a **Raspberry Pi 4B**. The goal is to validate a low-level **C driver** against a **Python golden model** so that register configuration, sensor parsing, scaling, and output behavior can be checked through measurable pass/fail criteria.

## System Under Test
- Raspberry Pi 4B
- MPU6050 IMU
- I2C interface
- Python golden model
- C DUT using Linux `i2c-dev`
- Servo-based motion fixture for repeatable angle changes

## Validation Approach
The IMU will be mounted to a servo-driven fixture so the Python golden model and C DUT can be tested under the same repeatable motion profile.

The validation flow is:
1. Mount the MPU6050 on a servo fixture.
2. Command the servo through a defined angle sequence.
3. Run the Python golden model and log outputs.
4. Repeat the same servo command sequence with the C DUT.
5. Compare both logs using validation metrics.
6. Determine PASS/FAIL based on defined thresholds.

## Signals Under Validation
The following outputs will be compared between the Python golden model and the C DUT:
- ax
- ay
- az
- gx
- gy
- gz

If angle estimation is added later through software processing, the following derived signals may also be compared:
- roll
- pitch

## Log Format
Both implementations must produce logs using the same schema so they can be compared directly.

Example CSV format:

timestamp_us,ax,ay,az,gx,gy,gz

If derived angles are included later:

timestamp_us,ax,ay,az,gx,gy,gz,roll,pitch

## Test Cases

### TC1 - WHO_AM_I / Bring-Up Check
Description:  
Verify that the device responds at the expected I2C address and returns the correct identity register value.

Purpose:  
Confirm basic communication and correct device targeting before running motion tests.

Expected behavior:
- device is detected on the I2C bus
- `WHO_AM_I` register matches expected value
- device exits sleep mode successfully
- no initialization or register access failure

### TC2 - Static Rest
Description:  
The IMU remains flat and stationary for 10 seconds.

Purpose:  
Verify low noise, low drift, and stable stationary output.

Expected behavior:
- accelerometer values remain stable
- gyroscope values remain near zero
- no invalid reads or dropped samples

### TC3 - Servo Step Angle Test
Description:  
The servo moves the IMU to fixed angular positions, for example:
- 0 degrees
- 30 degrees
- 60 degrees
- 90 degrees

with a hold period at each step.

Purpose:  
Verify that the DUT tracks repeatable motion changes similarly to the Python golden model.

Expected behavior:
- stable output at each hold position
- consistent sign and scaling
- small steady-state error relative to reference

### TC4 - Slow Servo Sweep
Description:  
The servo sweeps slowly through a defined angular range, for example 0 to 90 degrees and back.

Purpose:  
Verify agreement during smooth motion and check for lag or scaling mismatch.

Expected behavior:
- smooth change in accelerometer and gyroscope outputs
- similar trend and shape between Python and C logs
- limited timing mismatch

### TC5 - Fast Servo Sweep
Description:  
The servo performs a faster sweep through the same angular range.

Purpose:  
Test whether the DUT still tracks the motion correctly under higher-rate motion.

Expected behavior:
- correct sign and direction
- no major spikes or missing sections
- acceptable deviation from Python golden model

### TC6 - Repeated Cycle Test
Description:  
The servo repeats the same movement cycle multiple times, such as:
0 degrees -> 90 degrees -> 0 degrees, repeated 10 times.

Purpose:  
Check repeatability and look for drift, missed samples, or accumulating error.

Expected behavior:
- similar output on each cycle
- low drift over repeated cycles
- no register-read, parser, or logging failure

### TC7 - Stress / Fault Case
Description:  
The DUT is tested with an intentionally introduced software fault such as:
- wrong scaling factor
- sign inversion
- incorrect register mapping
- byte-order mistake

Purpose:  
Verify that the validation framework detects known faults.

Expected behavior:
- comparison script flags FAIL
- failing metric clearly identifies the issue

## Validation Metrics
The following metrics will be used to compare the Python golden model and C DUT:
- RMS error per signal
- maximum absolute deviation
- steady-state error at hold positions
- drift over time
- sample count mismatch
- timing or alignment offset if needed

## Pass/Fail Criteria
A test case passes if all required signals remain within defined limits and the output stream remains valid for the full test duration.

Initial target thresholds:
- RMS error < 2%
- maximum deviation < 5%
- steady-state hold error remains within target tolerance
- no sign inversion
- no invalid register access or parser failure
- no dropped-data behavior that invalidates the test

These thresholds may be refined after initial baseline data collection.

## Failure Injection Tests
The DUT will be intentionally modified to verify that the validation framework can catch faults.

Planned injected failures:
- incorrect scaling factor
- axis sign inversion
- incorrect register mapping
- byte-order/parsing error

Expected result:
- comparison output shows FAIL
- offending metric is clearly reported

## Test Procedure
1. Mount the MPU6050 on the servo fixture.
2. Verify wiring and I2C communication.
3. Confirm device address and `WHO_AM_I` value.
4. Select a predefined servo motion profile.
5. Run the Python golden model and record a log.
6. Reset the system if needed.
7. Run the C DUT and replay the same servo motion profile.
8. Save both logs using the same schema.
9. Run the comparison script.
10. Compute metrics and determine PASS/FAIL.
11. Save the validation report.

## Deliverables
- python_log.csv
- dut_log.csv
- servo_motion_profile.txt or source script
- validation_results.txt or JSON
- failure_injection_results.md
- final validation report