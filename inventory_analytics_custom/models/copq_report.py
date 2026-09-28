# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CopqReport(models.Model):
    """Cost of Poor Quality (COPQ) Report - aggregates yield losses into
    a comprehensive cost report for pricing decisions."""

    _name = 'copq.report'
    _description = 'Cost of Poor Quality Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    date_from = fields.Date(string='Date From', required=True,
                            track_visibility='onchange')
    date_to = fields.Date(string='Date To', required=True,
                          track_visibility='onchange')
    product_ids = fields.Many2many(
        'product.product', 'copq_report_product_rel',
        'report_id', 'product_id', string='Products (Filter)',
        help='Leave empty to include all products.')
    process_step_ids = fields.Many2many(
        'process.step', 'copq_report_step_rel',
        'report_id', 'step_id', string='Process Steps (Filter)',
        help='Leave empty to include all process steps.')
    material_grade = fields.Char(string='Material Grade (Filter)')
    line_ids = fields.One2many('copq.report.line', 'report_id', string='Report Lines')
    summary_ids = fields.One2many('copq.report.summary', 'report_id',
                                  string='Summary by Loss Type')

    # Aggregated totals
    total_input_qty = fields.Float(string='Total Input Qty', readonly=True,
                                   digits='Product Unit of Measure')
    total_output_qty = fields.Float(string='Total Output Qty', readonly=True,
                                    digits='Product Unit of Measure')
    total_loss_qty = fields.Float(string='Total Loss Qty', readonly=True,
                                  digits='Product Unit of Measure')
    total_input_cost = fields.Float(string='Total Input Cost', readonly=True,
                                    digits='Product Price')
    total_loss_cost = fields.Float(string='Total Loss Cost', readonly=True,
                                   digits='Product Price')
    copq_percentage = fields.Float(string='COPQ (%)', readonly=True,
                                   help='Cost of Poor Quality as percentage of total input cost.')
    avg_yield_pct = fields.Float(string='Avg Yield (%)', readonly=True)
    record_count = fields.Integer(string='Records Analyzed', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
    ], string='Status', default='draft', track_visibility='onchange')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id, required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('copq.report') or _('New')
        return super(CopqReport, self).create(vals)

    def action_generate(self):
        """Generate the COPQ report by analyzing yield tracking records."""
        for report in self:
            if report.state != 'draft':
                raise UserError(_('Only draft reports can be generated.'))
            # Clear existing lines
            report.line_ids.unlink()
            report.summary_ids.unlink()

            # Build domain for yield tracking records
            domain = [
                ('date', '>=', report.date_from),
                ('date', '<=', report.date_to),
                ('state', 'in', ('confirmed', 'done')),
                ('company_id', '=', report.company_id.id),
            ]
            if report.product_ids:
                domain.append(('product_id', 'in', report.product_ids.ids))
            if report.process_step_ids:
                domain.append(('process_step_id', 'in', report.process_step_ids.ids))
            if report.material_grade:
                domain.append(('material_grade', 'ilike', report.material_grade))

            trackings = self.env['yield.tracking'].search(domain)

            if not trackings:
                raise UserError(_('No yield tracking records found for the given criteria.'))

            # Create detail lines
            total_input_qty = 0.0
            total_output_qty = 0.0
            total_loss_qty = 0.0
            total_input_cost = 0.0
            total_loss_cost = 0.0
            loss_type_summary = {}

            for tracking in trackings:
                total_input_qty += tracking.input_qty
                total_output_qty += tracking.output_qty
                total_loss_qty += tracking.loss_qty
                total_input_cost += tracking.total_input_cost
                total_loss_cost += tracking.total_loss_cost

                self.env['copq.report.line'].create({
                    'report_id': report.id,
                    'yield_tracking_id': tracking.id,
                    'date': tracking.date,
                    'production_id': tracking.production_id.id if tracking.production_id else False,
                    'product_id': tracking.product_id.id,
                    'material_grade': tracking.material_grade,
                    'process_step_id': tracking.process_step_id.id,
                    'input_qty': tracking.input_qty,
                    'output_qty': tracking.output_qty,
                    'loss_qty': tracking.loss_qty,
                    'actual_yield_pct': tracking.actual_yield_pct,
                    'theoretical_yield_pct': tracking.theoretical_yield_pct,
                    'yield_variance': tracking.yield_variance,
                    'input_cost': tracking.total_input_cost,
                    'loss_cost': tracking.total_loss_cost,
                })

                # Aggregate by loss type from loss lines
                for loss_line in tracking.loss_line_ids:
                    lt_id = loss_line.loss_type_id.id
                    if lt_id not in loss_type_summary:
                        loss_type_summary[lt_id] = {
                            'loss_qty': 0.0, 'loss_cost': 0.0, 'count': 0}
                    loss_type_summary[lt_id]['loss_qty'] += loss_line.loss_qty
                    loss_type_summary[lt_id]['loss_cost'] += loss_line.loss_cost
                    loss_type_summary[lt_id]['count'] += 1

            # Create summary lines by loss type
            for lt_id, data in loss_type_summary.items():
                pct = (data['loss_cost'] / total_input_cost * 100.0) if total_input_cost > 0 else 0
                self.env['copq.report.summary'].create({
                    'report_id': report.id,
                    'loss_type_id': lt_id,
                    'total_loss_qty': data['loss_qty'],
                    'total_loss_cost': data['loss_cost'],
                    'occurrence_count': data['count'],
                    'copq_contribution_pct': pct,
                })

            # Update report totals
            avg_yield = (total_output_qty / total_input_qty * 100.0) if total_input_qty > 0 else 0
            copq_pct = (total_loss_cost / total_input_cost * 100.0) if total_input_cost > 0 else 0

            report.write({
                'total_input_qty': total_input_qty,
                'total_output_qty': total_output_qty,
                'total_loss_qty': total_loss_qty,
                'total_input_cost': total_input_cost,
                'total_loss_cost': total_loss_cost,
                'copq_percentage': copq_pct,
                'avg_yield_pct': avg_yield,
                'record_count': len(trackings),
                'state': 'generated',
            })
        return True

    def action_reset_draft(self):
        for report in self:
            report.line_ids.unlink()
            report.summary_ids.unlink()
            report.write({
                'state': 'draft',
                'total_input_qty': 0, 'total_output_qty': 0,
                'total_loss_qty': 0, 'total_input_cost': 0,
                'total_loss_cost': 0, 'copq_percentage': 0,
                'avg_yield_pct': 0, 'record_count': 0,
            })


