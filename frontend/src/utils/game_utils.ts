const HALF_MORALE = 50;
const MAX_MORALE = 100;

const newValueGivenMorale = (baseline: number, morale: number, k: number = 0.01): number => {
    if (morale < 0 || morale > MAX_MORALE) {
        throw new Error(`Morale must be between 0 and ${MAX_MORALE}, got ${morale}`);
    }
    return baseline * (2 / (1 + Math.exp(-k * (morale - HALF_MORALE))));
};

const lerpColor = (from: string, to: string, t: number): string => {
    const f = parseInt(from.slice(1), 16);
    const tInt = parseInt(to.slice(1), 16);

    const r1 = (f >> 16) & 0xff;
    const g1 = (f >> 8) & 0xff;
    const b1 = f & 0xff;

    const r2 = (tInt >> 16) & 0xff;
    const g2 = (tInt >> 8) & 0xff;
    const b2 = tInt & 0xff;

    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);

    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
};

export { lerpColor, newValueGivenMorale };