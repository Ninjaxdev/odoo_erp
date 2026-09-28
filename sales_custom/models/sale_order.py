from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # 🔹 Fields
    custom_note = fields.Char(string="Custom Note")
    is_approved = fields.Boolean(string='Approved', default=False)
    custom_field = fields.Char(string="Custom Field")
    mark_important = fields.Char(string="Mark Important")

    # 🔹 Add new state
    state = fields.Selection(selection_add=[
        ('approval_waiting', 'Approval Waiting')
    ])
    total_order_density = fields.Float(string="Total Order Density", compute="_compute_total_density")

    @api.depends('order_line.total_density')
    def _compute_total_density(self):
        for rec in self:
            rec.total_order_density = sum(line.total_density for line in rec.order_line)

    # 🔹 Open Approval Popup
    def action_open_approval(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval',
            'res_model': 'sale.order.approval',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_id': self.id}
        }

    # 🔹 Main Confirmation Logic
    def action_confirm(self):
        for rec in self:

            # ✅ Keep your existing validation
            if not rec.custom_note:
                raise UserError("Please add Custom Note before confirming the order.")


            if rec.amount_total > 50000 and not rec.is_approved:
                rec.state = 'approval_waiting'
                return   # stop confirmation here


        return super(SaleOrder, self).action_confirm()

    # 🔹 Approve Action (continue flow)
    def action_approve(self):
        for rec in self:
            rec.is_approved = True

        # Continue confirmation after approval
        return self.action_confirm()