import os
import shutil

import markdown
import toml

data = toml.load('config.toml')
site = data['site']
host_title = site['title']
host = site['host']

domain_css = 'theme/css/domain.css'
domain_target = 'public/meta_css'

if not os.path.exists(domain_target):
    os.makedirs(domain_target)
shutil.copyfile(domain_css, domain_target + "/domain.css")

# 处理每个目录要展示的内容
content = 'content'
len_content = len(content)
g = os.walk('content')
blog_titles = []
for path, dir_list, file_list in g:
    for file_name in file_list:
        file_name_no_ext = file_name[:-3]
        blog_titles.append(file_name_no_ext)
        full_path = f"{path}/{file_name}"
        f = f'content/{file_name}'
        file = open(full_path, encoding='utf-8')
        md_content = file.read()
        html = markdown.markdown(md_content, extensions=['fenced_code', 'codehilite'])
        blog_templ_path = 'theme/blog.html'
        blog_temp_file = open(blog_templ_path, encoding='utf-8')
        blog_html_template = blog_temp_file.read()
        blog_html_template = blog_html_template.replace('${{title}}', file_name_no_ext)
        blog_html_template = blog_html_template.replace('${{content}}', html)
        blog_html_template = blog_html_template.replace('${{host}}', host)
        # 将内容输出到 public 目录下
        path_no_prefix = path[len_content + 1:]
        target_parent = f"public/{path_no_prefix}"
        if not os.path.exists(target_parent):
            os.makedirs(target_parent)
        target_path = f'{target_parent}/{file_name_no_ext}.html'
        slash_count = target_path.count("/") - 1
        relative_path = ''
        if slash_count == 1:
            relative_path = '../'
        elif slash_count == 2:
            relative_path = '../../'
        relative_path += 'meta_css/'
        blog_html_template = blog_html_template.replace("${{relative_path}}", relative_path)
        with open(target_path, "w", encoding='utf-8') as wf:
            wf.write(blog_html_template)

# 处理首页的展示
titles_html = ''
blog_index_path = 'theme/index.html'
blog_index = open(blog_index_path, encoding='utf-8')
blog_index_html = blog_index.read()
public_path = 'public'
pub_files = os.listdir(public_path)
for pf in pub_files:
    if pf.find(".html") == -1 and pf.find("meta_css") == -1:
        titles_html += f'<li> <a href="{pf}/index.html">{pf}</a></li>'

blog_index_html = blog_index_html.replace("${{content}}", titles_html)
blog_index_html = blog_index_html.replace("${{relative_path}}", 'meta_css/')
blog_index_html = blog_index_html.replace("${{title}}", host_title)
blog_index_target_path = f'public/index.html'

with open(blog_index_target_path, "w", encoding='utf-8') as wf:
    wf.write(blog_index_html)

# 处理每个目录要展示的index.html

blog_index_path = 'theme/index.html'
blog_index = open(blog_index_path, encoding='utf-8')
blog_index_html = blog_index.read()
public_path = 'public'
pub_files = os.listdir(public_path)
for pf in pub_files:
    if pf.find(".html") == -1:
        titles_html = ''
        for pf2 in os.listdir(f"{public_path}/{pf}"):
            if pf2.find("index.html") == -1:
                titles_html += f'<li><a href="{pf2}">{pf2[:-5]}</a></li>'

        blog_index_copy = blog_index_html.replace("${{content}}", titles_html)
        blog_index_copy = blog_index_copy.replace("${{relative_path}}", '../meta_css/')
        blog_index_target_path = f'{public_path}/{pf}/index.html'
        with open(blog_index_target_path, "w", encoding='utf-8') as wf:
            wf.write(blog_index_copy)
