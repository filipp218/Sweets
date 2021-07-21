import contextlib
import sqlite3
from work_with_time import (
    reparse,
    intersect_diapazon,
    parse_wh,
    capacity,
    income_by_transport,
)
from datetime import datetime


@contextlib.contextmanager
def get_database():
    """
    sqlite3 -init init.sql doogs.db
    """
    db = sqlite3.connect("doogs.db")
    db.row_factory = sqlite3.Row
    yield db
    db.close()


def create_courier(db, courier_id, courier_type, working_hours, regions):
    """
    Добавляет курьера в базу данных
    """
    cur = db.cursor()

    sql = """
        SELECT * FROM Couriers
        WHERE courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    if cur.fetchone() is not None:  #После профилирования
        return courier_id

    sql = """
        INSERT INTO
            Couriers(
                courier_id,
                courier_type
                )
            VALUES (?, ?);
    """
    cur.execute(sql, (courier_id, courier_type))

    working_hours = parse_wh(working_hours)
    items = []
    for (start, end) in working_hours:
        items.append((courier_id, start, end))
    sql = """
        INSERT INTO
            CourierToHours(
                courier_id,
                working_hours_start,
                working_hours_end
                )
            VALUES (?, ?, ?);
    """
    cur.executemany(sql, items)

    items = []
    for num in regions:
        items.append((courier_id, num))
    sql = """
        INSERT INTO
            CourierToRegion(
                courier_id,
                region_id
                )
            VALUES (?, ?);
    """
    cur.executemany(sql, items)
    db.commit()
    return courier_id


def _count_income(db, courier_id):
    """Считает заработок курьера"""
    cur = db.cursor()
    sql = """
        SELECT
            SUM(income)
        FROM
            EarningsCourier
        INNER JOIN
            OrdersCompleted ON
            OrdersCompleted.order_id = EarningsCourier.order_id
        WHERE
            EarningsCourier.courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    for i in cur.fetchone():
        income = i
    return income


def _courier_rating(db, courier_id):
    """Считает рейтинг курьера, если он сделал хотя бы один заказ"""
    cur = db.cursor()
    sql = """
        SELECT
            count(1) as count
        FROM
            TimeDelivery
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))

    count = 0
    for i in cur.fetchone():
        count = i
    if not count:
        return None

    sql = """
        SELECT
            AVG(delivery_second) AS avg
        FROM
            TimeDelivery
        WHERE
            courier_id = ?
        GROUP BY
            region;
    """
    cur.execute(sql, (courier_id,))
    avg_time_delivery = cur.fetchall()
    min_time = []
    for row in avg_time_delivery:
        min_time.append(row["avg"])
    t = min(min_time)
    rate = (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5
    return rate


def profile_after_change(db, courier_id):
    """
    Показывает все данные курьера, кроме заработка и рейтинга
    """
    cur = db.cursor()
    sql = """
        SELECT
            courier_type
        FROM
            Couriers
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    transport = cur.fetchone()
    if not transport:  # если нет транспорта, значит нет курьера
        return False

    sql = """
        SELECT
            region_id
        FROM
            CourierToRegion
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    regions = cur.fetchall()
    region = [i["region_id"] for i in regions]

    sql = """
        SELECT
            working_hours_start,
            working_hours_end
        FROM
            CourierToHours
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    hours = cur.fetchall()
    working_hours = [reparse(i) for i in hours]
    answer = {
        "courier_id": courier_id,
        "courier_type": transport["courier_type"],
        "regions": region,
        "working_hours": working_hours,
    }
    return answer


def profile(db, courier_id):
    """
    Показывает данные курьера включая заработок и рейтинг
    """
    answer = profile_after_change(db, courier_id)
    if not answer:
        return False
    rating = _courier_rating(db, courier_id)
    earnings = _count_income(db, courier_id)
    if rating is not None:
        answer["rating"] = rating
    if earnings:
        answer["earnings"] = earnings
    else:
        answer["earnings"] = 0
    return answer


