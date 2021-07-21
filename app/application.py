from flask import Flask, request, abort
from jsonschema import validate, exceptions
from schema import (
    CourierItem,
    CourierUpdateRequest,
    OrderItem,
    OrdersAssignPostRequest,
    OrdersCompletePostRequest,
)
from sql import (
    get_database,
    create_courier,
    profile,
    change_courier_type,
    change_regions_courier,
    change_working_hours_courier,
    create_order,
    create_order_complete,
    assign_order,
    delete_order_assign,
    check_order_complete,
    check_order_in_assign,
    change_current_time,
    add_time_delivery,
    profile_after_change,
)
from work_with_time import (
    validate_work_hours,
    information_error_courier,
    information_error_order,
)

from cProfile import Profile


app = Flask(__name__)


@app.errorhandler(400)
def answer_400(error):
    return "BAD REQUEST", 400


@app.route("/couriers", methods=["POST"])
def add_couriers():
    """
    Обработчик принимает на вход в формате  json  список с данными о курьерах и графиком их работы.
    Курьеры работают только в заранее определенных районах, а так же различаются по типу: пеший, велокурьер
    и курьер на автомобиле. От типа курьера зависит его грузоподъемность — 10 кг, 15 кг и 50 кг соответственно.
    Районы задаются целыми положительными числами. График работы задается списком строк формата  HH:MM-HH:MM .
    """
    answer_error = {"validation_error": {"couriers": []}}
    id_error = answer_error["validation_error"]
    valid_couriers = {"couriers": []}

    json_couriers = request.get_json()
    for row in json_couriers["data"]:
        try:
            validate(instance=row, schema=CourierItem)
            for wh in row["working_hours"]:
                if not validate_work_hours(wh):
                    raise exceptions.ValidationError
            valid_couriers["couriers"].append({"id": row["courier_id"]})
        except exceptions.ValidationError as ex:
            id_error["couriers"].append(
                {"id": row["courier_id"], "message": information_error_courier(ex)}
            )

    if len(id_error["couriers"]) > 0:
        return answer_error, 400

    with get_database() as db:
        for row in json_couriers["data"]:
            create_courier(
                db,
                row["courier_id"],
                row["courier_type"],
                row["working_hours"],
                row["regions"],
            )
    return valid_couriers, 201


@app.route("/couriers/<int:courier_id>", methods=["GET"])
def get_courier(courier_id):
    """Возвращает информацию о курьере и дополнительную статистику: рейтинг и заработок."""

    with get_database() as db:
        answer = profile(db, courier_id)
    if not answer:
        abort(404)
    return answer


@app.route("/couriers/<int:courier_id>", methods=["PATCH"])
def edit_courier(courier_id):
    """Позволяет изменить информацию о курьере.

    Принимает  json  и любые поля из списка:  courier_type ,  regions ,
    working_hours. При редактировании следует учесть случаи, когда меняется график, регион и уменьшается грузоподъемность и появляются
    заказы, которые курьер уже не сможет развести — такие заказы должны сниматься и быть доступными для выдачи другим
    курьерам.
    """
    json_courier_change = request.get_json()
    try:
        validate(instance=json_courier_change, schema=CourierUpdateRequest)
        for wh in json_courier_change.get("working_hours", []):
            if not validate_work_hours(wh):
                raise exceptions.ValidationError
    except exceptions.ValidationError:
        return abort(400)

    with get_database() as db:
        for key in json_courier_change:
            if key == "regions":
                change_regions_courier(db, courier_id, json_courier_change[key])
            elif key == "courier_type":
                change_courier_type(db, courier_id, json_courier_change[key])
            elif key == "working_hours":
                change_working_hours_courier(db, courier_id, json_courier_change[key])
        answer = profile_after_change(db, courier_id)
    return answer


@app.route("/orders", methods=["POST"])
def add_orders():
    """Принимает на вход в формате  json  список с данными о заказах. Заказы характеризуются весом, районом и
    временем доставки."""

    answer_error = {"validation_error": {"orders": []}}
    id_error = answer_error["validation_error"]
    valid_orders = {"orders": []}

    json_orders = request.get_json()
    for row in json_orders["data"]:
        try:
            validate(instance=row, schema=OrderItem)
            for wh in row["delivery_hours"]:
                if not validate_work_hours(wh):
                    raise exceptions.ValidationError
            valid_orders["orders"].append({"id": row["order_id"]})

        except exceptions.ValidationError as ex:
            id_error["orders"].append(
                {"id": row["order_id"], "message": information_error_order(ex)}
            )

    if len(id_error["orders"]) > 0:
        return answer_error, 400

    with get_database() as db:
        for row in json_orders["data"]:
            create_order(
                db, row["order_id"], row["weight"], row["region"], row["delivery_hours"]
            )
    return valid_orders, 201


@app.route("/orders/assign", methods=["POST"])
def assign_orders():
    """
    Принимает id курьера и назначает максимальное количество заказов, подходящих по весу, району и графику работы.
    Обработчик идемпотентный. Заказы, выданные одному курьеру, не доступны для выдачи другому.
    """
    json_id_couriers = request.get_json()
    try:
        validate(instance=json_id_couriers, schema=OrdersAssignPostRequest)
    except exceptions.ValidationError:
        abort(400)
    courier_id = json_id_couriers["courier_id"]

    with get_database() as db:
        response = assign_order(db, courier_id)
    if not response:
        abort(400)
    return response


@app.route("/orders/complete", methods=["POST"])
def orders_complete():
    """Принимает 3 параметра: id курьера, id заказа и время выполнения заказа, отмечает заказ выполненным."""
    json_orders_complete = request.get_json()
    try:
        validate(instance=json_orders_complete, schema=OrdersCompletePostRequest)
    except exceptions.ValidationError:
        abort(400)

    with get_database() as db:
        if check_order_complete(db, json_orders_complete["order_id"]):
            return {"order_id": json_orders_complete["order_id"]}
        if not check_order_in_assign(
            db, json_orders_complete["courier_id"], json_orders_complete["order_id"]
        ):
            abort(400)
        create_order_complete(
            db,
            json_orders_complete["courier_id"],
            json_orders_complete["order_id"],
            json_orders_complete["complete_time"],
        )
        delete_order_assign(db, json_orders_complete["order_id"])
        add_time_delivery(
            db,
            json_orders_complete["order_id"],
            json_orders_complete["courier_id"],
            json_orders_complete["complete_time"],
        )
        change_current_time(
            db,
            json_orders_complete["order_id"],
            json_orders_complete["courier_id"],
            json_orders_complete["complete_time"],
        )
        db.commit()
    return {"order_id": json_orders_complete["order_id"]}


if __name__ == "__main__":
    app.run()

