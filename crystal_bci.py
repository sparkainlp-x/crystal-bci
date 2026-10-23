"""crystal-bci: what crystallization taught, applied to biosignal commands.

The membrane-crystallization lesson: Hebbian learning recovers the
SUBSPACE not the basis, and what optimizes is the RESIDUE --
structure extracted, white noise left. Here that machinery learns
a blink-command subspace ("the crystal") from a noisy synthetic
multichannel biosignal stream, then gates hologram UI commands
through it, fail-closed.

Pipeline: synthetic EOG-like stream -> peak-triggered Hebbian
learner -> crystal (top eigenvectors) + residue whiteness ->
projection-energy detector -> Youden-calibrated gate -> command
("next") or silence.

SYNTHETIC SIGNALS ONLY. Not a medical device, not a real
decoder, and not evaluated on human recordings. The device-data
adapter to real hardware (e.g. NeuroViu-class EOG recordings) is
explicitly still missing -- this is the learning-and-gating half
of that future pipeline.
"""

import math
import random


# ------------------------------------------------------------ synthetic stream
def blink_waveform(L=24):
    """Biphasic pulse: the synthetic blink."""
    return [math.sin(2 * math.pi * i / L) * math.sin(math.pi * i / L)
            for i in range(L)]


def synth_stream(T, C, blink_gap, noise, drift, rng, blinks=True,
               amp_lo=1.8, amp_hi=2.4):
    """Multichannel stream: blink waveform along a random direction
    (volume conduction), white noise, slow drift. Blinks are
    salient (real EOG blinks tower over background EEG -- that is
    why blink detection works at all). Returns
    (samples, blink_peak_times, true_direction)."""
    b = [rng.gauss(0, 1) for _ in range(C)]
    n = math.sqrt(sum(x * x for x in b))
    b = [x / n for x in b]
    w = blink_waveform()
    L = len(w)
    times = []
    if blinks:
        t = L + rng.randint(0, blink_gap)
        while t < T - L:
            times.append(t)
            t += L + rng.randint(blink_gap // 2, blink_gap * 2)
    s = [[0.0] * C for _ in range(T)]
    peak = set()
    for t0 in times:
        amp = rng.uniform(amp_lo, amp_hi)
        for i, wi in enumerate(w):
            for c in range(C):
                s[t0 + i][c] += amp * wi * b[c]
        peak.add(t0 + L // 4)  # positive lobe peak
    for t in range(T):
        dr = drift * math.sin(2 * math.pi * t / (T / 3))
        for c in range(C):
            s[t][c] += rng.gauss(0, noise) + dr * b[c]
    return s, sorted(peak), b


# ------------------------------------------------------------ the crystal
class CrystalLearner:
    """Peak-triggered Hebbian learner: collects high-energy windows,
    maintains their running covariance (Welford)."""

    def __init__(self, C, L):
        self.dim = C * L
        self.n = 0
        self.mean = [0.0] * self.dim
        self.M2 = [[0.0] * self.dim for _ in range(self.dim)]

    def window(self, s, t0, C, L):
        # baseline removal per channel (standard biosignal
        # preprocessing): kills drift common-mode so the crystal
        # learns shape, not offset.
        w = [[s[t0 + i][c] for c in range(C)] for i in range(L)]
        mu = [sum(w[i][c] for i in range(L)) / L for c in range(C)]
        return [w[i][c] - mu[c] for i in range(L) for c in range(C)]

    def energy(self, s, t, C):
        return math.sqrt(sum(x * x for x in s[t]))

    def observe(self, s, C, L, thresh):
        T = len(s)
        t = 0
        while t < T - L:
            if self.energy(s, t, C) > thresh:
                # align to the local energy peak (spike-sorting
                # practice): the window must start at the same phase
                # of every event or the mean washes out.
                t_pk = max(range(t, min(t + L, T - 1)),
                           key=lambda u: self.energy(s, u, C))
                t0 = max(0, t_pk - L // 4)
                if t0 + L > T:
                    break
                w = self.window(s, t0, C, L)
                self.n += 1
                d = self.dim
                delta = [wi - mi for wi, mi in zip(w, self.mean)]
                self.mean = [mi + di / self.n
                             for mi, di in zip(self.mean, delta)]
                for i in range(d):
                    di = w[i] - self.mean[i]
                    row = self.M2[i]
                    for j in range(d):
                        row[j] += delta[i] * di
                t = t_pk + L  # one window per event
            else:
                t += 1

    def covariance(self):
        d = self.dim
        if self.n < 2:
            return [[0.0] * d for _ in range(d)]
        return [[self.M2[i][j] / (self.n - 1)
                 for j in range(d)] for i in range(d)]


def top_eigenvectors(cov, k, iters=60, rng=None):
    """Power iteration + deflation. Returns (vectors, eigenvalues)."""
    d = len(cov)
    rng = rng or random.Random(0)
    vecs, vals = [], []
    A = [row[:] for row in cov]
    for _ in range(k):
        v = [rng.gauss(0, 1) for _ in range(d)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        v = [x / n for x in v]
        for _ in range(iters):
            w = [sum(A[i][j] * v[j] for j in range(d)) for i in range(d)]
            n = math.sqrt(sum(x * x for x in w)) or 1.0
            v = [x / n for x in w]
        lam = sum(v[i] * sum(A[i][j] * v[j] for j in range(d))
                  for i in range(d))
        vecs.append(v)
        vals.append(lam)
        for i in range(d):
            for j in range(d):
                A[i][j] -= lam * v[i] * v[j]
    return vecs, vals


def cosine(a, b):
    n = math.sqrt(sum(x * x for x in a) * sum(x * x for x in b)) or 1.0
    return abs(sum(x * y for x, y in zip(a, b)) / n)


def residue_whiteness(cov, k, vecs):
    """Flatness of the residual spectrum after removing top-k:
    1.0 = perfectly white. Uses top-8 residual eigenvalues."""
    d = len(cov)
    A = [row[:] for row in cov]
    for v in vecs[:k]:
        lam = sum(v[i] * sum(A[i][j] * v[j] for j in range(d))
                  for i in range(d))
        for i in range(d):
            for j in range(d):
                A[i][j] -= lam * v[i] * v[j]
    rng = random.Random(1)
    evals = []
    for _ in range(min(8, d - k)):
        v = [rng.gauss(0, 1) for _ in range(d)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        v = [x / n for x in v]
        for _ in range(40):
            w = [sum(A[i][j] * v[j] for j in range(d)) for i in range(d)]
            n = math.sqrt(sum(x * x for x in w)) or 1.0
            v = [x / n for x in w]
        lam = sum(v[i] * sum(A[i][j] * v[j] for j in range(d))
                  for i in range(d))
        evals.append(max(lam, 1e-12))
        for i in range(d):
            for j in range(d):
                A[i][j] -= lam * v[i] * v[j]
    m = sum(evals) / len(evals)
    sd = math.sqrt(sum((e - m) ** 2 for e in evals) / len(evals))
    return 1.0 / (1.0 + sd / m)


# ------------------------------------------------------------ detection + gate
def crystal_template(learner):
    """The crystal: mean of collected windows (spike-triggered
    average), normalized. Covariance measures variance around the
    mean -- but every blink shares nearly the same shape, so the
    template lives in the first moment, not the second. The
    covariance's job is characterizing what is LEFT."""
    n = math.sqrt(sum(x * x for x in learner.mean)) or 1.0
    return [x / n for x in learner.mean]


def template_statistic(window, crystal):
    """Normalized correlation of a centered window with the crystal."""
    num = sum(w * c for w, c in zip(window, crystal))
    den = math.sqrt(sum(w * w for w in window)) or 1.0
    return num / den


def template_match(window, template):
    """Normalized cross-correlation with the canonical waveform,
    tiled across channels by best channel."""
    C = len(template[0])
    L = len(template)
    best = 0.0
    for c in range(C):
        wv = [window[i * C + c] for i in range(L)]
        tv = [template[i][c] for i in range(L)]
        num = sum(a * b for a, b in zip(wv, tv))
        den = math.sqrt(sum(a * a for a in wv) * sum(b * b for b in tv))
        if den > 0:
            best = max(best, num / den)
    return best


def label_windows(s, peaks, C, L, stride):
    """Windows labeled by whether they contain a blink peak."""
    out = []
    T = len(s)
    for t0 in range(0, T - L, stride):
        lab = any(t0 <= p < t0 + L for p in peaks)
        out.append((t0, lab))
    return out


def youden_threshold(scores_labels):
    """tau maximizing Youden's J. Returns (tau, J)."""
    pts = sorted(scores_labels)
    if not pts:
        raise ValueError("need at least one scored candidate")
    best_tau, best_j = pts[0][0], -1.0
    for i in range(len(pts)):
        tau = pts[i][0]
        tp = sum(1 for s, l in pts if s >= tau and l)
        fn = sum(1 for s, l in pts if s < tau and l)
        tn = sum(1 for s, l in pts if s < tau and not l)
        fp = sum(1 for s, l in pts if s >= tau and not l)
        tpr = tp / (tp + fn) if tp + fn else 0.0
        fpr = fp / (fp + tn) if fp + tn else 0.0
        j = tpr - fpr
        if j > best_j:
            best_j, best_tau = j, tau
    return best_tau, best_j


def detect(s, crystal, tau, C, L, stride=4):
    """Event-level detection: statistic trace -> local maxima above
    tau. Returns (event_center_times, statistic_values)."""
    tmp = CrystalLearner(C, L)
    trace = [(t0, template_statistic(tmp.window(s, t0, C, L), crystal))
             for t0 in range(0, len(s) - L, stride)]
    events, svals = [], []
    for i in range(1, len(trace) - 1):
        t0, v = trace[i]
        if v >= tau and v >= trace[i - 1][1] and v >= trace[i + 1][1]:
            events.append(t0 + L // 2)
            svals.append(v)
    return events, svals


def score_events(events, peaks, tol):
    """Hit rate + false alarms at event level."""
    matched, hits = set(), 0
    for p in peaks:
        for e in events:
            if abs(e - p) <= tol and e not in matched:
                matched.add(e)
                hits += 1
                break
    return (hits / len(peaks) if peaks else 0.0), len(events) - len(matched)


def calibrate_tau(s, peaks, crystal, C, L, tol):
    """Youden's J over candidate-event statistics (tau=0 pre-pass),
    then frozen. Fail-closed: below tau -> silence."""
    events, svals = detect(s, crystal, 0.0, C, L)
    labs = [any(abs(e - p) <= tol for p in peaks) for e in events]
    tau, J = youden_threshold(list(zip(svals, labs)))
    return tau, J


def evaluate(s, peaks, crystal, tau, C, L, tol):
    """Frozen gate on a fresh stream: (hit_rate, false_alarms)."""
    events, _ = detect(s, crystal, tau, C, L)
    return score_events(events, peaks, tol)
