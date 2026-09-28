# -*- coding: utf-8 -*-
from . import models
from . import wizard

def pre_init_hook(cr):
    """Delete orphaned custom views that refer to fields from uninstalled modules."""
    cr.execute("DELETE FROM ir_ui_view WHERE name = 'stock.picking.form.custom' AND model = 'stock.picking'")
