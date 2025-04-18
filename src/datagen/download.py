import xml.etree.ElementTree as ET

from .utils import get_dir_location
from .mappings import Mappings
import requests
import json
import os


def main():
    # make sure the cache directory exists
    if not path_exists(get_dir_location('__cache__')):
        print('Made __cache__ directory.', get_dir_location('__cache__'))
        os.mkdir(get_dir_location('__cache__'))


def get_burger():
    if not path_exists(get_dir_location('__cache__/Burger')):
        print('\033[92mDownloading Burger...\033[m')
        os.system(
            f'cd {get_dir_location("__cache__")} && git clone https://github.com/mat-1/Burger && cd Burger && git pull'
        )

        print('\033[92mInstalling dependencies...\033[m')
        os.system(
            f'cd {get_dir_location("__cache__")}/Burger && python3 -m venv venv && venv/bin/pip install six jawa'
        )


def get_pixlyzer():
    if not path_exists(get_dir_location('__cache__/pixlyzer')):
        print('\033[92mDownloading bixilon/pixlyzer...\033[m')
        os.system(
            f'cd {get_dir_location("__cache__")} && git clone https://gitlab.bixilon.de/bixilon/pixlyzer.git && cd pixlyzer && git pull'
        )
    return get_dir_location('__cache__/pixlyzer')


def get_version_manifest():
    if not file_has_content(get_dir_location('__cache__/version_manifest.json')):
        print('\033[92mDownloading version manifest...\033[m')
        version_manifest_data = requests.get(
            'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
        ).json()
        with open(get_dir_location('__cache__/version_manifest.json'), 'w') as f:
            json.dump(version_manifest_data, f)
    else:
        with open(get_dir_location('__cache__/version_manifest.json'), 'r') as f:
            version_manifest_data = json.load(f)
    return version_manifest_data


def get_version_data(version_id: str, retry=True):
    if not file_has_content(get_dir_location(f'__cache__/{version_id}.json')):
        version_manifest_data = get_version_manifest()

        print(f'\033[92mGetting data for \033[1m{version_id}..\033[m')
        try:
            package_url = next(
                filter(
                    lambda v: v['id'] == version_id, version_manifest_data['versions']
                )
            )['url']
        except StopIteration:
            if retry:
                print(
                    f'No version with id {version_id} found. Deleting __cache__/version_manifest.json and retrying.'
                )
                os.remove(get_dir_location('__cache__/version_manifest.json'))
                return get_version_data(version_id, False)
            raise ValueError(f'No version with id {version_id} found.')
        package_data = requests.get(package_url).json()
        with open(get_dir_location(f'__cache__/{version_id}.json'), 'w') as f:
            json.dump(package_data, f)
    else:
        with open(get_dir_location(f'__cache__/{version_id}.json'), 'r') as f:
            package_data = json.load(f)
    return package_data


def get_client_jar(version_id: str):
    if not file_has_content(get_dir_location(f'__cache__/client-{version_id}.jar')):
        package_data = get_version_data(version_id)
        print(f'\033[92mDownloading client jar for {version_id}...\033[m')
        client_jar_url = package_data['downloads']['client']['url']
        with open(get_dir_location(f'__cache__/client-{version_id}.jar'), 'wb') as f:
            f.write(requests.get(client_jar_url).content)


def get_server_jar(version_id: str):
    if not file_has_content(get_dir_location(f'__cache__/server-{version_id}.jar')):
        package_data = get_version_data(version_id)
        print(f'\033[92mDownloading server jar for {version_id}...\033[m')
        server_jar_url = package_data['downloads']['server']['url']
        with open(get_dir_location(f'__cache__/server-{version_id}.jar'), 'wb') as f:
            f.write(requests.get(server_jar_url).content)


