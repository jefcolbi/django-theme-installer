# Django Theme Installer

### Why?
When you start a new Django project and you are not so good in HTML or don't want to waste your time or find a beautiful free theme, you manually copy it in your django project and start editing it.  
Django Theme Installer do this work for you.

### Installation
    $ pip install django-theme-installer
    
### Usage
##### Via the client
    $ theme_cl.py -n name -s /path/to/html/source/ -c /path/to/djangoproject/static/ -t /path/to/djangoproject/templates/
    
##### Via the code
    >>> th = ThemeInstaller(name, "/path/to/html/source/", "/path/to/djangoproject/static", "/path/to/djangoproject/templates"
    >>> th.proceed()

### Contributing
Contributions are welcome, all PRs will be reviewed and merged.

### License
Feel free to use it as you want.
