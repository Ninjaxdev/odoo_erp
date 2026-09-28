# -*- coding: utf-8 -*-
{
    'name': 'Smart Sales Discount & Coupon Management',
    'version': '13.0.1.0.0',
    'category': 'Sales',
    'summary': 'Manage discount rules and coupon codes for sales orders',
    'description': """
        Smart Sales Discount & Coupon Management System
        ================================================
        Features:
        - Create discount rules based on customer, product, or order amount
        - Auto-apply coupon codes at sales order level
        - Dashboard showing coupon usage and sales impact
        - Email notifications when coupon is applied
        - Coupon expiry date validation
        - One-time use coupon restriction
        - PDF reports of discounts applied
    """,
    'author': 'EOXS',
    'website': 'https://www.eoxs.com',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'mail',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/coupon_views.xml',
        'views/discount_rule_views.xml',
        'views/sale_order_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        'report/discount_report.xml',
        'report/discount_report_template.xml',
        'data/mail_template_data.xml',
        'data/sequence_data.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
