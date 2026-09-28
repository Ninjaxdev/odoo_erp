# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    coupon_code = fields.Char(
        string='Coupon Code',
        copy=False
    )
    coupon_id = fields.Many2one(
        'sale.coupon',
        string='Applied Coupon',
        copy=False,
        readonly=True
    )
    coupon_discount_amount = fields.Float(
        string='Coupon Discount Amount',
        compute='_compute_coupon_discount',
        store=True,
        readonly=True
    )
    discount_rule_id = fields.Many2one(
        'sale.discount.rule',
        string='Applied Discount Rule',
        copy=False,
        readonly=True
    )
    discount_rule_amount = fields.Float(
        string='Rule Discount Amount',
        compute='_compute_rule_discount',
        store=True,
        readonly=True
    )
    total_discount_amount = fields.Float(
        string='Total Discount',
        compute='_compute_total_discount',
        store=True
    )
    coupon_applied = fields.Boolean(
        string='Coupon Applied',
        default=False,
        copy=False
    )
    amount_after_discount = fields.Float(
        string='Amount After Discount',
        compute='_compute_amount_after_discount',
        store=True
    )

    @api.depends('coupon_id', 'amount_untaxed')
    def _compute_coupon_discount(self):
        for order in self:
            if order.coupon_id and order.coupon_applied:
                order.coupon_discount_amount = order.coupon_id.compute_discount_amount(
                    order.amount_untaxed
                )
            else:
                order.coupon_discount_amount = 0.0

    @api.depends('discount_rule_id', 'amount_untaxed')
    def _compute_rule_discount(self):
        for order in self:
            if order.discount_rule_id:
                order.discount_rule_amount = order.discount_rule_id.compute_discount(
                    order.amount_untaxed
                )
            else:
                order.discount_rule_amount = 0.0

    @api.depends('coupon_discount_amount', 'discount_rule_amount')
    def _compute_total_discount(self):
        for order in self:
            order.total_discount_amount = (
                order.coupon_discount_amount + order.discount_rule_amount
            )

    @api.depends('amount_total', 'total_discount_amount')
    def _compute_amount_after_discount(self):
        for order in self:
            order.amount_after_discount = max(
                0.0, order.amount_total - order.total_discount_amount
            )

    def action_apply_coupon(self):
        """Apply coupon code to the sale order"""
        self.ensure_one()
        if not self.coupon_code:
            raise UserError(_('Please enter a coupon code.'))

        # Find the coupon
        coupon = self.env['sale.coupon'].search([
            ('code', '=', self.coupon_code.strip().upper()),
        ], limit=1)

        if not coupon:
            raise UserError(_('Invalid coupon code: "%s"') % self.coupon_code)

        # Validate coupon
        is_valid, message = coupon.is_valid(
            partner_id=self.partner_id.id,
            order_amount=self.amount_untaxed
        )

        if not is_valid:
            raise UserError(message)

        # Check if coupon already applied
        if self.coupon_applied:
            raise UserError(_('A coupon is already applied to this order. Remove it first.'))

        # Apply coupon
        self.write({
            'coupon_id': coupon.id,
            'coupon_applied': True,
        })

        # Auto-apply discount to order lines
        self._apply_discount_to_lines(coupon)

        # Send email notification
        self._send_coupon_email(coupon)

        # Check and apply discount rules
        self._check_and_apply_discount_rules()

        return True

    def action_remove_coupon(self):
        """Remove applied coupon from sale order"""
        self.ensure_one()
        if not self.coupon_applied:
            raise UserError(_('No coupon is applied to this order.'))

        # Remove discount from order lines
        for line in self.order_line:
            if line.is_coupon_discount_line:
                line.unlink()
                break

        self.write({
            'coupon_id': False,
            'coupon_code': '',
            'coupon_applied': False,
        })

        return True

    def _apply_discount_to_lines(self, coupon):
        """Apply discount as a negative line item"""
        self.ensure_one()
        discount_amount = coupon.compute_discount_amount(self.amount_untaxed)

        if discount_amount <= 0:
            return

        # Remove existing coupon discount line if any
        existing_lines = self.order_line.filtered(lambda l: l.is_coupon_discount_line)
        existing_lines.unlink()

        # Create discount line
        discount_product = self.env.ref(
            'sale_discount_coupon.product_discount_coupon',
            raise_if_not_found=False
        )
        if not discount_product:
            discount_product = self.env['product.product'].search([
                ('name', '=', 'Coupon Discount')
            ], limit=1)

        if discount_product:
            self.env['sale.order.line'].create({
                'order_id': self.id,
                'product_id': discount_product.id,
                'name': _('Coupon Discount (%s)') % coupon.code,
                'product_uom_qty': 1,
                'price_unit': -discount_amount,
                'is_coupon_discount_line': True,
            })

    def _send_coupon_email(self, coupon):
        """Send email notification when coupon is applied"""
        self.ensure_one()
        template = self.env.ref(
            'sale_discount_coupon.mail_template_coupon_applied',
            raise_if_not_found=False
        )
        if template and self.partner_id.email:
            template.send_mail(self.id, force_send=True)

    def _check_and_apply_discount_rules(self):
        """Check applicable discount rules and apply the best one"""
        self.ensure_one()
        rules = self.env['sale.discount.rule'].search([
            ('active', '=', True),
        ], order='priority desc, sequence')

        best_rule = None
        best_discount = 0.0

        for rule in rules:
            if rule.is_applicable(self):
                discount = rule.compute_discount(self.amount_untaxed)
                if discount > best_discount:
                    best_discount = discount
                    best_rule = rule

        if best_rule:
            self.discount_rule_id = best_rule.id

    def action_confirm(self):
        """Override confirm to update coupon usage"""
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.coupon_id and order.coupon_applied:
                order.coupon_id.sudo().write({
                    'used_count': order.coupon_id.used_count + 1
                })
                if order.coupon_id.is_one_time_use and order.coupon_id.used_count >= 1:
                    order.coupon_id.sudo().write({'state': 'exhausted'})
                elif order.coupon_id.usage_limit > 0 and order.coupon_id.used_count >= order.coupon_id.usage_limit:
                    order.coupon_id.sudo().write({'state': 'exhausted'})
        return res

    def action_view_discount_report(self):
        """View discount report for this order"""
        self.ensure_one()
        return self.env.ref(
            'sale_discount_coupon.action_sale_discount_report'
        ).report_action(self)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_coupon_discount_line = fields.Boolean(
        string='Is Coupon Discount Line',
        default=False
    )
