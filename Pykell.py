#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import errno
import shutil
import glob
import logging


from PyPDF2 import PdfFileWriter, PdfFileReader
import pypandoc

import yaml
from colorlog import ColoredFormatter


class Pykell:
    """
    Class to generate documents from markdown files, right now html and pdf trough xelatex.

    Dependencies:
        Python 3
            colorlog
            pypandoc
            pyaml
            PyPDF2

        xelatex if you want to generate pdf files.

    Features:
        Syntax highlighting with listings

    """


    def __init__(self):
        cformatter = ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        )

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('build.log')
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        fformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(fformatter)
        ch.setFormatter(cformatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

    @staticmethod
    def genHtml(infile, path='page/', template='auto', outfile='infile'):
        """
        Generates a html file

        :param infile: markdown input file
        :param path: output directory (default: page/)
        :param template: template to use (default: /templates/<infile file name>.html)
        :param outfile: html output file (default: <path>/<infile file name>.html)
        """
        if outfile == 'infile':
            outfile = infile
        filename = os.path.basename(outfile)
        filename = os.path.splitext(filename)[0]
        logging.info('Writing: ' + path + os.path.splitext(outfile)[0] + '.html...')
        if template == 'auto':
            template = Pykell.checkTemplate(path, '.html')

        Pykell.checkPath(path)
        try:
            pypandoc.convert(infile, 'html-yaml_metadata_block', outputfile=path + filename + '.html',
                             extra_args=['-s', '--template=' + template])
        except p as RuntimeError:
            logging.error('Pandoc died with exitcode "%s" during conversation: %s' % (p.returncode, infile))
        except:
            raise

    @staticmethod
    def genPdf(infile, path='page/', template='auto', outfile='infile'):
        """
        Generates a pdf file

        :param infile: markdown input file
        :param path: output directory (default: page/)
        :param template: template to use (default: /templates/<infile file name>.pdf)
        :param outfile: pdf output file (default: <path>/<infile file name>.pdf)
        """
        if outfile == 'infile':
            outfile = infile
        filename = os.path.basename(outfile)
        filename = os.path.splitext(filename)[0]
        logging.info('Writing: ' + path + filename + '.pdf...')
        if template == 'auto':
            template = Pykell.checkTemplate(path, '.tex')
        Pykell.checkPath(path)
        try:
            pypandoc.convert(infile, 'latex-yaml_metadata_block', outputfile=path + filename + '.pdf',
                             extra_args=['-s', '--template=' + template, '--listings','--latex-engine=xelatex'])
        except RuntimeError:
            logging.exception('Pandoc RuntimeError')
        except:
            raise

    @staticmethod
    def combinePdf(files,path='page/',outfile = 'comb.pdf'):
        """
        Combines a list of pdf files into one file

        :param files: list of files
        :param path: output directory (default: page/)
        :param outfile:
        :return: pdf output file (default: <path>/comb.pdf)
        """
        output = PdfFileWriter()
        for f in files:
            pdfFile = PdfFileReader(open(f,"rb"))
            for p in range(pdfFile.getNumPages()):
                output.addPage(pdfFile.getPage(p))
        Pykell.checkPath(path)
        logging.info('Writing: ' + path + outfile)
        outputStream = open(path + outfile, "wb")
        output.write(outputStream)
        outputStream.close()


    @staticmethod
    def genTex(infile, path='page/', template='auto', outfile='infile'):
        """
        Generates a tex file

        :param infile: markdown input file
        :param path: output directory (default: page/)
        :param template: template to use (default: /templates/<infile file name>.tex)
        :param outfile: tex output file (default: <path>/<infile file name>.tex)
        """
        if outfile == 'infile':
            outfile = infile
        filename = os.path.basename(outfile)
        filename = os.path.splitext(filename)[0]
        logging.info('Writing: ' + path + filename + '.tex...')
        if template == 'auto':
            template = Pykell.checkTemplate(path, '.tex')
        Pykell.checkPath(path)
        pypandoc.convert(infile, 'latex-yaml_metadata_block', outputfile=path + filename + '.tex',
                         extra_args=['-s', '--template=' + template])

    # Utils
    @staticmethod
    def checkPath(path):
        """
        Checks if a path exists

        :param path: path to check
        """
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @staticmethod
    def checkTemplate(path, exten):
        """
        Check if a templat esxists

        :param path: path to check
        :param exten: extention of the template
        """
        if os.path.isfile('templates/' + path + exten):
            logging.info('    using templates/' + path + exten)
            return ('templates/' + path + exten)
        else:
            logging.info('    using templates/default' + exten)
            return ('templates/default' + exten)

    @staticmethod
    def copyDir(dir, path='page/'):
        """
        Copies a dir tree to a path (useful for images and so on)

        :param dir: dir to copy
        :param path: destination directory (default: page/)
        """
        if os.path.exists(path + dir):
            shutil.rmtree(path + dir)
        try:
            logging.info('Copying ' + dir + ' to ' + path + dir)
            Pykell.checkPath(path)
            shutil.copytree(dir, path + dir)
        except FileExistsError:
            logging.warning(path + dir + ' exists.')
        except:
            raise

    @staticmethod
    def copyFile(file, path='page/', new_name='auto'):
        """
        Copies a file to a path


        :param file: file to copy
        :param path: destination directory (default: page/)
        :param new_name: dest file name
        """
        if new_name == 'auto':
            new_name = file
        if os.path.exists(path + new_name):
            os.remove(path + new_name)
        try:
            logging.info('Copying ' + file + ' to ' + path + new_name)
            Pykell.checkPath(path)
            shutil.copy(file, path + new_name)
        except:
            raise

    @staticmethod
    def getYaml(file):
        """
        Get yaml block out of a file

        :param file: file with a yaml block at the beginning
        :return: yaml block as string
        """
        yaml = 0
        ret = ''
        for line in file:
            searchphrase = '---\n'
            if searchphrase in line:
                if yaml == 0:
                    yaml = 1
                else:
                    yaml = 2
                    ret += '...\n'

            searchphrase = '...\n'
            if searchphrase in line:
                yaml = 2
                ret += '...\n'

            if yaml == 1:
                ret += line
        return ret

    @staticmethod
    def getYamlVal(file, key):
        """
        Get a value out of a given yaml block

        :param file: file with a yaml block at the beginning
        :param key: key to search
        :return: value of the given key as string (empty if not found)
        """
        f = open(file, 'r')
        ret = ''
        try:
            my_yaml = yaml.load(Pykell.getYaml(f))
            if key.find('.')>0:
                ret += my_yaml[key.split('.')[0]][key.split('.')[1]]
            else:
                ret += my_yaml[key]
        except TypeError:
            logging.exception('getYamlVal: TypeError')
        except KeyError:
            logging.warning('getYamlVal: KeyError: Maybe ' + file + ' has no key ' + key)
        f.close()
        return ret

    @staticmethod
    def includeInFile(infile, variable, text, outfile='infile'):
        """
        Includes text in a template file, at a given variable

        :param infile:
        :param variable:
        :param text:
        :param outfile:
        :return:
        """
        logging.info('Including text in File')
        if outfile == 'infile':
            outfile = infile
        Pykell.checkPath(os.path.dirname(outfile) + '/')
        iF = open(infile, 'r')
        t = iF.read()
        iF.close()
        oF = open(outfile, 'w')
        oF.write(t.replace(variable, text))
        oF.close()
        logging.debug(variable + ' replaced by ' + text + ': In: ' + infile + ' Out: ' + outfile)

    # File lists
    @staticmethod
    def genFileListMod(dir, exten):
        logging.info('Generating filelist sorted by date modified')
        files = glob.glob(dir + '*' + exten)
        files.sort(key=lambda x: os.path.getmtime(x))
        files.reverse()
        logging.debug('Files: ' + files)
        return files

    @staticmethod
    def genFileListName(dir, exten):
        logging.info('Generating filelist sorted by filename')
        files = glob.glob(dir + '*' + exten)
        files.sort(key=lambda x: os.path.basename(x))
        logging.debug(files)
        return files

    @staticmethod
    def genFileListHTML(files):

        # <li>
        # <a href="/posts/2015-03-20-London.html">Eurotrip 15 London</a> - March 20, 2015
        # </li>

        ret = '<ul>\n'
        for f in files:
            try:
                logging.debug('genFileListHTML: ' + f)
                ret += '\t<li><a href="/' + os.path.splitext(f)[0] + '.html">' + Pykell.getYamlVal(f,
                                                                                                   'title') + '</a> - ' + Pykell.getYamlVal(
                    f, 'date').strftime('%B %d, %Y') + '</li>\n'
            except AttributeError:
                ret += '\t<li><a href="/' + os.path.splitext(f)[0] + '.html">' + Pykell.getYamlVal(f,
                                                                                                   'title') + '</a> </li>\n'
            except:
                raise
        ret += '</ul>\n'
        logging.debug('Filelist as HTML:\n' + ret)
        return ret
