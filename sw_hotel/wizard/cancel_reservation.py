from odoo import api, fields, models

class CancelReservationWizard(models.TransientModel):
    _name = "hotel.cancel_reservation.wizard"

    
    
    reason = fields.Html()

    def confirm_reservation_cancel(self):
        return