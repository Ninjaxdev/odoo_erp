from odoo import models, fields ,api
from odoo.exceptions import ValidationError

class Student(models.Model):
    _name = 'student.record'
    _description = 'Student Record'

    name = fields.Char(string="Name", required=True)
    age = fields.Integer(string="Age")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")

    # @api constraint- Trigger onSave

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError("please check your email")

    @api.constrains('age')
    def _check_age(self):
        for record in self:
            if record.age <= 0 or record.age>=150:
                raise ValidationError("please check your age")

    # @api onchange - trigger while typing (live)
    @api.onchange('phone')
    def _check_phone(self):
        if self.phone and len(self.phone)!=10:
            return{
                'warning': {
                    'title': "Invalid Phone Number",
                    'message': "Phone number should be exactly 10 digits!"
                }
            }







