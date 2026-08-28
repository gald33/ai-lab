"""Join a table and put an agent in the seat. A reference, not a requirement.

    python -m games.island.run_entrant --workspace island-lobby --name scout-v2

Everything else in `games/island/` is the house's side of the board: the lobby
settles tables, `run_game.py` deals and keeps the clock. This is the other
side, and it exists because **no agent has ever actually played** -- every
round so far was driven by scripted clients in a test.

**It is a reference and must stay one.** `games/island.md` is explicit that
entry is agent-agnostic and that there is no SDK to adopt: "You join a
Switchboard room with whatever you already run... if entering required this
code, the results would be about this code." So nothing here is privileged.
It joins a room, waits for an invite and starts a session -- all of which an
entrant can do any way it likes. It is the shortest honest demonstration that
the door opens, not the door.

What it does, in order:

1. Hold **one signing identity** and keep it alive for the whole game.
2. Register in the lobby room and claim a seat.
3. Wait for that seat's invite.
4. Start one long-lived agent session in the table's room, and stop.

Step 1 is the part that is not obvious and the part that breaks silently if
it is wrong. A seat binds by **signing key**, because a peer id is blinded per
workspace and the id the lobby witnessed is a different string in the table's
own room. So the key that claimed the seat has to be the key the agent posts
under, across two rooms and two processes. `switchboard-mcp` already provides
exactly this -- `signing.SigningServer` listens on a socket keyed by
`agent_id`, and every client for that agent attaches to it rather than minting
its own -- so this starts the signer *first* and lets both its own client and
the agent's MCP server attach to it. An entrant that skips this gets a seat
that never binds and a trader whose every line is ignored.

**Nothing here prompts the agent.** It starts one session and waits for it to
end. The agent reads the board and writes to it; there is no turn, no wave,
and nothing that wakes it up. That is the same line `run_game.py` holds from
the other side.

**The private half comes off the board, not out of the prompt.** `run_v3.py`
injects it at spawn because it launches every trader itself and there is no
board to read it from yet. Here the manager deals onto the table's board, so
the agent reads its own capacities and tastes there like anything else -- one
surface, and this process never learns them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import threading
import sys
import time
from pathlib import Path

from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL
from switchboard.invite import Invite

_ISLAND = Path(__file__).resolve().parents[2] / "experiments" / "005-deliberation-protocol"
sys.path.insert(0, str(_ISLAND))

from island import ca, toolchain  # noqa: E402

from .brief import FROZEN_GOODS, brief, goods_for  # noqa: E402
from .protocol import GOODS_DEFAULT  # noqa: E402


#: The only tools an entrant's agent has. Everything else it might want to do,
#: it does by writing on the board -- which is the whole design.
TOOLS = ["mcp__switchboard__checkin", "mcp__switchboard__say",
         "mcp__switchboard__history", "mcp__switchboard__inbox",
         "mcp__switchboard__dm", "mcp__switchboard__roster",
         # A sealed round is played through this one: the manager whispers
         # each seat its private half, `inbox` opens it, and a plan goes back
         # the same way. Without it an agent can read what it was dealt and
         # has no way to answer, which is a game it cannot play rather than a
         # game it plays badly.
         #
         # `whisper` is the only name this repo knows. It went by another
         # before 1.0.0, and the pin is `>=1.2.3`, so an allowlist naming the
         # old one would only be arming a release we do not run against.
         "mcp__switchboard__whisper",
         "mcp__switchboard__whoami", "Bash(sleep:*)"]

#: The goods are optional so an entrant still finds a table announced by a
#: lobby that predates them -- and falls back to the four the frozen rules were
#: written about, which is what such a lobby is dealing.
_FORMING = re.compile(
    r"^(\S+) is forming: (\d+) traders, (?:(\d+) goods, )?(\d+) episodes")
_INVITE = re.compile(r"^(\S+) invite: (swb1_\S+)")


def instructions(name: str, episodes: int,
                 goods: int | tuple[str, ...] = len(FROZEN_GOODS)) -> str:
    """What the agent is told. The island's rules, and where it is.

    The rules come from 005's frozen stimulus with its goods arithmetic put
    right for this game -- see `brief.py`. At the four goods that document was
    written about the two are byte-identical, so a four-good game reads exactly
    what game 001 read.
    """
    words = goods_for(goods) if isinstance(goods, int) else tuple(goods)
    return f"""{brief(words)}

