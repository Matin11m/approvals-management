{
    'name': 'Studio Approval Dynamic Routing',
    'summary': 'Dynamic approver and notify routing for Studio approvals',
    'version': '1.0',
    'category': 'Customizations/Studio',
    'depends': ['web_studio'],
    'pre_init_hook': 'pre_init_hook',
    'data': [
        'views/studio_approval_rule_views.xml',
    ],
    'license': 'OEEL-1',
    'installable': True,
    'application': False,
}
