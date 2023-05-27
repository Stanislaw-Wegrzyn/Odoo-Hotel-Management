from odoo import api, fields, models


class HotelTransaction(models.Model):
    _name = "hotel.transaction"
    _description = "hotel transaction/payment"

    name = fields.Char(compute="_compute_name")

    identifier = fields.Char(string="ID", required=True)
    application_datetime = fields.Datetime(string="Application date and time", required=True)
    reservation = fields.Many2one(comodel_name='hotel.reservation', string="Reservation paying of")
    price = fields.Float(string="Price", required=True)
    proceeded_datetime = fields.Datetime(string="Proceeded on", required=True)

    status = fields.Selection([('draft', 'Draft'), ('in_proces', 'In proces'), ('paid', 'Proceed'), ('canceled', 'Canceled')], string="Status", default='draft')

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
        for reservation in referred_reservations:
            if not reservation.referred_transaction:
                reservation.payment_status = "no_transaction"

    @api.model
    def create(self, vals):
        record = super(HotelTransaction, self).create(vals)

        referred_reservation = record.env['hotel.reservation'].search([('id', '=', record.reservation.id)])
        referred_reservation.payment_status = record.status
        referred_reservation.assigned_transaction = [(6, 0, [record.id])]

        return record

    @api.onchange('status')
    def onchange_status(self):
        for rec in self:
            referred_reservation = rec.env['hotel.reservation'].search([('id', '=', rec.reservation.id)])
            referred_reservation.payment_status = rec.status
