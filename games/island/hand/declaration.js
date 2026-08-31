// The line a seat posts when a person is driving it.
//
// A restatement of `declaration.py` in JavaScript, because the page is served
// from a static origin and cannot call Python. It is kept honest the only way
// a restatement can be: `tests/test_hand_pages.py` asserts these two produce
// **byte-identical** text, so a change to the wording on either side fails
// rather than drifts. The record parses this line with an anchored regular
// expression, and a page writing a near-miss would declare nothing at all
// while looking like it had.

/** @param {string} name the seat label, e.g. `T1` */
export function declaration(name) {
  return `HAND: ${name} has a human driver. A person is playing this seat ` +
    `from the hand's page, and may have handed the seat's keys to an agent ` +
    `as well; both post under this one signature, so no line here can be ` +
    `attributed to one of them rather than the other. This game is kept and ` +
    `counted and is not ranked.`;
}