def create_order(db, order_id, weight, region, delivery_hours):
    """
    Добавляет заказы в базу данных
    """
    cur = db.cursor()

    sql = """
        SELECT * FROM Orders
        WHERE order_id = ?;
    """
    cur.execute(sql, (order_id,))
    if cur.fetchone() is not None:  #После профилирования
        return order_id

    sql = """
        INSERT INTO
            Orders(
                order_id,
                weight,
                region
                )
            VALUES (?, ?, ?);
    """
    cur.execute(sql, (order_id, weight, region))

    delivery_hours = parse_wh(delivery_hours)
    items = []
    for (start, end) in delivery_hours:
        items.append((order_id, start, end))

    sql = """
        INSERT INTO
            OrderToHours(
                order_id,
                delivery_hours_start,
                delivery_hours_end
                )
            VALUES (?, ?, ?);
    """
    cur.executemany(sql, items)
    db.commit()
    return order_id


def _droped_orders_after_change(db, orders):
    cur = db.cursor()
    drop_orders_id = []
    for id in orders:
        drop_orders_id.append((id,))

    sql = """
        DELETE FROM
            OrdersAssigned
        WHERE
            order_id = ?;
    """
    cur.executemany(sql, drop_orders_id)


def change_regions_courier(db, courier_id, regions):
    """Меняет регион курьера"""
    cur = db.cursor()
    sql = """
        DELETE FROM
            CourierToRegion
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))

    items = []
    for num in regions:
        items.append((courier_id, num))

    sql = """
        INSERT INTO
            CourierToRegion(
                courier_id,
                region_id
                )
            VALUES (?, ?);
    """
    cur.executemany(sql, items)

    # Выбираем все id заказов, которые стоит удалить при изменении региона
    sql = """
        SELECT
            OrdersAssigned.order_id
        FROM
            OrdersAssigned
        LEFT JOIN
            Orders ON OrdersAssigned.order_id = Orders.order_id
        LEFT JOIN
            Couriers ON OrdersAssigned.courier_id = Couriers.courier_id
        WHERE
            OrdersAssigned.courier_id = ?
            and
            Orders.region NOT IN ({});
        """.format(
        ",".join("?" * len(regions))
    )

    cur.execute(sql, (courier_id, *regions))
    orders = cur.fetchall()
    result = []
    for row in orders:
        result.append(row["order_id"])
    _droped_orders_after_change(db, result)
    db.commit()
    return


def change_courier_type(db, courier_id, courier_type):
    """Меняет тип курьера"""
    cur = db.cursor()
    sql = """
        UPDATE
            Couriers
        SET
            courier_type = ?
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_type, courier_id))

    sql = """
        SELECT
            OrdersAssigned.order_id,
            Orders.weight
        FROM
            OrdersAssigned
        LEFT JOIN
            Orders ON OrdersAssigned.order_id = Orders.order_id
        WHERE
            OrdersAssigned.courier_id = ?
        ORDER BY
            Orders.weight ASC;
        """
    max_capacity = capacity(courier_type)
    cur.execute(sql, (courier_id,))
    orders = cur.fetchall()
    result = set()
    for row in orders:
        if row["weight"] > max_capacity:
            result.add(row["order_id"])
        else:
            max_capacity -= row["weight"]

    result = list(result)
    _droped_orders_after_change(db, result)
    db.commit()
    return


