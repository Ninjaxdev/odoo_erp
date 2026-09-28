# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Defining this here to resolve the "Field custom_note does not exist" error
    # occurring in the orphaned database view 'stock.picking.form.custom'.
    custom_note = fields.Char(string='Custom Note')
