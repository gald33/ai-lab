// The room, as text a chat model can read.
//
// **What this is for.** `games/island.md` ("A person may sit in a seat")
// describes the arrangement this serves: a person playing a seat by hand on
// advice from a non-agentic LLM -- "a chat window with no tools, no board
// access and no memory of the room beyond what the person pastes into it."
// The hand is the intermediary. This composes what they paste.
//
// Asked for by Gal, 2026-09-04, with the part that makes it worth building:
// **a copy that remembers what it copied.** A round is four to eight
// episodes of a manager talking, and pasting the whole room again every time
// a bell rings spends the model's context on lines it has already read. So
// there are two copies -- everything, and everything since the last one --
// and the mark that separates them is kept per room.
//
// **It restates no rule.** The manager posts the schedule and the house
// rules on the board itself, so a full copy already carries them, in the
// manager's words rather than this file's. A page that paraphrased them
// would be a second implementation of the grammar, which is the thing
// `games/island.md` refuses in every other place it comes up. The header
// says where the rules are and nothing about what they say.

//: Where a room's mark lives. **`localStorage`, not `sessionStorage`**, which
//: is what this page uses for everything else it remembers: the folds and the
//: levers are view state and may reset on a reload, but a mark is a claim
//: about what another process has already been told, and a driver who
//: reloads mid-round should not have to re-send the round. Keyed per room and
//: channel; rooms expire within a day, so nothing accumulates.
const MARK = "island:copied";

function markKey(room, channel) { return `${MARK}:${room}:${channel}`; }

/** What has already been copied out of this room, or a mark that has copied
 *  nothing. Never throws: storage can be unavailable (a private window,
 *  site data blocked) and a page that fell over there would be worse than
 *  one that offers to copy everything again. */
export function loadMark(room, channel) {
  try {
    const raw = localStorage.getItem(markKey(room, channel));
    const seen = raw ? JSON.parse(raw) : null;
    if (seen && typeof seen === "object") {
      return { board: Number(seen.board) || 0,
               whispers: Array.isArray(seen.whispers) ? seen.whispers : [] };
    }
  } catch { /* no storage, or nothing stored */ }
  return { board: 0, whispers: [] };
}

export function saveMark(room, channel, mark) {
  try {
    localStorage.setItem(markKey(room, channel), JSON.stringify(mark));
  } catch { /* a copy that happened is not undone by failing to record it */ }
}

/** Forget what was copied, so the next copy is the whole room again. */
export function clearMark(room, channel) {
  try { localStorage.removeItem(markKey(room, channel)); } catch { /* as above */ }
}

/** A row's body as text. An unreadable whisper arrives as an object and is
 *  shown as one -- saying "unreadable" is information the model should have,
 *  and quietly dropping it would leave a gap nobody could see. */
function bodyText(row) {
  return typeof row.body === "string" ? row.body : JSON.stringify(row.body);
}

/** Who said it: the roster's name where the page knows one, `you` for this
 *  seat's own lines, and the blinded id's first characters otherwise --
 *  which is what the board itself shows, so the paste and the page agree. */
function speaker(row, { names, meId, seat }) {
  const from = String(row.from || "?");
  if (meId && from === meId) return seat ? `you (${seat})` : "you";
  const name = names && names[from];
  return name || from.slice(0, 6);
}

/**
 * The room as text, from `since` onwards.
 *
 * Returns the text, the mark it advances to, and how many lines of each kind
 * it carries -- the counts so a button can say what it is about to copy, and
 * the mark so the caller advances it only once the copy has actually
 * happened. A mark moved before the clipboard accepted the text would lose
 * the lines it claimed to have sent.
 */
export function compose({ room, channel, seat, alias, board = [], whispers = [],
                          since = { board: 0, whispers: [] }, names = {},
                          meId = null, now = new Date() }) {
  const seen = new Set(since.whispers || []);
  const newBoard = board.filter((r) => (Number(r.seq) || 0) > (since.board || 0));
  const newWhispers = whispers.filter((r) => !seen.has(String(r.id)));
  const whole = !(since.board || seen.size);

  const stamp = now.toISOString().replace(/\.\d+Z$/, "Z");
  const where = `room ${room}, channel ${channel}`;
  const who = seat ? `seat ${seat}${alias ? ` (playing as "${alias}")` : ""}`
                   : "this seat";
  const lines = [];
  if (whole) {
    lines.push(`Island — ${where}. You are advising the driver of ${who}.`);
    lines.push(`The whole room so far: ${newBoard.length} board line(s) and ` +
               `${newWhispers.length} whisper(s), from the start. Copied ${stamp}.`);
    lines.push(`The manager's own lines below carry the schedule and the house ` +
               `rules; nothing here restates them.`);
  } else {
    lines.push(`Island — ${where}, continued. You are advising the driver of ${who}.`);
    lines.push(`New since the last copy: ${newBoard.length} board line(s) and ` +
               `${newWhispers.length} whisper(s). Copied ${stamp}.`);
    lines.push(`Everything before this was copied already and is not repeated.`);
  }

  if (newWhispers.length) {
    lines.push("", "--- whispered to this seat (private; nobody else in the " +
                   "room can read these) ---");
    for (const row of newWhispers) {
      lines.push(`[w] ${speaker(row, { names, meId, seat })}: ${bodyText(row)}`);
    }
  }
  if (newBoard.length) {
    lines.push("", "--- the board (public) ---");
    for (const row of newBoard) {
      lines.push(`[${row.seq}] ${speaker(row, { names, meId, seat })}: ${bodyText(row)}`);
    }
  }
  if (!newBoard.length && !newWhispers.length) {
    lines.push("", "(nothing new)");
  }

  const mark = {
    board: board.reduce((top, r) => Math.max(top, Number(r.seq) || 0),
                        since.board || 0),
    whispers: [...new Set([...(since.whispers || []),
                           ...whispers.map((r) => String(r.id))])],
  };
  return { text: lines.join("\n") + "\n", mark,
           board: newBoard.length, whispers: newWhispers.length };
}

/**
 * Put text on the clipboard, and say plainly when that could not be done.
 *
 * The clipboard needs a secure context and a permission the browser may
 * refuse, so this can fail for reasons the driver can do nothing about. It
 * returns whether it worked rather than throwing, because the caller has a
 * fallback worth reaching -- showing the text to be copied by hand beats a
 * button that silently did nothing.
 */
export async function toClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
