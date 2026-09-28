{
    'name':"Company Asset",
    'author': "Rohit",
    'category' : "Custom",
    'summary': "Oddo Custom Module",
    'description' : "custom odoo module ..",
    'version': '13.0.0',
    'depends' : ['base'],
    'data' : [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/Asset_data.xml',
    ],
    'installable' : True

}