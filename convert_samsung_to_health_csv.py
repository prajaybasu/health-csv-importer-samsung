#!/usr/bin/env python3
"""
Convert Samsung Health export data to Health CSV Importer format.

This script converts various Samsung Health exported CSV files to a format
compatible with the Health CSV Importer iOS app.

Usage:
    python convert_samsung_to_health_csv.py [input_directory] [output_directory]

If no arguments provided, uses current directory for both input and output.
"""

import csv
import os
import sys
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


# Samsung Health exercise type to Health CSV Importer workout type mapping
EXERCISE_TYPE_MAPPING = {
    0: "other",
    1001: "walking",
    1002: "running",
    2001: "baseball",
    2002: "softball",
    2003: "cricket",
    3001: "golf",
    3002: "other",  # billiards
    3003: "bowling",
    4001: "hockey",
    4002: "rugby",
    4003: "basketball",
    4004: "soccer",
    4005: "handball",
    4006: "american football",
    5001: "volleyball",
    5002: "volleyball",  # beach volleyball
    6001: "squash",
    6002: "tennis",
    6003: "badminton",
    6004: "table tennis",
    6005: "racquetball",
    7001: "tai chi",
    7002: "boxing",
    7003: "martial arts",
    8001: "barre",
    8002: "dance",
    8003: "social dance",
    9001: "pilates",
    9002: "yoga",
    10001: "stretching",
    10002: "jump rope",
    10003: "other",  # hula-hooping
    10004: "strength",
    10005: "strength",
    10006: "core",
    10007: "cross training",
    10008: "core",
    10009: "mixed cardio",
    10010: "hiit",
    10011: "strength",
    10012: "strength",
    10013: "strength",
    10014: "strength",
    10015: "strength",
    10016: "strength",
    10017: "strength",
    10018: "strength",
    10019: "strength",
    10020: "strength",
    10021: "strength",
    10022: "strength",
    10023: "core",
    10024: "core",
    10025: "core",
    10026: "strength",
    10027: "strength",
    11001: "skating",
    11002: "other",  # hang gliding
    11003: "other",  # pistol shooting
    11004: "archery",
    11005: "equestrian",
    11007: "cycling",
    11008: "disc",
    11009: "skating",
    12001: "mixed cardio",
    13001: "hiking",
    13002: "climbing",
    13003: "hiking",
    13004: "cycling",
    13005: "other",  # orienteering
    14001: "swimming",
    14002: "water fitness",
    14003: "paddle",
    14004: "sailing",
    14005: "underwater diving",
    14006: "underwater diving",
    14007: "paddle",
    14008: "surfing",
    14009: "paddle",
    14010: "rowing",
    14011: "surfing",
    14012: "sailing",
    14013: "water sports",
    15001: "stair climbing",
    15002: "strength",
    15003: "cycling",
    15004: "rowing",
    15005: "running",  # treadmill
    15006: "elliptical",
    16001: "cross country skiing",
    16002: "downhill skiing",
    16003: "skating",
    16004: "skating",
    16006: "hockey",
    16007: "snowboarding",
    16008: "downhill skiing",
    16009: "snow sports",
}

# Samsung Health sleep stage codes to Health CSV Importer sleep analysis values
SLEEP_STAGE_MAPPING = {
    40001: "awake",
    40002: "light",
    40003: "deep",
    40004: "rem",
}


