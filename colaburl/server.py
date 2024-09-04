"""Server code for ColabURL."""

import hashlib
import json
import os
import re
from base64 import urlsafe_b64decode
from datetime import datetime

import github
import lz4.block
from flask import Flask, redirect, request
from flask.typing import ResponseReturnValue
from flask_cors import CORS
from github import Github

gh = Github(os.environ['GITHUB_TOKEN'])
user = gh.get_user()

app = Flask("colaburl")
CORS(app)


@app.get('/')
def get() -> ResponseReturnValue:
    """GET /?py=... or /?ipynb=..."""
    assert len({'py', 'py64', 'ipynb', 'ipynb64'} & set(request.args)) == 1
    if 'ipynb' in request.args:
        code = request.args['ipynb']
        fmt = 'ipynb'
    if 'ipynb64' in request.args:
        code = request.args['ipynb64']
        fmt = 'ipynb.b64'
    elif 'py' in request.args:
        code = request.args['py']
        fmt = 'py'
    elif 'py64' in request.args:
        code = request.args['py64']
        fmt = 'py.b64'
    colab_url = generate(code, fmt, request.args.get('name', 'notebook.ipynb'))
    return redirect(colab_url)


@app.get('/<path:code>')
def get_code(code: str) -> ResponseReturnValue:
    """GET /..."""
    if code.endswith('.lz4'):
        code = code[:-len('.lz4')]
        fmt = 'py.lz4'
    elif code.endswith('.b64'):
        code = code[:-len('.b64')]
        fmt = 'py.b64'
    colab_url = generate(code, fmt, request.args.get('name', 'notebook.ipynb'))
    return redirect(colab_url)


@app.post('/')
def post() -> ResponseReturnValue:
    """POST /."""
    assert len({'ipynb', 'ipynb.b64', 'ipynb.lz4', 'py', 'py.b64', 'py.lz4'} & set(request.form)) == 1
    if 'ipynb' in request.form:
        code = request.form['ipynb']
        fmt = 'ipynb'
    elif 'ipynb.b64' in request.form:
        code = request.form['ipynb.b64']
        fmt = 'ipynb.b64'
    elif 'ipynb.lz4' in request.form:
        code = request.form['ipynb.lz4']
        fmt = 'ipynb.lz4'
    elif 'py' in request.form:
        code = request.form['py']
        fmt = 'py'
    elif 'py.b64' in request.form:
        code = request.form['py.b64']
        fmt = 'py.b64'
    elif 'py.lz4' in request.form:
        code = request.form['py.lz4']
        fmt = 'py.lz4'
    colab_url = generate(code, fmt, request.args.get('name', 'notebook.ipynb'))
    return redirect(colab_url)


def generate(code: str, fmt: str, notebook_name: str) -> str:
    """Generate a Colab URL from code."""
    if fmt == 'ipynb':
        notebook = code
    if fmt == 'ipynb.b64':
        notebook = urlsafe_b64decode(code.encode()).decode()
    if fmt == 'ipynb.lz4':
        notebook = lz4.block.decompress(urlsafe_b64decode(code.encode())).decode()
    else:
        if fmt == 'py':
            py = code
        elif fmt == 'py.b64':
            py = urlsafe_b64decode(code.encode()).decode()
        elif fmt == 'py.lz4':
            py = lz4.block.decompress(urlsafe_b64decode(code.encode())).decode()
        # two or more \n without indentation following indicates a new cell
        cells = re.split(r'(?:\r?\n){2,}(?!(?: |\n|\r))', py)
        notebook = json.dumps({
            "nbformat": 4,
            "nbformat_minor": 0,
            "metadata": {},
            "cells": [
                {
                    "cell_type": "code",
                    "source": cell,
                    "metadata": {"id": str(i)}
                } for i, cell in enumerate(cells)
            ]
        })
    repo_name = hashlib.md5(json.dumps({'name': notebook_name, 'content': notebook}).encode()).hexdigest()
    repo = None
    try:
        repo = user.create_repo(repo_name)
    except github.GithubException as ex:
        if ex.status != 422:
            raise

    if repo:
        repo.create_file(notebook_name, 'autocommit', notebook)

    return f'https://colab.research.google.com/github/colaburl/{repo_name}/blob/main/{notebook_name}'


@app.route('/cleanup', methods=['POST', 'DELETE'])
def cleanup() -> ResponseReturnValue:
    """Cleanup old repos."""
    user = gh.get_user()
    for repo in user.get_repos():
        delta = datetime.utcnow() - repo.created_at.replace(tzinfo=None)
        if delta.seconds > 60:
            repo.delete()
    return {'success': True}
