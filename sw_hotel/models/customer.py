import random
from odoo import api, fields, models
from datetime import date, datetime, timedelta


class HotelCustomer(models.Model):
    _inherit = "res.partner"
    # _name = "hotel.customer"
    # _description = "hotel visitor/customer"
    # _rec_name = 'full_name'

    date_of_birth = fields.Date(required=True)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    is_minor = fields.Boolean(compute="_compute_age", store=True)

    actual_transaction_id = fields.Many2one(comodel_name="hotel.reservation", readonly=True, store=True)  # TODO compute this field
    reservations_ids = fields.Many2many(comodel_name="hotel.reservation", readonly=True)
    rooms_his_ids = fields.Many2many(comodel_name="hotel.room", readonly=True) 
    transactions_ids = fields.Many2many(comodel_name="hotel.transaction", readonly=True)

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

    def ranomise_date_of_birts(env):
        print(f"[?]{env['base']}                                       [?]")
        for e in env['base']:
            print(e)
        # for partner in env['base']:
        #     print("[??]:", partner.date_of_birth)
        #     print("[???]:", not partner.date_of_birth)
        #     if not partner.date_of_birth:
        #         random_dob = date.today() - timedelta(days=random.randint(365*10, 365*60))  # Random date of birth within a range
        #         partner.write({'date_of_birth': random_dob})
