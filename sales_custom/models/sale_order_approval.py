from odoo import models,fields


class SaleOrderApproval(models.Model):
    _name = 'sale.order.approval'
    _description = 'Sale Order Approval'

    sale_id = fields.Many2one('sale.order')
    approve = fields.Boolean(string="Approve")

    def action_confirm_approval(self):
        if not self.approve:
            raise UserError("Please enable approval toggle!")

        self.sale_id.is_approved = True
        #self.sale_id.state = 'sale'  # Move to Sales Order
        self.sale_id.action_confirm() #new change

        return {'type': 'ir.actions.act_window_close'}