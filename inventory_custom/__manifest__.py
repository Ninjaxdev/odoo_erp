{
    'name': 'Inventory Custom',
    'version': '1.0',
    'depends': ['stock'],  # VERY IMPORTANT if we are making changes in exsiting module then in depends we have to mention app name
    'data': [
        'views/inventory_overview_views.xml',

    ],
    'installable': True,
}