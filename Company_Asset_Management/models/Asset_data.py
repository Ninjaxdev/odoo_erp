from odoo import models, fields,api
from odoo.exceptions import ValidationError

class CompanyAsset(models.Model):
    _name = 'company.asset'
    _description = 'Company Asset'

    name = fields.Char("Asset Name", required=True)

    asset_code = fields.Char(string="Asset Code",
    readonly=True,
    copy=False,
    default="New")

    asset_type = fields.Selection([
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('monitor', 'Monitor'),
        ('software', 'Software License'),
        ('other', 'Other')
    ], string="Asset Type")
    custom_asset_type = fields.Char(string="Custom Asset Type")
    employee_id = fields.Integer(string="Assigned Employee ID")
    employee_name = fields.Char(string="Employee Name")
    # employee_name=fields.Many2one('res.users', string='Employee') for future use
    assign_date = fields.Date(string="Assign Date",
        default=fields.Date.today)

    return_date = fields.Date("Return Date")

    status = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged')
    ], default='available')

    assigned_by = fields.Char(string="Assigned By")
    # assigned_by = fields.Many2one('res.users', string='Employee') for future use
    remarks = fields.Text("Remarks")

    @api.constrains('assign_date', 'return_date')
    def _check_dates(self):
        for rec in self:
            if rec.assign_date and rec.return_date:
                if rec.return_date < rec.assign_date:
                    raise ValidationError(
                        "Return Date cannot be earlier than Assign Date."
                    )

    @api.constrains('status', 'employee_id')
    def _check_employee(self):
        for rec in self:
            if rec.status == 'assigned' and not rec.employee_id:
                raise ValidationError(
                    "Assigned assets must have an employee."
                )
    # overriding create for asset code
    @api.model
    def create(self, vals):
        if vals.get('asset_code', 'New') == 'New':
            vals['asset_code'] = self.env['ir.sequence'].next_by_code(
                'company.asset'
            ) or 'New'
        return super(CompanyAsset, self).create(vals)

    #_sql_constraints = [
     #   ('asset_code_unique',
      #   'unique(asset_code)',
       #  'Asset Code must be unique!')
    #]