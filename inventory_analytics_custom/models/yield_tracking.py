# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class YieldTracking(models.Model):
    """Main model to track material yield at each manufacturing process step.
    Records input/output quantities, calculates losses, and can auto-raise scrap orders."""

    _name = 'yield.tracking'
    _description = 'Yield Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        track_visibility='onchange',
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        track_visibility='onchange',
        index=True,
    )
    process_step_id = fields.Many2one(
        'process.step',
        string='Process Step',
        required=True,
        track_visibility='onchange',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        track_visibility='onchange',
    )
    lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lot/Serial Number',
    )
    material_grade = fields.Char(
        string='Material Grade',
        help='Material grade (e.g. SS304, SS316, C45, etc.)',
        track_visibility='onchange',
    )

    # Quantities
    input_qty = fields.Float(
        string='Input Quantity',
        required=True,
        digits='Product Unit of Measure',
        track_visibility='onchange',
    )
    output_qty = fields.Float(
        string='Output Quantity',
        required=True,
        digits='Product Unit of Measure',
        track_visibility='onchange',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
    )
    loss_qty = fields.Float(
        string='Total Loss Quantity',
        compute='_compute_yield_metrics',
        store=True,
        digits='Product Unit of Measure',
    )

    # Yield metrics
    theoretical_yield_pct = fields.Float(
        string='Theoretical Yield (%)',
        compute='_compute_theoretical_yield',
        store=True,
        help='Expected yield percentage from the process step definition.',
    )
    actual_yield_pct = fields.Float(
        string='Actual Yield (%)',
        compute='_compute_yield_metrics',
        store=True,
    )
    yield_variance = fields.Float(
        string='Yield Variance (%)',
        compute='_compute_yield_metrics',
        store=True,
        help='Actual yield minus theoretical yield. Negative means underperformance.',
    )
    yield_status = fields.Selection([
        ('good', 'Within Tolerance'),
        ('warning', 'Near Tolerance Limit'),
        ('critical', 'Below Tolerance'),
    ], string='Yield Status',
        compute='_compute_yield_metrics',
        store=True,
    )

    # Cost fields
    unit_cost = fields.Float(
        string='Unit Cost',
        digits='Product Price',
        help='Cost per unit of input material.',
    )
    total_input_cost = fields.Float(
        string='Total Input Cost',
        compute='_compute_cost_metrics',
        store=True,
        digits='Product Price',
    )
    total_loss_cost = fields.Float(
        string='Total Loss Cost',
        compute='_compute_cost_metrics',
        store=True,
        digits='Product Price',
    )

    # Loss breakdown lines
    loss_line_ids = fields.One2many(
        'yield.tracking.loss.line',
        'tracking_id',
        string='Loss Breakdown',
    )

    # Scrap integration
    scrap_ids = fields.One2many(
        'stock.scrap',
        'yield_tracking_id',
        string='Scrap Orders',
    )
    scrap_count = fields.Integer(
        string='Scrap Orders',
        compute='_compute_scrap_count',
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft',
        track_visibility='onchange',
        copy=False,
    )

    notes = fields.Text(
        string='Notes',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'yield.tracking') or _('New')
        return super(YieldTracking, self).create(vals)

    @api.depends('process_step_id', 'process_step_id.expected_yield_pct')
    def _compute_theoretical_yield(self):
        for rec in self:
            rec.theoretical_yield_pct = (
                rec.process_step_id.expected_yield_pct
                if rec.process_step_id else 0.0
            )

    @api.depends('input_qty', 'output_qty', 'theoretical_yield_pct',
                 'process_step_id.tolerance_pct')
    def _compute_yield_metrics(self):
        for rec in self:
            rec.loss_qty = rec.input_qty - rec.output_qty
            if rec.input_qty > 0:
                rec.actual_yield_pct = (rec.output_qty / rec.input_qty) * 100.0
            else:
                rec.actual_yield_pct = 0.0
            rec.yield_variance = rec.actual_yield_pct - rec.theoretical_yield_pct

            # Determine yield status
            tolerance = rec.process_step_id.tolerance_pct if rec.process_step_id else 2.0
            if rec.yield_variance >= 0:
                rec.yield_status = 'good'
            elif abs(rec.yield_variance) <= tolerance:
                rec.yield_status = 'warning'
            else:
                rec.yield_status = 'critical'

    @api.depends('input_qty', 'loss_qty', 'unit_cost')
    def _compute_cost_metrics(self):
        for rec in self:
            rec.total_input_cost = rec.input_qty * rec.unit_cost
            rec.total_loss_cost = rec.loss_qty * rec.unit_cost

    def _compute_scrap_count(self):
        for rec in self:
            rec.scrap_count = len(rec.scrap_ids)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            self.unit_cost = self.product_id.standard_price
            self.material_grade = self.product_id.product_tmpl_id.material_grade

    @api.onchange('process_step_id')
    def _onchange_process_step_id(self):
        if self.process_step_id:
            self.theoretical_yield_pct = self.process_step_id.expected_yield_pct

    @api.onchange('production_id')
    def _onchange_production_id(self):
        if self.production_id:
            self.product_id = self.production_id.product_id.id

    @api.constrains('input_qty', 'output_qty')
    def _check_quantities(self):
        for rec in self:
            if rec.input_qty < 0:
                raise ValidationError(_('Input quantity cannot be negative.'))
            if rec.output_qty < 0:
                raise ValidationError(_('Output quantity cannot be negative.'))
            if rec.output_qty > rec.input_qty:
                raise ValidationError(
                    _('Output quantity (%.2f) cannot exceed input quantity (%.2f).')
                    % (rec.output_qty, rec.input_qty)
                )

    def action_confirm(self):
        """Confirm the yield tracking record and auto-create scrap orders if needed."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft records can be confirmed.'))
            rec.state = 'confirmed'
            # Auto-create scrap orders for loss lines with auto_scrap enabled
            rec._auto_create_scrap_orders()
        return True

    def action_done(self):
        """Mark yield tracking as done."""
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Only confirmed records can be marked as done.'))
            rec.state = 'done'
        return True

    def action_cancel(self):
        """Cancel the yield tracking record."""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Cannot cancel a completed record.'))
            rec.state = 'cancelled'
        return True

    def action_draft(self):
        """Reset to draft."""
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Only cancelled records can be reset to draft.'))
            rec.state = 'draft'
        return True

    def _auto_create_scrap_orders(self):
        """Automatically create scrap orders based on loss lines."""
        self.ensure_one()
        scrap_obj = self.env['stock.scrap']
        for line in self.loss_line_ids:
            if line.loss_type_id.auto_scrap and line.loss_qty > 0:
                scrap_vals = {
                    'product_id': self.product_id.id,
                    'scrap_qty': line.loss_qty,
                    'product_uom_id': self.uom_id.id,
                    'lot_id': self.lot_id.id if self.lot_id else False,
                    'production_id': self.production_id.id if self.production_id else False,
                    'yield_tracking_id': self.id,
                    'loss_type_id': line.loss_type_id.id,
                    'is_auto_generated': True,
                    'origin': self.name,
                }
                if line.loss_type_id.scrap_location_id:
                    scrap_vals['scrap_location_id'] = line.loss_type_id.scrap_location_id.id
                scrap_obj.create(scrap_vals)

        # If no loss lines but there is overall loss, create a generic scrap
        if not self.loss_line_ids and self.loss_qty > 0:
            scrap_obj.create({
                'product_id': self.product_id.id,
                'scrap_qty': self.loss_qty,
                'product_uom_id': self.uom_id.id,
                'lot_id': self.lot_id.id if self.lot_id else False,
                'production_id': self.production_id.id if self.production_id else False,
                'yield_tracking_id': self.id,
                'is_auto_generated': True,
                'origin': self.name,
            })

    def action_view_scrap_orders(self):
        """View scrap orders linked to this yield tracking record."""
        self.ensure_one()
        action = self.env.ref('stock.action_stock_scrap').read()[0]
        if self.scrap_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.scrap_ids[0].id
        else:
            action['domain'] = [('yield_tracking_id', '=', self.id)]
        return action


class YieldTrackingLossLine(models.Model):
    """Breakdown of losses by type within a yield tracking record."""

    _name = 'yield.tracking.loss.line'
    _description = 'Yield Tracking Loss Line'
    _order = 'sequence, id'

    tracking_id = fields.Many2one(
        'yield.tracking',
        string='Yield Tracking',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    loss_type_id = fields.Many2one(
        'yield.loss.type',
        string='Loss Type',
        required=True,
    )
    loss_category = fields.Selection(
        related='loss_type_id.category',
        string='Category',
        store=True,
        readonly=True,
    )
    loss_qty = fields.Float(
        string='Loss Quantity',
        required=True,
        digits='Product Unit of Measure',
    )
    uom_id = fields.Many2one(
        related='tracking_id.uom_id',
        string='UoM',
        readonly=True,
    )
    unit_cost = fields.Float(
        related='tracking_id.unit_cost',
        string='Unit Cost',
        readonly=True,
    )
    loss_cost = fields.Float(
        string='Loss Cost',
        compute='_compute_loss_cost',
        store=True,
        digits='Product Price',
    )
    loss_pct = fields.Float(
        string='Loss %',
        compute='_compute_loss_pct',
        store=True,
    )
    notes = fields.Text(
        string='Notes',
    )

    @api.depends('loss_qty', 'unit_cost')
    def _compute_loss_cost(self):
        for line in self:
            line.loss_cost = line.loss_qty * line.unit_cost

    @api.depends('loss_qty', 'tracking_id.input_qty')
    def _compute_loss_pct(self):
        for line in self:
            if line.tracking_id.input_qty > 0:
                line.loss_pct = (line.loss_qty / line.tracking_id.input_qty) * 100.0
            else:
                line.loss_pct = 0.0

    @api.constrains('loss_qty')
    def _check_loss_qty(self):
        for line in self:
            if line.loss_qty < 0:
                raise ValidationError(_('Loss quantity cannot be negative.'))
