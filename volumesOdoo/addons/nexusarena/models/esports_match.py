from odoo import fields, models, api
from odoo.exceptions import UserError


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

	ganador_id = fields.Many2one('res.partner', string='Ganador', compute='_compute_ganador', store=True)

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

	# campos calculados

	# El método _compute_ganador calcula el ganador de la partida en función de las puntuaciones locales y visitantes.
	# Si alguna de las puntuaciones es None, el ganador se establece como False. 
	#Si la puntuación local es mayor que la visitante, el ganador es el participante local; si la puntuación visitante es mayor, 
	#el ganador es el participante visitante; si ambas puntuaciones son iguales, el ganador se establece como False (empate).
	@api.depends('puntuacion_local', 'puntuacion_visitante', 'participante_local', 'participante_visitante')
	def _compute_ganador(self):
		for rec in self:
			if rec.puntuacion_local is None or rec.puntuacion_visitante is None:
				rec.ganador_id = False
			elif rec.puntuacion_local > rec.puntuacion_visitante:
				rec.ganador_id = rec.participante_local
			elif rec.puntuacion_local < rec.puntuacion_visitante:
				rec.ganador_id = rec.participante_visitante
			else:
				rec.ganador_id = False

	# El método action_register_result se encarga de registrar el resultado de la partida, marcándola como finalizada,
	# determinando el ganador en función de las puntuaciones, asegurando que exista un standing para cada participante 
	# y añadiendo la partida a su lista de partidas jugadas, y publicando
	# un mensaje en el hilo del torneo indicando que se ha registrado el resultado para esa partida.
	def action_register_result(self):
		for rec in self:
			if rec.puntuacion_local is None or rec.puntuacion_visitante is None:
				raise UserError('Rellene las puntuaciones antes de registrar el resultado.')

			# Determinar ganador
			if rec.puntuacion_local > rec.puntuacion_visitante:
				winner = rec.participante_local
			elif rec.puntuacion_local < rec.puntuacion_visitante:
				winner = rec.participante_visitante
			else:
				winner = False

			# Marcamos la partida como finalizada; el campo ganador se calcula automáticamente
			rec.state = 'finished'

			# Aseguramos que exista un standing por participante y añadimos la partida a su lista
			Standing = self.env['esports.standing']
			for participant in (rec.participante_local, rec.participante_visitante):
				if not participant:
					continue
				st = Standing.search([('torneo_id', '=', rec.torneo_id.id), ('participante_id', '=', participant.id)], limit=1)
				if not st:
					st = Standing.create({'torneo_id': rec.torneo_id.id, 'participante_id': participant.id})
				st.write({'partida_ids': [(4, rec.id)]})

			# Mensaje en el hilo del torneo
			rec.torneo_id.message_post(body='Resultado registrado para la partida %s' % (rec.id,))