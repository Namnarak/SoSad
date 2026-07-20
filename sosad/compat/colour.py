"""discord.py-compatible Colour / Color.

Subclasses hikari.Colour (which is an int subclass) for seamless
compatibility — pass directly to hikari.Embed(colour=...).
"""

from __future__ import annotations

import random as _random

import hikari


class Colour(hikari.Colour):
    """Represents a Discord colour.

    Usage::

        colour = discord.Colour(0xFF0000)
        colour = discord.Colour.red()
        colour = discord.Colour.from_rgb(255, 0, 0)
        rgb = colour.to_rgb()
    """

    def __new__(cls, value: int) -> Colour:
        return super().__new__(cls, value & 0xFFFFFF)

    def to_rgb(self) -> tuple[int, int, int]:
        return (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF

    @staticmethod
    def from_rgb(r: int, g: int, b: int) -> Colour:
        return Colour((r << 16) + (g << 8) + b)

    @staticmethod
    def from_hsv(h: float, s: float, v: float) -> Colour:
        hi = int(h * 6) % 6
        f = h * 6 - int(h * 6)
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = {
            0: (v, t, p),
            1: (q, v, p),
            2: (p, v, t),
            3: (p, q, v),
            4: (t, p, v),
            5: (v, p, q),
        }[hi]
        return Colour.from_rgb(int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def random(*, seed: int | None = None) -> Colour:
        if seed is not None:
            _random.seed(seed)
        return Colour(_random.randint(0, 0xFFFFFF))

    @staticmethod
    def default() -> Colour:
        return Colour(0)

    @staticmethod
    def teal() -> Colour:
        return Colour(0x1ABC9C)

    @staticmethod
    def dark_teal() -> Colour:
        return Colour(0x11806A)

    @staticmethod
    def brand_green() -> Colour:
        return Colour(0x57F287)

    @staticmethod
    def green() -> Colour:
        return Colour(0x57F287)

    @staticmethod
    def dark_green() -> Colour:
        return Colour(0x1F8B4C)

    @staticmethod
    def blue() -> Colour:
        return Colour(0x3498DB)

    @staticmethod
    def dark_blue() -> Colour:
        return Colour(0x206694)

    @staticmethod
    def purple() -> Colour:
        return Colour(0x9B59B6)

    @staticmethod
    def dark_purple() -> Colour:
        return Colour(0x71368A)

    @staticmethod
    def magenta() -> Colour:
        return Colour(0xE91E63)

    @staticmethod
    def dark_magenta() -> Colour:
        return Colour(0xAD1457)

    @staticmethod
    def gold() -> Colour:
        return Colour(0xF1C40F)

    @staticmethod
    def dark_gold() -> Colour:
        return Colour(0xC27C0E)

    @staticmethod
    def orange() -> Colour:
        return Colour(0xE67E22)

    @staticmethod
    def dark_orange() -> Colour:
        return Colour(0xA84300)

    @staticmethod
    def brand_red() -> Colour:
        return Colour(0xED4245)

    @staticmethod
    def red() -> Colour:
        return Colour(0xED4245)

    @staticmethod
    def dark_red() -> Colour:
        return Colour(0x992D22)

    @staticmethod
    def light_grey() -> Colour:
        return Colour(0x979C9F)

    @staticmethod
    def lighter_grey() -> Colour:
        return Colour(0xBCC0C0)

    @staticmethod
    def light_gray() -> Colour:
        return Colour(0x979C9F)

    @staticmethod
    def lighter_gray() -> Colour:
        return Colour(0xBCC0C0)

    @staticmethod
    def dark_grey() -> Colour:
        return Colour(0x607D8B)

    @staticmethod
    def darker_grey() -> Colour:
        return Colour(0x546E7A)

    @staticmethod
    def dark_gray() -> Colour:
        return Colour(0x607D8B)

    @staticmethod
    def darker_gray() -> Colour:
        return Colour(0x546E7A)

    @staticmethod
    def blurple() -> Colour:
        return Colour(0x5865F2)

    @staticmethod
    def greyple() -> Colour:
        return Colour(0x99AAB5)

    @staticmethod
    def dark_theme() -> Colour:
        return Colour(0x36393F)

    @staticmethod
    def fuse() -> Colour:
        return Colour(0xEB459E)

    @staticmethod
    def fb_white() -> Colour:
        return Colour(0xFFFFFF)

    @staticmethod
    def white() -> Colour:
        return Colour(0xFFFFFF)

    @staticmethod
    def yellow() -> Colour:
        return Colour(0xFEE75C)

    @staticmethod
    def pink() -> Colour:
        return Colour(0xEB459E)


Color = Colour


__all__ = ["Colour", "Color"]
