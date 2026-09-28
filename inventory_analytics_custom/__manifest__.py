# -*- coding: utf-8 -*-
{
    'name': 'Inventory Analytics Custom - Scrap & Yield Loss Management',
    'version': '13.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Track material yield at every process step, manage scrap & yield losses, '
               'generate Cost of Poor Quality (COPQ) reports for pricing decisions.',
    'description': """
Inventory Analytics Custom - Scrap & Yield Loss Management
==========================================================

Comprehensive scrap and yield loss management for manufacturing:

* **Process Step Tracking**: Define manufacturing process steps (rolling, furnace, cutting, etc.)
  with expected yield percentages.
* **Yield Tracking**: Record actual yield at each process step — track crop losses from rolling,
  scale loss in furnaces, off-spec rejections, and more.
* **Loss Categorization**: Classify losses by type (crop loss, scale loss, off-spec rejection,
  trim loss) with dedicated cost accounts.
* **Actual vs Theoretical Yield**: Compare actual yield against theoretical yield per grade,
  product, and process step.
* **Auto-Raise Scrap Orders**: Automatically generate scrap orders when yield losses are confirmed,
  with full traceability back to production orders.
* **Cost of Poor Quality (COPQ) Reports**: Generate comprehensive COPQ reports that quantify
  the cost impact of losses and feed directly into pricing decisions.
* **Grade-Based Analysis**: Track material grades with yield-adjusted costing for accurate pricing.
* **QWeb Reports**: Professional printable PDF reports for yield analysis and COPQ summaries.

Integrates with: Inventory, Manufacturing, Accounting
    """,
    'author': 'Custom',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'mrp',
        'account',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/loss_type_data.xml',
        'data/cron_data.xml',
        # Views
        'views/yield_loss_type_views.xml',
        'views/process_step_views.xml',
        'views/yield_tracking_views.xml',
        'views/stock_scrap_views.xml',
        'views/mrp_production_views.xml',
        'views/copq_report_views.xml',
        'views/product_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        # Wizards
        'wizard/yield_analysis_wizard_views.xml',
        # Reports
        'reports/report_actions.xml',
        'reports/yield_report_template.xml',
        'reports/copq_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook',
}
