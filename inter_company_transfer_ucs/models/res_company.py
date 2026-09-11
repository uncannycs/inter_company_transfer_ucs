# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    intercompany_apply_type = fields.Selection([
        ('sale', 'Sale Order Only'),
        ('purchase', 'Purchase Order Only'),
        ('both', 'Both Sale and Purchase Order')
    ], string='Intercompany Transaction Application On', default='both')

    link_intercompany_document = fields.Boolean(
        string='Link Intercompany Document',
        default=True,
        help='Option to link or unlink related documents of intercompany transaction.'
    )
    auto_validate_picking = fields.Boolean(
        string='Auto Validate Picking/Receipt',
        default=False,
        help='Option to automatically validate delivery orders and receipts.'
    )
    create_invoice_bill = fields.Boolean(
        string='Create Invoice/Bill',
        default=False,
        help='Customer invoice or vendor bill will be created automatically for intercompany transaction.'
    )
    validate_invoice_bill = fields.Boolean(
        string='Validate Invoice/Bill',
        default=False,
        help='Customer invoice or vendor bill will be automatically validated.'
    )
    intercompany_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='InterCompany Warehouse',
        domain="[('company_id', '=', id)]",
        help='Default warehouse used for intercompany transactions for this company.'
    )
