from pathlib import Path
from theme_installer.constants import *
import re
import shutil
import logging

logger = logging.getLogger('ThemeInstaller')


class ThemeInstaller:
    """
    This is the core class responsible of the installation of the theme
    
    :param str name: The name of the theme
    :param str from_dir: The path of the HTML theme
    :param str static_dir: the path to the static dir of the django project
    :param str templates_dir: The path to the templates dir of the django project.
    :param bool sub_theme: Whether or not this theme is a sub theme
    :param str parent: if this theme is a sub-theme his parent should be specified
    """
    
    rgx_html = re.compile(r"\.html?$")
    rgx_repl_format = r'\1="/static/{}/\2'
    rgx_find_format = r'(src|href)="({})'
    
    def __init__(self, name, from_dir, static_dir, templates_dir, 
                 sub_theme=False, parent=None, prefix=None):
        self.static_dir = Path(static_dir)
        self.from_dir = Path(from_dir)
        if not self.from_dir.exists():
            raise FileExistsError("The source path doesn't exist!")
        
        self.templates_dir = Path(templates_dir)
        self.name = name
        self.sub_theme = sub_theme
        self.parent_name = parent if parent else ''
        if prefix:
            self.rgx_repl_format = r'\1="/%s/{}/\2' % prefix
        
        if not self.static_dir.exists():
            if self.sub_theme:
                self.static_dir.mkdir()
            else:
                raise FileExistsError("The static dir doesn't exist")
            
        if not self.from_dir.exists():
            if sub_theme:
                self.from_dir.mkdir()
            else:
                raise FileExistsError("The theme dir doesn't exist")
            
        if not self.templates_dir.exists():
            if sub_theme:
                self.templates_dir.mkdir()
            else:
                raise FileExistsError("The template dir doesn't exist")
        
        print(self.static_dir, self.from_dir, self.templates_dir)
        self.html_files = []
        self.asset_dirs = []
        self.sub_dirs = []
                
    def load_from_dir(self):
        """
        Load all html files, assets and sub-themes from the source dir
        """
        for p in self.from_dir.iterdir():
            if p.is_dir() and p.name in ASSETS_NAMES:
                self.asset_dirs.append(p)
            elif p.is_dir():
                self.sub_dirs.append(p)
            elif self.rgx_html.search(p.name):
                self.html_files.append(p)
                
        
    def copy_html(self):
        """
        Copy the html files in the templates dir
        """
        dest_dir:Path = self.templates_dir.joinpath(self.name)
        try:
            dest_dir.mkdir()
        except FileExistsError:
            shutil.rmtree(dest_dir)
            dest_dir.mkdir()
            
        index_present = False
        for html in self.html_files:
            shutil.copyfile(html, dest_dir.joinpath(html.name))
            if html.name.startswith('index.htm'):
                index_present = True
                
        if not index_present:
            for html in self.html_files:
                if html.name.startswith('layout'):
                    shutil.copyfile(html, dest_dir.joinpath('index.html'))
                    break
                
    def copy_static(self):
        """
        Copy the assets to the static dir
        """
        dest_dir = self.static_dir.joinpath(self.name)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir()
        
        for f in self.asset_dirs:
            sta_dir = dest_dir.joinpath(f.name)
                
            shutil.copytree(f, sta_dir)
            
    def replace_static_html(self):
        """
        Fix asset paths to the static dir
        """
        for f in self.asset_dirs:
            for p in self.templates_dir.joinpath(self.name).iterdir():
                if p.is_dir():
                    continue
            
                old = self.rgx_find_format.format(f.name)
                if self.parent_name:
                    new = self.rgx_repl_format\
                        .format("{}/{}".format(self.parent_name, self.name))
                else:
                    new = self.rgx_repl_format.format(self.name)
                self.replacer(p, old, new)
            
    def replacer(self, source, old, new):
            sr_code = open(source).read()
            mod_code = re.sub(old, new, sr_code, flags=re.MULTILINE)
            open(source, "w").write(mod_code)
            
    def install_sub_themes(self):
        """
        Install all sub-themes.
        """
        for sub in self.sub_dirs:
            name = sub.name
            base = str(sub)
            static = str(self.static_dir.joinpath(self.name))
            template = str(self.templates_dir.joinpath(self.name))
            sub_th = ThemeInstaller(name, base, static, template,
                                    sub_theme=True, parent=self.name)
            sub_th.proceed()
            
    def proceed(self):
        """
        Method to do all the stuffs at once.
        """
        logger.info("Loading required files from directory...")
        self.load_from_dir()
        logger.info("Loading done.")
        
        logger.info("Copying html files....")
        self.copy_html()
        logger.info("Copying html files done.")
        
        logger.info("Copying static files...")
        self.copy_static()
        logger.info("Copying static files done.")
        
        logger.info("Fixing static paths in html files...")
        self.replace_static_html()
        logger.info("Fixing static paths in html files done.")
        
        logger.info("Installing sub themes...")
        self.install_sub_themes()
        logger.info("Installing sub themes done.")
        
        
if __name__ == "__main__":
    th = ThemeInstaller('dashboard', '/home/jefcolbi/Themes/Admin/elmerhtml/elmerhtml/elmer_themeforest/html/',
                        '/home/jefcolbi/Projets/MboateK/tambeh/src/tambeh/base/static/',
                        '/home/jefcolbi/Projets/MboateK/tambeh/src/tambeh/templates/')
    th.proceed()
