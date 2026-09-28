# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    """Extend product.template with material grade and yield-adjusted cost."""

    _inherit = 'product.template'

    material_grade = fields.Char(
        string='Material Grade',
        help='Material grade code (e.g. SS304, SS316, C45, EN8).',
    )
    theoretical_yield_pct = fields.Float(
        string='Theoretical Yield (%)',
        default=100.0,
        help='Overall expected yield percentage for this product/grade.',
    )
    avg_actual_yield_pct = fields.Float(
        string='Avg Actual Yield (%)',
        compute='_compute_yield_adjusted_cost',
        store=True,
    )
    yield_adjusted_cost = fields.Float(
        string='Yield-Adjusted Cost',
        compute='_compute_yield_adjusted_cost',
        store=True,
        digits='Product Price',
        help='Standard cost adjusted for historical yield loss. '
             'Use this for pricing decisions.',
    )
    yield_tracking_count = fields.Integer(
        string='Yield Records',
        compute='_compute_yield_tracking_count',
    )

    def _compute_yield_tracking_count(self):
        tracking_obj = self.env['yield.tracking']
        for tmpl in self:
            product_ids = tmpl.product_variant_ids.ids
            tmpl.yield_tracking_count = tracking_obj.search_count([
                ('product_id', 'in', product_ids),
                ('state', 'in', ('confirmed', 'done')),
            ])

    @api.depends('standard_price', 'theoretical_yield_pct')
    def _compute_yield_adjusted_cost(self):
        tracking_obj = self.env['yield.tracking']
        for tmpl in self:
            product_ids = tmpl.product_variant_ids.ids
            trackings = tracking_obj.search([
                ('product_id', 'in', product_ids),
                ('state', 'in', ('confirmed', 'done')),
            ])
            if trackings:
                total_input = sum(trackings.mapped('input_qty'))
                total_output = sum(trackings.mapped('output_qty'))
                if total_input > 0:
                    tmpl.avg_actual_yield_pct = (total_output / total_input) * 100.0
                else:
                    tmpl.avg_actual_yield_pct = 0.0

                if tmpl.avg_actual_yield_pct > 0:
                    tmpl.yield_adjusted_cost = (
                        tmpl.standard_price / (tmpl.avg_actual_yield_pct / 100.0))
                else:
                    tmpl.yield_adjusted_cost = tmpl.standard_price
            else:
                tmpl.avg_actual_yield_pct = 0.0
                if tmpl.theoretical_yield_pct > 0:
                    tmpl.yield_adjusted_cost = (
                        tmpl.standard_price / (tmpl.theoretical_yield_pct / 100.0))
                else:
                    tmpl.yield_adjusted_cost = tmpl.standard_price

    def action_view_yield_trackings(self):
        self.ensure_one()
        action = self.env.ref(
            'inventory_analytics_custom.action_yield_tracking').read()[0]
        product_ids = self.product_variant_ids.ids
        action['domain'] = [('product_id', 'in', product_ids)]
        return action

    def action_recompute_yield_cost(self):
        """Manually trigger recomputation of yield-adjusted cost."""
        self._compute_yield_adjusted_cost()
        return True
