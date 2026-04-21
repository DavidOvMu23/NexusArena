from odoo import fields, models


class EsportsMatch(models.Model):
	# Nombre del modelo y descripción
	_name = 'esports.match'
	_description = 'Partida de eSports'

	# Campos de la partida.
	fase = fields.Selection([
		('groups', 'Grupos'),
		('quarterfinal', 'Cuartos'),
		('semifinal', 'Semifinal'),
		('final', 'Final'),
		('third_place', 'Tercer puesto'),
	], string='Fase')

	fecha_hora_programada = fields.Datetime(string='Fecha y hora programada')

	# state de la partida.
	state = fields.Selection([
		('scheduled', 'Programada'),
		('playing', 'En juego'),
		('finished', 'Finalizada'),
		('walkover', 'Walkover'),
	], string='state', default='scheduled')

	resultado = fields.Integer(string='Resultado')
	puntuacion_local = fields.Integer(string='Puntuación local')
	puntuacion_visitante = fields.Integer(string='Puntuación visitante')

	# Relaciones
	torneo_id = fields.Many2one('esports.tournament', string='Torneo')
	participante_local = fields.Many2one('res.partner', string='Participante local')
	participante_visitante = fields.Many2one('res.partner', string='Participante visitante')
	standing_ids = fields.One2many('esports.standing', 'partida_final_id', string='Clasificación asociada')
	standing_computado_ids = fields.Many2many(
		'esports.standing',
		'esports_standing_match_rel',
		'match_id',
		'standing_id',
		string='Clasificaciones donde computa',
	)
	arbitro_ids = fields.Many2many(
		'res.partner',
		'esports_match_referee_rel',
		'match_id',
		'partner_id',
		string='Árbitros',
	)

	# campos calculados para una proxima entrega
	# ganador