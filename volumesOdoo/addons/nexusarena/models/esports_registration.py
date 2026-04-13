from odoo import models, fields


class EsportsRegistration(models.Model):

    # Nombre del modelo y descripción
    _name = 'esports.registration'
    _description = 'Inscripción de Participante'

    # Campos de la inscripción de un participante a un torneo.
    fecha_inscripcion = fields.Date(string="Fecha Inscripción", default=fields.Date.context_today)

    estado = fields.Selection([
        ('pending', 'Pendiente de Pago'), ('confirmed', 'Confirmada'), ('disqualified', 'Descalificada')
    ], default='pending')

    # Campos calculados para una proxima entrega
    # dias_desde_inscripcion

    # la restricción que pide el enunciado de que un participante no pueda 
    # inscribirse dos veces en el mismo torneo no se hacela todavía, de momento no lo pongo

    # Relaciones
    torneo_id = fields.Many2one('esports.tournament', string="Torneo", required=True)
    participante_id = fields.Many2one('res.partner', string="Participante", required=True)
    standing_ids = fields.One2many('esports.standing', 'inscripcion_id', string='Clasificación asociada')
    miembro_ids = fields.Many2many(
        'res.partner',
        'esports_registration_member_rel',
        'registration_id',
        'partner_id',
        string='Miembros del equipo',
    )