#!/bin/bash

set -e

CMODEL_PID=""
PYTHON_PID=""

cleanup() {
    echo
    echo "Caught interrupt. Cleaning up..."

    if [ -n "$CMODEL_PID" ] && kill -0 "$CMODEL_PID" 2>/dev/null; then
        echo "Stopping C model logger..."
        kill "$CMODEL_PID" 2>/dev/null || true
        wait "$CMODEL_PID" 2>/dev/null || true
    fi

    if [ -n "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
        echo "Stopping Python logger..."
        kill "$PYTHON_PID" 2>/dev/null || true
        wait "$PYTHON_PID" 2>/dev/null || true
    fi

    exit 1
}

trap cleanup INT TERM

echo "Starting servo validation test..."

# Run C model + motion
echo "Starting C model logger..."
./c_model/main &
CMODEL_PID=$!

sleep 1

echo "Running servo motion profile for C model..."
python3 motion/motion.py

echo "Stopping C model logger..."
kill "$CMODEL_PID" 2>/dev/null || true
wait "$CMODEL_PID" 2>/dev/null || true
CMODEL_PID=""

sleep 2

# Run Python model + motion
echo "Starting Python golden model logger..."
python3 python_model/python_test.py &
PYTHON_PID=$!

sleep 1

echo "Running servo motion profile for Python model..."
python3 motion/motion.py

echo "Stopping Python logger..."
kill "$PYTHON_PID" 2>/dev/null || true
wait "$PYTHON_PID" 2>/dev/null || true
PYTHON_PID=""

echo "Servo validation test complete."