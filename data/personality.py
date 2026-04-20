"""Big Five profile formatting and loading utilities."""

import csv
import os
from typing import List, Optional

from config import settings


def get_participant_names(csv_path: str = "res_out.csv") -> List[str]:
    """Return sorted unique participant names from CSV (empty list on any issue)."""
    if not os.path.exists(csv_path):
        return []

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            name_col = None
            for fn in fieldnames:
                if fn and fn.strip().lower() == "name":
                    name_col = fn
                    break

            if name_col is None:
                return []

            names = {(r.get(name_col) or "").strip() for r in reader}
            return sorted(n for n in names if n)
    except Exception:
        return []


def format_big5_for_prompt() -> str:
    """Adapt the feedback that would be suitable matching Big Five profile."""
    b = settings.BIG5_PERSONALITY
    return (
        f"- Openness: {b['openness']:.1f} / 10\n"
        f"- Conscientiousness: {b['conscientiousness']:.1f} / 10\n"
        f"- Extraversion: {b['extraversion']:.1f} / 10\n"
        f"- Agreeableness: {b['agreeableness']:.1f} / 10\n"
        f"- Neuroticism: {b['neuroticism']:.1f} / 10\n"
    )


def get_big5_from_user():
    """Ask user for Big Five scores (1-10), preserving original flow."""
    if not settings.USE_OLLAMA or not settings.PERSONALITY_ADAPTIVE_MODE:
        return

    print("\nEnter Big Five personality scores (1-10). Press Enter to keep default 5.0 for each trait.")
    traits_order = [
        ("openness", "Openness"),
        ("conscientiousness", "Conscientiousness"),
        ("extraversion", "Extraversion"),
        ("agreeableness", "Agreeableness"),
        ("neuroticism", "Neuroticism"),
    ]
    for key, label in traits_order:
        while True:
            s = input(f"{label} (1-10, default 5): ").strip()
            if s == "":
                break
            try:
                val = float(s)
                if 1.0 <= val <= 10.0:
                    settings.BIG5_PERSONALITY[key] = val
                    break
                print("  Please enter a number between 1 and 10.")
            except ValueError:
                print("  Invalid input, please enter a number between 1 and 10.")

    print("\nUsing Big Five profile:")
    print(format_big5_for_prompt())


def load_big5_from_csv(csv_path: str = "res_out.csv", participant_name: Optional[str] = None, interactive: bool = True):
    """Load Big Five scores from CSV, with optional non-interactive matching."""
    if not settings.USE_OLLAMA or not settings.PERSONALITY_ADAPTIVE_MODE:
        return

    if not os.path.exists(csv_path):
        print(f"\nCSV file '{csv_path}' not found.")
        if interactive:
            get_big5_from_user()
        return

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        name_col = None
        for fn in fieldnames:
            if fn and fn.strip().lower() == "name":
                name_col = fn
                break

        if name_col is None:
            print("\n'Name' column not found in CSV.")
            if interactive:
                get_big5_from_user()
            return

        rows = list(reader)
        if not rows:
            print("\nCSV has no data rows.")
            if interactive:
                get_big5_from_user()
            return

        chosen_row = None
        target = participant_name

        if interactive and not target:
            print("\nAvailable participants in res_out.csv:")
            unique_names = sorted({(r.get(name_col) or "").strip() for r in rows if (r.get(name_col) or "").strip()})
            for n in unique_names:
                print("  ", n)
            while True:
                target = input("\nEnter participant name: ").strip()
                if target:
                    break
                print("Please enter a non-empty name.")

        if target:
            matches = [r for r in rows if (r.get(name_col) or "").strip().lower() == target.lower()]
            if matches:
                chosen_row = matches[0]
            else:
                partial = [r for r in rows if target.lower() in (r.get(name_col) or "").strip().lower()]
                if len(partial) == 1:
                    chosen_row = partial[0]

        if chosen_row is None and not interactive:
            return

        if chosen_row is None:
            print("Name not found.")
            get_big5_from_user()
            return

        settings.PARTICIPANT_NAME = (chosen_row.get(name_col) or "").strip()

        col_map = {
            "extraversion": None,
            "agreeableness": None,
            "conscientiousness": None,
            "neuroticism": None,
            "openness": None,
        }
        for fn in fieldnames:
            if not fn:
                continue
            key = fn.strip().lower()
            if key == "extraversion_scaled":
                col_map["extraversion"] = fn
            elif key == "agreeableness_scaled":
                col_map["agreeableness"] = fn
            elif key == "conscientiousness_scaled":
                col_map["conscientiousness"] = fn
            elif key == "neuroticism_scaled":
                col_map["neuroticism"] = fn
            elif key == "openness_scaled":
                col_map["openness"] = fn

        missing = [trait for trait, col in col_map.items() if col is None]
        if missing:
            print(f"\nMissing scaled columns for: {', '.join(missing)}")
            if interactive:
                get_big5_from_user()
            return

        try:
            settings.BIG5_PERSONALITY["extraversion"] = float(chosen_row[col_map["extraversion"]]) * 10.0
            settings.BIG5_PERSONALITY["agreeableness"] = float(chosen_row[col_map["agreeableness"]]) * 10.0
            settings.BIG5_PERSONALITY["conscientiousness"] = float(chosen_row[col_map["conscientiousness"]]) * 10.0
            settings.BIG5_PERSONALITY["neuroticism"] = float(chosen_row[col_map["neuroticism"]]) * 10.0
            settings.BIG5_PERSONALITY["openness"] = float(chosen_row[col_map["openness"]]) * 10.0
        except (TypeError, ValueError) as e:
            print(f"\nCould not parse scaled values from CSV ({e}).")
            settings.PARTICIPANT_NAME = None
            if interactive:
                get_big5_from_user()
            return

    print("\nUsing Big Five profile from CSV for:", settings.PARTICIPANT_NAME)
    print(format_big5_for_prompt())
