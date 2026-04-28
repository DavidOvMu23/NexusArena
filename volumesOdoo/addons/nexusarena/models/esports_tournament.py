from odoo import models, fields, api
from odoo.exceptions import UserError


class EsportsTournament(models.Model):
    # Modelo torneos.
    _name = 'esports.tournament'
    _inherit = ['mail.thread']
    _description = 'Torneo de eSports'
    _rec_name = 'nombre'

    # Datos de el torneo
    nombre = fields.Char(string="Nombre del Torneo")
    edicion = fields.Char(string="Edición (Año)")

    formato = fields.Selection([
        ('league', 'Liga'),
        ('direct', 'Eliminación Directa'),
        ('double', 'Doble Eliminación'),
    ], string="Formato", default='league')

    modalidad = fields.Selection([
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('hibrido', 'Híbrido'),
    ], string="Modalidad")

    fecha_inicio = fields.Date(string="Fecha de Inicio")
    fecha_fin = fields.Date(string="Fecha de Fin")

    premio_total = fields.Float(string="Premio Total (€)")
    premio_1 = fields.Float(string="1er Puesto (€)")
    premio_2 = fields.Float(string="2º Puesto (€)")
    premio_3 = fields.Float(string="3er Puesto (€)")

    cuota_inscripcion = fields.Float(string="Cuota de Inscripción")

    # state del torneo.
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Inscripciones Abiertas'),
        ('ongoing', 'En Curso'),
        ('done', 'Finalizado'),
        ('cancel', 'Cancelado')
    ], string="state", default='draft')

    # Relaciones
    videojuego_id = fields.Many2one('esports.game', string="Videojuego", required=True)
    videojuego_imagen = fields.Image(related='videojuego_id.imagen', string='Imagen del juego', readonly=True)
    inscripcion_ids = fields.One2many('esports.registration', 'torneo_id', string="Líneas de Inscripción")
    partida_ids = fields.One2many('esports.match', 'torneo_id', string="Partidas del Torneo")
    standing_ids = fields.One2many('esports.standing', 'torneo_id', string='Clasificación final')
    participante_ids = fields.Many2many(
        'res.partner',
        'esports_tournament_partner_rel',
        'tournament_id',
        'partner_id',
        string='Participantes',
    )

    # Campos calculados
    # compute es para indicar que el valor de este campo se calcula a partir de otros campos, y store=True es para
    # almacenar el resultado en la base de datos y no tener que recalcularlo cada vez que se accede a él.
    inscripciones_count = fields.Integer(string='Líneas de inscripción', compute='_compute_statistics', store=True)
    partidas_count = fields.Integer(string='Partidas del torneo', compute='_compute_statistics', store=True)
    numero_participantes = fields.Integer(string='Número de participantes', compute='_compute_statistics', store=True)
    ingresos_totales = fields.Float(string='Ingresos totales', compute='_compute_statistics', store=True)


    # api.depends es para indicar que el valor de este campo se calcula a partir de otros campos y ahi debemos de indicar que campos son esos
    @api.depends('inscripcion_ids', 'partida_ids', 'cuota_inscripcion')

    # self es para referirnos al modelo actual a la hora de calcular el valor de los campos calculados.
    def _compute_statistics(self):
        for rec in self:

            # rec es para referirnos a cada registro individual dentro del modelo.
            rec.inscripciones_count = len(rec.inscripcion_ids)
            rec.partidas_count = len(rec.partida_ids)
            rec.numero_participantes = rec.inscripciones_count
            rec.ingresos_totales = rec.numero_participantes * (rec.cuota_inscripcion or 0.0)

    # Acciones para cambiar el estado del torneo y notificar a los participantes.
    def action_open_inscriptions(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Solo se puede abrir inscripciones desde el estado Borrador.')
            rec.state = 'open'

    def action_start_tournament(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError('El torneo debe tener las inscripciones abiertas para iniciarse.')
            if rec.numero_participantes < 2:
                raise UserError('Se necesitan al menos 2 participantes inscritos para iniciar el torneo.')
            rec.state = 'ongoing'

    def action_finalize_tournament(self):
        for rec in self:
            if rec.state not in ('ongoing', 'open'):
                raise UserError('Solo se puede finalizar un torneo que esté en curso o con inscripciones abiertas.')
            rec.state = 'done'

    def action_notify_participants(self, subject=None, body=None):
        subject = subject or 'Notificación del torneo'
        for rec in self:
            if not rec.participante_ids:
                continue
            msg = body or ('Notificación del torneo %s (estado: %s)' % (rec.nombre or '', rec.state or ''))
            
            # Enviamos un mensaje a cada participante (esto crea mail.message y notifica al partner)
            for partner in rec.participante_ids:
                try:
                    partner.message_post(body=msg, subject=subject)
                except Exception:
                    continue

    def write(self, vals):
        # Bloquear edición de torneos finalizados para usuarios no administradores
        for rec in self:
            if rec.state == 'done' and not self.env.user.has_group('nexusarena.group_tourney_admin'):
                raise UserError('El torneo está finalizado y no puede ser editado.')
        return super(EsportsTournament, self).write(vals)

    def unlink(self):
        # Bloquear eliminación de torneos finalizados para usuarios no administradores
        for rec in self:
            if rec.state == 'done' and not self.env.user.has_group('nexusarena.group_tourney_admin'):
                raise UserError('El torneo está finalizado y no puede ser eliminado.')
        return super(EsportsTournament, self).unlink()