# -*- coding: utf-8 -*-
{
    'name': 'Inter-Company Inventory Transfer | Company-to-Company Stock Transfer | Inter-Company Inventory Management | Inter-Company Warehouse Transfer | Cross-Company Warehouse Management',
    'version': '17.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Inter-Company Inventory Transfer, Stock Transfer, Sales Purchase Inter Company Transfer, Multi Company Transfer',
    'description': '''
Inter-Company Inventory Transfer (Community & Enterprise)
==============================================================================
Inter-Company Inventory Transfer Rules helps user to manage automatic stock and accounting
inter company transaction from different companies based on inter company rules setup.

Key Features:
- Stock InterCompany Transaction between multiple companies.
- Return / Reverse InterCompany Transaction.
- Auto Workflow based on "Intercompany Transaction application on" configuration (Sale Order only, Purchase Order only, Both).
- Easy access to related documents with smart buttons.
- Link or unlink intercompany documents.
- Auto validate picking or receipt.
- Auto create customer invoice and vendor bill.
- Auto validate customer invoice and vendor bill.
- Inter Company Transaction Access Rights (User / Manager).
- InterCompany Warehouse configuration per company.
- PDF Report for Inter Company Transfer and Return Transfer.
''',
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'account', 'sale_stock', 'purchase_stock'],
    'data': [
        'security/inter_company_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/inter_company_transfer_report_templates.xml',
        'report/inter_company_transfer_reports.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/inter_company_transfer_views.xml',
        'views/return_inter_company_transfer_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'website': 'https://uncannycs.com',
    'author': 'Uncanny Consulting Services LLP',
    'maintainer': 'Uncanny Consulting Services LLP',
    'license': 'Other proprietary',
    "images": ['static/description/banner.gif'],
    "price": 100,
    "currency": "USD",
}
