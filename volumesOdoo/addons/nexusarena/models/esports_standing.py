from odoo import models, fields, api
from odoo.exceptions import UserError


class EsportsStanding(models.Model):
    # Tabla de clasificación final de participantes por torneo.
    _name = 'esports.standing'
    _inherit = ['mail.thread']
    _description = 'Clasificación del Torneo'
    _inherit = ['mail.thread']
    
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

    # Campos calculados
    # Compute es para indicar que el valor de este campo se calcula a partir de otros campos, y store=True es para 
    # almacenar el resultado en la base de datos y no tener que recalcularlo cada vez que se accede a él.
    partidas_jugadas = fields.Integer(string='Partidas jugadas', compute='_compute_stats', store=True)
    partidas_ganadas = fields.Integer(string='Partidas ganadas', compute='_compute_stats', store=True)
    partidas_perdidas = fields.Integer(string='Partidas perdidas', compute='_compute_stats', store=True)
    puntos_acumulados = fields.Integer(string='Puntos acumulados', compute='_compute_stats', store=True)
    premio_obtenido = fields.Float(string='Premio obtenido', compute='_compute_premio', store=True)

    # api.depends es para indicar que el valor de este campo se calcula a partir de otros campos y ahi debemos de indicar que campos son esos
    @api.depends('partida_ids.ganador_id', 'partida_ids.state')

    # self es para referirnos al modelo actual a la hora de calcular el valor de los campos calculados.
    def _compute_stats(self):

        for rec in self:
            # rec es para referirnos a cada registro individual dentro del modelo.
            finished = [m for m in rec.partida_ids if m.state == 'finished']
            rec.partidas_jugadas = len(finished)
            rec.partidas_ganadas = sum(1 for m in finished if m.ganador_id and m.ganador_id.id == rec.participante_id.id)
            ties = sum(1 for m in finished if not m.ganador_id)
            rec.partidas_perdidas = rec.partidas_jugadas - rec.partidas_ganadas - ties
            rec.puntos_acumulados = rec.partidas_ganadas * 3 + ties

    # El método _compute_premio calcula el premio obtenido por el participante en función de su posición 
    #final en el torneo y los premios definidos para esa posición en el torneo.
    @api.depends('posicion_final', 'torneo_id.premio_1', 'torneo_id.premio_2', 'torneo_id.premio_3')
    def _compute_premio(self):
        for rec in self:
            premios = {
                1: rec.torneo_id.premio_1 or 0.0,
                2: rec.torneo_id.premio_2 or 0.0,
                3: rec.torneo_id.premio_3 or 0.0,
            }
            rec.premio_obtenido = premios.get(rec.posicion_final, 0.0)

    # El método action_generate_prize_invoice se encarga de generar una factura de premio para el participante 
    # en función del premio obtenido por su posición final en el torneo.
    def action_generate_prize_invoice(self):
        for rec in self:
            if rec.torneo_id.state != 'done':
                raise UserError('Solo se puede generar factura de premio cuando el torneo está finalizado.')
            if rec.factura_id:
                raise UserError('Ya existe una factura de premio para esta clasificación.')
            if not rec.participante_id:
                raise UserError('Debe indicar el participante para generar la factura de premio.')
            if not rec.posicion_final:
                raise UserError('Debe indicar la posición final para calcular el premio.')
            # El importe del premio se obtiene del campo premio_obtenido calculado previamente. 
            #Si el importe es cero o negativo, se lanza un error indicando que no hay premio asignado para esa posición.
            amount = rec.premio_obtenido or 0.0
            if amount <= 0.0:
                raise UserError('No hay premio asignado para esta posición.')

            # Buscar un diario de ventas o de reembolsos para generar la factura. Si no se encuentra, se lanza un error.
            journal = self.env['account.journal'].search([('type', 'in', ('sale_refund', 'sale'))], limit=1)
            if not journal:
                raise UserError('No hay diario de ventas/configurado para generar la factura de premio.')

            # Determinar la cuenta contable a usar para la línea de factura. Se intenta obtener del diario, luego del participante, y si no se encuentra, se busca cualquier cuenta contable disponible.        
            account = journal.default_account_id or rec.participante_id.property_account_receivable_id or self.env['account.account'].search([], limit=1)
            if not account:
                raise UserError('No se pudo determinar una cuenta contable para la factura.')

            # Crear los valores para la factura de premio, incluyendo el tipo de movimiento, el cliente, la fecha, el diario, el origen y las líneas de factura con la descripción del premio y el importe.
            move_vals = {
                'move_type': 'out_refund',
                'partner_id': rec.participante_id.id,
                'invoice_date': fields.Date.context_today(self),
                'journal_id': journal.id,
                'invoice_origin': 'Premio %s - %s' % (rec.torneo_id.nombre or '', rec.participante_id.name or ''),
                'invoice_line_ids': [(0, 0, {
                    'name': 'Premio posición %s' % (rec.posicion_final or ''),
                    'quantity': 1.0,
                    'price_unit': amount,
                    'account_id': account.id,
                })],
            }

            # Crear la factura de premio y vincularla al registro de clasificación. 
            #Luego se publica un mensaje en el registro de clasificación y en la factura para 
            #informar sobre la generación de la factura de premio.
            invoice = self.env['account.move'].create(move_vals)
            rec.factura_id = invoice.id
            invoice.message_post(body='Factura de premio generada automáticamente para %s' % (rec.participante_id.name,))
            rec.message_post(body='Factura de premio generada: %s' % (invoice.name or invoice.id,))
