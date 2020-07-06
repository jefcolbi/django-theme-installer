from pathlib import Path
from theme_installer.constants import *
import re
import shutil
import logging
from theme_installer.loaders import BaseLoader
from theme_installer.utils import *

#logger = logging.getLogger('ThemeInstaller')
logger = logging.getLogger('')
logger.info = print


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
    rgx_find_format = r'(src|href)="(?:../)*({})' # capture the enclosing parts of the link
    rgx_repl_format = r'\1="/static/{}/\2' # replace with the enclosing parts captured
    rgx_href_find_format = r"(href ?= ?['\"])(.+\.html)(['\"])"
    rgx_href_repl_format = r'\1{% url "{}" %}\3'
    
    
    def __init__(self, name:str, from_dir:str, loader:BaseLoader, 
                 sub_theme=False, parent=None, prefix=None,
                 parent_assets_dir:list=None, root_name=None):
        loader_dirs = loader.to_dict()
        self.static_dir = Path(loader_dirs['static_dir'])
        self.from_dir = Path(from_dir)
        if not self.from_dir.exists():
            raise FileExistsError("The source path doesn't exist!")
        
        self.templates_dir = Path(loader_dirs['templates_dir'])
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
        
        #print(self.static_dir, self.from_dir, self.templates_dir)
        self.html_files = []
        self.asset_dirs = []
        self.sub_dirs = []
        self.parent_assets_dir = parent_assets_dir
        self.html_installed = []
        self.is_parent_asset_dir = False
        self.root_name = root_name
                
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
                
        if len(self.asset_dirs) < 1:
            for p in self.parent_assets_dir:
                if isinstance(p, (str, bytes)):
                    self.asset_dirs.append(Path(p))
                elif isinstance(p, Path):
                    self.asset_dirs.append(p)
            self.is_parent_asset_dir = True
            
                
        
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
                
                # check if we are a sub theme and we are used parent asset dirs
                if self.sub_theme and self.is_parent_asset_dir:
                    new = self.rgx_repl_format.format(self.root_name)
                elif self.parent_name: # we are sub dir but we don't use parent asset dirs
                    new = self.rgx_repl_format\
                        .format("{}/{}".format(self.parent_name, self.name))
                else:
                    new = self.rgx_repl_format.format(self.name)
                
                self.replacer(p, old, new)
                
                self.html_installed.append("{}/{}".format(self.name, p.name))
                
    def replace_hrefs_html(self, html_paths, urls:dict):
        """
        Replace html href with url tag
        """
        print('Fixing href links in html files...')
        # compile the regex to find href
        cmp_rgx_find = re.compile(self.rgx_href_find_format)
        
        # get a list of urls keys for fast access
        urls_keys = list(urls.keys())
        #cmp_rgx_rpl = re.compile(self.rgx_href_repl_format)
        
        for hp in html_paths:
            p:Path = self.templates_dir.joinpath(hp)
            if p.is_dir():
                continue            
            
            # we fetch the source
            sr_code = open(p).read()
            # we search for href
            res = cmp_rgx_find.findall(sr_code)
            # find the sub dir related to templates dir
            sub_dir = '/'.join(hp.split('/')[:-1])
            
            for couple in res:
                html_path = couple[1]
                cur_parent_p = p.parent
                
                # if the path is a back reference search the parent
                while '../' in html_path:
                    cur_parent_p = cur_parent_p.parent
                    html_path = html_path[3:]
                    
                # if the html_path start with / then the cur_parent should be 
                # the templates dir + name
                if html_path.startswith('/'):
                    cur_parent_p = self.templates_dir.joinpath(self.name)
                    html_path = html_path[1:]
                
                final_p:Path = cur_parent_p.joinpath(html_path)
                if not final_p.exists():
                    logger.warn("Template {} doesn't exist".format(final_p))
                    continue
                    
                # the html path should be relative to the template dir of the app
                html_path = str(final_p.relative_to(self.templates_dir.joinpath(self.name)))
                
                url_path = get_url_path_from_html_name(self.name, html_path)
                url_name = url_path.replace('/', '_').replace('-', '_')
                
                url_arg = "{}:{}".format(self.name, url_name)                
                new_url = "{% url '"+url_arg+"' %}"
                sr_code = sr_code.replace(couple[0]+couple[1], couple[0]+new_url)
                
            open(p, "w").write(sr_code)
            
        print('Fixing href links in html files done.')
            
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
            loader = BaseLoader(templates_dir=template, static_dir=static)
            sub_th = ThemeInstaller(name, base, loader, sub_theme=True,
                                    parent=self.name, root_name=self.root_name,
                                    parent_assets_dir=self.asset_dirs)
            sub_html_installed = sub_th.proceed()
            for sub_html in sub_html_installed:
                self.html_installed.append(self.name+'/'+sub_html)
            
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
        
        return self.html_installed
    
    
