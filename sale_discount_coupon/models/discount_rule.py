# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleDiscountRule(models.Model):
    _name = 'sale.discount.rule'
    _description = 'Sales Discount Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        track_visibility='onchange'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange'
    )
    description = fields.Text(string='Description')

    # Rule Type
    rule_type = fields.Selection([
        ('order_amount', 'Based on Order Amount'),
        ('customer', 'Based on Customer'),
        ('product', 'Based on Product'),
        ('customer_category', 'Based on Customer Category'),
    ], string='Rule Type', required=True, default='order_amount', track_visibility='onchange')

    # Discount Settings
    discount_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], string='Discount Type', required=True, default='percentage', track_visibility='onchange')

    discount_value = fields.Float(
        string='Discount Value',
        required=True,
        track_visibility='onchange'
    )
    max_discount_amount = fields.Float(
        string='Maximum Discount Cap',
        default=0.0,
        help='0 means no cap on discount amount'
    )

    # Order Amount Conditions
    min_order_amount = fields.Float(
        string='Minimum Order Amount',
        default=0.0
    )
    max_order_amount = fields.Float(
        string='Maximum Order Amount',
        default=0.0,
        help='0 means no upper limit'
    )

    # Customer Conditions
    applicable_customer_ids = fields.Many2many(
        'res.partner',
        'discount_rule_partner_rel',
        'rule_id',
        'partner_id',
        string='Applicable Customers'
    )
    applicable_customer_category_ids = fields.Many2many(
        'res.partner.category',
        string='Customer Categories'
    )

    # Product Conditions
    applicable_product_ids = fields.Many2many(
        'product.product',
        'discount_rule_product_rel',
        'rule_id',
        'product_id',
        string='Applicable Products'
    )
    applicable_product_category_ids = fields.Many2many(
        'product.category',
        string='Product Categories'
    )

    # Date Conditions
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today
    )
    end_date = fields.Date(string='End Date')

    # Linked Coupons
    coupon_ids = fields.One2many(
        'sale.coupon',
        'discount_rule_id',
        string='Generated Coupons'
    )
    coupon_count = fields.Integer(
        string='Coupon Count',
        compute='_compute_coupon_count'
    )

    # Priority
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
    ], string='Priority', default='1')

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.user.company_id.currency_id
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id
    )

    @api.depends('coupon_ids')
    def _compute_coupon_count(self):
        for rec in self:
            rec.coupon_count = len(rec.coupon_ids)

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for rec in self:
            if rec.discount_value <= 0:
                raise ValidationError(_('Discount value must be greater than 0.'))
            if rec.discount_type == 'percentage' and rec.discount_value > 100:
                raise ValidationError(_('Percentage discount cannot exceed 100%.'))

    @api.constrains('end_date', 'start_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End date must be after start date.'))

    def is_applicable(self, order):
        """Check if this rule is applicable to given sale order"""
        self.ensure_one()
        from datetime import date
        today = date.today()

        # Check dates
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False

        partner = order.partner_id
        order_amount = order.amount_untaxed

        if self.rule_type == 'order_amount':
            if order_amount < self.min_order_amount:
                return False
            if self.max_order_amount > 0 and order_amount > self.max_order_amount:
                return False

        elif self.rule_type == 'customer':
            if self.applicable_customer_ids:
                if partner not in self.applicable_customer_ids:
                    return False

        elif self.rule_type == 'customer_category':
            if self.applicable_customer_category_ids:
                partner_categories = partner.category_id
                if not (partner_categories & self.applicable_customer_category_ids):
                    return False

        elif self.rule_type == 'product':
            if self.applicable_product_ids:
                order_products = order.order_line.mapped('product_id')
                if not (order_products & self.applicable_product_ids):
                    return False

        return True

    def compute_discount(self, order_amount):
        """Compute discount amount based on rule"""
        self.ensure_one()
        if self.discount_type == 'fixed':
            return min(self.discount_value, order_amount)
        elif self.discount_type == 'percentage':
            discount = (self.discount_value / 100.0) * order_amount
            if self.max_discount_amount > 0:
                discount = min(discount, self.max_discount_amount)
            return discount
        return 0.0

    def action_generate_coupon(self):
        """Generate a coupon from this rule"""
        self.ensure_one()
        coupon_model = self.env['sale.coupon']
        coupon = coupon_model.create({
            'name': _('Coupon for %s') % self.name,
            'code': coupon_model.generate_coupon_code(),
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'max_discount_amount': self.max_discount_amount,
            'min_order_amount': self.min_order_amount,
            'start_date': self.start_date or fields.Date.today(),
            'expiry_date': self.end_date or fields.Date.today(),
            'discount_rule_id': self.id,
            'state': 'active',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Coupon'),
            'res_model': 'sale.coupon',
            'res_id': coupon.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_coupons(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Coupons'),
            'res_model': 'sale.coupon',
            'view_mode': 'tree,form',
            'domain': [('discount_rule_id', '=', self.id)],
            'context': {'default_discount_rule_id': self.id},
        }
