{
    'name': 'Hotel Managment',
    'version': '1.0.0',
    'category': 'Hotel',
    'summary': 'Hotel Managment',
    'description': """ Hotel Managment System """,
    'depends': ['mail', "base"],
    'data': [
        'security/ir.model.access.csv',
        './views/room_class_view.xml',
        './views/room_type_view.xml',
        './views/customer_view.xml',
        './views/room_view.xml',
        './views/reservation_view.xml',
        './views/transaction_view.xml',
        './views/menu.xml',
    ],
    'demo': ["./data/hotel_demo.xml"],
    'post_init_hook': 'ranomise_date_of_birth',

    'installable': True,
    'application': True,

    'sequence': -100,
}


