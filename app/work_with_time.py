def intersect_diapazon(time_work, time_delivery):
    """
    Проверяет пересечение двух временных диапазонов
    """
    (start_delivery, end_delivery) = time_delivery
    for (start_work, end_work) in time_work:
        if end_work <= start_delivery or end_delivery <= start_work:
            continue
        else:
            return True
    return False

def capacity(courier_type):
    if courier_type == "foot":
        return 10
    elif courier_type == "bike":
        return 15
    elif courier_type == "car":
        return 50


def income_by_transport(courier_type):
    if courier_type == "foot":
        return 2
    elif courier_type == "bike":
        return 5
    elif courier_type == "car":
        return 9

def parse_wh(lines):
    """
    >>> parse_wh(["00:00-01:30"])
    [(0, 90)]
    >>> parse_wh(["23:30-01:30"])
    [(1410, 1440), (0, 90)]
    """
    result = []
    for line in lines:
        start, end = line.split('-')
        (start_h, start_m), (end_h, end_m) = start.split(':'), end.split(':')
        start, end = (int(start_h) * 60 + int(start_m)), (int(end_h) * 60 + int(end_m))
        if end > start:
            result.append((start, end))
        else:
            result.append((start, 1440))
            result.append((0, end))
    return result

def validate_work_hours(text):
    start, end = text.split('-')
    start_hours, start_minute = start.split(':')
    end_hours, end_minute = end.split(':')
    if int(start_hours)>23 or int(end_hours)>23:
        return False
    if int(start_minute)>59 or int(end_minute)>59:
        return False
    return True

def reparse(time):
    """
    >>> reparse([0, 90])
    '00:00-01:30'
    """
    start = time[0]
    start_hours = str(start//60)
    start_minute = str(start%60)
    start = (start_hours if len(start_hours)>1 else "0" + start_hours) + ":" + (start_minute if len(start_minute)>1 else "0" + start_minute)

    end = time[1]
    end_hours = str(end//60)
    end_minute = str(end%60)
    end = (end_hours if len(end_hours)>1 else "0" + end_hours) + ":" + (end_minute if len(end_minute)>1 else "0" + end_minute)

    return start + "-" + end


def information_error_courier(error):
    if error.relative_schema_path[1] == "courier_type":
        return f'Неправильно заполнено поле courier_type. Введите туда одно значение из [foot, bike , car].'
    elif error.relative_schema_path[1] == "regions":
        return f'Неправильно заполнено поле regions. Поле должно содержать один или несколько регионов в формате положительного числа внутри списка.'
    elif error.relative_schema_path[1] == "working_hours":
        return f'Неправильно заполнено поле working_hours. Поле должно содержать один или несколько промежутков времени в формате строки HH:MM-HH:MM внутри списка.'

def information_error_order(error):
    if error.relative_schema_path[1] == "weight":
        return f'Неправильно заполнено поле weight. Введите туда заказ весом от 0.01 до 50.'
    elif error.relative_schema_path[1] == "region":
        return f'Неправильно заполнено поле region. Поле должно содержать номер региона в формате положительного числа.'
    elif error.relative_schema_path[1] == "delivery_hours":
        return f'Неправильно заполнено поле delivery_hours. Поле должно содержать один или несколько промежутков времени в формате строки HH:MM-HH:MM внутри списка.'
