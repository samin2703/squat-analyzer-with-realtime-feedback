import pandas as pd
import numpy as np

CSV_PATH = "b5pt-20-form (Responses) - Form responses 1.csv"
OUTPUT_PATH = "C:/Users/sasam/OneDrive/Desktop/exerc_assess/res_out.csv"

traits = {
    "Extraversion":      [(1, False), (6, True),  (11, False), (16, True)],
    "Agreeableness":     [(2, False), (7, True),  (12, False), (17, True)],
    "Conscientiousness": [(3, False), (8, True),  (13, False), (18, True)],
    "Neuroticism":       [(4, False), (9, True),  (14, False), (19, True)],
    "Openness":          [(5, False), (10, True), (15, True),  (20, True)]
}

# Load CSV
df = pd.read_csv("responses.csv")

# Column 1 = Name, Columns 2–21 = Q1–Q20
names = df.iloc[:, 1]
responses = df.iloc[:, 2:22].apply(pd.to_numeric, errors="coerce")

def compute_big5(row):
    result = {}
    for trait, items in traits.items():
        total = 0
        for q_num, reverse in items:
            score = row.iloc[q_num - 1]
            score = 6 - score if reverse else score
            total += score

        avg = total / 4
        scaled = (avg - 1) / 4

        result[f"{trait}_avg"] = round(avg, 3)
        result[f"{trait}_scaled"] = round(scaled, 3)

    return pd.Series(result)

big5_df = responses.apply(compute_big5, axis=1)

# ---- FINAL OUTPUT (clean) ----
final_df = pd.concat([names, big5_df], axis=1)
final_df.to_csv(OUTPUT_PATH, index=False)
# -------- TERMINAL TABLE OUTPUT --------
print("\nBig Five Personality Scores (Avg | Scaled)")
print("-" * 110)

header = (
    f"{'Name':<20}"
    f"{'EXT(avg)':>10}{'EXT(s)':>8}"
    f"{'AGR(avg)':>10}{'AGR(s)':>8}"
    f"{'CON(avg)':>10}{'CON(s)':>8}"
    f"{'NEU(avg)':>10}{'NEU(s)':>8}"
    f"{'OPE(avg)':>10}{'OPE(s)':>8}"
)

print(header)
print("-" * 110)

for _, row in final_df.iterrows():
    print(
        f"{row.iloc[0]:<20}"
        f"{row['Extraversion_avg']:>10.2f}{row['Extraversion_scaled']:>8.2f}"
        f"{row['Agreeableness_avg']:>10.2f}{row['Agreeableness_scaled']:>8.2f}"
        f"{row['Conscientiousness_avg']:>10.2f}{row['Conscientiousness_scaled']:>8.2f}"
        f"{row['Neuroticism_avg']:>10.2f}{row['Neuroticism_scaled']:>8.2f}"
        f"{row['Openness_avg']:>10.2f}{row['Openness_scaled']:>8.2f}"
    )

print("-" * 110)

print("✅ Clean Big Five output saved")
print("📁 File:", OUTPUT_PATH)