def parse_samsung_datetime(dt_str: str) -> Optional[datetime]:
    """Parse Samsung Health datetime string to datetime object."""
    if not dt_str or dt_str.strip() == "":
        return None
    try:
        # Format: 2023-07-04 16:32:11.353
        return datetime.strptime(dt_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def format_datetime(dt: datetime) -> str:
    """Format datetime for Health CSV Importer (ISO 8601)."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def read_samsung_csv(filepath: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Read Samsung Health CSV file, handling the metadata header rows.
    Returns (headers, rows) where rows is a list of dicts.

    Samsung Health exports have trailing commas, so data rows often have
    one more column than the header row. We handle this by truncating
    data rows to match header length.
    """
    rows = []
    headers = []

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        lines = list(reader)

    if len(lines) < 3:
        return [], []

    # Row 0: metadata (file type, version, etc.)
    # Row 1: column headers
    # Row 2+: data
    headers = lines[1]
    num_headers = len(headers)

    for line in lines[2:]:
        # Handle trailing comma issue: truncate to header length
        if len(line) >= num_headers:
            row = dict(zip(headers, line[:num_headers]))
            rows.append(row)

    return headers, rows


def find_samsung_file(directory: str, pattern: str) -> Optional[str]:
    """Find a Samsung Health CSV file matching the pattern."""
    matches = glob.glob(os.path.join(directory, f"*{pattern}*.csv"))
    return matches[0] if matches else None


def convert_heart_rate(input_dir: str, output_dir: str) -> int:
    """Convert heart rate data."""
    filepath = find_samsung_file(input_dir, "tracker.heart_rate")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("com.samsung.health.heart_rate.start_time", ""))
        heart_rate = row.get("com.samsung.health.heart_rate.heart_rate", "")

        if start_time and heart_rate:
            try:
                hr_value = float(heart_rate)
                output_rows.append({
                    "date": format_datetime(start_time),
                    "heart rate": str(int(hr_value)),
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "heart_rate.csv"), ["date", "heart rate"], output_rows)

    return len(output_rows)


def convert_steps(input_dir: str, output_dir: str) -> int:
    """Convert step count data from daily summary."""
    filepath = find_samsung_file(input_dir, "tracker.pedometer_day_summary")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        # day_time is in milliseconds since epoch
        day_time_ms = row.get("day_time", "")
        step_count = row.get("step_count", "")
        distance = row.get("distance", "")
        calorie = row.get("calorie", "")

        if day_time_ms and step_count:
            try:
                dt = datetime.fromtimestamp(int(day_time_ms) / 1000)
                steps = int(float(step_count))
                output_rows.append({
                    "date": format_datetime(dt),
                    "steps": str(steps),
                })
            except (ValueError, OSError):
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "steps.csv"), ["date", "steps"], output_rows)

    return len(output_rows)


def convert_weight(input_dir: str, output_dir: str) -> int:
    """Convert weight data."""
    filepath = find_samsung_file(input_dir, "health.weight")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        weight = row.get("weight", "")
        body_fat = row.get("body_fat", "")

        if start_time and weight:
            try:
                weight_kg = float(weight)
                entry = {
                    "date": format_datetime(start_time),
                    "weight": f"{weight_kg:.1f}",
                }
                if body_fat:
                    try:
                        entry["body fat"] = f"{float(body_fat):.1f}"
                    except ValueError:
                        pass
                output_rows.append(entry)
            except ValueError:
                continue

    if output_rows:
        fieldnames = ["date", "weight"]
        if any("body fat" in r for r in output_rows):
            fieldnames.append("body fat")
        write_health_csv(os.path.join(output_dir, "weight.csv"), fieldnames, output_rows)

    return len(output_rows)


def convert_height(input_dir: str, output_dir: str) -> int:
    """Convert height data."""
    filepath = find_samsung_file(input_dir, "health.height")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        height = row.get("height", "")

        if start_time and height:
            try:
                # Samsung stores height in cm, convert to meters for Health CSV Importer
                height_cm = float(height)
                height_m = height_cm / 100
                output_rows.append({
                    "date": format_datetime(start_time),
                    "height": f"{height_m:.2f}",
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "height.csv"), ["date", "height"], output_rows)

    return len(output_rows)


def convert_floors_climbed(input_dir: str, output_dir: str) -> int:
    """Convert floors climbed data."""
    filepath = find_samsung_file(input_dir, "health.floors_climbed")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        floor = row.get("floor", "")

        if start_time and floor:
            try:
                floors = int(float(floor))
                output_rows.append({
                    "date": format_datetime(start_time),
                    "flights": str(floors),
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "floors_climbed.csv"), ["date", "flights"], output_rows)

    return len(output_rows)


def convert_blood_pressure(input_dir: str, output_dir: str) -> int:
    """Convert blood pressure data."""
    filepath = find_samsung_file(input_dir, "shealth.blood_pressure")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("com.samsung.health.blood_pressure.start_time", ""))
        systolic = row.get("com.samsung.health.blood_pressure.systolic", "")
        diastolic = row.get("com.samsung.health.blood_pressure.diastolic", "")

        if start_time and systolic and diastolic:
            try:
                sys_val = float(systolic)
                dia_val = float(diastolic)
                output_rows.append({
                    "date": format_datetime(start_time),
                    "systolic": str(int(sys_val)),
                    "diastolic": str(int(dia_val)),
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "blood_pressure.csv"), ["date", "systolic", "diastolic"], output_rows)

    return len(output_rows)


