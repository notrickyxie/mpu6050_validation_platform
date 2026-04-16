#include "cmodel_mpu6050.h"

static double timestamp_s(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);

    return (double)ts.tv_sec + (double)ts.tv_nsec / 1000000000.0;
}

int main() {
    char *f = "logs/cmodel_log.csv";
    FILE *file = fopen(f, "w");
    fprintf(file,"timestamp_s,ax,ay,az,gx,gy,gz\n");

    MPU6050_t dev = MPU6050_init("/dev/i2c-1", _MPU6050_DEVICE_ID);

    printf("%x\n",device_id(&dev));

    while (1) {
        double t = timestamp_s();

        read_accel(&dev);
        read_gyro(&dev);

        printf("time : %.3f\n", t);
        printf("accel: %.3f, %.3f, %.3f m/s^2\n", dev.ax, dev.ay, dev.az);
        printf("gyro : %.3f, %.3f, %.3f rad/s\n", dev.gx, dev.gy, dev.gz);
        printf("\n");

        fprintf(file, "%.7f,%.16f,%.16f,%.16f,%.16f,%.16f,%.16f\n",
                t,
                dev.ax, dev.ay, dev.az,
                dev.gx, dev.gy, dev.gz
                );

        fflush(file);

        usleep(500000);
    }

    fclose(file);
    return 0;
}