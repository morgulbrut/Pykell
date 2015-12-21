#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import errno
import shutil
import glob
import logging
import hashlib
import sqlite3

from subprocess import call

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
        pandoc

    Features:
        Syntax highlighting with listings

    """

    def __init__(self, db):
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
        Pykell.db = db
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
    def compile(infile, path='page/', template='auto', compiler='html', outfile='infile'):
        """
        Generates a file

        :param infile: markdown input file
        :param path: output directory (default: page/)
        :param template: template to use (default: /templates/<infile file name>.<compiler>)
        :param compiler: html, pdf (using XeLaTeX), tex, docx
        :param outfile: output file (default: <path>/<infile file name>.<compiler>)
        """
        if outfile == 'infile':
            outfile = infile
        if template == 'auto':
            template = Pykell.check_template(path, '.html')
        if compiler == 'docx':
            template = 'none'

        filename = os.path.basename(outfile)
        filename = os.path.splitext(filename)[0]
        logging.info('Writing: ' + path + filename + '.' + compiler)

        if Pykell.check_hash(infile, template) != 1:
            Pykell.write_to_cache(infile, template)
            Pykell.check_path(path)
            try:
                if compiler == 'html':
                    pypandoc.convert(infile, 'html-yaml_metadata_block', outputfile=path + filename + '.html',
                                     extra_args=['-s', '--template=' + template, '--mathjax'])
                elif compiler == 'pdf':
                    pypandoc.convert(infile, 'latex-yaml_metadata_block', outputfile=path + filename + '.pdf',
                                     extra_args=['-s', '--template=' + template, '--listings',
                                                 '--latex-engine=xelatex'])
                elif compiler == 'tex':
                    pypandoc.convert(infile, 'latex-yaml_metadata_block', outputfile=path + filename + '.tex',
                                     extra_args=['-s', '--template=' + template])
                elif compiler == 'docx':
                    pypandoc.convert(infile, 'docx', outputfile=path + filename + '.docx')
            except RuntimeError:
                logging.exception('Pandoc RuntimeError')
            except:
                raise
        else:
            logging.info('...nothing to do')

    @staticmethod
    def compile_string(instring, path='page/', template='auto', compiler='html', outfile='output'):
        """
        Generates a file

        :param instring: markdown input string
        :param path: output directory (default: page/)
        :param template: template to use (default: /templates/<infile file name>.<compiler>)
        :param compiler: html, pdf (using XeLaTeX), tex, docx
        :param outfile: output file (default: <path>/<infile file name>.<compiler>)
        """
        if template == 'auto':
            template = Pykell.check_template(path, '.html')
        if compiler == 'docx':
            template = 'none'

        filename = os.path.basename(outfile)
        filename = os.path.splitext(filename)[0]
        logging.info('Writing: ' + path + filename + '.' + compiler)

        Pykell.check_path(path)
        try:
            if compiler == 'html':
                pypandoc.convert(instring, 'html-yaml_metadata_block', format='md',
                                 outputfile=path + filename + '.html',
                                 extra_args=['-s', '--template=' + template, '--mathjax'])
            elif compiler == 'pdf':
                pypandoc.convert(instring, 'latex-yaml_metadata_block', format='md',
                                 outputfile=path + filename + '.pdf',
                                 extra_args=['-s', '--template=' + template, '--listings',
                                             '--latex-engine=xelatex'])
            elif compiler == 'tex':
                pypandoc.convert(instring, 'latex-yaml_metadata_block', format='md',
                                 outputfile=path + filename + '.tex',
                                 extra_args=['-s', '--template=' + template])
            elif compiler == 'docx':
                pypandoc.convert(instring, 'docx', format='md',
                                 outputfile=path + filename + '.docx')
        except RuntimeError:
            logging.exception('Pandoc RuntimeError')
        except:
            raise

    @staticmethod
    def combine_pdf(files, path='page/', outfile='comb.pdf'):
        """
        Combines a list of pdf files into one file

        :param files: list of files
        :param path: output directory (default: page/)
        :param outfile:
        :return: pdf output file (default: <path>/comb.pdf)
        """
        output = PdfFileWriter()
        for f in files:
            pdfFile = PdfFileReader(open(f, "rb"))
            for p in range(pdfFile.getNumPages()):
                output.addPage(pdfFile.getPage(p))
        Pykell.check_path(path)
        logging.info('Writing: ' + path + outfile)
        outputStream = open(path + outfile, "wb")
        output.write(outputStream)
        outputStream.close()

    # Utils
    @staticmethod
    def check_path(path):
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
    def check_template(path, exten):
        """
        Check if a template exists

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
    def copy_dir(dir, path='page/'):
        """
        Copies a dir tree to a path (useful for images and so on)

        :param dir: dir to copy
        :param path: destination directory (default: page/)
        """
        if os.path.exists(path + dir):
            shutil.rmtree(path + dir)
        try:
            logging.info('Copying ' + dir + ' to ' + path + dir)
            Pykell.check_path(path)
            shutil.copytree(dir, path + dir)
        except FileExistsError:
            logging.warning(path + dir + ' exists.')
        except:
            raise

    @staticmethod
    def copy_file(file, path='page/', new_name='auto'):
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
            Pykell.check_path(path)
            shutil.copy(file, path + new_name)
        except:
            raise

    @staticmethod
    def delete_file(file):
        try:
            os.remove(file)
        except OSError as e:  # this would be "except OSError, e:" before Python 2.6
            if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                raise  # re-raise exception if a different error occured

    @staticmethod
    def get_yaml(file):
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
    def get_yaml_val(file, key):
        """
        Get a value out of a given yaml block

        :param file: file with a yaml block at the beginning
        :param key: key to search
        :return: value of the given key as string (empty if not found)
        """
        f = open(file, 'r')
        ret = ''
        try:
            my_yaml = yaml.load(Pykell.get_yaml(f))
            if key.find('.') > 0:
                ret += my_yaml[key.split('.')[0]][key.split('.')[1]]
            else:
                ret += my_yaml[key]
        except TypeError:
            logging.exception('get_yaml_val: TypeError')
        except KeyError:
            logging.warning('get_yaml_val: KeyError: Maybe ' + file + ' has no key ' + key)
        f.close()
        return ret

    @staticmethod
    def replace_in_file(infile, variable, text, outfile='infile'):
        """
        Includes text in a template file, at a given variable

        :param infile: file in which text should be included
        :param variable: variable, I recommend something like $var$ since it's consistent with variables in templates
        :param text: text to include at variable
        :param outfile: file to write to
        """
        logging.info('Including text in File')
        if outfile == 'infile':
            outfile = infile
        Pykell.check_path(os.path.dirname(outfile))
        iF = open(infile, 'r')
        t = iF.read()
        iF.close()
        oF = open(outfile, 'w')
        oF.write(t.replace(variable, text))
        oF.close()
        logging.info(variable + ' replaced by ' + text + ': In: ' + infile + ' Out: ' + outfile)

    # File lists
    @staticmethod
    def gen_file_list_mod(dir, exten):
        """
        Generates a filelist sorted by the date modified of the files.

        :param dir: dir where the files to list are
        :param exten: extention of the files to list
        :return: list containing the filenames as strings
        """
        logging.info('Generating filelist sorted by date modified')
        files = glob.glob(dir + '*' + exten)
        files.sort(key=lambda x: os.path.getmtime(x))
        files.reverse()
        logging.debug('Files: ' + files)
        return files

    @staticmethod
    def gen_file_list_name(dir, exten):
        """
        Generates a filelist sorted by the filename.

        :param dir: dir where the files to list are
        :param exten: extention of the files to list
        :return: list containing the filenames as strings
        """
        logging.info('Generating filelist sorted by filename')
        files = glob.glob(dir + '*' + exten)
        files.sort(key=lambda x: os.path.basename(x))
        logging.debug(files)
        return files

    @staticmethod
    def gen_file_list_html(files):
        """
        generates a piece of html in the form

        <li>
        <a href="/posts/2015-03-20-London.html">Eurotrip 15 London</a> - March 20, 2015
        </li>

        out of a list of files

        :param files: list of filenames as strings
        :return: string containing html
        """

        ret = '<ul>\n'
        for f in files:
            try:
                logging.debug('gen_file_list_html: ' + f)
                ret += '\t<li><a href="/' + os.path.splitext(f)[0] + '.html">' + Pykell.get_yaml_val(f,
                                                                                                     'title') + '</a> - ' + Pykell.get_yaml_val(
                    f, 'date').strftime('%B %d, %Y') + '</li>\n'
            except AttributeError:
                ret += '\t<li><a href="/' + os.path.splitext(f)[0] + '.html">' + Pykell.get_yaml_val(f,
                                                                                                     'title') + '</a> </li>\n'
            except:
                raise
        ret += '</ul>\n'
        logging.debug('Filelist as HTML:\n' + ret)
        return ret

    @staticmethod
    def check_hash(file, template):
        """
        checks if the hash of a given file and template is equal to the hash stored in cache.db

        :param file: file to check
        :param template: template to check
        :return: 0 if not equal, 1 if equal, 2 if not exists
        """
        if Pykell.db == True:
            ret = 0
            hashs = Pykell.read_from_db('SELECT fileHash,templateHash FROM files WHERE name=? AND template=?',
                                        [file, template])
            if not hashs:
                ret = 2
            else:
                if Pykell.gen_file_hash(file) == hashs[0][0]:
                    if Pykell.gen_file_hash(template) == hashs[0][1]:
                        ret = 1
            return ret
        else:
            return 0

    @staticmethod
    def gen_file_hash(file):
        """
        calculates  md5 hash of a file

        :param file: file to calculate md5 of
        :return: string containing the md5 hash
        """

        hasher = hashlib.md5()
        logging.debug('generating Hash: ' + file)
        try:
            with open(file, 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            return hasher.hexdigest()
        except FileNotFoundError:
            if file == 'none':
                return '0'
            else:
                raise
        except:
            raise

    @staticmethod
    def write_to_db(sql_statement, vals):
        """
        Write to database cache.db

        :param sql_statement: SQL statement to execute
        :param vals: values of the statement
        """
        if not os.path.exists('cache.db'):
            Pykell.gen_db()
        con = sqlite3.connect('cache.db')
        c = con.cursor()
        try:
            c.execute(sql_statement, vals)
            con.commit()
        except sqlite3.OperationalError:
            logging.exception("Data base error")
        except sqlite3.IntegrityError:
            logging.info('ID already exists')
        except:
            raise
        con.close()

    @staticmethod
    def gen_db():
        """
        sets up a SQLite database file called cache.db
        """
        logging.info('Generating cache.db')
        con = sqlite3.connect('cache.db')
        c = con.cursor()
        c.execute(
            'CREATE TABLE files (id TEXT NOT NULL PRIMARY KEY,name TEXT, template TEXT,fileHash TEXT, templateHash TEXT);')
        con.commit()
        con.close()

    @staticmethod
    def read_from_db(sql_statement, vals):
        """
        reads from database cache.db

        :param sql_statement: SQL statement to execute
        :param vals: values of the statement
        :return:
        """
        ret = None
        if not os.path.exists('cache.db'):
            Pykell.gen_db()
        con = sqlite3.connect('cache.db')
        c = con.cursor()
        _c = c.execute(sql_statement, vals)
        if isinstance(_c, sqlite3.Cursor):
            ret = c.fetchall()
        con.close()
        return ret

    @staticmethod
    def write_to_cache(file, template):
        """
        writes hashes of file and template to cache.db

        :param file: file to
        :param template:
        :return:
        """
        key = file + '_' + template
        file_hash = Pykell.gen_file_hash(file)
        template_hash = Pykell.gen_file_hash(template)
        ch = Pykell.check_hash(file, template)
        if ch == 2:
            Pykell.write_to_db('INSERT INTO files(id,name,template,fileHash,templateHash) VALUES(?,?,?,?,?)',
                               [key, file, template, file_hash, template_hash])
        elif ch == 0:
            Pykell.write_to_db('UPDATE files SET fileHash=?,templateHash=? WHERE id=?', [file_hash, template_hash, key])

    @staticmethod
    def execute_exernal(cmd):
        logging.info('Executing ' + cmd)
        call(cmd, shell=True)
