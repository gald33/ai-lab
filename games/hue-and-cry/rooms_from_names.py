"""A landmark's room is derived from its name and the game's salt.

Gal's design, 2026-09-07, and it turned out not to be a new mechanism at
all: Switchboard already derives a room's wire identifier by hashing its
token, and says why in `rooms.workspace_for` --

    "An ordinary token is a secret somebody minted, and knowing it is what
     admits you."

So the whole of it is choosing what mints the token:

    workspace_token = KDF(landmark name, game salt)

Knowing a landmark's NAME, plus the game's salt, is then exactly what admits
you to that landmark's room. Nobody issues an invite; there is nothing to
distribute, revoke or leak. This replaces the whispered-warrant mechanism
that earlier drafts needed -- see `games/hue-and-cry.md`, "The room is the
hash".

The salt is what stops a room being the same room in every game. Without it
`hash(landmark)` is a fixed address anybody who ever learned it can walk
into forever; with it, the same landmark is a different room each game and
last week's addresses are worthless.

    python3 games/hue-and-cry/rooms_from_names.py
"""

import hashlib

from switchboard.invite import Invite
from switchboard import rooms

#: Domain separator, so a token minted here can never collide with one minted
#: for another purpose from the same name and salt.
INFO = b"hue-and-cry/v1/landmark"


def token_for(landmark: str, salt: bytes) -> str:
    """The secret that admits you to a landmark, from its name and the salt.

    Any string is a legal Switchboard token -- the library hashes it to get
    the wire identifier -- so the only requirements are that it is infeasible
    to guess without the name, and that both sides derive the same one.
    """
    return hashlib.sha256(
        INFO + b"\x00" + salt + b"\x00" + landmark.encode("utf-8")
    ).hexdigest()


def invite_for(landmark: str, salt: bytes, *, url: str, key: str) -> Invite:
    """A joinable room, constructed locally. No hub call, no manager."""
    return Invite(url=url, workspace_token=token_for(landmark, salt), key=key)


def main() -> None:
    url, key = "https://hub.example", "k" * 43 + "="
    salt_a, salt_b = b"game-A", b"game-B"

    print("the same landmark, two games -- two rooms:")
    for landmark in ("Reykjavik", "Cairo", "Quito"):
        a = invite_for(landmark, salt_a, url=url, key=key)
        b = invite_for(landmark, salt_b, url=url, key=key)
        print(f"  {landmark:<10} game A {a.workspace}")
        print(f"  {'':<10} game B {b.workspace}")
        assert a.workspace != b.workspace, "salt must move the room"

    print("\nthe identifier really is the hash of the token, per the library:")
    one = invite_for("Cairo", salt_a, url=url, key=key)
    assert one.workspace == rooms.workspace_for(one.workspace_token)
    print(f"  workspace_for(token) == invite.workspace  -> {one.workspace}")

    print("\nand it is joinable without anybody issuing an invite:")
    from switchboard.client import Client
    client = Client.from_invite(one, agent_id="searcher-1")
    print(f"  Client.from_invite(...)  ->  workspace {client.workspace!r},"
          f" no I/O performed")

    print("""
What this buys, and it is the whole of the access model:

  A searcher who can NAME a landmark can reach it, and one who cannot,
  cannot. There is no warrant to whisper, nothing to revoke, and nothing
  that leaks when a room key is handed on -- because handing on a name is
  the same act as handing on the room, and both are just talk.

  So the scarcity is KNOWLEDGE OF NAMES rather than permission. That works
  only because the map is large and unknown: you cannot enumerate the
  landmarks in play, so you cannot enumerate their rooms. It is the same
  property the sparse matrix was already buying, doing a second job.

  And the hash Carmel leaves beside her hint is the address she left for.
  Whoever is standing in the room she left can join it at once; whoever is
  not must work the name out from the hint instead.""")


if __name__ == "__main__":
    main()
