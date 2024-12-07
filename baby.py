import pandas as pd
import math
from scipy.stats import norm
import argparse
from pathlib import Path
import os
import sys

# Calculation taken from CDC website instructions for L S and M values (apply to WHO as well)
def calc_percentile(age, val, chart):
    
    chart_row = chart.loc[age]
    z_score = 0

    if chart_row["L"] == 0:
        z_score = math.log(val/chart_row["M"]) / chart_row["S"]

    else:
        z_score = (((val/chart_row["M"]) ** chart_row["L"]) - 1) / (chart_row["L"] * chart_row["S"])

    return norm.cdf(z_score) *100

# Get percentile.
def calc_value(months, days, val, chart, unit, isImperial = False):

    # Add days to month for age calculation. Based on instructions here: https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/instructions-en.pdf?sfvrsn=5cec8c61_23
    age = round(months * 30.4375 + days)

    # If we've gone over cap (5 years) by some number of days, cap.
    age = min(1856, age)

    # Determine what unit of measurement we're using.
    conv_measurement = val
    unMeasurement = None

    if unit == "weight":

        if isImperial:
            unMeasurement = "pounds"
            conv_measurement *= 0.45359237
        else:
            unMeasurement = "kilograms"
    elif (unit == "length") or unit == "head circumference":
        if isImperial:
            unMeasurement = "inches"
            conv_measurement *= 2.54
        else:
            unMeasurement = "centimeters"
    else:
        print(f"Error: No logic present for unit type {unit}")
        return
    
    # Get percentile
    resultant = calc_percentile(int(age), conv_measurement, chart)

    print(f"For {unit} of {val} {unMeasurement}, percentile at {months} months {days} days: {resultant}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pounds", help="Use weight measurement of pounds", action="store_true")
    parser.add_argument("-i", "--inches", help="Use length measurement of inches", action="store_true")
    parser.add_argument("-c", "--head", type=float, help="the length of the baby's head circumference")
    parser.add_argument("-l", "--length", type=float, help="the length of the baby")
    parser.add_argument("-w", "--weight", type=float, help="the weight of the baby")
    parser.add_argument("-m", "--months", type=int, help="How many months old the baby is.", required=True)
    parser.add_argument("-d", "--days", type=int, help="How many days old the baby is in addition to the month (ie: if the baby is 5 months 2 days old, this is 2 and the month is 5)")
    parser.add_argument("-g", "--gender", type=str, help="The baby's gender. Accepts 'boy' or 'girl'", required=True, action = "store")
    args = parser.parse_args()

    # Used to find script location with data files (makes invariant to script path as long as data files are in same folder)
    scriptPath = str(Path(os.path.dirname(sys.argv[0])).resolve())

    # sanity checks.
    isImperialWeight = args.pounds
    isImperialLength = args.inches

    if (args.gender is None) or ((args.gender != "boy") and (args.gender != "girl")):
        print(f"Error: gender argument must be 'boy' or 'girl', passed argument: {args.gender}")
        return

    if (args.months is None) or ((args.months < 0) or (args.months > 61)):
        print(f"Error: age in month must be between 0 and 61, passed value: {args.months}")
        return

    if args.days is not None:

        if (args.days < 0) or (args.days > 31):
            print(f"Error: days must be positive and less than 31, passed value: {args.days}")
            return
        
        # Since we're standardizing a month to 30 days, make 31 equal to 30 for calculation purposes.
        args.days = min(30, args.days)

        # If a month's worth of days has been added, add to month total and zero out days.
        if args.days == 30:
            args.months += 1
            args.days = 0

    else:
        args.days = 0
    
    if args.head is not None:
        if args.head <= 0:
            print("Error: Head circumference must be greater than 0")
            return
    
    if args.length is not None:
        if args.length <= 0:
            print("Error: Length must be greater than 0")
            return
        
    if args.weight is not None:
        if args.weight <= 0:
            print("Error: Weight must be greater than 0")
            return
    
    # weight calculation
    if args.weight is not None:
        weight_chart = None

        if args.gender == "girl":
            weight_chart = pd.read_excel(f"{scriptPath}/wfa-girls-zscore-expanded-tables.xlsx")
        else:
            weight_chart = pd.read_excel(f"{scriptPath}/wfa-boys-zscore-expanded-tables.xlsx")
           
        weight_chart = weight_chart.set_index(['Day'])

        print("Calculating weight percentile...")
        calc_value(args.months, args.days, args.weight, weight_chart, "weight", isImperialWeight)  
        print()
    
    # length calculation
    if args.length is not None:
        length_chart = None

        if args.gender == "girl":
            length_chart = pd.read_excel(f"{scriptPath}/lhfa-girls-zscore-expanded-tables.xlsx")
        else:
            length_chart = pd.read_excel(f"{scriptPath}/lhfa-boys-zscore-expanded-tables.xlsx")
           
        length_chart = length_chart.set_index(['Day'])

        print("Calculating length percentile...")
        calc_value(args.months, args.days, args.length, length_chart, "length", isImperialLength)
        print()

    # head calculation
    if args.head is not None:
        head_chart = None

        if args.gender == "girl":
            head_chart = pd.read_excel(f"{scriptPath}/hcfa-girls-zscore-expanded-tables.xlsx")
        else:
            head_chart = pd.read_excel(f"{scriptPath}/hcfa-boys-zscore-expanded-tables.xlsx")
           
        head_chart = head_chart.set_index(['Day'])

        print("Calculating head circumference percentile...")
        calc_value(args.months, args.days, args.head, head_chart, "head circumference", isImperialLength)
        print()


if __name__ == "__main__":
    main()


