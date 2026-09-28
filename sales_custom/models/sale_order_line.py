from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    density_per_unit = fields.Float(string="Density per Unit")
    total_density = fields.Float(string="Total Density", compute="_compute_total_density",
        store=True)

    @api.depends('density_per_unit', 'product_uom_qty')
    def _compute_total_density(self):
        for rec in self:
            if rec.density_per_unit and rec.product_uom_qty:
                rec.total_density = rec.density_per_unit * rec.product_uom_qty
            else:
                rec.total_density = 0