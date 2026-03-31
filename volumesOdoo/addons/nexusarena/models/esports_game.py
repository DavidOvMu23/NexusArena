from odoo import models, fields

class EsportsGame(models.Model):
    #Nombre del modelo y descripción
    _name = 'esports.game'
    _description = 'Videojuego de eSports'

    #Campos
    nombre = fields.Char(string="Nombre del Juego", required=True)

    genero = fields.Selection([
        ('moba', 'MOBA'), ('fps', 'FPS'), ('lucha', 'Lucha'),
        ('deportes', 'Deportes'), ('br', 'Battle Royale'), ('estrategia', 'Estrategia'), ('otro', 'Otro')
    ], string="Género", required=True)

    desarrollador = fields.Char(string="Desarrollador", required=True)

    modalidad = fields.Selection([
        ('individual', 'Individual'), ('teams', 'Equipos'), ('both', 'Ambas')
    ], string="Modalidad", default='both', required=True)

    max_jugadores_equipo = fields.Integer(string="Máx. Jugadores por Equipo", required=True)

    imagen = fields.Image(string="Logo/Imagen", required=True)