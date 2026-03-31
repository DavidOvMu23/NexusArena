from odoo import models, fields

class EsportsTournament(models.Model):
    #Nombre del modelo y descripción
    _name = 'esports.tournament'
    _description = 'Torneo de eSports'

    #Campos
    nombre = fields.Char(string="Nombre del Torneo", required=True)
    edicion = fields.Char(string="Edición (Año)", required=True)

    formato = fields.Selection([
        ('league', 'Liga'),
        ('direct', 'Eliminación Directa'),
        ('double', 'Doble Eliminación')
    ], string="Formato", default='league', required=True)

    modalidad = fields.Selection([
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('hibrido', 'Híbrido')
    ], string="Modalidad", required=True)

    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha de Fin", required=True)

    premio_total = fields.Float(string="Premio Total (€)", required=True)
    premio_1 = fields.Float(string="1er Puesto (€)", required=True)
    premio_2 = fields.Float(string="2º Puesto (€)", required=True)
    premio_3 = fields.Float(string="3er Puesto (€)", required=True)

    cuota = fields.Float(string="Cuota de Inscripción", required=True)

    estado = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Inscripciones Abiertas'),
        ('ongoing', 'En Curso'),
        ('done', 'Finalizado'),
        ('cancel', 'Cancelado')
    ], string="Estado", default='draft', required=True)

    #Relaciones
    videojuego_id = fields.Many2one('esports.game', string="Videojuego", required=True)
    inscripcion_ids = fields.One2many('esports.registration', 'torneo_id', string="Líneas de Inscripción")
    partida_ids = fields.One2many('esports.match', 'torneo_id', string="Partidas del Torneo")