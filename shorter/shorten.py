# -*- coding: utf-8 -*-
# Copyright (c) 2014 Ionuț Arțăriși <ionut@artarisi.eu>
# This file is part of shorter.

# shorter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# shorter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with shorter. If not, see <http://www.gnu.org/licenses/>.

DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def int_to_base36(i):
    factor = 0
    while True:
        factor += 1
        if i < 36 ** factor:
            factor -= 1
            break

    base36 = []
    while factor >= 0:
        j = 36 ** factor
        base36.append(DIGITS[i//j])
        i = i % j
        factor -= 1
    return ''.join(base36)
