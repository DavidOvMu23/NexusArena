from odoo import fields, models, api
from odoo.exceptions import UserError


class EsportsMatch(models.Model):
	# Nombre del modelo y descripción
	_name = 'esports.match'
	_description = 'Partida de eSports'
	_inherit = ['mail.thread']



	# ----- Atributos de la partida -----
	fase = fields.Selection([
		('groups', 'Grupos'),
		('quarterfinal', 'Cuartos'),
		('semifinal', 'Semifinal'),
		('final', 'Final'),
		('third_place', 'Tercer puesto'),
	], string='Fase')
	fecha_hora_programada = fields.Datetime(string='Fecha y hora programada')
	state = fields.Selection([
		('scheduled', 'Programada'),
		('playing', 'En juego'),
		('finished', 'Finalizada'),
		('walkover', 'Walkover'),
	], string='state', default='scheduled')
	# Marcador legible calculado a partir de las puntuaciones (p. ej. "5 - 0").
	# Vacío mientras la partida sigue en estado "programada" (aún no se ha jugado).
	resultado = fields.Char(string='Resultado', compute='_compute_resultado', store=True)
	puntuacion_local = fields.Integer(string='Puntuación local')
	puntuacion_visitante = fields.Integer(string='Puntuación visitante')
	ganador_id = fields.Many2one('res.partner', string='Ganador', compute='_compute_ganador', store=True)

	# Nombre legible para mostrar en la vista de calendario.
	# Sin este campo, Odoo usa "esports.match,<id>" porque el modelo no define name.
	display_name = fields.Char(string='Nombre', compute='_compute_display_name', store=False)




	# ----- Relaciones -----
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

	# ----- Enlaces de bracket (los rellena el wizard de generación de bracket) -----
	# Cuando una partida finaliza, su ganador se escribe automáticamente en el campo
	# indicado de "siguiente_partida_id". Si la partida es una semifinal y existe
	# "partida_tercer_puesto_id", el perdedor se propaga al 3er puesto.
	siguiente_partida_id = fields.Many2one(
		'esports.match',
		string='Siguiente partida del bracket',
		ondelete='set null',
		help='Partida a la que pasa el ganador automáticamente al registrar el resultado.',
	)
	siguiente_slot = fields.Selection([
		('local', 'Local'),
		('visitante', 'Visitante'),
	], string='Slot del ganador')
	partida_tercer_puesto_id = fields.Many2one(
		'esports.match',
		string='Partida 3er puesto',
		ondelete='set null',
		help='Partida del 3er puesto a la que pasa el perdedor (solo para semifinales).',
	)
	tercer_puesto_slot = fields.Selection([
		('local', 'Local'),
		('visitante', 'Visitante'),
	], string='Slot del perdedor (3er puesto)')




	# ----- Campos calculados -----
	# aqui comprobamos que el torneo seleccionado en la partida tenga como participantes a los participantes local y visitante,
	# y si no es así, se devuelve un dominio vacío para ambos campos de participante, 
	# lo que obliga al usuario a seleccionar participantes válidos dentro del torneo seleccionado.
	@api.onchange('torneo_id')
	def _onchange_torneo_id(self):
		domain = [('id', 'in', self.torneo_id.participante_ids.ids)] if self.torneo_id else []
		return {'domain': {'participante_local': domain, 'participante_visitante': domain}}

	# El método _compute_ganador calcula el ganador de la partida en función de las puntuaciones locales y visitantes.
	# Si alguna de las puntuaciones es None, el ganador se establece como False. 
	#Si la puntuación local es mayor que la visitante, el ganador es el participante local; si la puntuación visitante es mayor, 
	#el ganador es el participante visitante; si ambas puntuaciones son iguales, el ganador se establece como False (empate).
	# Componemos un nombre legible: "<Fase>: <Local> vs <Visitante>". Si faltan
	# participantes (placeholder de bracket), mostramos "Por definir" para no
	# romper la cadena. Si tampoco hay fase, caemos al nombre del torneo.
	@api.depends('fase', 'participante_local', 'participante_visitante', 'torneo_id')
	def _compute_display_name(self):
		fase_labels = dict(self._fields['fase'].selection)
		for rec in self:
			fase = fase_labels.get(rec.fase) if rec.fase else False
			local = rec.participante_local.name if rec.participante_local else 'Por definir'
			visit = rec.participante_visitante.name if rec.participante_visitante else 'Por definir'
			if fase:
				rec.display_name = '%s: %s vs %s' % (fase, local, visit)
			elif rec.torneo_id:
				rec.display_name = '%s: %s vs %s' % (rec.torneo_id.nombre or 'Partida', local, visit)
			else:
				rec.display_name = '%s vs %s' % (local, visit)

	# Componemos el marcador como "X - Y" usando las puntuaciones. Mientras la
	# partida esté programada (aún sin jugar) lo dejamos vacío para no mostrar
	# un engañoso "0 - 0" en el calendario y formularios.
	@api.depends('puntuacion_local', 'puntuacion_visitante', 'state')
	def _compute_resultado(self):
		for rec in self:
			if rec.state == 'scheduled':
				rec.resultado = ''
			else:
				rec.resultado = '%s - %s' % (rec.puntuacion_local or 0, rec.puntuacion_visitante or 0)

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




		# ----- Restricciones -----
		# La restricción _check_torneo_ongoing asegura que solo se puedan crear partidas asociadas a torneos que estén en estado 'ongoing' o 'done'.
	@api.constrains('torneo_id')
	def _check_torneo_ongoing(self):
		for rec in self:
			if rec.torneo_id and rec.torneo_id.state not in ('ongoing', 'done'):
				raise UserError('Solo se pueden crear partidas en un torneo en curso.')

		# La restricción _check_different_participants asegura que el participante local y el visitante no sean el mismo para una partida.
	@api.constrains('participante_local', 'participante_visitante')
	def _check_different_participants(self):
		for rec in self:
			if rec.participante_local and rec.participante_visitante:
				if rec.participante_local == rec.participante_visitante:
					raise UserError('El participante local y el visitante no pueden ser el mismo.')

		# La restricción _check_unique_participant_per_phase asegura que un participante no pueda estar en múltiples partidas en la misma fase.
	@api.constrains('torneo_id', 'fase', 'participante_local', 'participante_visitante')
	def _check_unique_participant_per_phase(self):
		for rec in self:
			if not rec.torneo_id or not rec.fase:
				continue
			for participante in [rec.participante_local, rec.participante_visitante]:
				if not participante:
					continue
				duplicate = self.search([
					('id', '!=', rec.id),
					('torneo_id', '=', rec.torneo_id.id),
					('fase', '=', rec.fase),
					'|',
					('participante_local', '=', participante.id),
					('participante_visitante', '=', participante.id),
				], limit=1)
				if duplicate:
					raise UserError(
						'El participante "%s" ya tiene una partida en la fase "%s" de este torneo.'
						% (participante.name, dict(self._fields['fase'].selection).get(rec.fase, rec.fase))
					)

	# La restricción _check_non_negative_scores asegura que las puntuaciones locales y visitantes no sean negativas.
	@api.constrains('puntuacion_local', 'puntuacion_visitante')
	def _check_non_negative_scores(self):
		for rec in self:
			if rec.puntuacion_local is not None and rec.puntuacion_local < 0:
				raise UserError('La puntuación local no puede ser negativa.')
			if rec.puntuacion_visitante is not None and rec.puntuacion_visitante < 0:
				raise UserError('La puntuación visitante no puede ser negativa.')




	# ----- Métodos de acción -----
	# El método action_start_match se encarga de iniciar la partida, cambiando su estado a 'playing' solo si la partida está programada y el torneo asociado está en curso.
	def action_start_match(self):
		for rec in self:
			if rec.state != 'scheduled':
				raise UserError('Solo se puede iniciar una partida que esté programada.')
			if rec.torneo_id.state != 'ongoing':
				raise UserError('El torneo debe estar en curso para iniciar una partida.')
			rec.state = 'playing'

	# El método action_register_result se encarga de registrar el resultado de la partida, marcándola como finalizada,
	# determinando el ganador en función de las puntuaciones, asegurando que exista un standing para cada participante 
	# y añadiendo la partida a su lista de partidas jugadas, y publicando
	# un mensaje en el hilo del torneo indicando que se ha registrado el resultado para esa partida.
	def action_register_result(self):
		for rec in self:
			if rec.torneo_id.state == 'done':
				raise UserError('No se puede registrar resultado en un torneo finalizado.')
			if rec.torneo_id.state == 'cancel':
				raise UserError('No se puede registrar resultado en un torneo cancelado.')
			if rec.torneo_id.state != 'ongoing':
				raise UserError('Solo se pueden registrar resultados con el torneo en curso.')
			if rec.state in ('finished', 'walkover'):
				raise UserError('Esta partida ya está cerrada y no admite nuevos resultados.')
			if not rec.participante_local or not rec.participante_visitante:
				raise UserError('Debe definir participante local y visitante antes de registrar resultado.')
			if rec.participante_local.id == rec.participante_visitante.id:
				raise UserError('Local y visitante no pueden ser el mismo participante.')
			if rec.puntuacion_local is None or rec.puntuacion_visitante is None:
				raise UserError('Rellene las puntuaciones antes de registrar el resultado.')
			if rec.puntuacion_local < 0 or rec.puntuacion_visitante < 0:
				raise UserError('Las puntuaciones no pueden ser negativas.')

			# Determinar ganador
			if rec.puntuacion_local > rec.puntuacion_visitante:
				winner = rec.participante_local
				loser = rec.participante_visitante
			elif rec.puntuacion_local < rec.puntuacion_visitante:
				winner = rec.participante_visitante
				loser = rec.participante_local
			else:
				winner = False
				loser = False

			# En una partida del bracket no puede haber empate: si hay siguiente
			# partida enlazada y el resultado es empate, no se puede continuar.
			if rec.siguiente_partida_id and not winner:
				raise UserError(
					'Esta partida pertenece al cuadro de eliminatorias y no admite empate. '
					'Ajuste las puntuaciones para que haya un ganador.'
				)

			# Marcamos la partida como finalizada; el campo ganador se calcula automáticamente
			rec.state = 'finished'

			# Propagación automática al bracket: el ganador pasa a la siguiente
			# partida y, si la partida tiene enlace al 3er puesto (semifinales),
			# el perdedor pasa a esa partida también.
			if winner and rec.siguiente_partida_id and rec.siguiente_slot:
				slot_field = 'participante_local' if rec.siguiente_slot == 'local' else 'participante_visitante'
				rec.siguiente_partida_id.write({slot_field: winner.id})
				# Añadimos el ganador a los participantes del torneo por si no lo estaba ya
				if rec.torneo_id:
					rec.torneo_id.write({'participante_ids': [(4, winner.id)]})
				rec.torneo_id.message_post(
					body='Ganador propagado: %s pasa a la siguiente ronda (%s).'
					% (winner.name, dict(rec.siguiente_partida_id._fields['fase'].selection).get(
						rec.siguiente_partida_id.fase, rec.siguiente_partida_id.fase))
				)

			if loser and rec.partida_tercer_puesto_id and rec.tercer_puesto_slot:
				slot_field = 'participante_local' if rec.tercer_puesto_slot == 'local' else 'participante_visitante'
				rec.partida_tercer_puesto_id.write({slot_field: loser.id})
				rec.torneo_id.message_post(
					body='Perdedor propagado: %s pasa a la partida por el 3er puesto.' % loser.name
				)

			# Mensaje en el hilo del torneo
			rec.torneo_id.message_post(body='Resultado registrado para la partida %s' % (rec.id,))