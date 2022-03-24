import os

from flask import abort, Flask, jsonify, redirect, render_template, request
from werkzeug.wsgi import DispatcherMiddleware

from . import getconfig, util
from .filekeeper import delete_files, insert_link_to_latest, parse_docfiles, unpack_project

app = Flask(__name__)

app.config["APPLICATION_ROOT"] = getconfig.prefix
app.config['MAX_CONTENT_LENGTH'] = getconfig.max_content_mb * 1024 * 1024


@app.route('/upload')
def upload():
    project = request.args.get("project", "")
    return render_template('upload.html', project=project, **getconfig.renderables)


@app.route('/hmfd', methods=['POST', 'DELETE'])
def hmfd():
    if getconfig.readonly:
        return abort(403)

    if request.method == 'POST':
        if not request.files:
            return abort(400, 'Request is missing a zip/tar file.')
        uploaded_file = util.file_from_request(request)
        unpack_project(
            uploaded_file,
            request.form,
            getconfig.docfiles_dir
        )
        uploaded_file.close()
    elif request.method == 'DELETE':
        if getconfig.disable_delete:
            return abort(403)

        delete_files(
            request.args['name'],
            request.args.get('version'),
            getconfig.docfiles_dir,
            request.args.get('entire_project'))
    else:
        abort(405)

    return jsonify({'success': True})


@app.route('/')
def home():
    projects = parse_docfiles(getconfig.docfiles_dir, getconfig.docfiles_link_root)
    # TODO relative or absolute paths?
    insert_link_to_latest(projects, '%(project)s/latest')
    return render_template('index.html', projects=projects, **getconfig.renderables)


@app.route('/<project>/latest/')
def latest_root(project):
    return latest(project, '')


@app.route('/<project>/latest/<path:path>')
def latest(project, path):
    return version(project, "latest", path)


@app.route('/<project>/<vers>/')
def version_root(project, vers):
    return version(project, vers, "")


@app.route('/<project>/<version>/<path:path>')
def version(project, version, path):
    parsed_docfiles = parse_docfiles(getconfig.docfiles_dir, getconfig.docfiles_link_root)
    proj_for_name = dict((p['name'], p) for p in parsed_docfiles)
    if project not in proj_for_name:
        return 'Project %s not found' % project, 404

    if version == "latest":
        version_index = proj_for_name[project]['versions'][-1]['link']
    else:
        version_to_index = {version["version"]: version["link"] for version in proj_for_name[project]['versions']}
        if version not in version_to_index:
            return 'Version %s not found' % version, 404
        version_index = version_to_index.get(version, None)

    if path:
        version_link = '/%s/%s/%s' % (getconfig.docfiles_link_root, os.path.dirname(version_index), path)
    else:
        version_link = f'/{getconfig.docfiles_link_root}/{version_index}/index.html'
    print(project, version, path, version_link)
    print()
    # return redirect('/' + latestlink)
    return render_template('wrapper.html', embed_url=f"{version_link}", **getconfig.renderables)


app.wsgi_app = DispatcherMiddleware(Flask("placeholder"), {
    app.config['APPLICATION_ROOT']: app.wsgi_app,
})
