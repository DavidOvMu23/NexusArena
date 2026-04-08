{
    'name': 'Nexus Arena',
    'summary': 'Base del módulo de gestión de torneos de eSports',
    'depends': ['base', 'account', 'contacts'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/esports_game_views.xml',
        'views/esports_tournament_views.xml',
        'views/esports_match_views.xml',
        'views/esports_registration_views.xml',
        'views/esports_standing_views.xml',
        'views/res_partner_views.xml',
        'views/nexusarena_menus.xml',
    ],
    'installable': True,
    'application': True,
}