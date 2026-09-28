# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockScrap(models.Model):
    """Extend stock.scrap to link back to yield tracking and loss types."""

    _inherit = 'stock.scrap'

    yield_tracking_id = fields.Many2one(
        'yield.tracking',
        string='Yield Tracking',
        readonly=True,
        help='The yield tracking record that generated this scrap order.',
    )
    loss_type_id = fields.Many2one(
        'yield.loss.type',
        string='Loss Type',
        help='Type of loss that caused this scrap.',
    )
    is_auto_generated = fields.Boolean(
        string='Auto-Generated',
        default=False,
        readonly=True,
        help='Indicates this scrap order was auto-generated from yield tracking.',
    )
    material_grade = fields.Char(
        string='Material Grade',
        related='yield_tracking_id.material_grade',
        store=True,
        readonly=True,
    )
    loss_cost = fields.Float(
        string='Loss Cost',
        compute='_compute_loss_cost',
        store=True,
        digits='Product Price',
    )

    @api.depends('scrap_qty', 'product_id', 'product_id.standard_price')
    def _compute_loss_cost(self):
        for rec in self:
            rec.loss_cost = rec.scrap_qty * rec.product_id.standard_price