## This round

You are **{name}**, and you have taken a seat at a table. The manager will
post your own capacities and taste weights on the **island** channel,
addressed to you by your seat name -- read the channel and find them. Nobody
will send them to you privately and nobody will repeat them.

There are {episodes} episodes. There are no stages inside an episode: from the
moment it opens until the bell, producing, proposing and approving all settle.
Your capacities and tastes are the same in every episode, and so is everyone
else's.

If the manager says this is a PRACTICE game, then every trader's capacities
and tastes are on the board in the clear, including yours and theirs. That is
worth reading rather than ignoring: you can see exactly what your partner is
good at and what they want.

Every deadline the manager posts is an absolute UTC clock time, and every
Switchboard tool result carries the current time as `now` in the same form. A
message you read is not a message just written -- work out how long you have
by comparing the stated time with `now`, never by counting from when you read
it.

**Begin now.** Do not ask whether to start and do not wait to be told; there
is nobody to answer you, and the clock is already running. Your first act
should be `checkin`.

Nobody will prompt you, ever. Nothing will wake you up. There is no turn that
comes round to you, and if you stop acting you have left the island for good --
the clock keeps running, the other traders keep dealing, and the bell rings on
an episode you did nothing in.

So keep yourself awake. `checkin` is the loop tool: it says you are still here
and returns anything addressed to you since last time, and with `wait` it
blocks for up to 25 seconds until something arrives. Call it, act on whatever
came back, call it again. That is how you schedule your own next moment.

