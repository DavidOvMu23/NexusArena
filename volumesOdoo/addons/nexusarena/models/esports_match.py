from odoo import api, fields, models
from odoo.exceptions import ValidationError

class EsportsMatch(models.Model):
    # Nombre del modelo y descripción
	_name = 'esports.match'
	_description = 'Partida de eSports'

    # Campos
	fase = fields.Selection([
		('groups', 'Grupos'),
		('quarterfinal', 'Cuartos'),
		('semifinal', 'Semifinal'),
		('final', 'Final'),
		('third_place', 'Tercer puesto'),
	], string='Fase')

	fecha_hora_programada = fields.Datetime(string='Fecha y hora programada')

	estado = fields.Selection([
		('scheduled', 'Programada'),
		('playing', 'En juego'),
		('finished', 'Finalizada'),
		('walkover', 'Walkover'),
	], string='Estado', default='scheduled')

	resultado = fields.integer(string='Resultado')
	puntuacion_local = fields.Integer(string='Puntuación local')
	puntuacion_visitante = fields.Integer(string='Puntuación visitante')
	
    #campos calculados para una proxima entrega
    #ganador

    # Relaciones que hice sin darme cuenta que eran para otra entrega
torneo_id = fields.Many2one('esports.tournament', string="Torneo")
participante_local = fields.Many2one('res.partner', string='Participante local')
participante_visitante = fields.Many2one('res.partner', string='Participante visitante')