#!c:\\python27\python.exe
# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=F0401

'''
Hex-Rays Decompiler Enhanced View plugin (HRDEV).

This is a simple plugin to view somewhat enhanced decompiler output. For more
information check out github: https://github.com/ax330d/hrdev/.
'''

import re
import os
import ConfigParser

from PySide import QtGui
import idaapi
import idc

import include.syntax
import include.gui
import include.helper

idaapi.require('include.syntax')
idaapi.require('include.gui')
idaapi.require('include.helper')


__author__ = 'Arthur Gerkis'
__version__ = '0.0.1 (beta)'


class Plugin(object):
    '''Implements the main plugin class, entry point.'''

    def __init__(self, real_dir):
        super(Plugin, self).__init__()
        self.tools = include.helper.Tools(self)
        self.config_main = ConfigParser.ConfigParser()
        self.config_theme = ConfigParser.ConfigParser()

        self._bin_md5 = idc.GetInputMD5()
        self._bin_name = re.sub(r'\.[^.]*$', '', idc.GetInputFile())

        self._read_config(real_dir)
        self.gui = None
        self.parser = None

    def _read_config(self, real_dir):
        '''Read config and initialise variables.'''

        dir_chunks = real_dir.split(os.path.sep)
        dir_chunks.pop()

        self.current_dir = os.path.sep.join(dir_chunks)
        config_path = os.path.sep.join([self.current_dir,
                                        'data', 'config.ini'])

        self.config_main.read(config_path)
        theme_name = str(self.config_main.get('editor', 'highlight_theme'))

        theme_config_path = os.path.sep.join([self.current_dir,
                                              'data', 'themes',
                                              '{}.ini'.format(theme_name)])

        self.config_theme.read(theme_config_path)
        return

    def run(self):
        '''Start the plugin.'''

        if not idaapi.init_hexrays_plugin():
            print "HRDEV Error: Failed to initialise Hex-Rays plugin."
            return

        function_name = idaapi.get_func_name(idaapi.get_screen_ea())
        demangled_name = self.tools.demangle_name(function_name)
        file_name = '{}.cpp'.format(self.tools.to_file_name(demangled_name))

        cache_path = os.path.sep.join([self.current_dir,
                                       'data', 'cache',
                                       self._bin_name])
        if not os.path.isdir(cache_path):
            os.mkdir(cache_path)

        complete_path = os.path.sep.join([cache_path, file_name])
        if not os.path.isfile(complete_path):
            src = str(idaapi.decompile(idaapi.get_screen_ea()))
            self.tools.save_file(complete_path, src)
        self.tools.set_file_path(complete_path)

        max_title = self.config_main.getint('etc', 'max_title')
        self.gui = include.gui.Canvas(self.config_main,
                                      self.config_theme,
                                      self.tools,
                                      demangled_name[:max_title])
        self.gui.Show('HRDEV')

        self.parser = include.syntax.Parser(self)
        self.parser.run(complete_path)
        return


def main(real_dir):
    '''Simple wrapper.'''
    try:
        Plugin(real_dir).run()
    except Exception, error:
        print error
    return

if __name__ == '__main__':
    PLUGIN_PATH = os.path.realpath(__file__)
    idaapi.CompileLine('static __run_main()'
                       '{ RunPythonStatement("main(PLUGIN_PATH)"); }')
    idc.AddHotkey('Alt-,', '__run_main')
