from importlib import metadata


def get_graia_version():
    extra: list[tuple[str, str]] = []
    official: list[tuple[str, str]] = []
    community: list[tuple[str, str]] = []

    for dist in metadata.distributions():
        name: str = dist.metadata['Name']
        version: str = dist.version
        if name in {'launart', 'creart', 'creart-graia', 'statv', 'richuru'}:
            extra.append((name, version))
        elif name.startswith('graia-'):
            official.append((name, version))
        elif name.startswith('graiax-'):
            community.append((name, version))

    return extra, official, community


def get_version(prefix: str):
    packages: list[tuple[str, str]] = []

    for dist in metadata.distributions():
        name: str = dist.metadata['Name']
        if name.startswith(prefix):
            packages.append((name, dist.version))

    return packages
