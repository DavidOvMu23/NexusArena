from odoo import models, fields, api
from odoo.exceptions import UserError


class EsportsStanding(models.Model):
    # Tabla de clasificación final de participantes por torneo.
    _name = 'esports.standing'
    _description = 'Clasificación del Torneo'
    _inherit = ['mail.thread']




    # ----- Atributos -----
    # La posición final se calcula automáticamente ordenando las clasificaciones
    # del mismo torneo por puntos acumulados (desc), partidas ganadas (desc) y, en
    # caso de empate total, por id de participante para mantener un orden estable.
    posicion_final = fields.Integer(
        string="Posición Final",
        compute='_compute_posicion_final',
        store=True,
        readonly=True,
    )






    # ----- Relaciones -----
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





    # ----- Campos calculados -----
    # Compute es para indicar que el valor de este campo se calcula a partir de otros campos, y store=True es para 
    # almacenar el resultado en la base de datos y no tener que recalcularlo cada vez que se accede a él.
    partidas_jugadas = fields.Integer(string='Partidas jugadas', compute='_compute_stats', store=True)
    partidas_ganadas = fields.Integer(string='Partidas ganadas', compute='_compute_stats', store=True)
    partidas_perdidas = fields.Integer(string='Partidas perdidas', compute='_compute_stats', store=True)
    puntos_acumulados = fields.Integer(string='Puntos acumulados', compute='_compute_stats', store=True)
    premio_obtenido = fields.Float(string='Premio obtenido', compute='_compute_premio', store=True)

    # este método se ejecuta cada vez que se cambia el torneo_id en el formulario de clasificación.
    # para actualizar el dominio del campo participante_id y mostrar solo los participantes inscritos en el torneo seleccionado.
    @api.onchange('torneo_id')
    def _onchange_torneo_id(self):
        domain = [('id', 'in', self.torneo_id.participante_ids.ids)] if self.torneo_id else []
        return {'domain': {'participante_id': domain}}

    #este método se encarga de calcular las estadísticas de partidas jugadas, ganadas, perdidas y puntos acumulados para cada clasificación.
    # Buscamos directamente las partidas finalizadas del torneo en las que participa
    # el participante (como local o visitante), de modo que las estadísticas se
    # actualizan automáticamente sin necesidad de mantener un M2M manual.
    @api.depends(
        'torneo_id',
        'participante_id',
        'torneo_id.partida_ids.state',
        'torneo_id.partida_ids.ganador_id',
        'torneo_id.partida_ids.participante_local',
        'torneo_id.partida_ids.participante_visitante',
    )
    def _compute_stats(self):
        for rec in self:
            if not rec.torneo_id or not rec.participante_id:
                rec.partidas_jugadas = 0
                rec.partidas_ganadas = 0
                rec.partidas_perdidas = 0
                rec.puntos_acumulados = 0
                continue
            finished = rec.torneo_id.partida_ids.filtered(
                lambda m: m.state == 'finished' and rec.participante_id.id in (
                    m.participante_local.id,
                    m.participante_visitante.id,
                )
            )
            rec.partidas_jugadas = len(finished)
            rec.partidas_ganadas = sum(
                1 for m in finished if m.ganador_id and m.ganador_id.id == rec.participante_id.id
            )
            ties = sum(1 for m in finished if not m.ganador_id)
            rec.partidas_perdidas = rec.partidas_jugadas - rec.partidas_ganadas - ties
            rec.puntos_acumulados = rec.partidas_ganadas * 3 + ties

    # El método _compute_posicion_final asigna automáticamente la posición de cada
    # clasificación dentro de su torneo. Se ordena por puntos descendentes, luego
    # por partidas ganadas descendentes y, por último, por id del participante
    # para garantizar un orden determinista cuando todo lo demás coincide.
    @api.depends(
        'torneo_id',
        'puntos_acumulados',
        'partidas_ganadas',
        'torneo_id.standing_ids.puntos_acumulados',
        'torneo_id.standing_ids.partidas_ganadas',
    )
    def _compute_posicion_final(self):
        # Agrupamos por torneo para calcular el ranking una sola vez por torneo
        # en lugar de re-ordenar para cada registro individual.
        tournaments = self.mapped('torneo_id')
        rankings = {}
        for tournament in tournaments:
            ordered = tournament.standing_ids.sorted(
                key=lambda s: (-s.puntos_acumulados, -s.partidas_ganadas, s.participante_id.id or 0)
            )
            rankings[tournament.id] = {s.id: idx + 1 for idx, s in enumerate(ordered)}
        for rec in self:
            if not rec.torneo_id:
                rec.posicion_final = 0
                continue
            rec.posicion_final = rankings.get(rec.torneo_id.id, {}).get(rec.id, 0)

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





    # ----- Restricciones -----
    #este método se encarga de validar que el torneo asociado a la clasificación esté en estado 'ongoing' o 'done',
    # lo que significa que el torneo debe estar en curso o finalizado para poder crear o modificar una clasificación. 
    # Si el torneo está en otro estado, se lanza un error
    @api.constrains('torneo_id')
    def _check_torneo_ongoing(self):
        for rec in self:
            if rec.torneo_id and rec.torneo_id.state not in ('ongoing', 'done'):
                raise UserError('Solo se pueden crear clasificaciones en un torneo en curso.')

    # este método se encarga de validar que no haya más de una clasificación para el mismo participante en el mismo torneo.
    # Si se intenta crear o modificar una clasificación con un participante que ya tiene una clasificación en el mismo torneo, 
    #se lanza un error indicando que el participante ya tiene una clasificación en ese torneo.
    @api.constrains('torneo_id', 'participante_id')
    def _check_unique_participant_standing(self):
        for rec in self:
            if not rec.torneo_id or not rec.participante_id:
                continue
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('torneo_id', '=', rec.torneo_id.id),
                ('participante_id', '=', rec.participante_id.id),
            ], limit=1)
            if duplicate:
                raise UserError(
                    'El participante "%s" ya tiene una clasificación en este torneo.'
                    % rec.participante_id.name
                )

    # La posición se calcula automáticamente, así que no necesita validación manual.
    # Se admite el valor 0 transitoriamente cuando el registro aún no tiene torneo
    # asignado (estado intermedio durante la creación desde el formulario).






    # ----- Metodos de acción -----
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
