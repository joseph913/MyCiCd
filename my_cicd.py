#! /usr/bin/python3
import os
import sys
import shutil
import signal

import git
import docker
from pyngrok import ngrok
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config, view_defaults
from pyramid.response import Response
from github import Github


DOC_CLI = docker.from_env()
LOCALHOST = '127.0.0.1'
EXPOSE_PORT = 65010
CONTAINER_EXPOSE_PORTS = {'tcp': 8000}
LOCAL_REPO_PATH = 'remote_path'
ENDPOINT = "webhook"
PROTOCOL = 'https://'
GIT_SUFFIX = '.git'
GIT_ACCESS_TPL = '{protocol}{user}:{token}@{hub}/{user}/{repo}'

create_hook_data = {
    'name': 'web', 'active': True, 'events': ['push'],
    'config': {'url': None, 'content_type': 'json', 'insecure_ssl': '0'}}
local_repo = None
container = None
expose_ports = None
local_repo_path = None


def reset_container():
    global container, expose_ports, local_repo_path

    print('resetting container...')
    container.stop()
    container.remove()

    img = DOC_CLI.images.build(path=local_repo_path, tag='local_img')[0]
    container = DOC_CLI.containers.run(img, name='local', ports=expose_ports, detach=True)


def shutdown(sig, frame):
    print('cleaning up...')
    container.stop()
    container.remove()
    sys.exit(0)


@view_defaults(
    route_name=ENDPOINT, renderer="json", request_method="POST"
)
class PayloadView(object):
    def __init__(self, request):
        self.request = request
        self.payload = self.request.json

    @view_config(header="X-Github-Event:push")
    def payload_push(self):
        print("Number of commits in push:", len(self.payload['commits']))
        local_repo.remote().pull()
        reset_container()
        return Response("success")

    @view_config(header="X-Github-Event:ping")
    def payload_else(self):
        print("Pinged! Webhook created with id {}!".format(self.payload["hook"]["id"]))
        return {"status": 200}


if __name__ == "__main__":
    try:
        usr_repo_url = sys.argv[1]
        token = sys.argv[2]
        url_parts = sys.argv[1][len(PROTOCOL):].split('/')
        user_name = url_parts[-2]
        repo_name = url_parts[-1][:len(url_parts[-1]) - len(GIT_SUFFIX)]
    except Exception as e:
        print('Something wrong with arguments')
        sys.exit()

    if os.path.isdir(repo_name):
        shutil.rmtree(repo_name)

    remote_repo_url = GIT_ACCESS_TPL.format(
        protocol=PROTOCOL, user=user_name, token=token, hub=url_parts[0], repo=url_parts[-1])
    local_repo_path = './{}'.format(repo_name)
    local_repo = git.Repo.clone_from(remote_repo_url, repo_name)

    print('running container...')
    image = DOC_CLI.images.build(path=local_repo_path, tag='local_img')[0]
    expose_ports = {c: CONTAINER_EXPOSE_PORTS.get(c.split('/')[1], dict())
                    for c, h in image.attrs['ContainerConfig']['ExposedPorts'].items()}
    container = DOC_CLI.containers.run(image, name='local', ports=expose_ports, detach=True)
    github = Github(token)
    remote_repo = github.get_repo('/'.join((user_name, repo_name)))
    create_hook_data['config']['url'] = '/'.join((ngrok.connect(EXPOSE_PORT), ENDPOINT))
    config = Configurator()

    print('hooking up...')
    remote_repo.create_hook(**create_hook_data)
    config.add_route(ENDPOINT, "/{}".format(ENDPOINT))
    config.scan()

    app = config.make_wsgi_app()
    server = make_server("0.0.0.0", EXPOSE_PORT, app)

    signal.signal(signal.SIGINT, shutdown)
    server.serve_forever()
