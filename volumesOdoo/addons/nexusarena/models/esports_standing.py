from odoo import models, fields


class EsportsStanding(models.Model):
    # Tabla de clasificación final de participantes por torneo.
    _name = 'esports.standing'
    _description = 'Clasificación del Torneo'
    
    # Campos
    posicion_final = fields.Integer(string="Posición Final")

    # Relaciones
    torneo_id = fields.Many2one('esports.tournament', string="Torneo", required=True)
    participante_id = fields.Many2one('res.partner', string="Participante", required=True)
    inscripcion_id = fields.Many2one('esports.registration', string='Inscripción')
    partida_final_id = fields.Many2one('esports.match', string='Partida final')
    parent_standing_id = fields.Many2one('esports.standing', string='Clasificación padre')
    child_standing_ids = fields.One2many('esports.standing', 'parent_standing_id', string='Subclasificaciones')
    partida_ids = fields.Many2many(
        'esports.match',
        'esports_standing_match_rel',
        'standing_id',
        'match_id',
        string='Partidas computadas',
    )
    factura_id = fields.Many2one('account.move', string="Factura de Premio", readonly=True)

    # Campos calculados para una proxima entrega
    # partidas_jugadas
    # partidas_ganadas
    # partidas_perdidas
    # puntos_acumulados
    # premio_obtenido
