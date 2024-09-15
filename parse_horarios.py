import csv
import argparse

# Diccionario para los días de la semana
DAYS_OF_WEEK = {
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes'
}

# Diccionario para los tramos horarios
HOURS_OF_DAY = {
    1: '1ª hora',
    2: '2ª hora',
    3: '3ª hora',
    4: 'Recreo',
    5: '4ª hora',
    6: '5ª hora',
    7: '6ª hora'
}


def parse_csv(file_path):
    schedule = []

    try:
        # Intentamos abrir el archivo con codificación UTF-8
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                day = int(row[0])
                hour = int(row[1])
                entries = row[2:]

                # Parse blocks of 4 columns
                for i in range(0, len(entries), 4):
                    if len(entries[i:i + 4]) == 4:
                        subject = entries[i]
                        teacher = entries[i + 1]
                        room = entries[i + 2]
                        unit = entries[i + 3]
                        schedule.append({
                            'day': day,
                            'hour': hour,
                            'subject': subject,
                            'teacher': teacher,
                            'room': room,
                            'unit': unit
                        })
    except UnicodeDecodeError:
        # Si falla con utf-8, intentamos con ISO-8859-1
        with open(file_path, newline='', encoding='ISO-8859-1') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                day = int(row[0])
                hour = int(row[1])
                entries = row[2:]

                # Parse blocks of 4 columns
                for i in range(0, len(entries), 4):
                    if len(entries[i:i + 4]) == 4:
                        subject = entries[i]
                        teacher = entries[i + 1]
                        room = entries[i + 2]
                        unit = entries[i + 3]
                        schedule.append({
                            'day': day,
                            'hour': hour,
                            'subject': subject,
                            'teacher': teacher,
                            'room': room,
                            'unit': unit
                        })

    return schedule


def print_teacher_schedule(schedule, teacher_name):
    print(f"Horario para el profesor {teacher_name}:")
    for entry in schedule:
        if entry['teacher'].lower() == teacher_name.lower():
            day_name = DAYS_OF_WEEK.get(entry['day'], f'Día {entry["day"]}')
            hour_name = HOURS_OF_DAY.get(entry['hour'], f'Hora {entry["hour"]}')
            print(f"{day_name}, {hour_name}: {entry['subject']} en aula {entry['room']} (Unidad: {entry['unit']})")


def print_unit_schedule(schedule, unit_name):
    print(f"Horario para la unidad {unit_name}:")
    for entry in schedule:
        if entry['unit'].lower() == unit_name.lower():
            day_name = DAYS_OF_WEEK.get(entry['day'], f'Día {entry["day"]}')
            hour_name = HOURS_OF_DAY.get(entry['hour'], f'Hora {entry["hour"]}')
            print(f"{day_name}, {hour_name}: {entry['subject']} con {entry['teacher']} en aula {entry['room']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Procesar y mostrar horarios.')
    parser.add_argument('csv_file', help='Ruta del archivo CSV con los horarios.')
    parser.add_argument('--profesor', help='Nombre del profesor para mostrar su horario.')
    parser.add_argument('--unidad', help='Nombre de la unidad para mostrar su horario.')

    args = parser.parse_args()

    schedule = parse_csv(args.csv_file)

    if args.profesor:
        print_teacher_schedule(schedule, args.profesor)
    elif args.unidad:
        print_unit_schedule(schedule, args.unidad)
    else:
        print("Por favor, indique si desea ver el horario de un profesor o de una unidad.")
