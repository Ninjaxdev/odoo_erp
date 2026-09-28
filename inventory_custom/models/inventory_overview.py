# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_note = fields.Char(string='Custom Note')

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def action_custom_button(self):
        raise UserError("Custom button clicked!")
