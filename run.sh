#!/bin/bash

set -e

CMODEL_PID=""
PYTHON_PID=""

MODE="${1:-both}"

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

usage() {
    echo "Usage: $0 [c|python|both]"
    exit 1
}

run_cmodel() {
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
}

run_python() {
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
}

trap cleanup INT TERM

case "$MODE" in
    c)
        echo "Starting servo validation test in C-only mode..."
        run_cmodel
        ;;
    python)
        echo "Starting servo validation test in Python-only mode..."
        run_python
        ;;
    both)
        echo "Starting servo validation test in both mode..."
        run_cmodel
        sleep 2
        run_python
        ;;
    *)
        usage
        ;;
esac

echo "Servo validation test complete."