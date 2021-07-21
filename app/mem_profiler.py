import requests


def bid_data_by_step(step: int):
    """
    Увеличивает объём данных в зависимости от шага. Первый шаг от 0 до 10 000 айдишников,
    2 шаг от 10 000 до 30 000 айдишников
    3 шаг от 30 000 до 60 000 айдишников и т.д.
    """
    data = {
        "data": []
    }
    stop = 0
    start = 0
    for i in range(step):
        stop += (i + 1) * 10000
        for j in range(start, stop):
            data["data"].append(
                    {
                        "courier_id": j,
                        "courier_type": "foot",
                        "regions": [1, 12, 22],
                        "working_hours": ["11:35-14:05", "09:00-11:00"]
                    }
            )
        r = requests.post('http://127.0.0.1:5000/couriers', json=data)
        start = stop


if __name__ == "__main__":
    bid_data_by_step(3)
