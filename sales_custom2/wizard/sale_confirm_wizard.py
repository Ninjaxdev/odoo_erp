from odoo import models, fields

class SaleConfirmWizard(models.TransientModel):
    _name = 'sale.confirm.wizard'
    _description = 'Sale Confirmation Wizard'

    sale_order_id = fields.Many2one('sale.order')

    def action_confirm(self):
        self.sale_order_id.action_confirm()

        return {
            'type': 'ir.actions.act_window_close'
        }

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window_close'
        }