#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import date

from Pykell import Pykell

site = Pykell()

def main():

    for f in ['README.md',]:
        site.genPdf(f, 'demo/', 'templates/example.tex')
        site.genHtml(f, 'demo/', 'templates/example.html')

    site.copyDir('css/','demo/')

class Site(Pykell):
    if __name__ == '__main__':
        main()
