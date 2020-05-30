#!/usr/bin/env python
"""
The client of Django Theme Installer
Usage:
    theme_cli.py -n name -s /path/to/html/source/ -c /path/to/djangoproject/static/
        -t /path/to/djangoproject/templates/
"""
from theme_installer.core import ThemeInstaller
import argparse

parser = argparse.ArgumentParser(description="Install a theme in the specified "
                                 "Django dirs")

parser.add_argument('-n', '--name', help='The name of the theme')
parser.add_argument('-s', '--source', help='The source dir of the theme')
parser.add_argument('-t', '--templates', help='The destination directory '
                    'of the templates')
parser.add_argument('-c', '--static', help="The destination directory "
                    "of the static files")
parser.add_argument('-p', '--prefix', help="The prefix of the static links "
                    "in template. Default /static/")

args = parser.parse_args()

if not(args.name and args.source and args.static and args.templates):
    parser.print_help()
    import os
    os._exit(0)

ti = ThemeInstaller(args.name, args.source, args.static, args.templates, 
                    prefix=args.prefix)
ti.proceed()

print("Installation done!")
