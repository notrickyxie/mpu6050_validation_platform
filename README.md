# MPU6050 IMU Validation Platform

## Overview

This project is a hardware-software validation platform built around an **MPU6050 IMU** connected to a **Raspberry Pi 4B** over **I2C**. The goal is to validate a low-level **C driver** against a **Python golden model** so that register configuration, sensor parsing, scaling, and output behavior can be checked through measurable pass/fail criteria.

The project focuses on building a repeatable validation workflow for IMU bring-up and sensor verification. By comparing the custom C device-under-test implementation against a known working Python reference, the platform helps confirm that initialization, raw data reads, and unit conversions behave as expected.

## System Architecture

The system is organized into three main layers:

1. **Hardware layer**   
    The MPU6050 communicates with the Raspberry Pi 4B over **I2C**.

    #### Wiring Diagram

    ```text
    Raspberry Pi 4B              MPU6050
    -----------------------------------------
    3.3V                     ->  VCC
    GND                      ->  GND
    GPIO3 / SCL / Pin 5      ->  SCL
    GPIO2 / SDA / Pin 3      ->  SDA

2. **Software layer**  
    Two software paths are used:
    - a **Python golden model** that serves as the reference. Adapted from the Adafruit MPU6050 driver using (`i2c-dev`) with (`ioctl`) instead of relying on the original Adafruit bus interface.
    - a **custom C driver** using the Linux **I2C userspace interface** (`i2c-dev`) with (`ioctl`) that serves as the DUT

3. **Validation layer**  
   Logged outputs from both paths are compared to evaluate:
    - device identification and register correctness
    - raw accelerometer and gyroscope agreement
    - scaling into engineering units
    - stationary bias and drift
    - response during simple motion tests

    These results are then checked against defined pass/fail thresholds to determine whether the custom implementation behaves correctly.

## Architecture Diagram
![Architecture Diagram](docs/mvp_architecture.png)
