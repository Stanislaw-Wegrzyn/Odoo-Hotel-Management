from odoo import api, fields, models


class HotelRoomClass(models.Model):
    _name = "hotel.room_class"
    _description = "hotel room class"

    name = fields.Char(string="Name", required=True)
    price = fields.Float(string="Price", required=True)

    active = fields.Boolean(default=True)


class HotelRoomType(models.Model):
    _name = "hotel.room_type"
    _description = "hotel room type"

    name = fields.Char(string="Name", required=True)
    extra_price_percent = fields.Float(string="Extra price percent", required=True)

    active = fields.Boolean(default=True)
