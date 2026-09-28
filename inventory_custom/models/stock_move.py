from odoo import models,fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    mark_important = fields.Boolean(string="Mark Important",default=False,)

