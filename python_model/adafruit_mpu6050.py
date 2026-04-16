"""
Adapted from the Adafruit MPU6050 driver.

Modified to use Linux i2c-dev with fcntl.ioctl and direct file reads/writes
instead of the original higher-level I2C abstraction.
"""

import math
import os
import fcntl
import struct
import time
from typing import Tuple

I2C_SLAVE = 0x0703

_MPU6050_DEFAULT_ADDRESS = 0x68  # MPU6050 default i2c address w/ AD0 low
_MPU6050_DEVICE_ID = 0x68  # The correct MPU6050_WHO_AM_I value

_MPU6050_SELF_TEST_X = 0x0D  # Self test factory calibrated values register
_MPU6050_SELF_TEST_Y = 0x0E  # Self test factory calibrated values register
_MPU6050_SELF_TEST_Z = 0x0F  # Self test factory calibrated values register
_MPU6050_SELF_TEST_A = 0x10  # Self test factory calibrated values register
_MPU6050_SMPLRT_DIV = 0x19  # sample rate divisor register
_MPU6050_CONFIG = 0x1A  # General configuration register
_MPU6050_GYRO_CONFIG = 0x1B  # Gyro specfic configuration register
_MPU6050_ACCEL_CONFIG = 0x1C  # Accelerometer specific configration register
_MPU6050_FIFO_EN = 0x23  # FIFO Enable
_MPU6050_INT_PIN_CONFIG = 0x37  # Interrupt pin configuration register
_MPU6050_ACCEL_OUT = 0x3B  # base address for sensor data reads
_MPU6050_TEMP_OUT = 0x41  # Temperature data high byte register
_MPU6050_GYRO_OUT = 0x43  # base address for sensor data reads
_MPU6050_SIG_PATH_RESET = 0x68  # register to reset sensor signal paths
_MPU6050_USER_CTRL = 0x6A  # FIFO and I2C Master control register
_MPU6050_PWR_MGMT_1 = 0x6B  # Primary power/sleep control register
_MPU6050_PWR_MGMT_2 = 0x6C  # Secondary power/sleep control register
_MPU6050_FIFO_COUNT = 0x72  # FIFO byte count register (high half)
_MPU6050_FIFO_R_W = 0x74  # FIFO data register
_MPU6050_WHO_AM_I = 0x75  # Divice ID register

STANDARD_GRAVITY = 9.80665


class ClockSource:
    """Allowed values for :py:attr:`clock_source`.

    * :py:attr:'ClockSource.CLKSEL_INTERNAL_8MHz
    * :py:attr:'ClockSource.CLKSEL_INTERNAL_X
    * :py:attr:'ClockSource.CLKSEL_INTERNAL_Y
    * :py:attr:'ClockSource.CLKSEL_INTERNAL_Z
    * :py:attr:'ClockSource.CLKSEL_EXTERNAL_32
    * :py:attr:'ClockSource.CLKSEL_EXTERNAL_19
    * :py:attr:'ClockSource.CLKSEL_RESERVED
    * :py:attr:'ClockSource.CLKSEL_STOP
    """

    CLKSEL_INTERNAL_8MHz = 0  # Internal 8MHz oscillator
    CLKSEL_INTERNAL_X = 1  # PLL with X Axis gyroscope reference
    CLKSEL_INTERNAL_Y = 2  # PLL with Y Axis gyroscope reference
    CLKSEL_INTERNAL_Z = 3  # PLL with Z Axis gyroscope reference
    CLKSEL_EXTERNAL_32 = 4  # External 32.768 kHz reference
    CLKSEL_EXTERNAL_19 = 5  # External 19.2 MHz reference
    CLKSEL_RESERVED = 6  # Reserved
    CLKSEL_STOP = 7  # Stops the clock, constant reset mode


class Range:
    """Allowed values for :py:attr:`accelerometer_range`.

    * :py:attr:`Range.RANGE_2_G`
    * :py:attr:`Range.RANGE_4_G`
    * :py:attr:`Range.RANGE_8_G`
    * :py:attr:`Range.RANGE_16_G`

    """

    RANGE_2_G = 0  # +/- 2g (default value)
    RANGE_4_G = 1  # +/- 4g
    RANGE_8_G = 2  # +/- 8g
    RANGE_16_G = 3  # +/- 16g


