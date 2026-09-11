# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    intercompany_apply_type = fields.Selection(
        related='company_id.intercompany_apply_type',
        string='Intercompany Transaction Application On',
        readonly=False
    )
    link_intercompany_document = fields.Boolean(
        related='company_id.link_intercompany_document',
        string='Link Intercompany Document',
        readonly=False
    )
    auto_validate_picking = fields.Boolean(
        related='company_id.auto_validate_picking',
        string='Auto Validate Picking/Receipt',
        readonly=False
    )
    create_invoice_bill = fields.Boolean(
        related='company_id.create_invoice_bill',
        string='Create Invoice/Bill',
        readonly=False
    )
    validate_invoice_bill = fields.Boolean(
        related='company_id.validate_invoice_bill',
        string='Validate Invoice/Bill',
        readonly=False
    )
    intercompany_warehouse_id = fields.Many2one(
        related='company_id.intercompany_warehouse_id',
        string='InterCompany Warehouse',
        readonly=False,
        domain="[('company_id', '=', company_id)]"
    )
