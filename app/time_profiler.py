import requests


def bid_data_stress(count: int):
    """
    Отправляют данные курьеров одним запросом
    в количество указанном в count
    """
    data = {
        "data": []
    }
    for i in range(count):
        data["data"].append(
                {
                    "courier_id": i,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                }
        )
    r = requests.post('http://127.0.0.1:5000/couriers', json=data)


def by_one_request(start: int, end: int):
    """
    Отправляет по одному курьеру на сервер
    """
    for i in range(start, end):
        body = {
            "data":
            [
                {
                    "courier_id": i,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                }
            ]
        }
        r = requests.post('http://127.0.0.1:5000/couriers', json=body)


if __name__ == "__main__":
    bid_data_stress(50000)
    by_one_request(50000, 50002)
