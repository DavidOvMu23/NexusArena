import random

from odoo import api, fields, models
from odoo.exceptions import UserError


class EsportsBracketWizard(models.TransientModel):
    # Wizard (modelo transitorio: no persiste en BD entre sesiones) para generar
    # automáticamente el cuadro de eliminatorias de un torneo a partir de sus
    # inscripciones confirmadas.
    _name = 'esports.bracket.wizard'
    _description = 'Asistente para generar bracket de eliminatorias'

    # ----- Campos de entrada -----
    torneo_id = fields.Many2one(
        'esports.tournament',
        string='Torneo',
        required=True,
        ondelete='cascade',
    )
    modo_emparejamiento = fields.Selection([
        ('seed', 'Por seed (1 vs N, 2 vs N-1, ...)'),
        ('random', 'Aleatorio'),
    ], string='Modo de emparejamiento', default='seed', required=True)
    fecha_inicio_partidas = fields.Datetime(
        string='Fecha y hora primera ronda',
        help='Fecha y hora a la que se programarán las partidas de la primera ronda. '
             'Las rondas siguientes quedan sin fecha hasta que se definan.',
    )
    incluir_tercer_puesto = fields.Boolean(
        string='Incluir partida por el 3er puesto',
        default=True,
        help='Si está marcado y hay al menos 4 participantes, se creará una partida vacía en la fase "Tercer puesto" para los perdedores de semifinales.',
    )
    limpiar_partidas_existentes = fields.Boolean(
        string='Eliminar partidas existentes del torneo',
        default=True,
        help='Si está marcado, se borrarán todas las partidas previas del torneo antes de generar el bracket. Solo se pueden borrar partidas que aún no estén finalizadas.',
    )

    # ----- Campos calculados (vista previa) -----
    participantes_confirmados_ids = fields.Many2many(
        'res.partner',
        string='Participantes confirmados',
        compute='_compute_participantes_confirmados',
    )
    numero_participantes = fields.Integer(
        string='Nº participantes confirmados',
        compute='_compute_participantes_confirmados',
    )
    info_bracket = fields.Text(
        string='Estructura propuesta',
        compute='_compute_info_bracket',
    )

    # Calculamos los participantes confirmados del torneo a partir de las
    # inscripciones en estado "confirmed". Estos serán los que entren al bracket.
    @api.depends('torneo_id', 'torneo_id.inscripcion_ids', 'torneo_id.inscripcion_ids.state')
    def _compute_participantes_confirmados(self):
        for wiz in self:
            if not wiz.torneo_id:
                wiz.participantes_confirmados_ids = [(5, 0, 0)]
                wiz.numero_participantes = 0
                continue
            confirmadas = wiz.torneo_id.inscripcion_ids.filtered(lambda i: i.state == 'confirmed')
            # Ordenamos por fecha de inscripción para que el seed sea estable
            # (los que se inscribieron antes obtienen mejor seed).
            confirmadas = confirmadas.sorted(key=lambda i: (i.fecha_inscripcion or fields.Date.today(), i.id))
            wiz.participantes_confirmados_ids = [(6, 0, confirmadas.mapped('participante_id').ids)]
            wiz.numero_participantes = len(confirmadas)

    # Texto descriptivo de la estructura del bracket que se generará en función
    # del número de participantes. Sirve como vista previa antes de confirmar.
    @api.depends('numero_participantes', 'incluir_tercer_puesto')
    def _compute_info_bracket(self):
        for wiz in self:
            n = wiz.numero_participantes
            if n == 2:
                texto = '1 partida en fase Final.'
            elif n == 4:
                texto = '2 partidas en Semifinal + 1 en Final'
                if wiz.incluir_tercer_puesto:
                    texto += ' + 1 partida por el 3er puesto'
                texto += '.'
            elif n == 8:
                texto = '4 partidas en Cuartos + 2 en Semifinal + 1 en Final'
                if wiz.incluir_tercer_puesto:
                    texto += ' + 1 partida por el 3er puesto'
                texto += '.'
            else:
                texto = (
                    'Número de participantes confirmados no soportado (%s).\n'
                    'El bracket requiere exactamente 2, 4 u 8 participantes confirmados.'
                    % n
                )
            wiz.info_bracket = texto

    # Default que precarga el torneo cuando el wizard se abre desde la acción
    # del formulario de torneo (active_id apunta al torneo actual).
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'esports.tournament' and active_id and 'torneo_id' in fields_list:
            res['torneo_id'] = active_id
            torneo = self.env['esports.tournament'].browse(active_id)
            # Si el torneo tiene fecha de inicio, la usamos como sugerencia para
            # las partidas de la primera ronda (a mediodía).
            if torneo.fecha_inicio and 'fecha_inicio_partidas' in fields_list:
                res['fecha_inicio_partidas'] = fields.Datetime.to_datetime(
                    '%s 12:00:00' % torneo.fecha_inicio
                )
        return res

    # Estructura del bracket: para cada nº de participantes soportado devolvemos
    # el orden de las parejas de la primera ronda en función del seed.
    # Cada elemento es (idx_local, idx_visitante) sobre la lista ordenada por seed.
    _BRACKET_PAIRS = {
        2: [(0, 1)],
        4: [(0, 3), (1, 2)],
        8: [(0, 7), (3, 4), (1, 6), (2, 5)],
    }

    # Fase de la primera ronda según el número de participantes.
    _FIRST_PHASE = {
        2: 'final',
        4: 'semifinal',
        8: 'quarterfinal',
    }

    # Acción principal del wizard: genera el bracket creando los registros de
    # esports.match correspondientes. Devuelve una acción que abre la lista de
    # partidas del torneo para que el organizador vea el resultado.
    def action_generate_bracket(self):
        self.ensure_one()
        torneo = self.torneo_id

        # Validaciones previas
        if not torneo:
            raise UserError('Debe seleccionar un torneo.')
        if torneo.state != 'ongoing':
            raise UserError(
                'El torneo debe estar en estado "En Curso" para generar el bracket. '
                'Pulse antes "Iniciar torneo" en el formulario del torneo.'
            )
        if torneo.formato not in ('direct', 'double'):
            raise UserError(
                'El bracket de eliminatorias solo se puede generar para torneos con '
                'formato "Eliminación Directa" o "Doble Eliminación". '
                'El torneo "%s" tiene formato "%s".'
                % (torneo.nombre or '', dict(torneo._fields['formato'].selection).get(torneo.formato, torneo.formato))
            )

        confirmadas = torneo.inscripcion_ids.filtered(lambda i: i.state == 'confirmed')
        confirmadas = confirmadas.sorted(key=lambda i: (i.fecha_inscripcion or fields.Date.today(), i.id))
        n = len(confirmadas)
        if n not in self._BRACKET_PAIRS:
            raise UserError(
                'Número de participantes confirmados no soportado (%s).\n'
                'El bracket requiere exactamente 2, 4 u 8 participantes confirmados.' % n
            )

        # Limpieza previa de partidas existentes (si procede)
        if self.limpiar_partidas_existentes and torneo.partida_ids:
            cerradas = torneo.partida_ids.filtered(lambda m: m.state in ('finished', 'walkover'))
            if cerradas:
                raise UserError(
                    'No se pueden eliminar las partidas existentes porque %d ya están '
                    'finalizadas o son walkover. Desmarque la opción de limpieza o '
                    'gestione esas partidas manualmente.' % len(cerradas)
                )
            torneo.partida_ids.unlink()
        elif not self.limpiar_partidas_existentes and torneo.partida_ids:
            raise UserError(
                'El torneo ya tiene %d partida(s). Marque la opción "Eliminar partidas '
                'existentes" o bórrelas manualmente antes de generar el bracket.'
                % len(torneo.partida_ids)
            )

        # Lista de participantes ordenada por seed (orden de inscripción confirmada).
        # Si el modo es aleatorio, se baraja antes de aplicar las parejas.
        participantes = list(confirmadas.mapped('participante_id'))
        if self.modo_emparejamiento == 'random':
            random.shuffle(participantes)

        Match = self.env['esports.match']
        fecha = self.fecha_inicio_partidas or False

        # Las partidas se crean en orden inverso (final → semifinales → cuartos)
        # para que cada partida de ronda anterior pueda enlazar directamente con
        # la posterior, ya creada. Así el ganador se propaga automáticamente al
        # registrar el resultado.
        partidas_creadas = self.env['esports.match']
        final = False
        tercer = False
        sf1 = False
        sf2 = False

        # 1) Final (siempre existe para n in 2/4/8)
        if n in (4, 8):
            final = Match.create({
                'torneo_id': torneo.id,
                'fase': 'final',
                'state': 'scheduled',
            })
            partidas_creadas |= final

        # 2) Partida por el 3er puesto (opcional, solo si hay semifinales)
        if self.incluir_tercer_puesto and n in (4, 8):
            tercer = Match.create({
                'torneo_id': torneo.id,
                'fase': 'third_place',
                'state': 'scheduled',
            })
            partidas_creadas |= tercer

        # 3) Semifinales (vacías) enlazadas a final y, si aplica, al 3er puesto
        if n == 8:
            sf1 = Match.create({
                'torneo_id': torneo.id,
                'fase': 'semifinal',
                'state': 'scheduled',
                'siguiente_partida_id': final.id,
                'siguiente_slot': 'local',
                'partida_tercer_puesto_id': tercer.id if tercer else False,
                'tercer_puesto_slot': 'local' if tercer else False,
            })
            sf2 = Match.create({
                'torneo_id': torneo.id,
                'fase': 'semifinal',
                'state': 'scheduled',
                'siguiente_partida_id': final.id,
                'siguiente_slot': 'visitante',
                'partida_tercer_puesto_id': tercer.id if tercer else False,
                'tercer_puesto_slot': 'visitante' if tercer else False,
            })
            partidas_creadas |= sf1 | sf2

        # 4) Primera ronda (con participantes). Los emparejamientos vienen de
        # _BRACKET_PAIRS, que aplica seed estándar (1 vs N, 2 vs N-1, ...).
        first_phase = self._FIRST_PHASE[n]
        pairs = self._BRACKET_PAIRS[n]

        for i, (idx_local, idx_visit) in enumerate(pairs):
            vals = {
                'torneo_id': torneo.id,
                'fase': first_phase,
                'fecha_hora_programada': fecha,
                'participante_local': participantes[idx_local].id,
                'participante_visitante': participantes[idx_visit].id,
                'state': 'scheduled',
            }
            # Para n=4 la primera ronda es la semifinal: enlazamos directamente
            # a final y al 3er puesto.
            if n == 4:
                vals['siguiente_partida_id'] = final.id
                vals['siguiente_slot'] = 'local' if i == 0 else 'visitante'
                if tercer:
                    vals['partida_tercer_puesto_id'] = tercer.id
                    vals['tercer_puesto_slot'] = 'local' if i == 0 else 'visitante'
            # Para n=8 la primera ronda son cuartos: cada par de cuartos alimenta
            # una semifinal. (QF1, QF2) → SF1 ; (QF3, QF4) → SF2.
            elif n == 8:
                if i in (0, 1):
                    vals['siguiente_partida_id'] = sf1.id
                    vals['siguiente_slot'] = 'local' if i == 0 else 'visitante'
                else:
                    vals['siguiente_partida_id'] = sf2.id
                    vals['siguiente_slot'] = 'local' if i == 2 else 'visitante'
            # Para n=2 no hay enlace: la primera ronda es ya la final.
            partida = Match.create(vals)
            partidas_creadas |= partida

        # Mensaje en el chatter del torneo con el resumen de la generación
        torneo.message_post(
            body='Bracket generado automáticamente: %d partidas creadas (%d participantes, '
                 'modo %s).' % (
                     len(partidas_creadas),
                     n,
                     dict(self._fields['modo_emparejamiento'].selection)[self.modo_emparejamiento],
                 )
        )

        # Devolvemos una acción que abre la lista de partidas filtradas por este torneo
        return {
            'type': 'ir.actions.act_window',
            'name': 'Partidas del bracket',
            'res_model': 'esports.match',
            'view_mode': 'list,form',
            'domain': [('torneo_id', '=', torneo.id)],
            'context': {'default_torneo_id': torneo.id},
        }
