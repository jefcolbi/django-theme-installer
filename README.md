# Django Theme Installer

### Why?
When you start a new Django project and you are not so good in HTML or don't want to waste your time or found a beautiful free theme, you manually copy it in your django project and start editing it.  
Django Theme Installer do this work for you.

### Installation
    $ pip install django-theme-installer
    
### Usage
Add 'theme_installer' in INSTALLED_APPS  
Then run 

    $ python manage.py theme_install theme_name /path/where/the/html/files/are/located
    
### Tutorial
Let's fetch a simple html5 templates and install it
```bash
mkdir myproj
cd myproj/
virtualenv -p python3 .env
source .env/bin/activate
pip install django~=2.2
pip install --upgrade django-theme-installer
wget https://github.com/BlackrockDigital/startbootstrap-creative/archive/gh-pages.zip
unzip gh-pages.zip
django-admin startproject myproj
cd startbootstrap-creative-gh-pages/
themedir=`pwd`
cd .. && cd myproj/
awk 'NR==36{print; print "    \"theme_installer\","; next}7' myproj/settings.py > testfile.tmp && mv testfile.tmp myproj/settings.py
python manage.py theme_install creative $themedir
python manage.py runserver 8000
```
Open your browser to http://localhost:8000/creative/index/

### Documentation
Django theme installer needs basically 3 folders to work: The source folder where the html template (html + assets dirs) is localted, the django static folder where the assets should go and the django templates folder where html files goes.  
Django theme installer is build on the standard pathlib and use a recursive model. This recursive model make him capable of handling sub-themes.  
Django theme installer is built over two types of classes: **Loaders** and **Installlers**

###### Loaders
Loaders are there to provide three folders to the ThemeInstaller class, those folders are: **static_dir**, **templates_dir** and **home_dir**. The home_dir can be null.

###### Installers
Installers are there to create and maybe modify/transform some files on the django side. For example the ThemeInstaller class install html and assets files, but ViewsInstaller creates views in app/views.py

#### Management command
The management command need barely two arguments: the name of the theme in django side and the path of the source html templates. We say `the name of the theme` here because this name is used for templates path, static path and sometimes for the app name.  
positional arguments:                                                                                                                        
-  name                  The name of the theme, it will be the name of the app if --app is omitted                                                                                    
-  source                The path of the theme                                                                                                
                                                                                                                                             
optional arguments:                                                                                                                          
-  --app APP             The name of the app where to install the static, templates, views and urls.
-  --assets-dir ASSETS_DIR [ASSETS_DIR ...]
                        The directory where to find assets, useful in case the assets are not in the same folder with the html files.
-  --subthemes           Include sub themes, if you want to process the sub themes
-  --prefix              The STATIC_URL prefix to override default `static`

Example:  
`python manage.py theme_install fine /home/xxx/themes/fine --app base`
  
#### Via the client
    $ theme_cl.py -n name -s /path/to/html/source/ -c /path/to/djangoproject/static/ -t /path/to/djangoproject/templates/
    
#### Via the code
    >>> th = ThemeInstaller(name, "/path/to/html/source/", loader)"
    >>> th.proceed()

### Contributing
If you find a html theme which can't be installed with django theme installer, open an issue with the link to this theme. I will download it and fix it.  
No nulled or cracked themes.  
Contributions are welcome, all PRs will be reviewed and merged.

### License
Feel free to use it as you want.
