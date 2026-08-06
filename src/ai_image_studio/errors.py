"""Excepciones propias del proyecto.

Existen para que la interfaz de linea de comandos pueda distinguir *por que* se
detuvo el trabajo sin inspeccionar mensajes de texto.
"""

from __future__ import annotations


class FailClosed(ValueError):
    """Una puerta de integridad se nego a continuar.

    La entrada es formalmente valida, pero una comprobacion de seguridad no se
    cumple: el SHA-256 declarado no coincide con el original, el espacio de trabajo
    ya contiene un original distinto, o la maquina de estados no permite la
    transicion. Hereda de ``ValueError`` para no romper el codigo que ya capturaba
    ese tipo.
    """
