CC      = gcc
CFLAGS  = -g -Wall -Iinclude
LDFLAGS = -lm

TARGET  = c_model/main

SRCDIR  = c_model
OBJDIR  = c_model

MODULES = $(OBJDIR)/cmodel_mpu6050.o
MAIN    = $(OBJDIR)/main.o

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(MAIN) $(MODULES)
	$(CC) $(CFLAGS) -o $(TARGET) $(MAIN) $(MODULES) $(LDFLAGS)

$(OBJDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	$(RM) $(TARGET) $(MAIN) $(MODULES) core