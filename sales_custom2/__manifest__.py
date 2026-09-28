{
    'name': 'Sale Custom 2',
    'version': '1.0',
    'depends': ['sale'],  # VERY IMPORTANT if we are making changes in exsiting module then in depends we have to mention app name
    'data': [
        'views/saleorder.xml',
        'security/ir.model.access.csv',
        'wizard/sale_confirm_wizard_view.xml',
        'report/customer_report.xml'

    ],
    'installable': True,
}