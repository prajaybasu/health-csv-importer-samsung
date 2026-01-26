# Samsung Health to Health CSV Importer Converter

Convert [Samsung Health]() data exports to CSV files compatibile with the [Health CSV Importer](https://apps.apple.com/app/health-csv-importer/id1582272946) iOS app.

This allows you to import your Samsung health data into Apple Health.

## Prerequisites

- Python 3.6+
- Samsung data export

## Features

Converts the following Samsung Health data types:

| Data Type | Description |
|-----------|-------------|
| Heart Rate | Individual heart rate measurements |
| Steps | Daily step counts |
| Weight | Body weight measurements (with optional body fat %) |
| Height | Height measurements (converted from cm to meters) |
| Floors Climbed | Flights of stairs climbed |
| Blood Pressure | Systolic and diastolic readings |
| Oxygen Saturation | SpO2 measurements |
| Water Intake | Water consumption (converted from mL to liters) |
| Respiratory Rate | Breathing rate measurements |
| Sleep Stages | Sleep analysis (awake, light, deep, REM) |
| Workouts | Exercise sessions with type, duration, calories, distance |
| Nutrition | Macronutrients and micronutrients |
| Active Calories | Daily active energy burned |

## Usage

1. Export your data from Samsung Health and place the CSV files in this directory.
   - Open Samsung Health on your Android device
   - Go to Settings > Download personal data
   - Request and download your data export
   - Extract the ZIP file to your computer

2. Run the conversion script:
   ```bash
   # Using default directories (current directory for input, creates output subdirectory)
   python3 convert_samsung_to_health_csv.py
   
   # Specify input directory
   python3 convert_samsung_to_health_csv.py /path/to/samsung/export
   
   # Specify both input and output directories
   python3 convert_samsung_to_health_csv.py /path/to/samsung/export /path/to/output
   ```

3. Import the generated CSV files using the Health CSV Importer app.

## Output Files

The script creates the following CSV files in the output directory:

| File | Apple Health Data Type |
| `heart_rate.csv` | Heart rate measurements
| `steps.csv` | Daily step counts
| `weight.csv` | Weight and body fat measurements
| `height.csv` | Height measurements
| `floors_climbed.csv` | Flights climbed
| `blood_pressure.csv` | Blood pressure readings
| `oxygen_saturation.csv` | SpO2 measurements
| `water_intake.csv` | Water consumption
| `respiratory_rate.csv` | Respiratory rate
| `sleep_analysis.csv` | Sleep stages
| `workouts.csv` | Exercise sessions
| `nutrition.csv` | Nutritional data
| `active_calories.csv` | Active energy burned

## Data Mappings

### Exercise Types

Samsung Health exercise codes are mapped to Health CSV Importer workout types:

| Samsung Code | Workout Type |
|--------------|--------------|
| 1001 | Walking |
| 1002 | Running |
| 11007 | Cycling |
| 13001 | Hiking |
| 14001 | Swimming |
| 9002 | Yoga |
| 15005 | Running (Treadmill) |
| 15006 | Elliptical |
| ... | (70+ exercise types supported) |

### Sleep Stages

| Samsung Code | Sleep Stage |
|--------------|-------------|
| 40001 | Awake |
| 40002 | Light |
| 40003 | Deep |
| 40004 | REM |

## Unit Conversions

The script automatically handles unit conversions:

- Height: cm → meters
- Water intake: mL → liters
- Nutrition: grams → milligrams (where required by Health CSV Importer)

## Limitations

- Some Samsung Health data types may not have direct equivalents in Apple Health
- Workout routes/GPS data are not converted
- Some Samsung-specific metrics (stress, sleep scores) cannot be imported

## License

MIT License - feel free to use and modify as needed.

---

*This script was written in close collaboration with Claude Opus 4.5 (Anthropic).*
