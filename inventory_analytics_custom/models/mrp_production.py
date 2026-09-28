# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    yield_tracking_ids = fields.One2many(
        'yield.tracking', 'production_id', string='Yield Tracking Records')
    yield_tracking_count = fields.Integer(
        string='Yield Trackings', compute='_compute_yield_metrics')
    total_yield_pct = fields.Float(
        string='Overall Yield (%)', compute='_compute_yield_metrics', store=True)
    total_loss_qty = fields.Float(
        string='Total Loss Qty', compute='_compute_yield_metrics', store=True,
        digits='Product Unit of Measure')
    total_loss_cost = fields.Float(
        string='Total Loss Cost', compute='_compute_yield_metrics', store=True,
        digits='Product Price')
    yield_status = fields.Selection([
        ('not_tracked', 'Not Tracked'),
        ('good', 'Good'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Yield Status', compute='_compute_yield_metrics', store=True)

    @api.depends('yield_tracking_ids', 'yield_tracking_ids.actual_yield_pct',
                 'yield_tracking_ids.loss_qty', 'yield_tracking_ids.total_loss_cost',
                 'yield_tracking_ids.state', 'yield_tracking_ids.yield_status')
    def _compute_yield_metrics(self):
        for production in self:
            trackings = production.yield_tracking_ids.filtered(
                lambda t: t.state in ('confirmed', 'done'))
            production.yield_tracking_count = len(production.yield_tracking_ids)
            if trackings:
                total_input = sum(trackings.mapped('input_qty'))
                total_output = sum(trackings.mapped('output_qty'))
                production.total_loss_qty = sum(trackings.mapped('loss_qty'))
                production.total_loss_cost = sum(trackings.mapped('total_loss_cost'))
                production.total_yield_pct = (
                    (total_output / total_input) * 100.0 if total_input > 0 else 0.0)
                statuses = trackings.mapped('yield_status')
                if 'critical' in statuses:
                    production.yield_status = 'critical'
                elif 'warning' in statuses:
                    production.yield_status = 'warning'
                else:
                    production.yield_status = 'good'
            else:
                production.total_yield_pct = 0.0
                production.total_loss_qty = 0.0
                production.total_loss_cost = 0.0
                production.yield_status = 'not_tracked'

    def action_view_yield_trackings(self):
        self.ensure_one()
        action = self.env.ref(
            'inventory_analytics_custom.action_yield_tracking').read()[0]
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {
            'default_production_id': self.id,
            'default_product_id': self.product_id.id,
        }
        return action

    def action_create_yield_tracking(self):
        self.ensure_one()
        return {
            'name': _('New Yield Tracking'),
            'type': 'ir.actions.act_window',
            'res_model': 'yield.tracking',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_uom_id': self.product_uom_id.id,
            },
        }
