from odoo import models, fields

class EsportsStanding(models.Model):
    # Nombre del modelo y descripción
    _name = 'esports.standing'
    _description = 'Clasificación del Torneo'
    
    # Campos
    posicion = fields.Integer(string="Posición Final")
    partidas_jugadas = fields.Integer(string="Partidas Jugadas")
    partidas_ganadas = fields.Integer(string="Ganadas")
    partidas_perdidas = fields.Integer(string="Perdidas")
    puntos_acumulados = fields.Integer(string="Puntos Totales")

    # Relaciones
    torneo_id = fields.Many2one('esports.tournament', string="Torneo", required=True)
    participante_id = fields.Many2one('res.partner', string="Participante", required=True)
    factura_id = fields.Many2one('account.move', string="Factura de Premio", readonly=True)