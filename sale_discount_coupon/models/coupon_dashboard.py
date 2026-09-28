# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta


class CouponDashboard(models.Model):
    _name = 'coupon.dashboard'
    _description = 'Coupon Dashboard'
    _auto = False  # No database table

    @api.model
    def get_dashboard_data(self):
        """Get all data for dashboard"""
        today = date.today()
        month_start = today.replace(day=1)

        # Total coupons
        total_coupons = self.env['sale.coupon'].search_count([])
        active_coupons = self.env['sale.coupon'].search_count([('state', '=', 'active')])
        expired_coupons = self.env['sale.coupon'].search_count([('state', '=', 'expired')])
        exhausted_coupons = self.env['sale.coupon'].search_count([('state', '=', 'exhausted')])

        # Orders with coupons
        orders_with_coupon = self.env['sale.order'].search_count([
            ('coupon_applied', '=', True)
        ])
        orders_this_month = self.env['sale.order'].search_count([
            ('coupon_applied', '=', True),
            ('date_order', '>=', month_start.strftime('%Y-%m-%d'))
        ])

        # Total discount given
        orders = self.env['sale.order'].search([('coupon_applied', '=', True)])
        total_discount = sum(orders.mapped('coupon_discount_amount'))
        month_discount = sum(
            self.env['sale.order'].search([
                ('coupon_applied', '=', True),
                ('date_order', '>=', month_start.strftime('%Y-%m-%d'))
            ]).mapped('coupon_discount_amount')
        )

        # Top coupons
        top_coupons = self.env['sale.coupon'].search([], order='used_count desc', limit=5)
        top_coupons_data = [{
            'name': c.name,
            'code': c.code,
            'used_count': c.used_count,
            'total_discount': c.total_discount_given,
            'state': c.state,
        } for c in top_coupons]

        # Discount rules count
        total_rules = self.env['sale.discount.rule'].search_count([('active', '=', True)])

        # Monthly usage chart data (last 6 months)
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=i * 30)
            month_s = month_date.replace(day=1)
            if month_date.month == 12:
                month_e = month_date.replace(day=31)
            else:
                month_e = (month_date.replace(month=month_date.month + 1, day=1) -
                           timedelta(days=1))
            count = self.env['sale.order'].search_count([
                ('coupon_applied', '=', True),
                ('date_order', '>=', month_s.strftime('%Y-%m-%d')),
                ('date_order', '<=', month_e.strftime('%Y-%m-%d')),
            ])
            monthly_data.append({
                'month': month_s.strftime('%b %Y'),
                'count': count
            })

        return {
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'expired_coupons': expired_coupons,
            'exhausted_coupons': exhausted_coupons,
            'orders_with_coupon': orders_with_coupon,
            'orders_this_month': orders_this_month,
            'total_discount': total_discount,
            'month_discount': month_discount,
            'top_coupons': top_coupons_data,
            'total_rules': total_rules,
            'monthly_data': monthly_data,
            'currency_symbol': self.env.user.company_id.currency_id.symbol,
        }
