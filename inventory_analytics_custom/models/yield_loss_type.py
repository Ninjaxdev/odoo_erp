# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class YieldLossType(models.Model):
    """Master data for categorizing different types of material losses
    in the manufacturing process (crop loss, scale loss, off-spec, etc.)."""

    _name = 'yield.loss.type'
    _description = 'Yield Loss Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Loss Type',
        required=True,
        track_visibility='onchange',
    )
    code = fields.Char(
        string='Code',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    description = fields.Text(
        string='Description',
    )
    category = fields.Selection([
        ('crop_loss', 'Crop Loss (Rolling)'),
        ('scale_loss', 'Scale Loss (Furnace)'),
        ('off_spec', 'Off-Spec Rejection'),
        ('trim_loss', 'Trim / Cut Loss'),
        ('handling_loss', 'Handling Loss'),
        ('other', 'Other'),
    ], string='Category', required=True, default='other',
        track_visibility='onchange',
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Loss Expense Account',
        help='Account to book loss costs against. Used in COPQ reporting.',
        domain=[('deprecated', '=', False)],
    )
    auto_scrap = fields.Boolean(
        string='Auto-Create Scrap Order',
        default=True,
        help='If enabled, confirming a yield tracking record with this loss type '
             'will automatically create a scrap order.',
    )
    scrap_location_id = fields.Many2one(
        'stock.location',
        string='Scrap Location',
        domain=[('scrap_location', '=', True)],
        help='Default scrap location for auto-generated scrap orders.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )
    color = fields.Integer(
        string='Color Index',
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'Loss type code must be unique per company!'),
    ]
