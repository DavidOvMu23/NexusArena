from odoo import models, fields

class EsportsStanding(models.Model):
    # Nombre del modelo y descripción
    _name = 'esports.standing'
    _description = 'Clasificación del Torneo'
    
    # Campos
    posicion_final = fields.Integer(string="Posición Final")

    # Campos calculados para una proxima entrega
    # partidas_jugadas
    # partidas_ganadas
    # partidas_perdidas
    # puntos_acumulados
    # premio_obtenido

    # Relaciones que hice sin darme cuenta que eran para otra entrega
    torneo_id = fields.Many2one('esports.tournament', string="Torneo", required=True)
    participante_id = fields.Many2one('res.partner', string="Participante", required=True)
    factura_id = fields.Many2one('account.move', string="Factura de Premio", readonly=True)