from odoo import models, fields, api
from odoo.exceptions import UserError


class EsportsRegistration(models.Model):

    # Nombre del modelo y descripción
    _name = 'esports.registration'
    _description = 'Inscripción de Participante'

    # Campos de la inscripción de un participante a un torneo.
    fecha_inscripcion = fields.Date(string="Fecha Inscripción", default=fields.Date.context_today)

    state = fields.Selection([
        ('pending', 'Pendiente de Pago'), ('confirmed', 'Confirmada'), ('disqualified', 'Descalificada')
    ], default='pending')

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

    # Campos calculados
    #Compute es para indicar que el valor de este campo se calcula a partir de otros campos, y store=True es para 
    #almacenar el resultado en la base de datos y no tener que recalcularlo cada vez que se accede a él.
    dias_desde_inscripcion = fields.Integer(string='Días desde inscripción', compute='_compute_dias_desde_inscripcion', store=True)

    # api.depends es para indicar que el valor de este campo se calcula a partir de otros campos y ahi debemos de indicar que campos son esos
    # self es para referirnos al modelo actual a la hora de calcular el valor de los campos calculados.

    #aqui lo que hacemos es sobreescribir el método create para añadir una validación que impida que un mismo participante 
    #se inscriba varias veces en el mismo torneo.
    @api.model_create_single
    def create(self, vals):
        torneo_id = vals.get('torneo_id')
        participante_id = vals.get('participante_id')
        if torneo_id and participante_id:
            exists = self.search([('torneo_id', '=', torneo_id), ('participante_id', '=', participante_id)], limit=1)
            if exists:
                raise UserError('El participante ya está inscrito en este torneo.')
        return super(EsportsRegistration, self).create(vals)


    # Calculamos los días transcurridos desde la fecha de inscripción hasta hoy para mostrar esta 
    # información en la vista del formulario de inscripción.
    @api.depends('fecha_inscripcion')
    def _compute_dias_desde_inscripcion(self):
        for rec in self:
            if not rec.fecha_inscripcion:
                rec.dias_desde_inscripcion = 0
                continue
            today = fields.Date.context_today(self)

            # El cálculo se realiza restando la fecha de inscripción a la fecha actual, 
            # utilizando fields.Date.from_string para convertir las fechas a objetos de fecha y luego obteniendo el
            rec.dias_desde_inscripcion = (
                fields.Date.from_string(today) - fields.Date.from_string(rec.fecha_inscripcion)
            ).days


    # Acción para confirmar la inscripción, que genera una factura de venta para la cuota de inscripción del torneo.
    def action_confirm_registration(self):
        self.ensure_one()
        if self.state != 'pending':
            raise UserError('Solo se pueden confirmar inscripciones en estado Pendiente de Pago.')

        # Obtener el monto de la cuota de inscripción del torneo
        tournament = self.torneo_id
        amount = tournament.cuota_inscripcion or 0.0

        # Buscar diario de ventas
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            journal = self.env['account.journal'].search([], limit=1)
        if not journal:
            raise UserError('No hay ningún diario configurado. Configure un diario para crear la factura.')

        # Determinar cuenta contable para la línea
        account_id = False
        if getattr(journal, 'default_account_id', False):
            account_id = journal.default_account_id.id
        elif getattr(self.participante_id, 'property_account_receivable_id', False):
            account_id = self.participante_id.property_account_receivable_id.id
        else:
            acc = self.env['account.account'].search([], limit=1)
            if acc:
                account_id = acc.id

        if not account_id:
            raise UserError('No se pudo determinar una cuenta contable para la factura. Revise la configuración contable.')

        # Crear los valores para la factura de cuota de inscripción, incluyendo el tipo de movimiento, el cliente, la fecha, 
        #el diario, el origen y las líneas de factura con la descripción de la cuota y el importe.
        move_vals = { 
            'move_type': 'out_invoice',
            'partner_id': self.participante_id.id,
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal.id,
            'invoice_origin': tournament.nombre,
            'invoice_line_ids': [(0, 0, {
                'name': 'Cuota inscripción %s' % (tournament.nombre or ''),
                'quantity': 1.0,
                'price_unit': amount,
                'account_id': account_id,
            })],
        }

        # Crear la factura de cuota de inscripción utilizando el modelo account.move y los valores definidos anteriormente.
        invoice = self.env['account.move'].create(move_vals)

        # Marcar como confirmada y añadir participante al torneo
        self.state = 'confirmed'
        if self.participante_id and tournament:
            tournament.write({'participante_ids': [(4, self.participante_id.id)]})

        # Mensajes de seguimiento
        try:
            invoice.message_post(body='Factura generada automáticamente para la inscripción %s' % (self.id,))
            self.message_post(body='Inscripción confirmada y factura %s creada.' % (invoice.name or invoice.id,))
        except Exception:
            pass

        return invoice