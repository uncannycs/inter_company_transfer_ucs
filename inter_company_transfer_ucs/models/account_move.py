# -*- coding: utf-8 -*-
from odoo import models, fields, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    intercompany_transfer_id = fields.Many2one('inter.company.transfer', string='Inter Company Transfer', copy=False)
    intercompany_transfer_count = fields.Integer(string='Inter Company Transfers', compute='_compute_intercompany_transfer_count')

    def _compute_intercompany_transfer_count(self):
        for move in self:
            if move.intercompany_transfer_id:
                move.intercompany_transfer_count = 1
            else:
                move.intercompany_transfer_count = self.env['inter.company.transfer'].search_count([('invoice_ids', 'in', move.id)])

    def action_view_intercompany_transfer(self):
        self.ensure_one()
        transfers = self.env['inter.company.transfer'].search(['|', ('id', '=', self.intercompany_transfer_id.id), ('invoice_ids', 'in', self.id)])
        return {
            'name': _('Inter Company Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'inter.company.transfer',
            'view_mode': 'form' if len(transfers) == 1 else 'tree,form',
            'res_id': transfers.id if len(transfers) == 1 else False,
            'domain': [('id', 'in', transfers.ids)],
        }
