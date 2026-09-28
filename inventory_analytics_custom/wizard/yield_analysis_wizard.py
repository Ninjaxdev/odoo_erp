# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class YieldAnalysisWizard(models.TransientModel):
    """Wizard for analyzing yield data with flexible grouping and filtering."""

    _name = 'yield.analysis.wizard'
    _description = 'Yield Analysis Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    product_ids = fields.Many2many(
        'product.product', 'wizard_yield_product_rel',
        'wizard_id', 'product_id', string='Products')
    process_step_ids = fields.Many2many(
        'process.step', 'wizard_yield_step_rel',
        'wizard_id', 'step_id', string='Process Steps')
    material_grade = fields.Char(string='Material Grade')
    state_filter = fields.Selection([
        ('all', 'All'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string='Status Filter', default='all')
    group_by = fields.Selection([
        ('product', 'Product'),
        ('process_step', 'Process Step'),
        ('grade', 'Material Grade'),
        ('date_month', 'Month'),
    ], string='Primary Group By', default='product')
    report_type = fields.Selection([
        ('pivot', 'Pivot Table'),
        ('graph', 'Graph'),
        ('list', 'List'),
    ], string='Report Type', default='pivot')

    def action_analyze(self):
        """Open the yield tracking records with applied filters."""
        self.ensure_one()

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.state_filter == 'confirmed':
            domain.append(('state', '=', 'confirmed'))
        elif self.state_filter == 'done':
            domain.append(('state', '=', 'done'))
        else:
            domain.append(('state', 'in', ('confirmed', 'done')))

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.process_step_ids:
            domain.append(('process_step_id', 'in', self.process_step_ids.ids))
        if self.material_grade:
            domain.append(('material_grade', 'ilike', self.material_grade))

        # Build context for grouping
        context = {}
        group_map = {
            'product': 'search_default_group_product',
            'process_step': 'search_default_group_step',
            'grade': 'search_default_group_grade',
            'date_month': 'search_default_group_date',
        }
        if self.group_by in group_map:
            context[group_map[self.group_by]] = 1

        # Determine view mode
        view_mode_map = {
            'pivot': 'pivot,graph,tree,form',
            'graph': 'graph,pivot,tree,form',
            'list': 'tree,form,pivot,graph',
        }
        view_mode = view_mode_map.get(self.report_type, 'pivot,graph,tree,form')

        return {
            'name': _('Yield Analysis: %s to %s') % (self.date_from, self.date_to),
            'type': 'ir.actions.act_window',
            'res_model': 'yield.tracking',
            'view_mode': view_mode,
            'domain': domain,
            'context': context,
        }

    def action_generate_copq(self):
        """Create a COPQ report from the wizard parameters."""
        self.ensure_one()
        copq = self.env['copq.report'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'product_ids': [(6, 0, self.product_ids.ids)],
            'process_step_ids': [(6, 0, self.process_step_ids.ids)],
            'material_grade': self.material_grade or False,
        })
        copq.action_generate()
        return {
            'name': _('COPQ Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'copq.report',
            'view_mode': 'form',
            'res_id': copq.id,
        }
