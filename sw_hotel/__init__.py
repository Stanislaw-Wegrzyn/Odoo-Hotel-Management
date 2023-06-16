from datetime import date, datetime, timedelta
import random
from . import models
from odoo import api, SUPERUSER_ID

def ranomise_date_of_birth(cr, registry):
    models.customer.HotelCustomer.ranomise_date_of_birts(api.Environment(cr, SUPERUSER_ID, {}))
