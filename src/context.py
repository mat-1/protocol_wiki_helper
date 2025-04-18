from .datagen import download, extract


class UpdateContext:
    __slots__ = (
        'version',
        '_mappings',
        '_burger_data',
        '_registries',
        '_packets',
        '_blocks',
    )

    def __init__(self, version: str):
        self.version = version

        self._mappings = None
        self._burger_data = None
        self._registries = None
        self._packets = None
        self._blocks = None

    def protocol_version(self):
        burger_data = self.burger_data()
        return burger_data[0]['version']['protocol']

    #

    def mappings(self):
        if self._mappings is None:
            self._mappings = download.get_mappings_for_version(self.version)

        return self._mappings

    def burger_data(self):
        if self._burger_data is None:
            self._burger_data = extract.get_burger_data_for_version(self.version)

        return self._burger_data

    def registries_report(self):
        if self._registries is None:
            self._registries = extract.get_registries_report(self.version)

        return self._registries

    def packets_report(self):
        if self._packets is None:
            self._packets = extract.get_packets_report(self.version)

        return self._packets

    def blocks_report(self):
        if self._blocks is None:
            self._blocks = extract.get_block_states_report(self.version)

        return self._blocks
