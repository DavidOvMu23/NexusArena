{
    'name': 'Nexus Arena',
    'summary': 'Base del módulo de gestión de torneos de eSports',
    'depends': ['base', 'account'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
    ],
    'installable': True,
    'application': True,
}