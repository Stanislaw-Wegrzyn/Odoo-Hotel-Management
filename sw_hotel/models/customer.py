import random
from odoo import api, fields, models
from datetime import date, datetime, timedelta


class HotelCustomer(models.Model):
    _inherit = "res.partner"
    # _name = "hotel.customer"
    # _description = "hotel visitor/customer"
    # _rec_name = 'full_name'

    date_of_birth = fields.Date()
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    is_minor = fields.Boolean(compute="_compute_age", store=True)

    actual_transaction_id = fields.Many2one(comodel_name="hotel.reservation", readonly=True, store=True)
    reservations_ids = fields.Many2many(comodel_name="hotel.reservation", readonly=True)
    rooms_his_ids = fields.Many2many(comodel_name="hotel.room", readonly=True) 
    transactions_ids = fields.Many2many(comodel_name="hotel.transaction", readonly=True)
    
    reservations_count = fields.Integer(compute="_compute_reservations_count")
    rooms_count = fields.Integer(compute="_compute_rooms_count")
    transactions_count = fields.Integer(compute="_compute_transactions_count")

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                current_date = fields.Date.today()
                rec.age = current_date.year - rec.date_of_birth.year
                rec.is_minor = rec.age < 18
            else:
                rec.age = False
                rec.is_minor = False

    def _compute_reservations_count(self):
        for rec in self:
            rec.reservations_count = len(rec.env['hotel.reservation'].search([('persons_ids', 'in', rec.ids)]))
    
    def _compute_rooms_count(self):
        for rec in self:
            rec.rooms_count = sum(len(reservation.rooms_ids) for reservation in rec.env['hotel.reservation'].search([('persons_ids', 'in', rec.ids)]))

    def _compute_transactions_count(self):
        for rec in self:
            rec.transactions_count = sum(int(reservation.payment_status != 'no_transaction') for reservation in rec.env['hotel.reservation'].search([('persons_ids', 'in', rec.ids)]))

    def action_view_customers_reservations(self):
        action = self.env.ref('sw_hotel.action_hotel_reservation').read()[0]
        action['domain'] = [('persons_ids', 'in', self.ids)]
        action['context'] = {'search_default_by_status': True}
        return action

    def action_view_customers_rooms(self):
        action = self.env.ref('sw_hotel.action_hotel_room').read()[0]

        customer_rooms_ids = []
        for reservation in self.env['hotel.reservation'].search([('persons_ids', 'in', self.ids)]):
            customer_rooms_ids += reservation.rooms_ids.ids

        action['domain'] = [('id', 'in', customer_rooms_ids)]

        return action
    
    def action_view_customers_transactions(self):
        action = self.env.ref('sw_hotel.action_hotel_transaction').read()[0]

        action['domain'] = [('id', 'in', [reservation.transaction_id.id for reservation in self.env['hotel.reservation'].search([('persons_ids', 'in', self.ids)])])]
        action['context'] = {'search_default_by_status': True}

        return action

    def scheduled_change_age(self):
        self._compute_age()
