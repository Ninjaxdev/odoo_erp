from odoo import models,fields,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    invoice_address=fields.Char(string="invoice address")
    delivery_address=fields.Char(string="delivery address")
    shipping=fields.Selection([('truck', 'Truck'),
        ('ship', 'Ship'),
        ('frate', 'Frate'),
        ('other', 'Other')], string="Shipping")

   # order_date=fields.Date(string="Order Date")
    delivery_date=fields.Date(string="Delivery Date")
    so_ship_date=fields.Date(string="so Date Ship Date")
    customer_po=fields.Char(string="Customer PO #")
    #payment_terms=fields.Char(string="Payment Terms")
   # incoterm=fields.Char(string="Incoterm")

#wizard functionality
    def open_confirm_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'sale.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                      'default_sale_order_id': self.id,
                      }
        }