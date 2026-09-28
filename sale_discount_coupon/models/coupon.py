# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import random
import string


class SaleCoupon(models.Model):
    _name = 'sale.coupon'
    _description = 'Sales Coupon'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Coupon Name',
        required=True,
        track_visibility='onchange'
    )
    code = fields.Char(
        string='Coupon Code',
        required=True,
        copy=False,
        track_visibility='onchange'
    )
    discount_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], string='Discount Type', required=True, default='percentage', track_visibility='onchange')

    discount_value = fields.Float(
        string='Discount Value',
        required=True,
        track_visibility='onchange'
    )
    min_order_amount = fields.Float(
        string='Minimum Order Amount',
        default=0.0,
        track_visibility='onchange'
    )
    max_discount_amount = fields.Float(
        string='Maximum Discount Amount',
        default=0.0,
        help='Maximum discount cap for percentage discounts. 0 means no cap.'
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        track_visibility='onchange'
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        required=True,
        track_visibility='onchange'
    )
    is_one_time_use = fields.Boolean(
        string='One Time Use',
        default=False,
        track_visibility='onchange'
    )
    usage_limit = fields.Integer(
        string='Usage Limit',
        default=0,
        help='0 means unlimited usage'
    )
    used_count = fields.Integer(
        string='Used Count',
        default=0,
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('exhausted', 'Exhausted'),
    ], string='Status', default='draft', track_visibility='onchange')

    applicable_customer_ids = fields.Many2many(
        'res.partner',
        string='Applicable Customers',
        help='Leave empty to apply for all customers'
    )
    applicable_product_ids = fields.Many2many(
        'product.product',
        string='Applicable Products',
        help='Leave empty to apply for all products'
    )
    discount_rule_id = fields.Many2one(
        'sale.discount.rule',
        string='Linked Discount Rule'
    )
    sale_order_ids = fields.One2many(
        'sale.order',
        'coupon_id',
        string='Sales Orders'
    )
    total_orders = fields.Integer(
        string='Total Orders',
        compute='_compute_total_orders',
        store=True
    )
    total_discount_given = fields.Float(
        string='Total Discount Given',
        compute='_compute_total_discount_given',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.user.company_id.currency_id
    )
    description = fields.Text(string='Description')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id
    )

    @api.depends('sale_order_ids')
    def _compute_total_orders(self):
        for rec in self:
            rec.total_orders = len(rec.sale_order_ids)

    @api.depends('sale_order_ids.coupon_discount_amount')
    def _compute_total_discount_given(self):
        for rec in self:
            rec.total_discount_given = sum(
                rec.sale_order_ids.mapped('coupon_discount_amount')
            )

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for rec in self:
            if rec.discount_value <= 0:
                raise ValidationError(_('Discount value must be greater than 0.'))
            if rec.discount_type == 'percentage' and rec.discount_value > 100:
                raise ValidationError(_('Percentage discount cannot exceed 100%.'))

    @api.constrains('expiry_date', 'start_date')
    def _check_dates(self):
        for rec in self:
            if rec.expiry_date < rec.start_date:
                raise ValidationError(_('Expiry date must be after start date.'))

    @api.constrains('code')
    def _check_unique_code(self):
        for rec in self:
            existing = self.search([
                ('code', '=', rec.code),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError(_('Coupon code must be unique! "%s" already exists.') % rec.code)

    def action_activate(self):
        for rec in self:
            if rec.expiry_date < date.today():
                raise ValidationError(_('Cannot activate an expired coupon.'))
            rec.state = 'active'

    def action_expire(self):
        for rec in self:
            rec.state = 'expired'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def is_valid(self, partner_id=None, order_amount=0.0):
        """Check if coupon is valid for given partner and order amount"""
        self.ensure_one()
        today = date.today()

        # Check state
        if self.state != 'active':
            return False, _('Coupon is not active.')

        # Check date validity
        if today < self.start_date:
            return False, _('Coupon is not yet valid.')
        if today > self.expiry_date:
            return False, _('Coupon has expired.')

        # Check usage limit
        if self.is_one_time_use and self.used_count >= 1:
            return False, _('This coupon has already been used.')
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False, _('Coupon usage limit has been reached.')

        # Check minimum order amount
        if order_amount < self.min_order_amount:
            return False, _('Order amount must be at least %s to use this coupon.') % self.min_order_amount

        # Check applicable customers
        if self.applicable_customer_ids and partner_id:
            if partner_id not in self.applicable_customer_ids.ids:
                return False, _('This coupon is not applicable for this customer.')

        return True, _('Coupon is valid.')

    def compute_discount_amount(self, order_amount):
        """Compute discount amount for a given order amount"""
        self.ensure_one()
        if self.discount_type == 'fixed':
            return min(self.discount_value, order_amount)
        elif self.discount_type == 'percentage':
            discount = (self.discount_value / 100.0) * order_amount
            if self.max_discount_amount > 0:
                discount = min(discount, self.max_discount_amount)
            return discount
        return 0.0

    @api.model
    def generate_coupon_code(self, length=10):
        """Generate a random unique coupon code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not self.search([('code', '=', code)]):
                return code

    def action_generate_code(self):
        """Generate a new coupon code"""
        for rec in self:
            rec.code = self.generate_coupon_code()

    def update_usage(self):
        """Increment usage count and update state if needed"""
        self.ensure_one()
        self.used_count += 1
        if self.is_one_time_use and self.used_count >= 1:
            self.state = 'exhausted'
        elif self.usage_limit > 0 and self.used_count >= self.usage_limit:
            self.state = 'exhausted'

    @api.model
    def _cron_check_expiry(self):
        """Cron job to auto-expire coupons"""
        today = date.today()
        expired_coupons = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', today)
        ])
        expired_coupons.write({'state': 'expired'})
