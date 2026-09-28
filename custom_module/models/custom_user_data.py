from odoo import fields,models,api

class CustomUserData(models.Model):
    _name="custom.user.data"
    _description="Custom User Data"

    name=fields.Char('Name')
    email=fields.Char('Email')
