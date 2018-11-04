#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# urania
# Copyright (c) Nov 2018 Nacho Mas

import click


@click.command()
@click.option('--input',  help='fits input file')
def uSex(input):
    """Source extraction. Sextractor wrapper"""
    import urania.extraction.sex as sex
    sex(input)

