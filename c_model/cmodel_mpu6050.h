#ifndef cmodel_mpu6050_h
#define cmodel_mpu6050_h

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#define  I2C_SLAVE 0x0703

#define _MPU6050_DEFAULT_ADDRESS    0x68
#define _MPU6050_DEVICE_ID          0x68
#define _MPU6050_SELF_TEST_X        0x0D
#define _MPU6050_SELF_TEST_Y        0x0E
#define _MPU6050_SELF_TEST_Z        0x0F
#define _MPU6050_SELF_TEST_A        0x10
#define _MPU6050_SMPLRT_DIV         0x19
#define _MPU6050_CONFIG             0x1A
#define _MPU6050_GYRO_CONFIG        0x1B
#define _MPU6050_ACCEL_CONFIG       0x1C 
#define _MPU6050_FIFO_EN            0x23
#define _MPU6050_INT_PIN_CONFIG     0x37
#define _MPU6050_ACCEL_OUT          0x3B 
#define _MPU6050_TEMP_OUT           0x41 
#define _MPU6050_GYRO_OUT           0x43 
#define _MPU6050_SIG_PATH_RESET     0x68  
#define _MPU6050_USER_CTRL          0x6A 
#define _MPU6050_PWR_MGMT_1         0x6B 
#define _MPU6050_PWR_MGMT_2         0x6C  
#define _MPU6050_FIFO_COUNT         0x72  
#define _MPU6050_FIFO_R_W           0x74 
#define _MPU6050_WHO_AM_I           0x75 

#define STANDARD_GRAVITY 9.80665

#define CLKSEL_INTERNAL_8MHZ  0
#define CLKSEL_INTERNAL_X     1
#define CLKSEL_INTERNAL_Y     2
#define CLKSEL_INTERNAL_Z     3
#define CLKSEL_EXTERNAL_32    4
#define CLKSEL_EXTERNAL_19    5
#define CLKSEL_RESERVED       6
#define CLKSEL_STOP           7

#define RANGE_2_G       0   /* +/- 2g (default value) */
#define RANGE_4_G       1   /* +/- 4g */
#define RANGE_8_G       2   /* +/- 8g */
#define RANGE_16_G      3   /* +/- 16g */

#define RANGE_250_DPS   0   /* +/- 250 deg/s (default value) */
#define RANGE_500_DPS   1   /* +/- 500 deg/s */
#define RANGE_1000_DPS  2   /* +/- 1000 deg/s */
#define RANGE_2000_DPS  3   /* +/- 2000 deg/s */

#define BAND_260_HZ     0   /* Docs imply this disables the filter */
#define BAND_184_HZ     1   /* 184 Hz */
#define BAND_94_HZ      2   /* 94 Hz */
#define BAND_44_HZ      3   /* 44 Hz */
#define BAND_21_HZ      4   /* 21 Hz */
#define BAND_10_HZ      5   /* 10 Hz */
#define BAND_5_HZ       6   /* 5 Hz */

typedef struct {
    int fd;
    uint8_t address;
    float ax;
    float ay;
    float az;

    float gx;
    float gy;
    float gz;
} MPU6050_t;

MPU6050_t MPU6050_init(char *i2c, uint8_t address);

void reset(MPU6050_t *dev);
int device_id(MPU6050_t *dev);

void read_accel(MPU6050_t *dev);
float scale_accel(float a);

void read_gyro(MPU6050_t *dev);
float scale_gyro(float g);

int _write_reg(MPU6050_t *dev, uint8_t reg, uint8_t value);
int _read_reg(MPU6050_t *dev, uint8_t reg);
int _read_block(MPU6050_t *dev, uint8_t reg, uint8_t *buf, uint8_t len);
int _read_bit(MPU6050_t *dev, uint8_t reg, uint8_t bit);
int _write_bit(MPU6050_t *dev, uint8_t reg, uint8_t bit, bool value);
int _read_bits(MPU6050_t *dev, uint8_t reg, uint8_t bit_start, uint8_t length);
int _write_bits(MPU6050_t *dev, uint8_t reg, uint8_t bit_start, uint8_t length, uint8_t value);


#endif