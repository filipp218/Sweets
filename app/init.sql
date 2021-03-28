CREATE TABLE Couriers (
    courier_id integer PRIMARY KEY,
    courier_type varchar(4)
);


CREATE TABLE CourierToHours (
    courier_id integer,
    working_hours_start integer,
    working_hours_end integer
);


CREATE INDEX index_courier_CourierToHours ON CourierToHours(courier_id);


CREATE TABLE CourierToRegion (
    courier_id integer,
    region_id integer
);

CREATE INDEX index_courier_CourierToRegion ON CourierToRegion(courier_id);


CREATE TABLE Orders (
    order_id integer PRIMARY KEY,
    weight integer,
    region integer
);

CREATE INDEX index_region ON Orders(region);

CREATE TABLE OrderToHours (
    order_id integer,
    delivery_hours_start integer,
    delivery_hours_end integer
);

CREATE INDEX index_order_OrderToHours ON OrderToHours(order_id);


CREATE TABLE OrdersAssigned (
    courier_id integer,
    order_id integer,
    assign_time float,
    region integer
);

CREATE INDEX index_order_OrdersAssigned ON OrdersAssigned(order_id);
CREATE INDEX index_courier_OrdersAssigned ON OrdersAssigned(courier_id);

CREATE TABLE OrdersCompleted (
    courier_id integer,
    order_id integer,
    complete_time float,
    region integer
);

CREATE INDEX index_order_OrdersCompleted ON OrdersCompleted(order_id);

CREATE TABLE EarningsCourier (
    courier_id integer,
    order_id integer,
    income integer
);

CREATE INDEX index_order_EarningsCourier ON EarningsCourier(order_id);
CREATE INDEX index_courier_EarningsCourier ON EarningsCourier(courier_id);

CREATE TABLE CurrentOrders (
  courier_id integer,
  order_id integer,
  start integer,
  region integer
);

CREATE INDEX index_order_CurrentOrders ON CurrentOrders(order_id);
CREATE INDEX index_courier_CurrentOrders ON CurrentOrders(courier_id);

CREATE TABLE TimeDelivery (
  courier_id integer,
  region integer,
  order_id integer,
  delivery_second integer
);

CREATE INDEX index_courier_TimeDelivery ON TimeDelivery(courier_id);