class GyroRange:
    """Allowed values for :py:attr:`gyro_range`.

    * :py:attr:`GyroRange.RANGE_250_DPS`
    * :py:attr:`GyroRange.RANGE_500_DPS`
    * :py:attr:`GyroRange.RANGE_1000_DPS`
    * :py:attr:`GyroRange.RANGE_2000_DPS`

    """

    RANGE_250_DPS = 0  # +/- 250 deg/s (default value)
    RANGE_500_DPS = 1  # +/- 500 deg/s
    RANGE_1000_DPS = 2  # +/- 1000 deg/s
    RANGE_2000_DPS = 3  # +/- 2000 deg/s


class Bandwidth:
    """Allowed values for :py:attr:`filter_bandwidth`.

    * :py:attr:`Bandwidth.BAND_260_HZ`
    * :py:attr:`Bandwidth.BAND_184_HZ`
    * :py:attr:`Bandwidth.BAND_94_HZ`
    * :py:attr:`Bandwidth.BAND_44_HZ`
    * :py:attr:`Bandwidth.BAND_21_HZ`
    * :py:attr:`Bandwidth.BAND_10_HZ`
    * :py:attr:`Bandwidth.BAND_5_HZ`

    """

    BAND_260_HZ = 0  # Docs imply this disables the filter
    BAND_184_HZ = 1  # 184 Hz
    BAND_94_HZ = 2  # 94 Hz
    BAND_44_HZ = 3  # 44 Hz
    BAND_21_HZ = 4  # 21 Hz
    BAND_10_HZ = 5  # 10 Hz
    BAND_5_HZ = 6  # 5 Hz


