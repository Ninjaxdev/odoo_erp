{
    'name': 'Sale Custom',
    'version': '1.0',
    'depends': ['sale'],  # VERY IMPORTANT if we are making changes in exsiting module then in depends we have to mention app name
    'data': [
        'views/sale_order_views.xml',

    ],
    'installable': True,
}