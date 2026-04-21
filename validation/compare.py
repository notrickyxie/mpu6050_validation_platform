from pathlib import Path
import csv
import math

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

PYTHON_LOG = LOG_DIR / "python_log.csv"
CMODEL_LOG = LOG_DIR / "cmodel_log.csv"
REPORT_FILE = REPORT_DIR / "validation_results.txt"

SIGNALS = ["ax", "ay", "az", "gx", "gy", "gz"]

# Tuned for current rig behavior. Refine after more baseline runs.
THRESHOLDS = {
    "ax": 0.50,   # m/s^2
    "ay": 2.00,
    "az": 2.00,
    "gx": 2.50,   # rad/s
    "gy": 0.15,
    "gz": 0.20,
}

# Only perform sign-flip checks when the signal mean magnitude is large enough
# to make sign meaningful for the current motion profile.
SIGN_MEAN_THRESHOLDS = {
    "ax": 0.20,
    "ay": 0.20,
    "az": 0.50,
    "gx": 0.05,
    "gy": 0.05,
    "gz": 0.05,
}

WHO_AM_I_EXPECTED = 104.0  # 0x68
MAX_SAMPLE_MISMATCH_PCT = 5.0


def read_log_with_metadata(path: Path):
    metadata = {}
    rows = []

    with open(path, "r", newline="") as f:
        first_line = f.readline().strip()

        if first_line.startswith("#"):
            if first_line.startswith("# WHO_AM_I="):
                metadata["who_am_i"] = float(first_line.split("=", 1)[1].strip())
            header_line = f.readline()
        else:
            header_line = first_line + "\n"

        reader = csv.DictReader([header_line] + f.readlines())

        for row in reader:
            clean = {}
            for key, value in row.items():
                if value is None or value == "":
                    continue
                clean[key] = float(value)
            rows.append(clean)

    return metadata, rows


def strip_initial_zero_rows(rows):
    idx = 0
    while idx < len(rows):
        if any(abs(rows[idx][sig]) > 1e-12 for sig in SIGNALS):
            break
        idx += 1
    return rows[idx:]


def mean(values):
    return sum(values) / len(values)


def rmse(errors):
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def mae(errors):
    return sum(abs(e) for e in errors) / len(errors)


def max_abs(errors):
    return max(abs(e) for e in errors)