def convert_oxygen_saturation(input_dir: str, output_dir: str) -> int:
    """Convert oxygen saturation data."""
    # Try the tracker file first
    filepath = find_samsung_file(input_dir, "tracker.oxygen_saturation")
    if not filepath:
        filepath = find_samsung_file(input_dir, "oxygen_saturation.raw")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("com.samsung.health.oxygen_saturation.start_time", ""))
        spo2 = row.get("com.samsung.health.oxygen_saturation.spo2", "")

        if start_time and spo2:
            try:
                spo2_val = float(spo2)
                output_rows.append({
                    "date": format_datetime(start_time),
                    "oxygen": str(int(spo2_val)),
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "oxygen_saturation.csv"), ["date", "oxygen"], output_rows)

    return len(output_rows)


def convert_water_intake(input_dir: str, output_dir: str) -> int:
    """Convert water intake data."""
    filepath = find_samsung_file(input_dir, "health.water_intake")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        amount = row.get("amount", "")  # in mL

        if start_time and amount:
            try:
                # Convert mL to L
                amount_ml = float(amount)
                amount_l = amount_ml / 1000
                output_rows.append({
                    "date": format_datetime(start_time),
                    "water": f"{amount_l:.3f}",
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "water_intake.csv"), ["date", "water"], output_rows)

    return len(output_rows)


def convert_respiratory_rate(input_dir: str, output_dir: str) -> int:
    """Convert respiratory rate data."""
    filepath = find_samsung_file(input_dir, "health.respiratory_rate")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        average = row.get("average", "")

        if start_time and average:
            try:
                rate = float(average)
                output_rows.append({
                    "date": format_datetime(start_time),
                    "respiratory rate": f"{rate:.1f}",
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "respiratory_rate.csv"), ["date", "respiratory rate"], output_rows)

    return len(output_rows)


def convert_sleep_stages(input_dir: str, output_dir: str) -> int:
    """Convert sleep stage data."""
    filepath = find_samsung_file(input_dir, "health.sleep_stage")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))
        end_time = parse_samsung_datetime(row.get("end_time", ""))
        stage = row.get("stage", "")

        if start_time and end_time and stage:
            try:
                stage_code = int(stage)
                stage_name = SLEEP_STAGE_MAPPING.get(stage_code, "")
                if stage_name:
                    output_rows.append({
                        "date": format_datetime(start_time),
                        "end date": format_datetime(end_time),
                        "sleep analysis": stage_name,
                    })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "sleep_analysis.csv"), ["date", "end date", "sleep analysis"], output_rows)

    return len(output_rows)


def convert_exercises(input_dir: str, output_dir: str) -> int:
    """Convert exercise/workout data."""
    filepath = find_samsung_file(input_dir, "shealth.exercise.2")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        start_time = parse_samsung_datetime(row.get("com.samsung.health.exercise.start_time", ""))
        end_time = parse_samsung_datetime(row.get("com.samsung.health.exercise.end_time", ""))
        exercise_type = row.get("com.samsung.health.exercise.exercise_type", "")
        calories = row.get("com.samsung.health.exercise.calorie", "")
        distance = row.get("com.samsung.health.exercise.distance", "")
        duration_ms = row.get("com.samsung.health.exercise.duration", "")

        if start_time and exercise_type:
            try:
                type_code = int(exercise_type)
                workout_type = EXERCISE_TYPE_MAPPING.get(type_code, "other")

                entry = {
                    "date": format_datetime(start_time),
                    "workout": workout_type,
                }

                if end_time:
                    entry["end date"] = format_datetime(end_time)

                if calories:
                    try:
                        cal = float(calories)
                        entry["calories"] = f"{cal:.1f}"
                    except ValueError:
                        pass

                if distance:
                    try:
                        dist_m = float(distance)
                        # Convert to km for better readability
                        entry["distance"] = f"{dist_m:.1f}"
                    except ValueError:
                        pass

                output_rows.append(entry)
            except ValueError:
                continue

    if output_rows:
        fieldnames = ["date", "end date", "workout", "calories", "distance"]
        write_health_csv(os.path.join(output_dir, "workouts.csv"), fieldnames, output_rows)

    return len(output_rows)


