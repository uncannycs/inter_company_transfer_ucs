# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ReturnInterCompanyTransfer(models.Model):
    _name = 'return.inter.company.transfer'
    _description = 'Return Inter Company Transfer'
    _order = 'id desc'

    name = fields.Char(string='Return Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    inter_company_transfer_id = fields.Many2one('inter.company.transfer', string='Original Transfer', readonly=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Processed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True, copy=False)

    from_company_id = fields.Many2one('res.company', string='From Company', required=True, default=lambda self: self.env.company)
    from_warehouse_id = fields.Many2one('stock.warehouse', string='From Warehouse', required=True, domain="[('company_id', '=', from_company_id)]")
    to_company_id = fields.Many2one('res.company', string='To Company', required=True)
    to_warehouse_id = fields.Many2one('stock.warehouse', string='To Warehouse', required=True, domain="[('company_id', '=', to_company_id)]")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    line_ids = fields.One2many('return.inter.company.transfer.line', 'return_transfer_id', string='Return Lines')

    sale_order_ids = fields.Many2many('sale.order', 'rict_sale_order_rel', 'return_transfer_id', 'order_id', string='Sale Orders')
    purchase_order_ids = fields.Many2many('purchase.order', 'rict_purchase_order_rel', 'return_transfer_id', 'order_id', string='Purchase Orders')
    picking_ids = fields.Many2many('stock.picking', 'rict_stock_picking_rel', 'return_transfer_id', 'picking_id', string='Pickings')
    invoice_ids = fields.Many2many('account.move', 'rict_account_move_rel', 'return_transfer_id', 'move_id', string='Invoices/Bills')

    sale_order_count = fields.Integer(string='Sale Order Count', compute='_compute_counts')
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_counts')
    picking_count = fields.Integer(string='Picking Count', compute='_compute_counts')
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_counts')

    @api.depends('sale_order_ids', 'purchase_order_ids', 'picking_ids', 'invoice_ids')
    def _compute_counts(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)
            rec.purchase_order_count = len(rec.purchase_order_ids)
            rec.picking_count = len(rec.picking_ids)
            rec.invoice_count = len(rec.invoice_ids)

    @api.onchange('from_company_id')
    def _onchange_from_company_id(self):
        if self.from_company_id:
            if self.from_company_id.intercompany_warehouse_id:
                self.from_warehouse_id = self.from_company_id.intercompany_warehouse_id
            else:
                wh = self.env['stock.warehouse'].search([('company_id', '=', self.from_company_id.id)], limit=1)
                self.from_warehouse_id = wh

    @api.onchange('from_warehouse_id')
    def _onchange_from_warehouse_id(self):
        if self.from_warehouse_id:
            self.from_company_id = self.from_warehouse_id.company_id

    @api.onchange('to_company_id')
    def _onchange_to_company_id(self):
        if self.to_company_id:
            if self.to_company_id.intercompany_warehouse_id:
                self.to_warehouse_id = self.to_company_id.intercompany_warehouse_id
            else:
                wh = self.env['stock.warehouse'].search([('company_id', '=', self.to_company_id.id)], limit=1)
                self.to_warehouse_id = wh

    @api.onchange('to_warehouse_id')
    def _onchange_to_warehouse_id(self):
        if self.to_warehouse_id:
            self.to_company_id = self.to_warehouse_id.company_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('return.inter.company.transfer') or _('New')
        return super().create(vals_list)

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_process(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Please add at least one line before processing the return transfer.'))
            if rec.from_company_id == rec.to_company_id:
                raise UserError(_('From Company and To Company must be different.'))

            customer_partner = rec.to_company_id.partner_id
            vendor_partner = rec.from_company_id.partner_id

            # 1. Return Sale Order in from_company_id
            so_vals = {
                'partner_id': customer_partner.id,
                'company_id': rec.from_company_id.id,
                'warehouse_id': rec.from_warehouse_id.id,
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'price_unit': line.price_unit,
                    'name': line.product_id.display_name,
                }) for line in rec.line_ids]
            }
            so = self.env['sale.order'].with_company(rec.from_company_id).with_context(skip_intercompany_auto=True).create(so_vals)
            so.with_company(rec.from_company_id).action_confirm()

            # 2. Return Purchase Order in to_company_id
            po_vals = {
                'partner_id': vendor_partner.id,
                'company_id': rec.to_company_id.id,
                'picking_type_id': rec.to_warehouse_id.in_type_id.id,
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'price_unit': line.price_unit,
                    'name': line.product_id.display_name,
                    'date_planned': fields.Datetime.now(),
                }) for line in rec.line_ids]
            }
            po = self.env['purchase.order'].with_company(rec.to_company_id).with_context(skip_intercompany_auto=True).create(po_vals)
            po.with_company(rec.to_company_id).button_confirm()

            rec.sale_order_ids = [(4, so.id)]
            rec.purchase_order_ids = [(4, po.id)]

            # 3. Delivery / Receipts Pickings
            for picking in so.picking_ids:
                rec.picking_ids = [(4, picking.id)]
                if rec.from_company_id.auto_validate_picking:
                    for move in picking.move_ids:
                        move.quantity = move.product_uom_qty
                    picking.with_company(rec.from_company_id).button_validate()

            for picking in po.picking_ids:
                rec.picking_ids = [(4, picking.id)]
                if rec.to_company_id.auto_validate_picking:
                    for move in picking.move_ids:
                        move.quantity = move.product_uom_qty
                    picking.with_company(rec.to_company_id).button_validate()

            # 4. Invoices and Bills
            if rec.from_company_id.create_invoice_bill:
                so_invoices = so.with_company(rec.from_company_id)._create_invoices()
                for inv in so_invoices:
                    if not inv.invoice_date:
                        inv.invoice_date = fields.Date.context_today(self)
                    rec.invoice_ids = [(4, inv.id)]
                    if rec.from_company_id.validate_invoice_bill and inv.state == 'draft':
                        inv.with_company(rec.from_company_id).action_post()

            if rec.to_company_id.create_invoice_bill:
                bill_vals = po.with_company(rec.to_company_id)._prepare_invoice()
                bill_vals['invoice_date'] = fields.Date.context_today(self)
                bill_vals['invoice_line_ids'] = [(0, 0, po_line._prepare_account_move_line()) for po_line in po.order_line if not po_line.display_type]
                bill = self.env['account.move'].with_company(rec.to_company_id).create(bill_vals)
                rec.invoice_ids = [(4, bill.id)]
                if rec.to_company_id.validate_invoice_bill and bill.state == 'draft':
                    bill.with_company(rec.to_company_id).action_post()

            rec.state = 'process'

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
            'context': {'create': False},
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'create': False},
        }

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'name': _('Transfers / Pickings'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'context': {'create': False},
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices & Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': {'create': False},
        }


class ReturnInterCompanyTransferLine(models.Model):
    _name = 'return.inter.company.transfer.line'
    _description = 'Return Inter Company Transfer Line'

    return_transfer_id = fields.Many2one('return.inter.company.transfer', string='Return Transfer', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, default=0.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.price_unit = self.product_id.lst_price
