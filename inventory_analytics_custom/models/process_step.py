# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProcessStep(models.Model):
    """Manufacturing process steps (e.g. Rolling, Furnace Heating, Cutting)
    with expected/theoretical yield percentages."""

    _name = 'process.step'
    _description = 'Manufacturing Process Step'
    _order = 'sequence, name'

    name = fields.Char(
        string='Process Step',
        required=True,
        track_visibility='onchange',
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in which this step appears in the manufacturing process.',
    )
    description = fields.Text(
        string='Description',
    )
    expected_yield_pct = fields.Float(
        string='Expected Yield (%)',
        required=True,
        default=100.0,
        help='Theoretical/expected yield percentage for this process step. '
             'E.g. 95.0 means 5% loss is expected.',
        track_visibility='onchange',
    )
    tolerance_pct = fields.Float(
        string='Tolerance (%)',
        default=2.0,
        help='Acceptable deviation from expected yield before flagging as critical.',
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        help='Optional link to the manufacturing work center performing this step.',
    )
    loss_type_ids = fields.Many2many(
        'yield.loss.type',
        'process_step_loss_type_rel',
        'process_step_id',
        'loss_type_id',
        string='Applicable Loss Types',
        help='Loss types that can occur at this process step.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )
    yield_tracking_count = fields.Integer(
        string='Tracking Records',
        compute='_compute_yield_tracking_count',
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'Process step code must be unique per company!'),
        ('expected_yield_positive', 'CHECK(expected_yield_pct > 0 AND expected_yield_pct <= 100)',
         'Expected yield must be between 0 and 100!'),
    ]

    @api.constrains('expected_yield_pct')
    def _check_expected_yield(self):
        for rec in self:
            if rec.expected_yield_pct <= 0 or rec.expected_yield_pct > 100:
                raise ValidationError(
                    _('Expected Yield must be between 0%% and 100%% for step "%s".') % rec.name
                )

    @api.constrains('tolerance_pct')
    def _check_tolerance(self):
        for rec in self:
            if rec.tolerance_pct < 0:
                raise ValidationError(
                    _('Tolerance cannot be negative for step "%s".') % rec.name
                )

    def _compute_yield_tracking_count(self):
        tracking_obj = self.env['yield.tracking']
        for rec in self:
            rec.yield_tracking_count = tracking_obj.search_count([
                ('process_step_id', '=', rec.id),
            ])

    def action_view_yield_trackings(self):
        """Open yield tracking records for this process step."""
        self.ensure_one()
        action = self.env.ref(
            'inventory_analytics_custom.action_yield_tracking'
        ).read()[0]
        action['domain'] = [('process_step_id', '=', self.id)]
        action['context'] = {'default_process_step_id': self.id}
        return action