def change_working_hours_courier(db, courier_id, working_hours):
    """Меняет часы работы курьера"""
    cur = db.cursor()
    sql = """
        DELETE FROM
            CourierToHours
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))

    time_work = parse_wh(working_hours)
    items = []
    for (start, end) in time_work:
        items.append((courier_id, start, end))

    sql = """
        INSERT INTO
            CourierToHours(
                courier_id,
                working_hours_start,
                working_hours_end
                )
            VALUES (?, ?, ?);
    """
    cur.executemany(sql, items)

    sql = """
        SELECT
            OrdersAssigned.order_id,
            OrderToHours.delivery_hours_start,
            OrderToHours.delivery_hours_end
        FROM
            OrdersAssigned
        LEFT JOIN
            OrderToHours ON OrdersAssigned.order_id = OrderToHours.order_id
        WHERE
            courier_id = ?;
    """

    cur.execute(sql, (courier_id,))
    orders = cur.fetchall()
    result = set()

    for row in orders:
        item = row["delivery_hours_start"], row["delivery_hours_end"]
        if row["order_id"] in result:
            continue
        elif not intersect_diapazon(time_work, item):
            result.add(row["order_id"])

    result = list(result)
    _droped_orders_after_change(db, result)
    db.commit()
    return


def check_order_complete(db, order_id):
    """
    Проверяет, может быть заказ уже отмечен, как выполненный
    """
    cur = db.cursor()
    sql = """
        SELECT
            order_id
        FROM
            OrdersCompleted
        WHERE
            order_id = ?;
    """
    cur.execute(sql, (order_id,))
    if cur.fetchone():
        return True
    return False


def check_order_in_assign(db, courier_id, order_id):
    """
    Проверяет, что заказ выполнил курьер на которого он был выписан
    """
    cur = db.cursor()
    sql = """
        SELECT
            order_id
        FROM
            OrdersAssigned
        WHERE
            order_id = ? and courier_id = ?;
    """
    cur.execute(sql, (order_id, courier_id))
    if cur.fetchone():
        return True
    return False


def change_current_time(db, order_id, courier_id, current_time):
    """
    Отмечает время последнего действия, чтобы вычислять время доставки
    """
    cur = db.cursor()
    sql = """
        DELETE FROM
            CurrentOrders
        WHERE
            order_id = ?;
    """
    cur.execute(sql, (order_id,))

    sql = """
        UPDATE
            CurrentOrders
        SET
            start = ?
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (current_time, courier_id))


def add_time_delivery(db, order_id, courier_id, complete_time):
    """
    Вычисляет время доставки заказа в секундах
    """
    cur = db.cursor()
    sql = """
        SELECT
            region
        FROM
            OrdersCompleted
        WHERE
            order_id = ?;
    """
    cur.execute(sql, (order_id,))
    region = int()
    for i in cur.fetchone():
        region = i

    sql = """
        SELECT
            start
        FROM
            CurrentOrders
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    first_time = int()
    for i in cur.fetchone():
        first_time = i

    first_time = datetime.strptime(first_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    complete_time = datetime.strptime(complete_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    duration = complete_time - first_time
    delivery_second = duration.total_seconds()

    sql = """
        INSERT INTO
            TimeDelivery(
                courier_id,
                region,
                order_id,
                delivery_second
                )
            VALUES (?, ?, ?, ?);
    """
    cur.execute(sql, (courier_id, region, order_id, delivery_second))


def create_order_complete(db, courier_id, order_id, complete_time):
    """Добавляет выполненные заказы в базу данных"""
    cur = db.cursor()
    sql = """
        SELECT
            region
        FROM
            OrdersAssigned
        WHERE
            order_id = ?;
    """
    cur.execute(sql, (order_id,))
    region = int()
    for i in cur.fetchone():
        region = i

    sql = """
        INSERT INTO
            OrdersCompleted(
                courier_id,
                order_id,
                complete_time,
                region
                )
            VALUES (?, ?, ?, ?);
    """
    cur.execute(sql, (courier_id, order_id, complete_time, region))


def _idempt_assign_order(db, courier_id):
    cur = db.cursor()
    sql = """
        SELECT
            order_id,
            assign_time
        FROM
            OrdersAssigned
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))
    orders = cur.fetchall()
    result = []
    assign_time = float()
    for row in orders:
        result.append(row["order_id"])
        assign_time = row["assign_time"]

    if result:
        return {"orders": [{"id": i} for i in result], "assign_time": assign_time}
    else:
        return False


