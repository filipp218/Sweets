
CourierItem = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "courier_id": {"type": "integer"},
            "courier_type":{
                "type": "string",
                "enum":["foot", "bike" , "car"]},
            "regions": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "integer", "exclusiveMinimum": 0}},
            "working_hours":{
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern":"^[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$"}}
            },
        "required": ["courier_id", "courier_type", "regions", "working_hours"],
}

OrdersAssignPostRequest = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "courier_id": {"type": "integer"}
        },
    "required": ["courier_id"]
}

OrderItem = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "order_id": {"type" : "integer"},
        "weight": {"type" : "number", "exclusiveMinimum": 0.01, "exclusiveMaximum": 50},
        "region": {"type" : "integer", "exclusiveMinimum": 0},
        "delivery_hours":{
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern":"^[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$"}}
        },
        "required": ["order_id", "weight", "region", "delivery_hours"],
}

CourierUpdateRequest = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "courier_type":{
                "type": "string",
                "enum":["foot", "bike" , "car"]},
            "regions": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "integer", "exclusiveMinimum": 0}},
            "working_hours":{
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern":"^[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$"}}
            },
}

OrdersCompletePostRequest = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "courier_id": {"type": "integer"},
            "order_id": {"type": "integer"},
            "complete_time": {"type": "string"},
            },
        "required": ["courier_id", "order_id", "complete_time"]
}
