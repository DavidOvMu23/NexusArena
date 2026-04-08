from odoo import models, fields


class EsportsTournament(models.Model):
    # Modelo torneos.
    _name = 'esports.tournament'
    _description = 'Torneo de eSports'

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

    # Estado del torneo.
    estado = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Inscripciones Abiertas'),
        ('ongoing', 'En Curso'),
        ('done', 'Finalizado'),
        ('cancel', 'Cancelado')
    ], string="Estado", default='draft')

    # Campos calculados reservados para fases posteriores.
    # lineas_inscripcion
    # partidas_torneo
    # numero_participantes
    # ingresos_totales

    #Relaciones que hice sin darme cuenta que eran para otra entrega
    videojuego_id = fields.Many2one('esports.game', string="Videojuego", required=True)
    inscripcion_ids = fields.One2many('esports.registration', 'torneo_id', string="Líneas de Inscripción")
    partida_ids = fields.One2many('esports.match', 'torneo_id', string="Partidas del Torneo")