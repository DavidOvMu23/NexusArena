from odoo import models, fields

class EsportsRegistration(models.Model):

    # Nombre del modelo y descripción
    _name = 'esports.registration'
    _description = 'Inscripción de Participante'

    # Campos
    fecha_inscripcion = fields.Date(string="Fecha Inscripción", default=fields.Date.context_today)
    
    estado = fields.Selection([
        ('pending', 'Pendiente de Pago'), ('confirmed', 'Confirmada'), ('disqualified', 'Descalificada')
    ], default='pending')

    # Relaciones
    torneo_id = fields.Many2one('esports.tournament', string="Torneo", required=True)
    participante_id = fields.Many2one('res.partner', string="Participante", required=True)