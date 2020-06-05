from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from theme_installer.loaders import CommandLoader
from theme_installer.core import ThemeInstaller, ViewInstaller, UrlInstaller


class Command(BaseCommand):
    """Install the theme"""
    
    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help="The name of the theme")
        parser.add_argument('source', type=str, help="The path of the theme")
        parser.add_argument('--app', help="The name of the app")
        parser.add_argument('--assets-dir', nargs='+', help="The directory where to find assets")
        parser.add_argument('--subthemes', action="store_true",
                            help="Include sub themes")
        parser.add_argument('--prefix', action="store_true",
                    help="The STATIC_URL prefix to override default `static`")
    
    def handle(self, *args, **options):        
        try:
            try:
                loader = CommandLoader(settings, app=options['app'])
                app = options['app']
            except FileNotFoundError:
                loader = CommandLoader(settings, app=options['name'])
                app = options['name']
                
            asset_dirs = options.get('assets_dir')
                
            th = ThemeInstaller(options['name'], options['source'], 
                                loader, sub_theme=options.get('subthemes'),
                                prefix=options.get('prefix'),
                                root_name=app, parent_assets_dir=asset_dirs)
            installed_htmls = th.proceed()
            
            vh = ViewInstaller(app, html_paths=installed_htmls,
                               home_dir=loader.to_dict().get('home_dir'))
            created_views = vh.proceed()
            
            uh = UrlInstaller(app, installed_htmls, created_views,
                              home_dir=loader.to_dict().get('home_dir'))
            created_urls = uh.proceed()
            
            th.replace_hrefs_html(installed_htmls, created_urls)
            
            uh.install_in_root(app, settings,
                               home_dir=loader.to_dict().get('home_dir'))
        except Exception as e:
            import traceback
            traceback.print_exc()

