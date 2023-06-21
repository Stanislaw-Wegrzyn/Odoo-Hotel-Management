from datetime import datetime, date
from odoo import api, fields, models
from odoo.exceptions import UserError


class HotelReservation(models.Model):
    _name = "hotel.reservation"
    _description = "hotel reservation"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", compute='_compute_name')

    application_datetime = fields.Datetime(default=fields.Datetime.now(), required=True)
    reservation_date_start = fields.Date(required=True, tracking=True)
    reservation_date_end = fields.Date(required=True, tracking=True)

    calendar_date_start = fields.Datetime(default=lambda self: fields.Datetime.now())

    reservation_price = fields.Float(string="Price", compute="_compute_rooms_ids")

    persons_number = fields.Integer(store=True, compute="_compute_persons_number")
    reservation_host_id = fields.Many2one(comodel_name='res.partner', domain="[('date_of_birth', '!=', None)]", required=True, tracking=True)
    persons_ids = fields.Many2many(comodel_name='res.partner', domain="[('date_of_birth', '!=', None)]", string="Customers in reservation", required=True)
    children_number = fields.Integer(string="Amount of children", compute="_compute_persons_number", store=True)
    children_included = fields.Boolean(compute='_compute_persons_number', store=True)
    reservation_class_id = fields.Many2one(comodel_name='hotel.room_class', string="Reservation's class", compute="_compute_rooms_ids")

    rooms_amount = fields.Integer(compute="_compute_rooms_ids")
    rooms_ids = fields.Many2many(comodel_name='hotel.room', string="Rooms in reservation",
                             domain="[('status', '=', 'available')]", required=True, tracking=True)

    preferred_rooms_class = fields.Many2one(comodel_name='hotel.room_class', required=False)

    transaction_id = fields.Many2many(comodel_name="hotel.transaction", readonly=True, store=True)
    referred_transaction = fields.Many2one(comodel_name="hotel.transaction", compute="_compute_referred_transaction", sore=True, tracking=True)
    payment_status = fields.Selection(
        [('no_transaction', 'No transaction'), ('draft', 'Draft'), ('in_proces', 'In proces'), ('paid', 'Paid'), ('canceled', 'Canceled')],
        string="Payment status", compute="_compute_referred_transaction", store=True, tracking=True)

    special_requirements = fields.Html()

    status = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('in_proces', 'In proces'),
        ('ended', 'Ended'),
        ('canceled', 'Canceled')
    ], required=True, default='draft', compute="_compute_status", tracking=True, store=True)

    customers_count = fields.Integer(compute="_compute_customers_count")
    rooms_count = fields.Integer(compute="_compute_rooms_count")

    active = fields.Boolean(default=True)

    def _compute_name(self):
        for rec in self:
            if rec.reservation_date_start and rec.reservation_date_end and rec.reservation_host_id:
                rec.name = rec.reservation_date_start.strftime("%d/%m/%y") + "-" + rec.reservation_date_end.strftime(
                    "%d/%m/%y") + " " + rec.reservation_host_id.name
                
    def print_button_action(self):
        # Add your logic here to perform the desired action
        # For example, you can generate a report or open a print dialog
        # You can use the `self` variable to access the current record(s)
        # or use `self.env` to access the Odoo environment
        
        # Example: Open a print dialog
        return {
            'type': 'ir.actions.report',
            'report_name': 'sw_hotel.report_template',
            'report_type': 'qweb-pdf',
            'report_action': self.env.ref('sw_hotel.report_template').id,
        }
                
    @api.model
    def create(self, vals):
        if 'persons_ids' in vals.keys():
            if vals['reservation_host_id'] not in vals['persons_ids']:
                vals['persons_ids'].append(vals['reservation_host_id'])
        else:
            vals.update({'persons_ids': [(4, vals['reservation_host_id'])]})

        if 'rooms_ids' in vals.keys():
            for room in self.rooms_ids:
                room.status = 'occupied'

        record = super(HotelReservation, self).create(vals)
        return record
    
    def write(self, vals):
        super().write(vals)
        if 'rooms_ids' in vals.keys():
            for room in self.rooms_ids:
                room.status = 'occupied'

    @api.onchange('reservation_host_id')
    def onchange_reservation_host_id(self):
        for rec in self:
            if rec.reservation_host_id not in rec.persons_ids and rec.reservation_host_id:
                rec.persons_ids = [(4, rec.reservation_host_id.id, 0)]

    @api.onchange('persons_ids')
    def onchange_persons(self):
        for rec in self:
            if rec.reservation_host_id.id not in rec.persons_ids.ids:
                rec.reservation_host_id = None

    @api.depends('persons_ids')
    def _compute_persons_number(self):
        for rec in self:
            if rec.persons_ids:
                rec.persons_number = len(rec.persons_ids)
                rec.children_number = len([x for x in rec.persons_ids if x.is_minor])
                rec.children_included = rec.children_number > 0

    @api.depends('transaction_id')
    def _compute_referred_transaction(self):
        for rec in self:
            if len(list(rec.transaction_id)) > 0:
                rec.referred_transaction = rec.transaction_id[0]
                rec.payment_status = rec.transaction_id.status
            else:
                rec.referred_transaction = None
                rec.payment_status = "no_transaction"

    @api.depends('rooms_ids')
    def _compute_rooms_ids(self):
        for rec in self:
            rec.rooms_amount = len(list(rec.rooms_ids))
            rec.reservation_price = sum(room.price for room in rec.rooms_ids)
            if rec.rooms_ids:
                rec.reservation_class_id = sorted([room for room in rec.rooms_ids], key=lambda x: x.room_class_id.price, reverse=True)[0].room_class_id.id
            else:
                rec.reservation_class_id = None

    def auto_rooms(self):
        for rec in self:
            req_places = rec.persons_number
            req_children = rec.children_number if not rec.children_number else rec.children_included
            assigned_rooms_ids = []
            for assigned_room in rec.rooms_ids:
                assigned_rooms_ids.append(assigned_room.id)

            rooms_adults = list(
                rec.env['hotel.room'].search([('status', '=', 'available'), ('for_children', '=', False)]))
            rooms_children = False

            if req_children:
                rooms_children = list(
                    rec.env['hotel.room'].search([('status', '=', 'available'), ('for_children', '=', True)]))
            else:
                rooms_adults.sort(key=lambda x: x.customers_capacity, reverse=True)
                rooms_children.sort(key=lambda x: x.children_capacity, reverse=True) if req_children else None

            if req_children:
                for room in rooms_children:
                    if req_children <= 0:
                        break
                    if room.room_class_id == rec.preferred_rooms_class:
                        if room.children_capacity <= req_children:
                            room.status = 'occupied'
                            assigned_rooms_ids.append(room.id)
                            req_children -= room.children_capacity
                            req_places -= room.customers_capacity

            for room in rooms_adults:
                if req_places <= 0:
                    break
                if room.room_class_id == rec.preferred_rooms_class:
                    if room.customers_capacity <= req_places:
                        room.status = 'occupied'
                        assigned_rooms_ids.append(room.id)
                        req_places -= room.customers_capacity

            if req_children > 0 or req_places > 0:
                error_message = "Automatic rooms assign error!\n" \
                                "There are no available rooms that meet the requirements.\n" \
                                "Assign rooms manually or cancel the order."
                raise UserError(error_message)
            else:
                rec.rooms_ids = assigned_rooms_ids

    def create_transaction(self):
        for rec in self:
            if not rec.referred_transaction:
                action = rec.env.ref("sw_hotel.action_create_transaction").read()[0]
                action['context'] = {
                    'default_application_datetime': rec.application_datetime,
                    'default_proceeded_datetime': fields.Datetime.now(),
                    'default_reservation': rec.id
                }
                return action
            else:
                raise UserError("There is already a transaction assigned to this reservation!")

    def cancel_reservation(self):
        for rec in self:
            if rec.payment_status in ['in_process', 'paid']:
                raise UserError("You can't cancel a reservation while the transaction is paid or in progress.")
            rec.status = 'canceled'

            for room in rec.rooms_ids:
                room.status = "available"
            if rec.referred_transaction:
                rec.referred_transaction.status = 'canceled'

    def proceed_reservation(self):
        for rec in self:
            if rec.status in ['draft', 'canceled']:
                rec.status = 'ready'
                rec._compute_status()
            else:
                raise UserError("Reservation is already in process.")

    def _compute_customers_count(self):
        for rec in self:
            rec.customers_count = len(rec.persons_ids.ids)

    def _compute_rooms_count(self):
        for rec in self:
            rec.rooms_count = len(rec.rooms_ids.ids)

    def action_view_reservation_customers(self):
        action = self.env.ref('sw_hotel.action_hotel_customer').read()[0]
        action['domain'] = [('id', 'in', self.persons_ids.ids)]
        return action

    def action_view_reservation_rooms(self):
        action = self.env.ref('sw_hotel.action_hotel_room').read()[0]
        action['domain'] = [('id', 'in', self.rooms_ids.ids)]
        action['context'] = {'search_default_by_status': True}

        return action
    
    @api.depends('reservation_date_start', 'reservation_date_end')
    def _compute_status(self):
        for rec in self:
            if rec.reservation_date_start and rec.reservation_date_end:
                if rec.status not in ('draft', 'canceled'):
                    if rec.reservation_date_start > fields.Date.today():
                        rec.status = "ready"
                    elif rec.reservation_date_end < fields.Date.today():
                        rec.status = "ended"
                    elif rec.reservation_date_start <= fields.Date.today():
                        rec.status = "in_proces"
            

    def scheduled_change_status(self):
        self._compute_status()    