class CopqReportLine(models.Model):
    _name = 'copq.report.line'
    _description = 'COPQ Report Detail Line'
    _order = 'date, id'

    report_id = fields.Many2one('copq.report', string='Report',
                                required=True, ondelete='cascade')
    yield_tracking_id = fields.Many2one('yield.tracking', string='Yield Tracking')
    date = fields.Date(string='Date')
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    product_id = fields.Many2one('product.product', string='Product')
    material_grade = fields.Char(string='Grade')
    process_step_id = fields.Many2one('process.step', string='Process Step')
    input_qty = fields.Float(string='Input Qty', digits='Product Unit of Measure')
    output_qty = fields.Float(string='Output Qty', digits='Product Unit of Measure')
    loss_qty = fields.Float(string='Loss Qty', digits='Product Unit of Measure')
    actual_yield_pct = fields.Float(string='Actual Yield (%)')
    theoretical_yield_pct = fields.Float(string='Theoretical Yield (%)')
    yield_variance = fields.Float(string='Variance (%)')
    input_cost = fields.Float(string='Input Cost', digits='Product Price')
    loss_cost = fields.Float(string='Loss Cost', digits='Product Price')
    copq_pct = fields.Float(string='COPQ (%)', compute='_compute_copq_pct', store=True)

    @api.depends('loss_cost', 'input_cost')
    def _compute_copq_pct(self):
        for line in self:
            line.copq_pct = (
                (line.loss_cost / line.input_cost * 100.0)
                if line.input_cost > 0 else 0.0)


class CopqReportSummary(models.Model):
    _name = 'copq.report.summary'
    _description = 'COPQ Report Summary by Loss Type'
    _order = 'total_loss_cost desc'

    report_id = fields.Many2one('copq.report', string='Report',
                                required=True, ondelete='cascade')
    loss_type_id = fields.Many2one('yield.loss.type', string='Loss Type')
    loss_category = fields.Selection(related='loss_type_id.category',
                                     string='Category', store=True, readonly=True)
    total_loss_qty = fields.Float(string='Total Loss Qty', digits='Product Unit of Measure')
    total_loss_cost = fields.Float(string='Total Loss Cost', digits='Product Price')
    occurrence_count = fields.Integer(string='Occurrences')
    copq_contribution_pct = fields.Float(string='COPQ Contribution (%)')
