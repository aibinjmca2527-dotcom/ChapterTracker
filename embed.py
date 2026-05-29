import os

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

with open('api/index.py', 'r', encoding='utf-8') as f:
    api_content = f.read()

# Replace render_template with render_template_string
api_content = api_content.replace('from flask import Flask, request, jsonify, render_template, make_response', 'from flask import Flask, request, jsonify, render_template_string, make_response')

# Replace the index route
old_route = '''@app.route("/")
def index():
    resp = make_response(render_template("index.html"))'''

new_route = f'''HTML_TEMPLATE = """{html_content}"""

@app.route("/")
def index():
    resp = make_response(render_template_string(HTML_TEMPLATE))'''

api_content = api_content.replace(old_route, new_route)

with open('api/index.py', 'w', encoding='utf-8') as f:
    f.write(api_content)
print('Successfully embedded HTML into api/index.py')
