# -*- coding: utf-8 -*-
from odoo import models, fields, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    intercompany_transfer_id = fields.Many2one('inter.company.transfer', string='Inter Company Transfer', copy=False)
    intercompany_transfer_count = fields.Integer(string='Inter Company Transfers', compute='_compute_intercompany_transfer_count')

    def _compute_intercompany_transfer_count(self):
        for order in self:
            if order.intercompany_transfer_id:
                order.intercompany_transfer_count = 1
            else:
                order.intercompany_transfer_count = self.env['inter.company.transfer'].search_count([('sale_order_ids', 'in', order.id)])

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if self.env.context.get('skip_intercompany_auto'):
                continue
            company = order.company_id
            if company.intercompany_apply_type in ('sale', 'both'):
                # Check if partner corresponds to another company
                target_company = self.env['res.company'].search([('partner_id', '=', order.partner_id.id)], limit=1)
                if target_company and target_company != company and not order.intercompany_transfer_id:
                    # Create ICT
                    from_wh = order.warehouse_id or company.intercompany_warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
                    to_wh = target_company.intercompany_warehouse_id or self.env['stock.warehouse'].search([('company_id', '=', target_company.id)], limit=1)

                    ict_vals = {
                        'from_company_id': company.id,
                        'from_warehouse_id': from_wh.id if from_wh else False,
                        'to_company_id': target_company.id,
                        'to_warehouse_id': to_wh.id if to_wh else False,
                        'sale_order_ids': [(4, order.id)],
                        'line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'quantity': line.product_uom_qty,
                            'uom_id': line.product_uom_id.id,
                            'price_unit': line.price_unit,
                        }) for line in order.order_line if not line.display_type]
                    }
                    ict = self.env['inter.company.transfer'].create(ict_vals)
                    if company.link_intercompany_document:
                        order.intercompany_transfer_id = ict.id

                    # Create matching PO in target_company
                    po_vals = {
                        'partner_id': company.partner_id.id,
                        'company_id': target_company.id,
                        'picking_type_id': to_wh.in_type_id.id if to_wh else False,
                        'intercompany_transfer_id': ict.id if target_company.link_intercompany_document else False,
                        'order_line': [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom_id': line.product_uom_id.id,
                            'price_unit': line.price_unit,
                            'name': line.product_id.display_name,
                            'date_planned': fields.Datetime.now(),
                        }) for line in order.order_line if not line.display_type]
                    }
                    po = self.env['purchase.order'].with_company(target_company).with_context(skip_intercompany_auto=True).create(po_vals)
                    po.with_company(target_company).button_confirm()
                    ict.purchase_order_ids = [(4, po.id)]

                    # Link & Validate Pickings
                    for picking in order.picking_ids:
                        if company.link_intercompany_document:
                            picking.intercompany_transfer_id = ict.id
                        ict.picking_ids = [(4, picking.id)]
                        if company.auto_validate_picking:
                            for move in picking.move_ids:
                                move.quantity = move.product_uom_qty
                            picking.with_company(company).button_validate()

                    for picking in po.picking_ids:
                        if target_company.link_intercompany_document:
                            picking.intercompany_transfer_id = ict.id
                        ict.picking_ids = [(4, picking.id)]
                        if target_company.auto_validate_picking:
                            for move in picking.move_ids:
                                move.quantity = move.product_uom_qty
                            picking.with_company(target_company).button_validate()

                    # Invoices / Bills
                    if company.create_invoice_bill:
                        so_invs = order.with_company(company)._create_invoices()
                        for inv in so_invs:
                            if not inv.invoice_date:
                                inv.invoice_date = fields.Date.context_today(self)
                            if company.link_intercompany_document:
                                inv.intercompany_transfer_id = ict.id
                            ict.invoice_ids = [(4, inv.id)]
                            if company.validate_invoice_bill and inv.state == 'draft':
                                inv.with_company(company).action_post()

                    if target_company.create_invoice_bill:
                        bill_vals = po.with_company(target_company)._prepare_invoice()
                        bill_vals['invoice_date'] = fields.Date.context_today(self)
                        bill_vals['intercompany_transfer_id'] = ict.id if target_company.link_intercompany_document else False
                        bill_vals['invoice_line_ids'] = [(0, 0, po_line._prepare_account_move_line()) for po_line in po.order_line if not po_line.display_type]
                        bill = self.env['account.move'].with_company(target_company).create(bill_vals)
                        ict.invoice_ids = [(4, bill.id)]
                        if target_company.validate_invoice_bill and bill.state == 'draft':
                            bill.with_company(target_company).action_post()

                    ict.state = 'process'
        return res

    def action_view_intercompany_transfer(self):
        self.ensure_one()
        transfers = self.env['inter.company.transfer'].search(['|', ('id', '=', self.intercompany_transfer_id.id), ('sale_order_ids', 'in', self.id)])
        return {
            'name': _('Inter Company Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'inter.company.transfer',
            'view_mode': 'form' if len(transfers) == 1 else 'list,form',
            'res_id': transfers.id if len(transfers) == 1 else False,
            'domain': [('id', 'in', transfers.ids)],
        }