def convert_nutrition(input_dir: str, output_dir: str) -> int:
    """Convert nutrition data."""
    filepath = find_samsung_file(input_dir, "health.nutrition")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    # Mapping from Samsung fields to Health CSV Importer fields
    # Note: Health CSV Importer expects values in mg for most nutrients
    field_mapping = {
        "carbohydrate": ("carbohydrate", 1000),  # g to mg
        "protein": ("protein", 1000),  # g to mg
        "total_fat": ("total fat", 1000),  # g to mg
        "saturated_fat": ("saturated fat", 1000),  # g to mg
        "cholesterol": ("cholesterol", 1),  # already in mg
        "sodium": ("sodium", 1),  # already in mg
        "dietary_fiber": ("fiber", 1000),  # g to mg
        "sugar": ("sugar", 1000),  # g to mg
        "calcium": ("calcium", 1),  # already in mg
        "iron": ("iron", 1),  # already in mg
        "potassium": ("potassium", 1),  # already in mg
        "vitamin_a": ("vitamin a", 1),  # mcg
        "vitamin_c": ("vitamin c", 1),  # mg
        "vitamin_d": ("vitamin d", 1),  # mg
        "caffeine": ("caffeine", 1),  # mg
    }

    output_rows = []
    all_fields = set(["date"])

    for row in rows:
        start_time = parse_samsung_datetime(row.get("start_time", ""))

        if not start_time:
            continue

        entry = {"date": format_datetime(start_time)}

        for samsung_field, (health_field, multiplier) in field_mapping.items():
            value = row.get(samsung_field, "")
            if value:
                try:
                    val = float(value) * multiplier
                    if val > 0:
                        entry[health_field] = f"{val:.1f}"
                        all_fields.add(health_field)
                except ValueError:
                    continue

        if len(entry) > 1:  # Has more than just date
            output_rows.append(entry)

    if output_rows:
        fieldnames = ["date"] + sorted(list(all_fields - {"date"}))
        write_health_csv(os.path.join(output_dir, "nutrition.csv"), fieldnames, output_rows)

    return len(output_rows)


def convert_active_calories(input_dir: str, output_dir: str) -> int:
    """Convert active calories burned from daily activity summary."""
    filepath = find_samsung_file(input_dir, "activity.day_summary")
    if not filepath:
        return 0

    headers, rows = read_samsung_csv(filepath)
    if not rows:
        return 0

    output_rows = []
    for row in rows:
        day_time = parse_samsung_datetime(row.get("day_time", ""))
        calorie = row.get("calorie", "")

        if day_time and calorie:
            try:
                cal = float(calorie)
                output_rows.append({
                    "date": format_datetime(day_time),
                    "calories": f"{cal:.1f}",
                })
            except ValueError:
                continue

    if output_rows:
        write_health_csv(os.path.join(output_dir, "active_calories.csv"), ["date", "calories"], output_rows)

    return len(output_rows)


def write_health_csv(filepath: str, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    """Write data in Health CSV Importer format."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Main conversion function."""
    # Parse arguments
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = os.getcwd()

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = os.path.join(input_dir, "health_csv_importer_output")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print(f"Samsung Health to Health CSV Importer Converter")
    print(f"=" * 50)
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Run all conversions
    conversions = [
        ("Heart Rate", convert_heart_rate),
        ("Steps", convert_steps),
        ("Weight", convert_weight),
        ("Height", convert_height),
        ("Floors Climbed", convert_floors_climbed),
        ("Blood Pressure", convert_blood_pressure),
        ("Oxygen Saturation", convert_oxygen_saturation),
        ("Water Intake", convert_water_intake),
        ("Respiratory Rate", convert_respiratory_rate),
        ("Sleep Stages", convert_sleep_stages),
        ("Workouts", convert_exercises),
        ("Nutrition", convert_nutrition),
        ("Active Calories", convert_active_calories),
    ]

    total_records = 0
    for name, converter in conversions:
        try:
            count = converter(input_dir, output_dir)
            if count > 0:
                print(f"  {name}: {count:,} records converted")
                total_records += count
            else:
                print(f"  {name}: No data found")
        except Exception as e:
            print(f"  {name}: Error - {e}")

    print()
    print(f"Total: {total_records:,} records converted")
    print(f"Output files written to: {output_dir}")


if __name__ == "__main__":
    main()