view_tpl = """
from django.shortcuts import render, redirect, reverse
from django.views.generic import TemplateView

{% for html_path, view_name in datas.items %}
class {{ view_name}}View(TemplateView):
    template_name = "{{ html_path }}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add data to context
        return context
    
{% endfor %}

class DefaultHandlerView(TemplateView):
    
    def get(self, *args, **kwargs):
        page = self.kwargs.get('page')
        self.template_name = "{{ app }}/"+page
        return super().get(*args, **kwargs)
"""
    
    
class ViewInstaller:
    
    def __init__(self, app, html_paths:list, home_dir=None):
        if not html_paths:
            raise ValueError("No valid list of html files")
        
        self.html_paths = html_paths
        self.app = app
        self.home_dir = home_dir
        
    def proceed(self) -> dict:
        print("Installing {}.views ...".format(self.app))
        from django.template import Template, Context
        
        res = {}
        for html_path in self.html_paths:
            res[html_path] = get_view_name_from_html_name(self.app, html_path)
            
        tpl = Template(view_tpl)
        view_content = tpl.render(Context({'datas':res, 'app':self.app}))
        
        if self.home_dir:
            view_file:Path = Path(self.home_dir).joinpath(self.app).joinpath('views.py')
        else:
            view_file:Path = Path(Path.cwd()).joinpath(self.app).joinpath('views.py')
            
        with view_file.open('w') as fp:
            fp.write(view_content)
            
        print("Installing {}.views done.".format(self.app))
        return res
    
    
url_tpl = """
from .views import *
from django.urls import path, re_path

urlpatterns = [
    {% if has_index %}path('', IndexView.as_view(), name='index0'),{% endif %}
    {% for html_path, values in datas.items %}path('{{ values.0 }}/', {{ values.1 }}View.as_view(), name="{{ values.2 }}"),    
    {% endfor %}
    re_path(r'(?P<page>[a-z0-a\-/]+\.html?)$', DefaultHandlerView.as_view(), name="defaut_handler"),
]
"""
    
    
class UrlInstaller:
    
    rgx_find_format = r'(urlpatterns[\t ]*=[\t ]*\[)'
    rgx_repl_format = r'\1\n    path("{app}/", include(("{app}.urls", "{app}"), namespace="{app}")), '\
        '# added by theme installer'
    
    rgx_set_find_format = r'(INSTALLED_APPS[\t ]*=[\t ]*\[)'
    rgx_set_repl_format = r'\1\n    "{app}", # added by theme installer'    
    
    def __init__(self, app, html_paths:list, views:dict, home_dir=None):
        if not html_paths:
            raise ValueError("No valid list of html files")
        
        self.html_paths = html_paths
        self.app = app
        self.home_dir = home_dir
        self.views = views
        
    def proceed(self):
        print("Installing {}.urls...".format(self.app))
        from django.template import Template, Context
        
        res = {}
        for html_path in self.html_paths:
            url_path = get_url_path_from_html_name(self.app, html_path)
            url_name = url_path.replace('/', '_').replace('-', '_')
            view_name = self.views.get(html_path)
            res[html_path] = (url_path, view_name, url_name)
            
        tpl = Template(url_tpl)
        has_index = True if 'Index' in self.views.values() else False
        url_content = tpl.render(Context({'datas':res, 'has_index':has_index}))
        
        if self.home_dir:
            url_file:Path = Path(self.home_dir).joinpath(self.app).joinpath('urls.py')
        else:
            url_file:Path = Path(Path.cwd()).joinpath(self.app).joinpath('urls.py')
            
        with url_file.open('w') as fp:
            fp.write(url_content)
            
        print("Installing {}.urls done.".format(self.app))
        return res
    
    def install_in_root(self, app, settings, home_dir=None):
        if home_dir:
            home_path = Path(home_dir)
        else:
            home_path = Path(settings.BASE_DIR)
            
        root_url_file:Path = home_path.joinpath(settings.ROOT_URLCONF.replace('.', '/')+'.py')
        print("Adding {}.urls in {} ...".format(self.app, root_url_file))
        src_code = root_url_file.open().read()
        
        pattern = r'path\("{app}/", include\(\("{app}.urls", "{app}"\), namespace="{app}"\)\)'.format(app=app)
        res = re.search(pattern, src_code, flags=re.MULTILINE)
        if not res:
            old = self.rgx_find_format
            new = self.rgx_repl_format.format(app=app)
            
            src_code = re.sub(old, new, src_code, flags=re.MULTILINE)
            if "import {}".format(app, src_code) not in src_code:
                src_code = "import {} # added by theme installer\nfrom django.urls import include\n\n{}".format(app, src_code)
            
            root_url_file.open('w').write(src_code)
        print("Adding {}.urls in {} done.".format(self.app, root_url_file))
            
        # adding in INSTALLED_APPS
        settings_file:Path = home_path.joinpath(settings.SETTINGS_MODULE.replace('.', '/')+'.py')
        print("Adding {} in {} ...".format(self.app, settings_file))
        src_code = settings_file.open().read()
        
        res = re.search(r'[\t ]*["\']{}["\']'.format(app), src_code, flags=re.MULTILINE)
        if not res:        
            old = self.rgx_set_find_format
            new = self.rgx_set_repl_format.format(app=app)
            
            src_code = re.sub(old, new, src_code, flags=re.MULTILINE)
            
            settings_file.open('w').write(src_code)
        
        print("Adding {} in {} done.".format(self.app, settings_file))
        
        
if __name__ == "__main__":
    th = ThemeInstaller('dashboard', '/home/jefcolbi/Themes/Admin/elmerhtml/elmerhtml/elmer_themeforest/html/',
                        '/home/jefcolbi/Projets/MboateK/tambeh/src/tambeh/base/static/',
                        '/home/jefcolbi/Projets/MboateK/tambeh/src/tambeh/templates/')
    th.proceed()