def get_mappings_for_version(version_id: str):
    if not file_has_content(get_dir_location(f'__cache__/mappings-{version_id}.txt')):
        package_data = get_version_data(version_id)

        client_mappings_url = package_data['downloads']['client_mappings']['url']

        mappings_text = requests.get(client_mappings_url).text

        with open(get_dir_location(f'__cache__/mappings-{version_id}.txt'), 'w') as f:
            f.write(mappings_text)
    else:
        with open(get_dir_location(f'__cache__/mappings-{version_id}.txt'), 'r') as f:
            mappings_text = f.read()
    return Mappings.parse(mappings_text)


def get_yarn_versions():
    # https://meta.fabricmc.net/v2/versions/yarn
    if not file_has_content(get_dir_location('__cache__/yarn_versions.json')):
        print('\033[92mDownloading yarn versions...\033[m')
        yarn_versions_data = requests.get(
            'https://meta.fabricmc.net/v2/versions/yarn'
        ).json()
        with open(get_dir_location('__cache__/yarn_versions.json'), 'w') as f:
            json.dump(yarn_versions_data, f)
    else:
        with open(get_dir_location('__cache__/yarn_versions.json'), 'r') as f:
            yarn_versions_data = json.load(f)
    return yarn_versions_data


def get_yarn_data(version_id: str):
    for version in get_yarn_versions():
        if version['gameVersion'] == version_id:
            return version


def get_fabric_api_versions():
    # https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml
    if not file_has_content(get_dir_location('__cache__/fabric_api_versions.json')):
        print('\033[92mDownloading Fabric API versions...\033[m')
        fabric_api_versions_xml_text = requests.get(
            'https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml'
        ).text
        # parse xml
        fabric_api_versions_data_xml = ET.fromstring(fabric_api_versions_xml_text)
        fabric_api_versions = []

        versioning_el = fabric_api_versions_data_xml.find('versioning')
        assert versioning_el
        versions_el = versioning_el.find('versions')
        assert versions_el

        for version_el in versions_el.findall('version'):
            fabric_api_versions.append(version_el.text)

        with open(get_dir_location('__cache__/fabric_api_versions.json'), 'w') as f:
            f.write(json.dumps(fabric_api_versions))
    else:
        with open(get_dir_location('__cache__/fabric_api_versions.json'), 'r') as f:
            fabric_api_versions = json.loads(f.read())
    return fabric_api_versions


def get_fabric_loader_versions():
    # https://meta.fabricmc.net/v2/versions/loader
    if not file_has_content(get_dir_location('__cache__/fabric_loader_versions.json')):
        print('\033[92mDownloading Fabric loader versions...\033[m')
        fabric_api_versions_json = requests.get(
            'https://meta.fabricmc.net/v2/versions/loader'
        ).json()

        fabric_api_versions = []
        for version in fabric_api_versions_json:
            fabric_api_versions.append(version['version'])

        with open(get_dir_location('__cache__/fabric_loader_versions.json'), 'w') as f:
            f.write(json.dumps(fabric_api_versions))
    else:
        with open(get_dir_location('__cache__/fabric_loader_versions.json'), 'r') as f:
            fabric_api_versions = json.loads(f.read())
    return fabric_api_versions


def clear_version_cache():
    print('\033[92mClearing version cache...\033[m')
    files = [
        'version_manifest.json',
        'yarn_versions.json',
        'fabric_api_versions.json',
        'fabric_loader_versions.json',
    ]
    for file in files:
        if os.path.exists(get_dir_location(f'__cache__/{file}')):
            os.remove(get_dir_location(f'__cache__/{file}'))

    burger_path = get_dir_location('__cache__/Burger')
    if os.path.exists(burger_path):
        os.system(f'cd {burger_path} && git pull')
    pixlyzer_path = get_dir_location('__cache__/pixlyzer')
    if os.path.exists(pixlyzer_path):
        os.system(f'cd {pixlyzer_path} && git pull')


def file_has_content(file_path: str):
    return path_exists(file_path) and os.path.getsize(file_path) > 0


def path_exists(path: str):
    return os.path.exists(path)


main()
