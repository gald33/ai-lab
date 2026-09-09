# three.js, vendored

`three@0.184.0`, taken from unpkg and committed here rather than fetched at
runtime. Three files: `three.module.js`, the `three.core.js` it imports, and
`OrbitControls.js`.

**Why it is in the repo.** The viewer had no external dependency at all, and a
replay is a link somebody opens later — often the point of opening it is that
the room is gone. A CDN in that path means the island does not draw when the
network is unhappy, and it means `freeze_static.py` cannot fingerprint the one
part of the page most likely to change. Vendored, the page keeps working with
no network and every module is versioned the same way.

**Provenance.** The design these came with pinned SRI hashes for the same
version. What is committed here matches them byte for byte:

| file | sha384 |
|---|---|
| `three.module.js` | `8FCZ1eVO6it4+pbec2aDtnTrwjWXZLJRC+MAGCIPDgsYnUrl/E0A2YlF8ioMKI/J` |
| `three.core.js` | `dw2ooPewaEIrAgl6oFDBmmBWCE9oW9LxRGcfwZ0hLvEprzo202wXl7vCYHRlSnOT` |
| `OrbitControls.js` | `4rziNxOBZKQ69i+w+f89KJ55TCYquwchVbByQwmaOeIOXdOU2PLDn3kOfXHwIJC9` |

Recompute with:

    openssl dgst -sha384 -binary three.module.js | openssl base64 -A

**Upgrading** is replacing all three together and rerunning the render harness:
they are one release and `three.module.js` imports `three.core.js` by relative
path. MIT, © the three.js authors; the licence header is in each file.
