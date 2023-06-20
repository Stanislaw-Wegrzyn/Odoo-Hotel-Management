from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.tests.common import TransactionCase, Form


class ReservationTest(TransactionCase):
    def setUp(self):
        super(ReservationTest, self).setUp()

        self.customer_adult_1 = self.env['res.partner'].create(
            {"name": "Adult1 Customer", "date_of_birth": datetime.today() - relativedelta(years=25)}
        )

        self.customer_adult_2 = self.env['res.partner'].create(
            {"name": "Adult2 Customer", "date_of_birth": datetime.today() - relativedelta(years=30)}
        )

        self.customer_minor_1 = self.env['res.partner'].create(
            {"name": "Minor1 Customer", "date_of_birth": datetime.today() - relativedelta(years=10)}
        )

    def test_reservation_host_id_in_persons_ids(self):
        self.reservation_form_1 = Form(self.env["hotel.reservation"])
        
        
        self.reservation_form_1.application_datetime = datetime.now()
        self.reservation_form_1.reservation_date_start = datetime.today()
        self.reservation_form_1.reservation_date_end = datetime.today() + relativedelta(days=5)
        self.reservation_form_1.reservation_host_id = self.customer_adult_1

        self.assertIn(self.reservation_form_1.reservation_host_id, self.reservation_form_1.persons_ids)
        self.assertEqual(len(self.reservation_form_1.persons_ids), 1)

        self.reservation_form_1.reservation_host_id = self.customer_adult_2

        self.assertIn(self.reservation_form_1.reservation_host_id, self.reservation_form_1.persons_ids)
        self.assertEqual(len(self.reservation_form_1.persons_ids), 2)

        self.reservation_form_1.persons_ids.add(self.customer_minor_1)
        self.assertEqual(self.reservation_form_1.reservation_host_id, self.customer_adult_2)
        self.assertIn(self.reservation_form_1.reservation_host_id, self.reservation_form_1.persons_ids)
        self.assertEqual(len(self.reservation_form_1.persons_ids), 3)
        
    def test_payment_status_reservation(self):
        self.reservation_test_1 = self.env['hotel.reservation'].create(
            {
                "application_datetime": datetime.now(),
                "reservation_date_start": datetime.today(),
                "reservation_date_end": datetime.today() + relativedelta(days=5),
                "reservation_host_id": self.customer_adult_1.id
            }
        )

        self.assertEqual(self.reservation_test_1.payment_status, 'no_transaction')

        self.transaction_test_1_1 = self.env['hotel.transaction'].create(
            {
                "application_datetime": datetime.now(),
                "reservation_id": self.reservation_test_1.id,
                "proceeded_datetime": datetime.now(),
                "status": 'draft',
            }
        )

        self.assertEqual(self.reservation_test_1.payment_status, 'draft')

        self.transaction_test_1_1.write({"status": "in_proces"})
        self.assertEqual(self.reservation_test_1.payment_status, 'in_proces')

        self.transaction_test_1_1.write({"status": "paid"})
        self.assertEqual(self.reservation_test_1.payment_status, 'paid')

        self.transaction_test_1_1.write({"active": False})
        self.assertEqual(self.reservation_test_1.payment_status, 'paid')

    def test_archive_customer(self):
        self.reservation_test_1 = self.env['hotel.reservation'].create(
            {
                "application_datetime": datetime.now(),
                "reservation_date_start": datetime.today(),
                "reservation_date_end": datetime.today() + relativedelta(days=5),
                "reservation_host_id": self.customer_adult_1.id
            }
        )
        
        self.customer_adult_1.write({"active": False})
        self.assertEqual(self.customer_adult_1, self.reservation_test_1.reservation_host_id)
        self.assertIn(self.customer_adult_1, self.reservation_test_1.with_context(active_test=False).persons_ids)
