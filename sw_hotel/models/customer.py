from odoo import api, fields, models
from datetime import datetime


class HotelCustomer(models.Model):
    _name = "hotel.customer"
    _description = "hotel visitor/customer"
    _rec_name = 'full_name'

    full_name = fields.Char(string="Full name", compute='_compute_fullname')

    first_name = fields.Char(string="First name", required=True)
    last_name = fields.Char(string="Last name", required=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    date_of_birth = fields.Date(string="Date of birth", required=True)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    minor = fields.Boolean(string="Is minor?", compute="_compute_age", store=True)

    active = fields.Boolean(default=True)

    def _compute_fullname(self):
        for rec in self:
            if rec.first_name and rec.last_name:
                rec.full_name = rec.first_name + " " + rec.last_name

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                current_date = datetime.now().date()
                rec.age = current_date.year - rec.date_of_birth.year
                rec.minor = rec.age < 18
            else:
                rec.age = None
