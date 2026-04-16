#include "cmodel_mpu6050.h"

MPU6050_t MPU6050_init(char *i2c, uint8_t address) {
    MPU6050_t dev;

    dev.address = address;
    dev.fd = open(i2c, O_RDWR);

    ioctl(dev.fd, I2C_SLAVE, 0x68);

    if (device_id(&dev) != _MPU6050_DEVICE_ID) {
        dev.fd = -1;
        return dev;
    }
    reset(&dev);

    _write_reg(&dev, _MPU6050_SMPLRT_DIV, 0);
    _write_bits(&dev, _MPU6050_CONFIG, 2, 3, BAND_260_HZ);
    _write_bits(&dev, _MPU6050_GYRO_CONFIG, 4, 2, RANGE_500_DPS);
    _write_bits(&dev, _MPU6050_ACCEL_CONFIG, 4, 2, RANGE_2_G);

    usleep(1000);
    _write_bits(&dev, _MPU6050_PWR_MGMT_1, 2, 3, CLKSEL_INTERNAL_X);
    usleep(1000);
    _write_bit(&dev, _MPU6050_PWR_MGMT_1, 6, false);
    usleep(100);

    return dev;
}

void reset(MPU6050_t *dev) {
    _write_bit(dev, _MPU6050_PWR_MGMT_1, 7, true);
    while (_read_bit(dev, _MPU6050_PWR_MGMT_1, 7)) {
        usleep(1000);
    }
    usleep(1000);

    _write_bits(dev, _MPU6050_SIG_PATH_RESET, 2, 3, 0b111);
    usleep(100000);
}

int device_id(MPU6050_t *dev) {
    return _read_reg(dev, _MPU6050_WHO_AM_I);
}  

void read_accel(MPU6050_t *dev){
    uint8_t data[6];
    int16_t ax, ay, az;

    _read_block(dev, _MPU6050_ACCEL_OUT, data, 6);

    ax = (int16_t)((data[0] << 8) | data[1]);
    ay = (int16_t)((data[2] << 8) | data[3]);
    az = (int16_t)((data[4] << 8) | data[5]);

    dev->ax = scale_accel(ax);
    dev->ay = scale_accel(ay);
    dev->az = scale_accel(az);
}

float scale_accel(float a) {
    float accel_scale = 1.0f / 16384.0f;   // for +/- 2g range
    return a * accel_scale * STANDARD_GRAVITY;
}

void read_gyro(MPU6050_t *dev){
    uint8_t data[6];
    int16_t gx, gy, gz;

    _read_block(dev, _MPU6050_GYRO_OUT, data, 6);

    gx = (int16_t)((data[0] << 8) | data[1]);
    gy = (int16_t)((data[2] << 8) | data[3]);
    gz = (int16_t)((data[4] << 8) | data[5]);

    dev->gx = scale_gyro(gx);
    dev->gy = scale_gyro(gy);
    dev->gz = scale_gyro(gz);
}
float scale_gyro(float g) {
    float gyro_scale = 65.5;   // for 500 DPS
    return (g / gyro_scale) * (3.14159265f / 180.0f);
}

int _write_reg(MPU6050_t *dev, uint8_t reg, uint8_t value) {
    uint8_t buf[2] = {reg, value & 0xFF};

    if (write(dev->fd, buf, 2) != 2)
        return -1;
    
    return 0;
}

int _read_reg(MPU6050_t *dev, uint8_t reg) {
    uint8_t value = 0;

    if (write(dev->fd, &reg, 1) != 1)
        return -1;

    if (read(dev->fd, &value, 1) != 1)
        return -1;

    return value;
}

int _read_block(MPU6050_t *dev, uint8_t reg, uint8_t *buf, uint8_t len) {
    if (write(dev->fd, &reg, 1) != 1) {
        return -1;
    }

    if (read(dev->fd, buf, len) != len) {
        return -1;
    }

    return 0;
}

int _read_bit(MPU6050_t *dev, uint8_t reg, uint8_t bit) {
    int value = _read_reg(dev, reg);
    if (value < 0) {
        return -1;
    }

    return (value >> bit) & 0x1;
}

int _write_bit(MPU6050_t *dev, uint8_t reg, uint8_t bit, bool value) {
    int current = _read_reg(dev, reg);
    if (current < 0) {
        return -1;
    }

    if (value) {
        current |= (1 << bit);
    } else {
        current &= ~(1 << bit);
    }

    return _write_reg(dev, reg, (uint8_t)current);
}

int _read_bits(MPU6050_t *dev, uint8_t reg, uint8_t bit_start, uint8_t length) {
    int value = _read_reg(dev, reg);
    uint8_t shift;
    uint8_t mask;

    if (value < 0) {
        return -1;
    }

    shift = bit_start - length + 1;
    mask = ((1 << length) - 1) << shift;

    return (value & mask) >> shift;
}

int _write_bits(MPU6050_t *dev, uint8_t reg, uint8_t bit_start, uint8_t length, uint8_t value) {
    int current = _read_reg(dev, reg);
    uint8_t shift;
    uint8_t mask;

    if (current < 0) {
        return -1;
    }

    shift = bit_start - length + 1;
    mask = ((1 << length) - 1) << shift;

    current &= ~mask;
    current |= (value << shift) & mask;

    return _write_reg(dev, reg, (uint8_t)current);
}
 