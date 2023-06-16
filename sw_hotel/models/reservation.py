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

    persons_number = fields.Integer(string='Number of persons_ids', store=True, compute="_compute_persons_number")
    reservation_host_id = fields.Many2one(comodel_name='res.partner', string="Customer host of reservation", required=True)
    reservation_class_id = fields.Many2one(comodel_name='hotel.room_class', string="Reservation's class",
                                           compute="_compute_reservation_class")
    persons_ids = fields.Many2many(comodel_name='res.partner', string="Customers in reservation", required=True)
    children_number = fields.Integer(string="Amount of children", compute="_compute_children_number", store=True)
    children_included = fields.Boolean(string="Children included?", compute='_compute_children_included', store=True)

    rooms_amount = fields.Integer(string='Amount of rooms', compute="_compute_rooms_amount")
    rooms_ids = fields.Many2many(comodel_name='hotel.room', string="Rooms in reservation",
                             domain="[('status', '=', 'available')]", required=True)

    preferred_rooms_class = fields.Many2one(comodel_name='hotel.room_class', string="Preferred rooms class",
                                            required=False)

    assigned_transaction = fields.Many2many(comodel_name="hotel.transaction", limit=1, readonly=True, store=True)
    referred_transaction = fields.Many2one(comodel_name="hotel.transaction", compute="_compute_referred_transaction", sore=True)
    payment_status = fields.Selection(
        [('no_transaction', 'No transaction'), ('draft', 'Draft'), ('in_proces', 'In proces'), ('paid', 'Paid'), ('canceled', 'Canceled')],
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
            if rec.reservation_date_start and rec.reservation_date_end and rec.reservation_host_id:
                rec.name = rec.reservation_date_start.strftime("%d/%m/%y") + "-" + rec.reservation_date_end.strftime(
                    "%d/%m/%y") + " " + rec.reservation_host_id.first_name + " " + rec.reservation_host_id.last_name

    @api.onchange('reservation_host_id')
    def onchange_reservation_host_id(self):
        for rec in self:
            if rec.reservation_host_id:
                persons_ids_list = list(rec.persons_ids.ids)

                persons_ids_list.append(rec.reservation_host_id.id)

                rec.persons_ids = persons_ids_list
                rec.reservation_host_id = rec.reservation_host_id

    @api.onchange('persons_ids')
    def onchange_persons(self):
        for rec in self:
            deleted = list(set(rec._origin.persons_ids.ids) - set(rec.persons_ids.ids))
            if rec.reservation_host_id.id in deleted:
                rec.reservation_host_id = rec.persons_ids[0] if len(rec.persons_ids) else None

    @api.depends('persons_ids')
    def _compute_persons_number(self):
        for rec in self:
            if rec.persons_ids:
                rec.persons_number = len(rec.persons_ids)

    @api.depends('persons_ids')
    def _compute_children_number(self):
        for rec in self:
            if rec.persons_ids:
                rec.children_number = len([x for x in rec.persons_ids if x.minor])

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

    @api.depends('rooms_ids')
    def _compute_price(self):
        for rec in self:
            price = 0
            if rec.rooms_ids:
                for room in rec.rooms_ids:
                    price += room.price
            rec.reservation_price = price

    @api.depends('rooms_ids')
    def _compute_reservation_class(self):
        for rec in self:
            if rec.rooms_ids:
                rec.reservation_class_id = sorted([room for room in rec.rooms_ids], key=lambda x: x.room_class_id.price, reverse=True)[0].room_class_id.id
            else:
                rec.reservation_class_id = None

    @api.depends('rooms_ids')
    def _compute_rooms_amount(self):
        for rec in self:
            rec.rooms_amount = len(list(rec.rooms_ids))

    @api.onchange('rooms_ids')
    def onchange_rooms(self):
        for rec in self:
            to_need_preparation = set(rec._origin.rooms_ids.ids) - set(rec.rooms_ids.ids)

            for room in rec._origin.rooms_ids:
                if room.id in to_need_preparation:
                    room.status = 'need_preparation'
            for room in rec.rooms_ids:
                room.status = 'occupied'

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
            rec.status = "canceled"
            for room in rec.rooms_ids:
                room.status = "available"
            if rec.referred_transaction:
                rec.referred_transaction.status = 'canceled'

