from pathlib import Path
from theme_installer.constants import TEMPLATES_DIR_NAMES, STATIC_DIR_NAMES


class BaseLoader:
    
    def __init__(self, home_dir=None, templates_dir=None,
                 static_dir=None, **kwargs):
        self.home_dir = home_dir
        self.templates_dir = templates_dir
        self.static_dir = static_dir
        
    def to_dict(self):
        return {
            "home_dir": self.home_dir,
            "templates_dir": self.templates_dir,
            "static_dir": self.static_dir
        }
    
    
class ClientLoader(BaseLoader):
    
    def __init__(self, home_dir=None, templates_dir=None, static_dir=None, **kwargs):
        self.templates_dir =None
        self.static_dir = None
        self.home_dir = None
        home_dir_sent = home_dir
        
        for home_dir in [home_dir_sent, Path.cwd()]:
        
            if templates_dir:
                self.templates_path = Path(templates_dir)
                if self.templates_path.exists() and self.templates_path.is_absolute():
                    self.templates_dir = str(self.templates_path)
                    
            if static_dir:
                self.static_path = Path(static_dir)
                if self.static_path.exists() and self.static_path.is_absolute():
                    self.static_dir = str(self.static_path)
                    
            if home_dir:
                self.home_path = Path(home_dir)
                if self.home_path.exists():
                    self.home_dir = str(self.home_path)
                                    
            # if the templates_dir was not an absolute path try to see 
            # if it is relative to relative to self.home_path
            if not self.templates_dir and self.home_path:
                if templates_dir:
                    if self.home_path.joinpath(templates_dir).exists():
                        self.templates_dir = str(self.home_path.joinpath(templates_dir))
                
                if not self.templates_dir:                
                    # we didn't find the templates_dir so we try a list of 
                    # common templates dir names
                    for tp_dir in TEMPLATES_DIR_NAMES:
                        if self.home_path.joinpath(tp_dir).exists():
                            ch = input("We didn't find `{}`, but we found `{}` do "
                                       "you want to use it as a the template dir? [Y|n]"\
                                       .format(templates_dir if templates_dir else ""
                                               , tp_dir))
                            ch = ch.lower()
                            if len(ch) == 0 or ch[0] == 'y':
                                self.templates_dir = str(self.home_path.joinpath(tp_dir))
                                break
                            
            # if the static_dir was not an absolute path try to see 
            # if it is relative to relative to self.home_path
            if not self.static_dir and self.home_path:
                if static_dir:
                    if self.home_path.joinpath(static_dir).exists():
                        self.static_dir = str(self.home_path.joinpath(static_dir))
                
                if not self.static_dir:
                    # we didn't find the static_dir so we try a list of 
                    # common static dir names
                    for st_dir in STATIC_DIR_NAMES:
                        if self.home_path.joinpath(st_dir).exists():
                            ch = input("We didn't find `{}`, but we found `{}` do "
                                           "you want to use it as a the template dir? [Y|n]"\
                                           .format(static_dir if static_dir else ""
                                                   , st_dir))
                            ch = ch.lower()
                            if len(ch) == 0 or ch[0] == 'y':
                                self.static_dir = str(self.home_path.joinpath(st_dir))
                                break
                            
            if self.static_dir and self.templates_dir:
                break
                              
        if not self.static_dir:
            raise FileNotFoundError("We are unable to find the static dir")
        if not self.templates_dir:
            raise FileNotFoundError("We are unable to find the templates dir")
        
        # not very important but we respect the MRO
        super().__init__(self.home_dir, self.templates_dir, self.static_dir, **kwargs)
        
        
class CommandLoader(BaseLoader):
    """
    This class should be used in a django management commands
    """
    
    def __init__(self, settings, app=None, **kwargs):
        self.static_dir = None
        self.templates_dir = None
        
        self.home_dir = getattr(settings, 'BASE_DIR', '')
        if not self.home_dir:
            self.home_dir = getattr(settings, 'HOME_DIR', '')
        if not self.home_dir:
            raise FileNotFoundError('Unable to find BASE_DIR or HOME_DIR in settings')
        
        self.home_path = Path(self.home_dir)
        if app:
            self.create_app_and_dirs(app)
        else:
            self.find_dirs_from_settings(settings)
            
        if not self.static_dir:
            raise FileNotFoundError("We are unable to find the static dir")
        if not self.templates_dir:
            raise FileNotFoundError("We are unable to find the templates dir")
        
        # not very important but we respect the MRO
        super().__init__(self.home_dir, self.templates_dir, self.static_dir, **kwargs)        
        
    def create_app_and_dirs(self, app):
        self.app_path:Path = self.home_path.joinpath(app)
        if not (self.app_path.exists() or \
                self.app_path.joinpath('__init__.py').exists()):
            from django.core.management import execute_from_command_line
            args = ['manage.py', 'startapp', app]
            execute_from_command_line(args)        
        
        self.static_path:Path = self.app_path.joinpath('static')
        self.templates_path:Path = self.app_path.joinpath('templates')
        
        self.static_path.mkdir(exist_ok=True, parents=True)
        self.templates_path.mkdir(exist_ok=True, parents=True)
              
        self.static_dir = str(self.static_path)
        self.templates_dir = str(self.templates_path)
        
    def find_dirs_from_settings(self, settings):
        if settings.TEMPLATES:
            s_tpl_dirs = settings.TEMPLATES[0]['DIRS']
            if len(s_tpl_dirs):
                self.templates_dir = s_tpl_dirs[0]
                
        if getattr(settings, 'STATICFILES_DIRS', None)\
           and len(settings.STATICFILES_DIRS):
           self.static_dir = settings.STATICFILES_DIRS[0] 
        
                

if __name__ == "__main__":
    loader = ClientLoader(home_dir="/home/jefcolbi/Projets/Yaknema/zoutil/src/zoutil",
                          static_dir="/home/jefcolbi/Projets/Yaknema/zoutil/src/zoutil/dev_static", 
                          templates_dir="/home/jefcolbi/Projets/Yaknema/zoutil/src/zoutil/templates")
    print(loader.to_dict())
