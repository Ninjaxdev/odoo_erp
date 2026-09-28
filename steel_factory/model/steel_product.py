from odoo import models,fields,api


class SteelProduct(models.Model):
    _name="steel_product"
    _description="steel_product"
    company_name=fields.Char(string="Company Name",required=True)
    type_of_product=fields.Selection([('sheet',"Sheet"),('rod',"Rod"),('wire',"Wire")],string="type_of_product")
    quantity=fields.Integer(string="quantity",required=True)
    price=fields.Float(string="Price")
    discount=fields.Float(string="Discount %")
    total_price=fields.Float(string="total_price",compute="_compute_total_price",store=True)

    @api.onchange('type_of_product')
    def _onchange_product(self):
        if self.type_of_product=='sheet':
            self.price=800
        elif self.type_of_product=='rod':
            self.price=500
        elif self.type_of_product=='wire':
            self.price=300
        else:
            self.price=0

    @api.depends('price','discount','quantity')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price=rec.price*rec.quantity-(rec.price*rec.quantity*rec.discount/100)
