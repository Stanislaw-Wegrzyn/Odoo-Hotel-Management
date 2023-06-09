import random
from odoo import api, fields, models


class HotelTransaction(models.Model):
    _name = "hotel.transaction"
    _description = "hotel transaction/payment"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_name")

    identifier = fields.Char(string="ID", tracking=True)
    application_datetime = fields.Datetime(required=True, tracking=True)
    reservation_id = fields.Many2one(comodel_name='hotel.reservation', tracking=True)
    price = fields.Float(tracking=True)
    proceeded_datetime = fields.Datetime(string="Proceeded on", required=True, tracking=True)

    status = fields.Selection([('draft', 'Draft'), ('in_proces', 'In proces'), ('paid', 'Proceed'), ('canceled', 'Canceled')], string="Status", default='draft', required=True, tracking=True)

    active = fields.Boolean(default=True)

    def _compute_name(self):
        for rec in self:
            if rec.identifier:
                rec.name = rec.identifier
            else:
                rec.name = 'Unknown'

    def unlink(self):
        super(HotelTransaction, self).unlink()
        referred_reservations = self.env['hotel.reservation'].search([])
        for reservation_id in referred_reservations:
            if not reservation_id.referred_transaction:
                reservation_id.payment_status = "no_transaction"

    @api.model
    def create(self, vals):
        record = super(HotelTransaction, self).create(vals)
        referred_reservation = record.env['hotel.reservation'].search([('id', '=', record.reservation_id.id)])
        
        record.identifier = self.create_transaction_identifier()
        referred_reservation.payment_status = record.status
        referred_reservation.transaction_id = [(6, 0, [record.id])]

        record.price = referred_reservation.reservation_price

        return record

    @api.onchange('status')
    def onchange_status(self):
        for rec in self:
            referred_reservation = rec.env['hotel.reservation'].search([('id', '=', rec.reservation_id.id)])
            referred_reservation.payment_status = rec.status

    def write(self, values):
        super().write(values)
        self.onchange_status()

    def create_transaction_identifier(self):
        identifier = "ID"
        for _ in range(10):
            if random.randrange(0, 2):
                identifier += str(random.randrange(0, 9))
            else:
                identifier += chr(random.randrange(65, 91))
        identifier += str(len(self.env['hotel.transaction'].search([])))

        return identifier
