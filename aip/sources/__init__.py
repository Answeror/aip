from . import (
    danbooru_donmai_us,
    gelbooru,
    konachan,
    yande_re
)

sources = {}

for mod in (
    danbooru_donmai_us,
    gelbooru,
    konachan,
    yande_re
):
    source = mod.Source(dict)
    sources[source.id] = source