class MPU6050:
    def __init__(self, device: str = "/dev/i2c-1", address: int = _MPU6050_DEFAULT_ADDRESS):
        self.address = address
        self.fd = os.open(device, os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, address)

        if self.device_id != _MPU6050_DEVICE_ID:
            raise RuntimeError("Failed to find MPU6050 - check your wiring!")

        self.reset()

        self.sample_rate_divisor = 0
        self.filter_bandwidth = Bandwidth.BAND_260_HZ
        self.gyro_range = GyroRange.RANGE_500_DPS
        self.accelerometer_range = Range.RANGE_2_G

        time.sleep(0.1)
        self.clock_source = ClockSource.CLKSEL_INTERNAL_X
        time.sleep(0.1)
        self.sleep = False
        time.sleep(0.01)

    # -------------------------
    # low-level i2c-dev helpers
    # -------------------------
    def _write_reg(self, reg: int, value: int) -> None:
        os.write(self.fd, bytes([reg, value & 0xFF]))

    def _read_reg(self, reg: int) -> int:
        os.write(self.fd, bytes([reg]))
        data = os.read(self.fd, 1)
        return data[0]

    def _read_block(self, reg: int, length: int) -> bytes:
        os.write(self.fd, bytes([reg]))
        return os.read(self.fd, length)

    def _read_bit(self, reg: int, bit: int) -> int:
        return (self._read_reg(reg) >> bit) & 0x1

    def _write_bit(self, reg: int, bit: int, value: bool) -> None:
        current = self._read_reg(reg)
        if value:
            current |= (1 << bit)
        else:
            current &= ~(1 << bit)
        self._write_reg(reg, current)

    def _read_bits(self, reg: int, bit_start: int, length: int) -> int:
        value = self._read_reg(reg)
        shift = bit_start - length + 1
        mask = ((1 << length) - 1) << shift
        return (value & mask) >> shift

    def _write_bits(self, reg: int, bit_start: int, length: int, value: int) -> None:
        current = self._read_reg(reg)
        shift = bit_start - length + 1
        mask = ((1 << length) - 1) << shift
        current &= ~mask
        current |= (value << shift) & mask
        self._write_reg(reg, current)

    # -------------------------
    # device config
    # -------------------------
    @property
    def device_id(self) -> int:
        return self._read_reg(_MPU6050_WHO_AM_I)

    def reset(self) -> None:
        self._write_bit(_MPU6050_PWR_MGMT_1, 7, True)
        while self._read_bit(_MPU6050_PWR_MGMT_1, 7):
            time.sleep(0.001)
        time.sleep(0.1)

        self._write_bits(_MPU6050_SIG_PATH_RESET, 2, 3, 0b111)
        time.sleep(0.1)

    @property
    def sleep(self) -> bool:
        return bool(self._read_bit(_MPU6050_PWR_MGMT_1, 6))

    @sleep.setter
    def sleep(self, value: bool) -> None:
        self._write_bit(_MPU6050_PWR_MGMT_1, 6, value)

    @property
    def clock_source(self) -> int:
        return self._read_bits(_MPU6050_PWR_MGMT_1, 2, 3)

    @clock_source.setter
    def clock_source(self, value: int) -> None:
        if value not in range(8):
            raise ValueError("clock_source must be 0 through 7")
        self._write_bits(_MPU6050_PWR_MGMT_1, 2, 3, value)

    @property
    def sample_rate_divisor(self) -> int:
        return self._read_reg(_MPU6050_SMPLRT_DIV)

    @sample_rate_divisor.setter
    def sample_rate_divisor(self, value: int) -> None:
        self._write_reg(_MPU6050_SMPLRT_DIV, value)
        time.sleep(0.01)

    @property
    def filter_bandwidth(self) -> int:
        return self._read_bits(_MPU6050_CONFIG, 2, 3)

    @filter_bandwidth.setter
    def filter_bandwidth(self, value: int) -> None:
        if value < 0 or value > 6:
            raise ValueError("filter_bandwidth must be a Bandwidth value")
        self._write_bits(_MPU6050_CONFIG, 2, 3, value)
        time.sleep(0.01)

    @property
    def gyro_range(self) -> int:
        return self._read_bits(_MPU6050_GYRO_CONFIG, 4, 2)

    @gyro_range.setter
    def gyro_range(self, value: int) -> None:
        if value < 0 or value > 3:
            raise ValueError("gyro_range must be a GyroRange value")
        self._write_bits(_MPU6050_GYRO_CONFIG, 4, 2, value)
        time.sleep(0.01)

    @property
    def accelerometer_range(self) -> int:
        return self._read_bits(_MPU6050_ACCEL_CONFIG, 4, 2)

    @accelerometer_range.setter
    def accelerometer_range(self, value: int) -> None:
        if value < 0 or value > 3:
            raise ValueError("accelerometer_range must be a Range value")
        self._write_bits(_MPU6050_ACCEL_CONFIG, 4, 2, value)
        time.sleep(0.01)

    # -------------------------
    # raw sensor reads
    # -------------------------
    def _read_raw_accel(self) -> Tuple[int, int, int]:
        data = self._read_block(_MPU6050_ACCEL_OUT, 6)
        return struct.unpack(">hhh", data)

    def _read_raw_temp(self) -> int:
        data = self._read_block(_MPU6050_TEMP_OUT, 2)
        return struct.unpack(">h", data)[0]

    def _read_raw_gyro(self) -> Tuple[int, int, int]:
        data = self._read_block(_MPU6050_GYRO_OUT, 6)
        return struct.unpack(">hhh", data)

    @property
    def temperature(self) -> float:
        raw = self._read_raw_temp()
        return (raw / 340.0) + 36.53

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        raw_x, raw_y, raw_z = self._read_raw_accel()
        return self.scale_accel((raw_x, raw_y, raw_z))

    def scale_accel(self, raw_data: Tuple[int, int, int]) -> Tuple[float, float, float]:
        accel_scale = 1.0 / [16384, 8192, 4096, 2048][self.accelerometer_range]
        ax = raw_data[0] * accel_scale * STANDARD_GRAVITY
        ay = raw_data[1] * accel_scale * STANDARD_GRAVITY
        az = raw_data[2] * accel_scale * STANDARD_GRAVITY
        return (ax, ay, az)

    @property
    def gyro(self) -> Tuple[float, float, float]:
        raw_x, raw_y, raw_z = self._read_raw_gyro()
        return self.scale_gyro((raw_x, raw_y, raw_z))

    def scale_gyro(self, raw_data: Tuple[int, int, int]) -> Tuple[float, float, float]:
        gyro_range = self.gyro_range

        if gyro_range == GyroRange.RANGE_250_DPS:
            scale = 131.0
        elif gyro_range == GyroRange.RANGE_500_DPS:
            scale = 65.5
        elif gyro_range == GyroRange.RANGE_1000_DPS:
            scale = 32.8
        else:
            scale = 16.4

        gx = math.radians(raw_data[0] / scale)
        gy = math.radians(raw_data[1] / scale)
        gz = math.radians(raw_data[2] / scale)
        return (gx, gy, gz)

    def close(self) -> None:
        os.close(self.fd)