def drift_metric(rows, signal, window=20):
    if len(rows) == 0:
        return float("nan")

    if len(rows) < 2 * window:
        window = max(1, len(rows) // 4)

    start_mean = sum(r[signal] for r in rows[:window]) / window
    end_mean = sum(r[signal] for r in rows[-window:]) / window
    return end_mean - start_mean


def sign_inversion_check(py_vals, c_vals, min_mean_mag):
    py_mean = mean(py_vals)
    c_mean = mean(c_vals)

    if abs(py_mean) < min_mean_mag or abs(c_mean) < min_mean_mag:
        return False

    return py_mean * c_mean < 0


def sample_period(rows):
    if len(rows) < 2:
        return float("nan")
    dt = rows[-1]["timestamp_s"] - rows[0]["timestamp_s"]
    return dt / (len(rows) - 1)


def compare_logs(py_rows, c_rows):
    n = min(len(py_rows), len(c_rows))
    results = []

    for sig in SIGNALS:
        py_vals = [py_rows[i][sig] for i in range(n)]
        c_vals = [c_rows[i][sig] for i in range(n)]
        errors = [c_vals[i] - py_vals[i] for i in range(n)]

        py_drift = drift_metric(py_rows[:n], sig)
        c_drift = drift_metric(c_rows[:n], sig)
        drift_error = c_drift - py_drift
        sign_inverted = sign_inversion_check(py_vals, c_vals, SIGN_MEAN_THRESHOLDS[sig])

        result = {
            "signal": sig,
            "python_mean": mean(py_vals),
            "cmodel_mean": mean(c_vals),
            "mean_error": mean(errors),
            "mae": mae(errors),
            "rmse": rmse(errors),
            "max_error": max_abs(errors),
            "python_drift": py_drift,
            "cmodel_drift": c_drift,
            "drift_error": drift_error,
            "sign_inverted": sign_inverted,
            "threshold": THRESHOLDS[sig],
        }

        result["status"] = "PASS"
        if result["rmse"] > result["threshold"]:
            result["status"] = "FAIL"
        if sign_inverted:
            result["status"] = "FAIL"

        results.append(result)

    return results, n


def who_am_i_status(py_meta, c_meta):
    py_who = py_meta.get("who_am_i")
    c_who = c_meta.get("who_am_i")

    if py_who is None or c_who is None:
        return {
            "status": "MISSING",
            "python": py_who,
            "cmodel": c_who,
        }

    ok = (py_who == WHO_AM_I_EXPECTED) and (c_who == WHO_AM_I_EXPECTED)
    return {
        "status": "PASS" if ok else "FAIL",
        "python": py_who,
        "cmodel": c_who,
    }


def print_results(results, py_count, c_count, compared_count, who_result, py_rows_trimmed, c_rows_trimmed):
    print("MPU6050 Validation Results")
    print("=" * 150)
    print(f"Python samples : {py_count}")
    print(f"C model samples: {c_count}")
    print(f"Compared       : {compared_count}")

    mismatch_pct = abs(py_count - c_count) / max(py_count, c_count) * 100 if max(py_count, c_count) else 0.0
    print(f"Sample mismatch: {mismatch_pct:.2f}%")

    if who_result["status"] != "MISSING":
        print(
            f"WHO_AM_I       : Python={int(who_result['python'])} "
            f"C={int(who_result['cmodel'])} "
            f"-> {who_result['status']}"
        )
    else:
        print("WHO_AM_I       : MISSING in one or both logs")

    print()
    print(
        f"{'Signal':<8}"
        f"{'Py Mean':>12}"
        f"{'C Mean':>12}"
        f"{'Mean Err':>12}"
        f"{'MAE':>12}"
        f"{'RMSE':>12}"
        f"{'Max Err':>12}"
        f"{'Py Drift':>12}"
        f"{'C Drift':>12}"
        f"{'Drift Err':>12}"
        f"{'Sign Flip':>12}"
        f"{'Limit':>12}"
        f"{'Result':>10}"
    )
    print("-" * 150)

    for r in results:
        print(
            f"{r['signal']:<8}"
            f"{r['python_mean']:>12.6f}"
            f"{r['cmodel_mean']:>12.6f}"
            f"{r['mean_error']:>12.6f}"
            f"{r['mae']:>12.6f}"
            f"{r['rmse']:>12.6f}"
            f"{r['max_error']:>12.6f}"
            f"{r['python_drift']:>12.6f}"
            f"{r['cmodel_drift']:>12.6f}"
            f"{r['drift_error']:>12.6f}"
            f"{str(r['sign_inverted']):>12}"
            f"{r['threshold']:>12.6f}"
            f"{r['status']:>10}"
        )

    py_dt = sample_period(py_rows_trimmed)
    c_dt = sample_period(c_rows_trimmed)
    start_offset = c_rows_trimmed[0]["timestamp_s"] - py_rows_trimmed[0]["timestamp_s"]
    end_offset = c_rows_trimmed[-1]["timestamp_s"] - py_rows_trimmed[-1]["timestamp_s"]

    print("-" * 150)
    print(f"Python avg sample period : {py_dt:.6f} s")
    print(f"C model avg sample period: {c_dt:.6f} s")
    print(f"Start timestamp offset   : {start_offset:.6f} s")
    print(f"End timestamp offset     : {end_offset:.6f} s")

    overall = "PASS"
    if any(r["status"] == "FAIL" for r in results):
        overall = "FAIL"
    if who_result["status"] == "FAIL":
        overall = "FAIL"
    if mismatch_pct > MAX_SAMPLE_MISMATCH_PCT:
        overall = "FAIL"

    print(f"Overall result: {overall}")
    return overall, mismatch_pct, py_dt, c_dt, start_offset, end_offset


def save_report(
    results,
    py_count,
    c_count,
    compared_count,
    who_result,
    overall,
    mismatch_pct,
    py_dt,
    c_dt,
    start_offset,
    end_offset,
):
    with open(REPORT_FILE, "w") as f:
        f.write("MPU6050 Validation Results\n")
        f.write("=" * 150 + "\n")
        f.write(f"Python log     : {PYTHON_LOG}\n")
        f.write(f"C model log    : {CMODEL_LOG}\n")
        f.write(f"Python samples : {py_count}\n")
        f.write(f"C model samples: {c_count}\n")
        f.write(f"Compared       : {compared_count}\n")
        f.write(f"Sample mismatch: {mismatch_pct:.2f}%\n")
        f.write(f"Sample mismatch limit: {MAX_SAMPLE_MISMATCH_PCT:.2f}%\n")
        f.write("Initial zero rows trimmed: yes\n")

        if who_result["status"] != "MISSING":
            f.write(
                f"WHO_AM_I       : Python={int(who_result['python'])} "
                f"C={int(who_result['cmodel'])} "
                f"-> {who_result['status']}\n"
            )
        else:
            f.write("WHO_AM_I       : MISSING in one or both logs\n")

        f.write(f"Python avg sample period : {py_dt:.6f} s\n")
        f.write(f"C model avg sample period: {c_dt:.6f} s\n")
        f.write(f"Start timestamp offset   : {start_offset:.6f} s\n")
        f.write(f"End timestamp offset     : {end_offset:.6f} s\n\n")

        f.write(
            f"{'Signal':<8}"
            f"{'Py Mean':>12}"
            f"{'C Mean':>12}"
            f"{'Mean Err':>12}"
            f"{'MAE':>12}"
            f"{'RMSE':>12}"
            f"{'Max Err':>12}"
            f"{'Py Drift':>12}"
            f"{'C Drift':>12}"
            f"{'Drift Err':>12}"
            f"{'Sign Flip':>12}"
            f"{'Limit':>12}"
            f"{'Result':>10}\n"
        )
        f.write("-" * 150 + "\n")

        for r in results:
            f.write(
                f"{r['signal']:<8}"
                f"{r['python_mean']:>12.6f}"
                f"{r['cmodel_mean']:>12.6f}"
                f"{r['mean_error']:>12.6f}"
                f"{r['mae']:>12.6f}"
                f"{r['rmse']:>12.6f}"
                f"{r['max_error']:>12.6f}"
                f"{r['python_drift']:>12.6f}"
                f"{r['cmodel_drift']:>12.6f}"
                f"{r['drift_error']:>12.6f}"
                f"{str(r['sign_inverted']):>12}"
                f"{r['threshold']:>12.6f}"
                f"{r['status']:>10}\n"
            )

        f.write("-" * 150 + "\n")
        f.write(f"Overall result: {overall}\n")


if __name__ == "__main__":
    if not PYTHON_LOG.exists():
        raise FileNotFoundError(f"Missing Python log: {PYTHON_LOG}")
    if not CMODEL_LOG.exists():
        raise FileNotFoundError(f"Missing C model log: {CMODEL_LOG}")

    py_meta, py_rows = read_log_with_metadata(PYTHON_LOG)
    c_meta, c_rows = read_log_with_metadata(CMODEL_LOG)

    if not py_rows or not c_rows:
        raise RuntimeError("One or both CSV files are empty.")

    py_rows_trimmed = strip_initial_zero_rows(py_rows)
    c_rows_trimmed = strip_initial_zero_rows(c_rows)

    if not py_rows_trimmed or not c_rows_trimmed:
        raise RuntimeError("No usable rows remain after trimming startup zero rows.")

    who_result = who_am_i_status(py_meta, c_meta)
    results, compared_count = compare_logs(py_rows_trimmed, c_rows_trimmed)

    overall, mismatch_pct, py_dt, c_dt, start_offset, end_offset = print_results(
        results,
        len(py_rows_trimmed),
        len(c_rows_trimmed),
        compared_count,
        who_result,
        py_rows_trimmed,
        c_rows_trimmed,
    )

    save_report(
        results,
        len(py_rows_trimmed),
        len(c_rows_trimmed),
        compared_count,
        who_result,
        overall,
        mismatch_pct,
        py_dt,
        c_dt,
        start_offset,
        end_offset,
    )

    print()
    print(f"Saved report to: {REPORT_FILE}")