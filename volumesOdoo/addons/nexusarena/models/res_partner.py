from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #Usamos el modelo contactos de Odoo y a partir de ahí añadimos el resto de campos
    #que nos interesen, en nuestro caso, los relacionados con los participantes



    # ----- Atributos de los participantes -----
    tipo_jugador = fields.Selection([
        ('jugador', 'Jugador Individual'),
        ('equipo', 'Equipo Competitivo'),
    ], string="Tipo de Jugador")
    nick = fields.Char(string="Nick / Nombre Equipo")
    pais_origen = fields.Char(string="País de Origen")
    plataforma = fields.Selection([
        ('pc', 'PC'), ('console', 'Consola'), ('mobile', 'Móvil')
    ], string="Plataforma")
    experiencia = fields.Selection([
        ('amateur', 'Amateur'), ('pro', 'Profesional'), ('semi', 'Semiprofesional')
    ], string="Nivel de Experiencia")
    equipo_id = fields.Many2one(
        'res.partner',
        string='Equipo',
        domain=[('tipo_jugador', '=', 'equipo')],
    )
    jugador_ids = fields.One2many(
        'res.partner',
        'equipo_id',
        string='Jugadores integrantes',
    )




    # ----- Relaciones -----
    juego_principal_id = fields.Many2one('esports.game', string='Juego principal')
    inscripcion_ids = fields.One2many('esports.registration', 'participante_id', string='Inscripciones')
    clasificacion_ids = fields.One2many('esports.standing', 'participante_id', string='Clasificaciones')
    partida_local_ids = fields.One2many('esports.match', 'participante_local', string='Partidas como local')
    partida_visitante_ids = fields.One2many('esports.match', 'participante_visitante', string='Partidas como visitante')
    partida_arbitro_ids = fields.Many2many(
        'esports.match',
        'esports_match_referee_rel',
        'partner_id',
        'match_id',
        string='Partidas arbitradas',
    )
    juego_gestionado_ids = fields.One2many('esports.game', 'gestor_id', string='Juegos gestionados')
    torneo_ids = fields.Many2many(
        'esports.tournament',
        'esports_tournament_partner_rel',
        'partner_id',
        'tournament_id',
        string='Torneos',
    )
    juego_ids = fields.Many2many(
        'esports.game',
        'esports_game_partner_rel',
        'partner_id',
        'game_id',
        string='Videojuegos',
    )
    miembro_en_inscripcion_ids = fields.Many2many(
        'esports.registration',
        'esports_registration_member_rel',
        'partner_id',
        'registration_id',
        string='Inscripciones como miembro de equipo',
    )





    # ----- Campos calculados -----
    # compute es para indicar que el valor de este campo se calcula a partir de otros campos, y store=True es para
    # almacenar el resultado en la base de datos y no tener que recalcularlo cada vez que se accede a él.
    total_participaciones = fields.Integer(string='Total participaciones', compute='_compute_stats', store=True)
    total_victorias = fields.Integer(string='Total victorias (1er puesto)', compute='_compute_stats', store=True)

    # api.depends es para indicar que el valor de este campo se calcula a partir de otros campos y ahi debemos de indicar que campos son esos
    @api.depends('inscripcion_ids', 'clasificacion_ids.posicion_final')

    # self es para referirnos al modelo actual a la hora de calcular el valor de los campos calculados.
    def _compute_stats(self):

        # rec es para referirnos a cada registro individual dentro del modelo.
        for rec in self:
            rec.total_participaciones = len(rec.inscripcion_ids)
            rec.total_victorias = len([c for c in rec.clasificacion_ids if c.posicion_final == 1])