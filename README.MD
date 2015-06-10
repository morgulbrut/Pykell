---
title: How to Pykell
author:
    name: Tillo Bosshart
...

# About Pykell

Pykell is a Python 3 module for generating static websites or goodlooking documents. Thanks to [pandoc](http://pandoc.org/) and [pypandoc](https://pypi.python.org/pypi/pypandoc/).

## Features
- generating html from an input markdown file
- generating pdf from an input markdown file ([XeLaTeX](http://www.xelatex.org/) required, easyiest way to get it: install [TeXLive](http://www.tug.org/texlive/) or [MiKTeX](http://miktex.org/)
- input files can have a [yaml](http://yaml.org/)
- if the tex template uses the [listings](https://www.ctan.org/pkg/listings) package, syntax highlighted code listings are possible.
- merge pdfs.
- copy directory structures and files (useful for images, css and js stuff).
- generate filelists, either for internal stuff or as a html snippet.
- including text via a variable in a template (for example a filelist html snippet)

 
## TODO:
 - implementing a server listening to the output directory
 - checking files, only process if either the input or the template changed
 - maybe some kind of gallery thing 
 
# Example

The following code shows how the example is build

```python
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
```
