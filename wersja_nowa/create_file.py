import datetime

def create_mission_report(
    team_name,
    recognized_objects,
    traveled_path,
    optimal_path,
    optimal_path_length,
    filename="raport_misji.txt"
):
    # Zbieranie aktualnej daty
    current_date = datetime.datetime.now().strftime("%d.%m.%Y")

    # Tworzenie zawartości raportu
    report_content = f"""RAPORT Z MISJI REKONESANSOWEJ

Drużyna: {team_name}
Data: {current_date}

Rozpoznane obiekty:
"""

    if recognized_objects:
        for obj in recognized_objects:
            report_content += f"- {obj}\n"
    else:
        report_content += "Brak rozpoznanych obiektów.\n"

    report_content += "\nPrzebyta trasa:\n"
    if traveled_path:
        report_content += " -> ".join(traveled_path) + "\n"
    else:
        report_content += "Brak danych o przebytej trasie.\n"

    report_content += "\nTrasa optymalna:\n"
    if optimal_path:
        report_content += " -> ".join(optimal_path) + "\n"
    else:
        report_content += "Brak danych o trasie optymalnej.\n"

    report_content += f"\nDługość trasy optymalnej:\n{optimal_path_length:.2f} m\n"

    # Zapis do pliku
    with open(filename, "w", encoding="utf-8") as file:
        file.write(report_content)

    print(f"Raport zapisany do pliku: {filename}")

# PRZYKŁAD UŻYCIA:
if __name__ == "__main__":
    team_name = "UGV-Tech"
    recognized_objects = ["czerwona kula", "zielony sześcian", "niebieski stożek"]
    traveled_path = ["A1", "B1", "B2", "C2", "C3"]
    optimal_path = ["A1", "B2", "C3"]
    optimal_path_length = 7.42

    create_mission_report(
        team_name,
        recognized_objects,
        traveled_path,
        optimal_path,
        optimal_path_length
    )
