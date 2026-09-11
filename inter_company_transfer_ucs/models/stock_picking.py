# -*- coding: utf-8 -*-
from odoo import models, fields, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    intercompany_transfer_id = fields.Many2one('inter.company.transfer', string='Inter Company Transfer', copy=False)
    intercompany_transfer_count = fields.Integer(string='Inter Company Transfers', compute='_compute_intercompany_transfer_count')

    def _compute_intercompany_transfer_count(self):
        for picking in self:
            if picking.intercompany_transfer_id:
                picking.intercompany_transfer_count = 1
            else:
                picking.intercompany_transfer_count = self.env['inter.company.transfer'].search_count([('picking_ids', 'in', picking.id)])

    def action_view_intercompany_transfer(self):
        self.ensure_one()
        transfers = self.env['inter.company.transfer'].search(['|', ('id', '=', self.intercompany_transfer_id.id), ('picking_ids', 'in', self.id)])
        return {
            'name': _('Inter Company Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'inter.company.transfer',
            'view_mode': 'form' if len(transfers) == 1 else 'list,form',
            'res_id': transfers.id if len(transfers) == 1 else False,
            'domain': [('id', 'in', transfers.ids)],
        }
