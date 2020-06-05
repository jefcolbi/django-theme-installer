
import re

rgx_bad_start = re.compile("^([^A-Za-z]+)")

def get_view_name_from_html_name(app:str, html_name:str) -> str:
    if html_name.startswith(app):
        html_name = html_name.replace(app+'/', '', 1)
        
    html_name = html_name.replace('.html', '')
    html_name = html_name.replace('/', '_').replace('-', '_').replace(' ', '_')
    view_name = ''.join(x.capitalize() or '_' for x in html_name.split('_'))
    res = rgx_bad_start.search(view_name)
    if res:
        bad = res.group(1)
        view_name = view_name.replace(bad, '', 1)+bad
        
    return view_name

def get_url_path_from_html_name(app:str, html_name:str) -> str:
    if html_name.startswith(app):
        html_name = html_name.replace(app+'/', '', 1)
        
    html_name = html_name.replace('.html', '')
    url_name = html_name.lower()
        
    return url_name

def html_name_key(html_name:str):
    sl_cnt = html_name.count('/')
    real_len = len(html_name.split('/')[-1].split('.html')[0])
    return sl_cnt*100 + real_len


if __name__ == "__main__":
    print(get_view_name_from_html_name('bruce', 'bruce/index.html'))
    print(html_name_key('bruce/index.html'))
