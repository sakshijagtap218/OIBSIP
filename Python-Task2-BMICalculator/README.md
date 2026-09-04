# Task 2: BMI Calculator
# Developed for Oasis Infobyte Internship

def calculate_bmi(weight, height_m):
    return weight / (height_m ** 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 24.9:
        return "Normal weight (Healthy)"
    elif 25 <= bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"

def main():
    print("=" * 35)
    print("     OASIS INFOBYTE - BMI CALCULATOR     ")
    print("=" * 35)
    
    try:
        weight = float(input("Enter your weight in kg (e.g., 65): "))
        height_cm = float(input("Enter your height in cm (e.g., 170): "))
        
        if weight <= 0 or height_cm <= 0:
            print("❌ Please enter positive numbers for weight and height.")
            return

        height_m = height_cm / 100
        bmi = calculate_bmi(weight, height_m)
        category = get_bmi_category(bmi)

        print("\n--- RESULTS ---")
        print(f"Your BMI: {bmi:.2f}")
        print(f"Category: {category}")
        print("----------------")

    except ValueError:
        print("❌ Invalid input! Please enter numbers only.")

if __name__ == "__main__":
    main()
