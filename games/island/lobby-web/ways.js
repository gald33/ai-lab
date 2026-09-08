/** The ways to play, behind the arrow on the front door's own button.
 *
 * **Most visitors send in an agent; that is what the button says and what it
 * does.** But the island is playable by hand -- four pages of it, from a
 * terminal that takes the manager's grammar to a drawn island a child presses
 * buttons on -- and until this menu existed the only sign of that on the door
 * was a sentence half a page down, inside a fold, on the lobby page after it.
 * Asked for by Gal, 2026-09-08: a small arrow on "Send in my agent" that opens
 * the other ways in.
 *
 * **Every way by hand goes through the hand's lobby first, and cannot not.**
 * None of the playing pages exists until a table has settled and whispered its
 * room, so what these link to is the lobby that seats you, carrying `?play=`
 * for the page you asked for. That lobby puts the named way first when the
 * room arrives -- see `hand/lobby.html`, `waysInOrder`. Without the parameter
 * the click would mean nothing by the time it mattered.
 *
 * The last two rows go to one page each; the middle two go to the same page
 * and say so, because `play.html` is both the terminal you type into and the
 * page carrying the brief. Naming it twice with one URL is honest; giving the
 * brief a page of its own so the menu would look tidy is two pages to keep in
 * step for a cosmetic reason.
 */

//: Absolute, and on the other origin: the hand's pages are served from Pages
//: and this door is not. The lobby's own render carries the same constant
//: (`lobby-web/render.js`, `HAND`), and `test_front_door.py` holds the two to
//: the same string so the door and the page behind it cannot drift.
export const HAND = "https://gald33.github.io/ai-lab/island/hand/lobby.html";

export const WAYS = [
  { key: "agent", href: "/lobby", name: "Send in my agent",
    what: "open or join a table and hand your agent the brief — you do not play" },
  { key: "hand", href: `${HAND}?play=hand`, name: "Hacker hand",
    what: "take the seat yourself and type the manager’s grammar" },
  { key: "agent-too", href: `${HAND}?play=agent`, name: "Hand and agent",
    what: "the same page: take the seat, then hand its keys to an agent and " +
          "drive alongside it" },
  { key: "kids", href: `${HAND}?play=kids`, name: "Nice buttons",
    what: "sliders and dropdowns instead of the grammar" },
  { key: "island", href: `${HAND}?play=island`, name: "My kid wants to play",
    what: "the same buttons under the drawn island itself" },
];

const $ = (id) => document.getElementById(id);

function build() {
  const menu = $("waysIn");
  const arrow = $("moreWays");
  if (!menu || !arrow) return;
  for (const way of WAYS) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = way.href;
    a.dataset.way = way.key;
    a.textContent = way.name;
    const what = document.createElement("span");
    what.className = "what";
    what.textContent = way.what;
    li.append(a, what);
    menu.append(li);
  }
  // The button is the first way, taken from the same list, so the door's
  // headline action and the menu's top row cannot drift apart.
  const first = $("sendAgent");
  if (first) {
    first.href = WAYS[0].href;
    first.textContent = WAYS[0].name;
  }
  arrow.addEventListener("click", () => {
    menu.hidden = !menu.hidden;
    arrow.setAttribute("aria-expanded", String(!menu.hidden));
  });
}

build();
