from odoo import api, fields, models


class HotelRoom(models.Model):
    _name = "hotel.room"
    _description = "hotel room/apartment"
    _rec_name = 'number'

    number = fields.Integer(string="Room number", required=True)
    floor = fields.Integer(string="Floor number", required=True)

    room_class_id = fields.Many2one(comodel_name='hotel.room_class', string="Room's class", required=True)
    room_type_id = fields.Many2one(comodel_name='hotel.room_type', string="Type of room", required=True)

    price = fields.Float(string="Price", compute="_compute_price", store=True)

    customers_capacity = fields.Integer(string="Customer capacity", required=True)
    children_capacity = fields.Integer(string="Children capacity")
    for_children = fields.Boolean(string="Children included", compute="_compute_for_children", store=True)

    status = fields.Selection([
        ('in_preparation', 'In preparation'),
        ('available', 'Available'),
        ('need_preparation', 'Need preparation'),
        ('occupied', 'Occupied')
    ], string="Status", required=True, default="in_preparation")

    active = fields.Boolean(default=True)

    @api.depends('room_class_id', 'room_type_id')
    def _compute_price(self):
        for rec in self:
            price = 0
            if rec.room_class_id and rec.room_type_id:
                for class_id in rec.room_class_id:
                    price += class_id.price
                total_percent = 0
                for type_id in rec.room_type_id:
                    total_percent += type_id.extra_price_percent
                price = price + (price * (total_percent / 100))
                rec.price = price

    @api.depends('children_capacity')
    def _compute_for_children(self):
        for rec in self:
            rec.for_children = rec.children_capacity > 0
