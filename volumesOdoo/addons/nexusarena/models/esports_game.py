from odoo import models, fields


class EsportsGame(models.Model):
    # Modelo de videojuegos
    _name = 'esports.game'
    _description = 'Videojuego de eSports'

    # Datos del videojuego.
    nombre = fields.Char(string="Nombre del Juego")

    genero = fields.Selection([
        ('moba', 'MOBA'), ('fps', 'FPS'), ('lucha', 'Lucha'),
        ('deportes', 'Deportes'), ('br', 'Battle Royale'), ('estrategia', 'Estrategia'), ('otro', 'Otro')
    ], string="Género")

    desarrollador = fields.Char(string="Desarrollador")

    modalidad = fields.Selection([
        ('individual', 'Individual'), ('teams', 'Equipos'), ('both', 'Ambas')
    ], string="Modalidad", default='both')

    max_jugadores_equipo = fields.Integer(string="Máx. Jugadores por Equipo")

    imagen = fields.Image(string="Logo/Imagen")

    # Campo calculado reservado para fases posteriores.
    # torneos_activos