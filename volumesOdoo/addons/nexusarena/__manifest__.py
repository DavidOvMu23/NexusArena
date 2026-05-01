{
    'name': 'Nexus Arena',
    'summary': 'Base del módulo de gestión de torneos de eSports',

    # base para modelos, account para facturación, contacts para gestión de jugadores/equipos, mail para notificaciones
    'depends': ['base', 'account', 'contacts', 'mail'],
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
    'demo': [
        
        # datos demo, se cargan a la hora de instalar el modulo habiendo creado la base de datos con el check de cargar datos demo activado
        'demo/nexusarena_demo.xml',
    ],
    'installable': True,
    'application': True,
}