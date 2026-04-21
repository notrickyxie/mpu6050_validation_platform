# Test Specification - MPU6050 Validation Platform

## Purpose
This project is a hardware-software validation platform built around an **MPU6050 IMU** connected to a **Raspberry Pi 4B**. The goal is to validate a low-level **C driver** against a **Python golden model** so that register configuration, sensor parsing, scaling, and output behavior can be checked through measurable pass/fail criteria.

## System Under Test
- Raspberry Pi 4B
- MPU6050 IMU
- I2C interface
- Python golden model
- C DUT using Linux `i2c-dev` and `ioctl`
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

### Motion Test Assumption
The listed servo angles represent commanded positions, not calibrated physical angles. Because this project compares the C DUT against the Python golden model under the same input motion, exact angle accuracy is less important than repeatability and consistency between runs.

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
The servo moves the IMU through the commanded step profile:
- 0 degrees for 3 seconds
- 30 degrees for 3 seconds
- 60 degrees for 3 seconds
- 90 degrees for 3 seconds
- 120 degrees for 3 seconds
- 150 degrees for 3 seconds
- 180 degrees for 3 seconds
- 150 degrees for 3 seconds
- 120 degrees for 3 seconds
- 90 degrees for 3 seconds
- 60 degrees for 3 seconds
- 30 degrees for 3 seconds
- 0 degrees for 3 seconds

Purpose:  
Verify that the DUT tracks repeatable position changes and settles correctly at each commanded hold angle compared to the Python golden model.

Expected behavior:
- stable output at each hold position
- clear transitions between commanded angles
- consistent sign and scaling across the full commanded range
- small steady-state error relative to reference

### TC4 - Slow Servo Sweep
Description:  
The servo follows the commanded slow sweep profile:
- sweep from 0 degrees to 180 degrees in 5 degree steps
- hold each step for 0.25 seconds
- sweep back from 175 degrees to 0 degrees in 5 degree steps
- hold each step for 0.25 seconds

Purpose:  
Verify agreement during smooth low-speed motion and check for lag, scaling mismatch, or timing offset between the DUT and the Python golden model.

Expected behavior:
- smooth change in accelerometer and gyroscope outputs
- similar trend and shape between Python and C logs
- limited timing mismatch during the sweep
- no missing or corrupted samples during continuous motion

### TC5 - Fast Servo Sweep
Description:  
The servo follows the commanded fast sweep profile:
- sweep from 0 degrees to 180 degrees in 10 degree steps
- hold each step for 0.10 seconds
- sweep back from 170 degrees to 0 degrees in 10 degree steps
- hold each step for 0.10 seconds

Purpose:  
Test whether the DUT still tracks the commanded motion correctly during higher-rate movement.

Expected behavior:
- correct sign and direction during rapid motion
- no major spikes, dropouts, or missing sections
- acceptable deviation from the Python golden model
- consistent response during both forward and return sweeps

### TC6 - Repeated Cycle Test
Description:  
The servo repeats the commanded cycle 10 times:
- 0 degrees for 1 second
- 90 degrees for 1 second
- 180 degrees for 1 second
- 90 degrees for 1 second

Purpose:  
Check repeatability over repeated cycles and look for drift, missed samples, or accumulating error over time.

Expected behavior:
- similar output on each repeated cycle
- low drift over the full test duration
- consistent response at each repeated commanded angle
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
