from odoo import api, fields, models
from odoo.exceptions import UserError

class CancelReservationWizard(models.TransientModel):
    _name = "hotel.cancel_reservation.wizard"
    
    reason = fields.Html()

    def confirm_reservation_cancel(self):
        if self.reason == "<p><br></p>":
            raise UserError("You need to provide some reason")

        active_id = self._context.get("active_ids")[0]
        active_model = self.env[self._context.get("active_model")].browse(active_id)
        active_model.cancel_reservation()
        active_model.add_log_note("<h3>Cancelation reason</h3><hr/>"+self.reason)
        return