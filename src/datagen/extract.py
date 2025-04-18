# Extracting data from the Minecraft jars

from .download import (
    get_mappings_for_version,
    get_server_jar,
    get_burger,
    get_client_jar,
)
from .utils import get_dir_location
from zipfile import ZipFile
import subprocess
import json
import re
import os


def generate_data_from_server_jar(version_id: str):
    if os.path.exists(get_dir_location(f'__cache__/generated-{version_id}')):
        return

    get_server_jar(version_id)
    os.system(
        f'cd {get_dir_location("__cache__")} && java -DbundlerMainClass=net.minecraft.data.Main -jar {get_dir_location(f"__cache__/server-{version_id}.jar")} --all --output "{get_dir_location(f"__cache__/generated-{version_id}")}"'
    )


def get_block_states_report(version_id: str):
    return get_report(version_id, 'blocks')


def get_registries_report(version_id: str):
    return get_report(version_id, 'registries')


def get_packets_report(version_id: str):
    return get_report(version_id, 'packets')


def get_report(version_id: str, name: str):
    generate_data_from_server_jar(version_id)
    with open(
        get_dir_location(f'__cache__/generated-{version_id}/reports/{name}.json'), 'r'
    ) as f:
        return json.load(f)


def get_registry_tags(version_id: str, name: str):
    generate_data_from_server_jar(version_id)
    tags_directory = get_dir_location(
        f'__cache__/generated-{version_id}/data/minecraft/tags/{name}'
    )
    if not os.path.exists(tags_directory):
        return {}
    tags = {}
    for root, dirs, files in os.walk(tags_directory, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            relative_path = file.replace(tags_directory, '')[1:]
            if not file.endswith('.json'):
                continue
            with open(file, 'r') as f:
                tags[relative_path[:-5]] = json.load(f)
    return tags


python_command = None


def run_python_command_and_download_deps(command):
    print('>', command)
    for _ in range(10):
        p = subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)

        stderr = b''
        while True:
            data = p.stderr.read()
            if data == b'':
                break
            print(data.decode(), end='', flush=True)
            stderr += data

        regex_match = re.search(
            r'ModuleNotFoundError: No module named \'(\w+?)\'', stderr.decode()
        )
        if not regex_match:
            out, err = p.communicate()
            if out:
                print(out)
            if err:
                print(err)
            break
        missing_lib = regex_match.group(1)
        print('Missing required lib:', missing_lib)
        os.system(f'venv/bin/pip install {missing_lib}')
    print('ok')


def get_burger_data_for_version(version_id: str):
    generated_data_path = get_dir_location(f'__cache__/burger-{version_id}.json')
    if os.path.exists(generated_data_path):
        with open(generated_data_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass

    get_burger()
    get_client_jar(version_id)
    get_mappings_for_version(version_id)

    print('\033[92mRunning Burger...\033[m')

    run_python_command_and_download_deps(
        f'cd {get_dir_location("__cache__/Burger")} && '
        f'venv/bin/python munch.py {get_dir_location("__cache__")}/client-{version_id}.jar '
        f'--output {get_dir_location("__cache__")}/burger-{version_id}.json '
        f'--mappings {get_dir_location("__cache__")}/mappings-{version_id}.txt'
    )

    with open(generated_data_path, 'r') as f:
        return json.load(f)


def get_file_from_jar(version_id: str, file_dir: str):
    get_client_jar(version_id)
    with ZipFile(get_dir_location(f'__cache__/client-{version_id}.jar')) as z:
        with z.open(file_dir) as f:
            return f.read()


def get_en_us_lang(version_id: str):
    return json.loads(get_file_from_jar(version_id, 'assets/minecraft/lang/en_us.json'))
