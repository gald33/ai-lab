// Utility, and only where it is allowed to exist.
//
// Utility needs tastes. Tastes are private to each trader and never reach the
// board, so nothing in this file can run on a live page -- the reveal sidecar
// is the only source of an alpha, and it is written after the round is over.
// A live island shows stocks and trades and no score at all, which is the same
// thing every trader in it can see.
//
// This is `barter.economy.utility` in JavaScript, including the part that looks
// like a rounding guard and is not: a trader holding none of some good has zero
// Cobb-Douglas utility, and that zero is the outcome most worth seeing.

const EPS = 1e-12;

export function utility(alpha, bundle) {
  let total = 0;
  for (const good of Object.keys(alpha)) {
    const x = bundle[good] || 0;
    if (x <= EPS) return 0;          // ruined, not rounded
    total += alpha[good] * Math.log(x);
  }
  return Math.exp(total);
}

/** What a trader is holding right now, scored with what they turn out to want. */
export function utilityOf(reveal, trader, holdings) {
  const taste = reveal?.traders?.[trader]?.taste;
  return taste ? utility(taste, holdings || {}) : null;
}

/** Per-episode utility summed over the round: what `eff_round` is built from. */
export function accumulate(trajectory, index) {
  return trajectory.reduce((sum, row) => sum + (row[index] || 0), 0);
}

/**
 * The page's own reading of the board against the manager's score.
 *
 * `reveal.py --check` does this in Python before the page ever loads; doing it
 * again here is not redundant, because this runs the code path the page
 * actually draws with. If these disagree the island is drawing a different
 * economy from the one that ran, and the page says so rather than showing a
 * confident wrong number.
 *
 * They never agree exactly: receipts carry four decimals while the manager kept
 * full precision, which is worth ~1e-4 in a quantity and ~2e-5 in a utility.
 */
export const TOLERANCE = 1e-3;

export function audit(timeline, reveal) {
  const trajectory = reveal?.round?.trajectory;
  if (!trajectory) return null;
  const closed = timeline.final.episodes_closed;
  const rows = [];
  let worst = 0;
  for (let e = 0; e < Math.min(closed.length, trajectory.length); e++) {
    timeline.traders.forEach((name, i) => {
      const rebuilt = utilityOf(reveal, name, closed[e].holdings[name]);
      if (rebuilt === null) return;
      const recorded = trajectory[e][i];
      const gap = Math.abs(rebuilt - recorded);
      worst = Math.max(worst, gap);
      if (gap > TOLERANCE) rows.push({ episode: e + 1, trader: name, rebuilt, recorded, gap });
    });
  }
  return { worst, disagreements: rows, episodes: Math.min(closed.length, trajectory.length) };
}