Never finish a reply without having called `checkin` or `say`. If you have
nothing to do, call `checkin` with `wait` set to 25 and see what arrives. Keep
going until the manager says the round is over. Only then stop."""


def _mcp_env(invite: Invite, *, agent_id: str, home: Path) -> dict[str, str]:
    """The environment an agent's MCP server gets, and the only one it gets.

    Built once and used by both `launch()` and `preflight()`, so the path the
    gate proves is the path the session takes. Two copies of this that drifted
    would make the gate a reassurance rather than a check.
    """
    home.mkdir(parents=True, exist_ok=True)
    bundle = ca.bundle(home / ".ca-bundle.pem")
    env_for_mcp = {
        "SWITCHBOARD_URL": invite.url,
        "SWITCHBOARD_WORKSPACE": invite.workspace,
        "SWITCHBOARD_AGENT_ID": agent_id,
        # An MCP server gets this env and not the parent's, so the trust and
        # proxy settings have to be named here or every tool the agent holds
        # fails at the TLS handshake.
        "SSL_CERT_FILE": bundle,
        "REQUESTS_CA_BUNDLE": bundle,
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "HTTPS_PROXY": os.environ.get("HTTPS_PROXY", ""),
        "NO_PROXY": os.environ.get("NO_PROXY", ""),
    }
    if invite.token:
        env_for_mcp["SWITCHBOARD_TOKEN"] = invite.token
    if invite.key:
        env_for_mcp["SWITCHBOARD_KEY"] = invite.key
    return env_for_mcp


def launch(invite: Invite, *, name: str, agent_id: str, episodes: int,
           goods: int, model: str, workdir: Path,
           max_turns: int) -> subprocess.Popen:
    """One agent, one long-lived session, in the table's room.

    The MCP server is pointed at the *table's* workspace and key from the
    invite, and given the same `agent_id` this process holds the signer for --
    which is what makes its posts carry the key the lobby witnessed.
    """
    # Absolute, because the session runs with `cwd=home`: a relative
    # --mcp-config would resolve inside the directory it already names, and
    # `claude` exits 1 with "MCP config file not found" pointing at the
    # doubled path. Which is what a real run did, on both seats, in the first
    # second -- a harness failure that reads exactly like two silent traders
    # if you only look at the board.
    home = (workdir / name).resolve()
    env_for_mcp = _mcp_env(invite, agent_id=agent_id, home=home)
    bundle = env_for_mcp["SSL_CERT_FILE"]
    (home / ".mcp.json").write_text(json.dumps(
        {"mcpServers": {"switchboard": {"command": "switchboard-mcp",
                                        "env": env_for_mcp}}}, indent=1))

    env = dict(os.environ)
    env.update({k: v for k, v in env_for_mcp.items() if k.startswith("SWITCHBOARD")})
    env.update({"SSL_CERT_FILE": bundle, "REQUESTS_CA_BUNDLE": bundle})
    return subprocess.Popen(
        ["claude", "-p", instructions(name, episodes, goods),
         "--model", model, "--max-turns", str(max_turns),
         "--mcp-config", str(home / ".mcp.json"),
         "--allowedTools", *TOOLS],
        cwd=home, env=env,
        stdout=open(home / "session.log", "w"), stderr=subprocess.STDOUT)


def hold_signer(server: signing.SigningServer, *, every: float = 1.0,
                stop: threading.Event | None = None) -> threading.Thread:
    """Keep this process's signer answering on its own socket.

    Working around an upstream bug, reported in
    `games/switchboard-bug-signer-serves-itself.md`. `switchboard-mcp`
    attaches to whatever signer is already listening for its `agent_id` --
    which is the whole mechanism this entrant relies on -- and then starts a
    `SigningServer` of its own on the same path. `SigningServer.start()`
    unlinks the existing socket first, so the agent's server replaces ours
    while proxying to a `RemoteSigningIdentity` that points back at that same
    path: it asks itself, its single-threaded accept loop is already busy
    answering, and every signature times out as *"the session's signer did
    not answer"*. Reads need no signature, so a session in this state looks
    exactly like a trader that joined and then chose silence.

    Taking the path back breaks the loop: the agent's `RemoteSigningIdentity`
    then reaches us, and we hold the only real key. Checked rather than
    re-bound blindly, so an untouched socket is left alone.
    """
    stop = stop or threading.Event()

    def _held() -> bool:
        reply = signing._ask(server.path, {"op": "pubkey"})
        return bool(reply) and reply.get("pubkey") == server.identity.public_key

    def _hold() -> None:
        while not stop.is_set():
            if not _held():
                server.start()
            stop.wait(every)

    thread = threading.Thread(target=_hold, daemon=True)
    thread.start()
    return thread


def preflight(invite: Invite, *, agent_id: str, workdir: Path) -> None:
    """Prove this agent's toolchain reaches the table's room before spending.

    Pointed at *this* module's config rather than `run_v3.py`'s: they are
    different environments and a pass on one proves nothing about the other.
    The check itself is shared, because it was wrong once and one copy of it
    is one place to be wrong.
    """
    env = _mcp_env(invite, agent_id=agent_id,
                   home=workdir / f"{agent_id}-preflight")
    env["SWITCHBOARD_AGENT_ID"] = f"{agent_id}-preflight"
    try:
        toolchain.check(env, where=f"{invite.url}/{invite.workspace}")
    except toolchain.Broken as exc:
        raise SystemExit(f"preflight: {exc}") from None
    print(f"preflight: an agent's switchboard-mcp reached {invite.workspace}",
          flush=True)


def claim(client: Client, channel: str, *, name: str, table: str | None,
          opening: tuple[int, int, int] | None, goods: int, every: float,
          deadline: float, nonce: str = "") -> tuple[str, int, int]:
    """Take a seat, and return which table it is on, how long it runs, and
    how many goods it is drawn over.

    With `--table` it claims that one. With `--open` it forms one and claims
    a seat on it. With neither it waits for a table somebody else opened --
    which is what a second entrant does.
    """
    if opening:
        traders, episodes, rounds = opening
        client.post(channel, f"OPEN traders={traders} episodes={episodes} "
                             f"rounds={rounds} goods={goods}")

    episodes = 0
    while time.time() < deadline:
        for msg in sorted(client.history(channel, limit=200),
                          key=lambda r: r.get("seq", 0)):
            body = msg.get("body")
            if not isinstance(body, str):
                continue
            found = _FORMING.match(body)
            if found and (table is None or found.group(1) == table):
                table, episodes = found.group(1), int(found.group(4))
                goods = int(found.group(3)) if found.group(3) else len(FROZEN_GOODS)
        if table and episodes:
            break
        time.sleep(every)
    else:
        raise SystemExit("no table formed before the deadline")

    # A seat that brings no nonce is a seat the island was not drawn with, and
    # the lobby says so on the settlement line: "not every seat brought a
    # nonce, so the draw is not checkable afterwards". Optional here only
    # because it always was.
    client.post(channel, f"JOIN {table} as {name}"
                         + (f" nonce={nonce}" if nonce else ""))
    return table, episodes, goods


def wait_for_invite(client: Client, channel: str, table: str, *,
                    every: float, deadline: float) -> Invite:
    """The table's invite, once the lobby settles it.

    A seat that was refused is not a seat, and waiting out the clock for an
    invite that will never come is the least useful way to find that out -- so
    a refusal addressed here is raised with the lobby's own reason.
    """
    while time.time() < deadline:
        for msg in sorted(client.history(channel, limit=200),
                          key=lambda r: r.get("seq", 0)):
            body = msg.get("body")
            if not isinstance(body, str):
                continue
            found = _INVITE.match(body)
            if found and found.group(1) == table:
                return Invite.decode(found.group(2))
            if body.startswith("@") and "not settled:" in body:
                raise SystemExit(f"the lobby refused this seat: {body}")
        time.sleep(every)
    raise SystemExit(f"{table} did not settle before the deadline")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="the seat name to claim")
    ap.add_argument("--hub", default=os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL)
    ap.add_argument("--token", default=os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN)
    ap.add_argument("--workspace", default=os.environ.get("SWITCHBOARD_WORKSPACE", "island-lobby"))
    ap.add_argument("--key", default=os.environ.get("SWITCHBOARD_KEY"))
    ap.add_argument("--channel", default="lobby")
    ap.add_argument("--table", default=None, help="join this table rather than waiting")
    ap.add_argument("--open", dest="opening", nargs=3, type=int, default=None,
                    metavar=("TRADERS", "EPISODES", "ROUNDS"),
                    help="form a table, then claim a seat on it")
    ap.add_argument("--goods", type=int, default=GOODS_DEFAULT,
                    help="how many goods, when this entrant opens the table. "
                         "Ignored when joining somebody else's -- the table "
                         "announces its own, and the level is theirs to set")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--every", type=float, default=3.0)
    ap.add_argument("--wait", type=float, default=900.0,
                    help="seconds to wait for a table to settle")
    ap.add_argument("--workdir", type=Path, default=Path("games/entrants"))
    args = ap.parse_args(argv)

    # The signer first, and held for the whole game: everything else depends
    # on one key answering for this agent in both rooms.
    agent_id = args.name
    server = signing.SigningServer(signing.SigningIdentity.generate(), agent_id)
    if not server.start():
        raise SystemExit(
            "could not start a signer on this platform, so this entrant "
            "cannot hold one key across both rooms and its seat would never "
            "bind")
    try:
        client = Client(ClientConfig(url=args.hub, url_source="explicit",
                                     token=args.token, workspace=args.workspace,
                                     key=args.key), agent_id=agent_id)
        # Registering is what publishes the key for the lobby to witness: a
        # JOIN from a peer nobody has a key for is refused, by design.
        client.register(name=args.name, kind="local", branch="main",
                        task=f"playing the island as {args.name}")
        print(f"{args.name}: signing as {client.public_key}", flush=True)

        deadline = time.time() + args.wait
        table, episodes, goods = claim(client, args.channel, name=args.name,
                                       table=args.table,
                                       opening=tuple(args.opening) if args.opening else None,
                                       goods=args.goods,
                                       every=args.every, deadline=deadline)
        print(f"{args.name}: claimed a seat on {table} "
              f"({episodes} episodes, {goods} goods)", flush=True)

        invite = wait_for_invite(client, args.channel, table,
                                 every=args.every, deadline=deadline)
        print(f"{args.name}: {table} settled, joining {invite.workspace}",
              flush=True)

        # Before the one step that spends: prove this agent's own toolchain
        # reaches the table's room, because the failure is indistinguishable
        # from a trader that started and chose to stop.
        preflight(invite, agent_id=agent_id, workdir=args.workdir)

        agent = launch(invite, name=args.name, agent_id=agent_id, goods=goods,
                       episodes=episodes, model=args.model,
                       workdir=args.workdir,
                       max_turns=max(400, 40 * episodes))
        print(f"{args.name}: session {agent.pid} is on the island", flush=True)
        # Only now: the agent's MCP server takes this socket as it starts,
        # and holding it from here keeps its signatures reaching a real key.
        hold_signer(server)
        agent.wait()
        print(f"{args.name}: session ended ({agent.returncode})", flush=True)
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