def _check_courier(db, courier_id):
    cur = db.cursor()
    sql = """
        SELECT
            courier_type
        FROM
            Couriers
        WHERE
            courier_id = ?;
    """
    cur.execute(sql, (courier_id,))  # если нет такого курьера
    if not cur.fetchone():
        return False
    return True


def assign_order(db, courier_id):
    """
    Принимает id курьера и назначает максимальное количество заказов, подходящих по весу, району и графику работы.
    Обработчик идемпотентный. Заказы, выданные одному курьеру, не доступны для выдачи другому.
    """

    check = _check_courier(db, courier_id)  # если курьера нет в БД
    if not check:
        return check

    answer = _idempt_assign_order(db, courier_id)  # если уже есть заказы у курьера
    if answer:
        return answer

    cur = db.cursor()
    sql = """
        SELECT
            Couriers.courier_id,
            Couriers.courier_type,
            CourierToRegion.region_id,
            CourierToHours.working_hours_start,
            CourierToHours.working_hours_end
        FROM
            Couriers
        LEFT JOIN
            CourierToRegion
                ON Couriers.courier_id = CourierToRegion.courier_id
        LEFT JOIN
            CourierToHours
                ON Couriers.courier_id = CourierToHours.courier_id
        WHERE
            Couriers.courier_id = ?;
        """

    cur.execute(sql, (courier_id,))
    courier = cur.fetchall()

    regions = set()
    time_work = []
    courier_type = ""
    for row in courier:
        regions.add(row["region_id"])
        items = (row["working_hours_start"], row["working_hours_end"])
        time_work.append((items))
        courier_type = row["courier_type"]

    max_capacity = capacity(courier_type)

    sql = """
        SELECT
            Orders.order_id,
            Orders.region,
            Orders.weight,
            OrderToHours.delivery_hours_start,
            OrderToHours.delivery_hours_end
        FROM
            Orders
        LEFT JOIN
            OrderToHours
                ON Orders.order_id = OrderToHours.order_id
        LEFT JOIN
            OrdersAssigned
                ON Orders.order_id = OrdersAssigned.order_id
        WHERE
            OrdersAssigned.order_id is NULL
            and Orders.weight <= ?
            and Orders.region IN ({})
        ORDER BY
            Orders.weight ASC;
        """.format(
        ",".join("?" * len(regions))
    )

    cur.execute(sql, (max_capacity, *regions))
    orders = cur.fetchall()

    result = {}
    for row in orders:
        item = row["delivery_hours_start"], row["delivery_hours_end"]
        if row["order_id"] in result:
            continue
        elif intersect_diapazon(time_work, item):
            if row["weight"] > max_capacity:
                break
            result[row["order_id"]] = row["region"]
            max_capacity -= row["weight"]

    items_for_assign = []
    itmes_for_income = []
    income = income_by_transport(courier_type)*500

    assign_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4] + "Z"
    for order in result:
        items_for_assign.append((courier_id, order, assign_time, result[order]))
        itmes_for_income.append((courier_id, order, income))

    sql = """
        INSERT INTO
            OrdersAssigned(
                courier_id,
                order_id,
                assign_time,
                region
                )
            VALUES (?, ?, ?, ?);
    """
    cur.executemany(sql, items_for_assign)

    sql = """
        INSERT INTO
            EarningsCourier(
                courier_id,
                order_id,
                income
                )
            VALUES (?, ?, ?);
    """
    cur.executemany(sql, itmes_for_income)

    sql = """
        INSERT INTO
            CurrentOrders(
                courier_id,
                order_id,
                start,
                region
                )
            VALUES (?, ?, ?, ?);
    """
    cur.executemany(sql, items_for_assign)
    db.commit()

    if not result:
        return {"orders": []}
    return {"orders": [{"id": i} for i in result], "assign_time": assign_time}


def delete_order_assign(db, order_id):
    cur = db.cursor()
    sql = """
        DELETE FROM
            OrdersAssigned
        WHERE
            order_id = ?
    """
    cur.execute(sql, (order_id,))
