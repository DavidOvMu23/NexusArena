from odoo import models, fields, api


class EsportsGame(models.Model):
    # Modelo de videojuegos
    _name = 'esports.game'
    _description = 'Videojuego de eSports'
    _rec_name = 'nombre'

    # Datos del videojuego.
    nombre = fields.Char(string="Nombre del Juego")

    genero = fields.Selection([
        ('moba', 'MOBA'), ('fps', 'FPS'), ('lucha', 'Lucha'),
        ('deportes', 'Deportes'), ('br', 'Battle Royale'), ('estrategia', 'Estrategia'), ('otro', 'Otro')
    ], string="Género")

    desarrollador = fields.Char(string="Desarrollador")

    modalidad = fields.Selection([
        ('individual', 'Individual'), ('teams', 'Equipos'), ('both', 'Ambas')
    ], string="Modalidad", default='both')

    max_jugadores_equipo = fields.Integer(string="Máx. Jugadores por Equipo")

    imagen = fields.Image(string="Logo/Imagen")

    # Relaciones
    gestor_id = fields.Many2one('res.partner', string='Responsable')
    torneo_ids = fields.One2many('esports.tournament', 'videojuego_id', string='Torneos')
    participante_ids = fields.Many2many(
        'res.partner',
        'esports_game_partner_rel',
        'game_id',
        'partner_id',
        string='Participantes frecuentes',
    )

    torneos_activos_count = fields.Integer(string='Número de torneos activos', compute='_compute_actives', store=True)

    # El método _compute_actives calcula el número de torneos activos asociados a este videojuego, 
    #contando aquellos torneos cuyo estado es 'open' o 'ongoing'.
    @api.depends('torneo_ids.state')
    def _compute_actives(self):
        for rec in self:
            rec.torneos_activos_count = len([t for t in rec.torneo_ids if t.state in ('open', 'ongoing')])