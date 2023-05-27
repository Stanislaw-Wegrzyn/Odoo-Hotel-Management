import random
import uuid
from odoo import api, fields, models
from odoo.exceptions import UserError


class HotelReservation(models.Model):
    _name = "hotel.reservation"
    _description = "hotel reservation"

    name = fields.Char(string="Name", compute='_compute_name')

    application_datetime = fields.Datetime(string='Application date', default=fields.Datetime.now(), required=True)
    reservation_date_start = fields.Date(string='Reservation start date', required=True)
    reservation_date_end = fields.Date(string='Reservation end date', required=True)

    reservation_price = fields.Float(string="Price", compute="_compute_price")

    persons_number = fields.Integer(string='Number of persons', store=True, compute="_compute_persons_number")
    reservation_host = fields.Many2one(comodel_name='hotel.customer', string="Customer host of reservation", required=True)
    reservation_class_id = fields.Many2one(comodel_name='hotel.room_class', string="Reservation's class",
                                           compute="_compute_reservation_class")
    persons = fields.Many2many(comodel_name='hotel.customer', string="Customers in reservation", required=True)
    children_number = fields.Integer(string="Amount of children", compute="_compute_children_number", store=True)
    children_included = fields.Boolean(string="Children included?", compute='_compute_children_included', store=True)

    rooms_amount = fields.Integer(string='Amount of rooms', compute="_compute_rooms_amount")
    rooms = fields.Many2many(comodel_name='hotel.room', string="Rooms in reservation",
                             domain="[('status', '=', 'available')]")

    preferred_rooms_class = fields.Many2one(comodel_name='hotel.room_class', string="Preferred rooms class",
                                            required=False)

    assigned_transaction = fields.Many2many(comodel_name="hotel.transaction", limit=1, readonly=True, store=True)
    referred_transaction = fields.Many2one(comodel_name="hotel.transaction", compute="_compute_referred_transaction", sore=True)
    payment_status = fields.Selection(
        [('no_transaction', 'No transaction'), ('draft', 'Draft'), ('in_proces', 'In proces'), ('paid', 'Paid')],
        string="Payment status", compute="_compute_payment_status", store=True)

    special_requirements = fields.Html(string="Special requirements for the reservation")

    status = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('in_proces', 'In proces'),
        ('ended', 'Ended'),
        ('suspended', 'Suspended'),
        ('canceled', 'Canceled')
    ], string="Status", required=True, default='draft')

    active = fields.Boolean(default=True)

    def _compute_name(self):
        for rec in self:
            if rec.reservation_date_start and rec.reservation_date_end and rec.reservation_host:
                rec.name = rec.reservation_date_start.strftime("%d/%m/%y") + "-" + rec.reservation_date_end.strftime(
                    "%d/%m/%y") + " " + rec.reservation_host.first_name + " " + rec.reservation_host.last_name

    @api.onchange('reservation_host')
    def onchange_reservation_host(self):
        for rec in self:
            if rec.reservation_host:
                persons_ids = list(rec.persons.ids)

                persons_ids.append(rec.reservation_host.id)

                rec.persons = persons_ids
                rec.reservation_host = rec.reservation_host

    @api.onchange('persons')
    def onchange_persons(self):
        for rec in self:
            deleted = list(set(rec._origin.persons.ids) - set(rec.persons.ids))
            if rec.reservation_host.id in deleted:
                rec.reservation_host = rec.persons[0] if len(rec.persons) else None

    @api.depends('persons')
    def _compute_persons_number(self):
        for rec in self:
            if rec.persons:
                rec.persons_number = len(rec.persons)

    @api.depends('persons')
    def _compute_children_number(self):
        for rec in self:
            if rec.persons:
                rec.children_number = len([x for x in rec.persons if x.minor])

    @api.depends('children_number')
    def _compute_children_included(self):
        for rec in self:
            if rec.children_number and rec.children_number > 0:
                rec.children_included = True
            else:
                rec.children_included = False

    @api.depends('assigned_transaction')
    def _compute_referred_transaction(self):
        for rec in self:
            if len(list(rec.assigned_transaction)) > 0:
                rec.referred_transaction = rec.assigned_transaction[0]
            else:
                rec.referred_transaction = None

    @api.depends('assigned_transaction')
    def _compute_payment_status(self):
        for rec in self:
            if len(list(rec.assigned_transaction)) > 0:
                rec.payment_status = rec.assigned_transaction.status
            else:
                rec.payment_status = "no_transaction"

    @api.depends('rooms')
    def _compute_price(self):
        for rec in self:
            price = 0
            if rec.rooms:
                for room in rec.rooms:
                    price += room.price
            rec.reservation_price = price

    @api.depends('rooms')
    def _compute_reservation_class(self):
        for rec in self:
            if rec.rooms:
                rec.reservation_class_id = sorted([room for room in rec.rooms], key=lambda x: x.room_class_id.price, reverse=True)[0].room_class_id.id
            else:
                rec.reservation_class_id = None

    @api.depends('rooms')
    def _compute_rooms_amount(self):
        for rec in self:
            rec.rooms_amount = len(list(rec.rooms))

    @api.onchange('rooms')
    def onchange_rooms(self):
        for rec in self:
            to_need_preparation = set(rec._origin.rooms.ids) - set(rec.rooms.ids)

            for room in rec._origin.rooms:
                if room.id in to_need_preparation:
                    room.status = 'need_preparation'
            for room in rec.rooms:
                room.status = 'occupied'

    def auto_rooms(self):
        for rec in self:
            req_places = rec.persons_number
            req_children = rec.children_number if not rec.children_number else rec.children_included
            assigned_rooms_ids = []
            for assigned_room in rec.rooms:
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
                rec.rooms = assigned_rooms_ids

    def create_transaction(self):
        for rec in self:
            if not rec.referred_transaction:
                action = rec.env.ref("sw_hotel.action_create_transaction").read()[0]
                action['context'] = {
                    'default_identifier': rec.create_transaction_identifier(),
                    'default_application_datetime': rec.application_datetime,
                    'default_proceeded_datetime': fields.Datetime.now(),
                    'default_reservation': rec.id,
                    'default_price': rec.reservation_price
                }
                return action
            else:
                raise UserError("There is already a transaction assigned to this reservation!")

    def create_transaction_identifier(self):
        for rec in self:
            identifier = "ID"

            for _ in range(10):
                if random.randrange(0, 2):
                    identifier += str(random.randrange(0, 9))
                else:
                    identifier += chr(random.randrange(65, 91))
            identifier += str(len(rec.env['hotel.transaction'].search([])))

            return identifier

    def cancel_reservation(self):
        for rec in self:
            if rec.payment_status in ['in_process', 'paid']:
                raise UserError("You can't cancel a reservation while the transaction is paid or in progress.")
            rec.status = "canceled"
            for room in rec.rooms:
                room.status = "available"
            if rec.referred_transaction:
                rec.referred_transaction.status = 'canceled'

