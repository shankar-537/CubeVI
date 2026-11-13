// Turns a move string like "R", "U'" or "F2" into what the animation needs:
//   axis  - which axis the layer turns around
//   layer - +1 or -1: which half of the cube turns (the side the face is on)
//   angle - radians (clockwise when looking at that face)
const HALF = Math.PI / 2;

const FACE_MOVES = {
  R: { axis: 'x', layer: 1, angle: -HALF },
  L: { axis: 'x', layer: -1, angle: HALF },
  U: { axis: 'y', layer: 1, angle: -HALF },
  D: { axis: 'y', layer: -1, angle: HALF },
  F: { axis: 'z', layer: 1, angle: -HALF },
  B: { axis: 'z', layer: -1, angle: HALF },
};

export function parseMove(text) {
  const match = /^([URFDLB])([2'’]?)$/.exec(String(text).trim());
  if (!match) throw new Error(`Unknown move "${text}"`);

  const [, face, suffix] = match;
  const base = FACE_MOVES[face];
  let angle = base.angle;
  let double = false;

  if (suffix === '2') {
    angle *= 2;
    double = true;
  } else if (suffix === "'" || suffix === '’') {
    angle = -angle;
  }

  return { axis: base.axis, layer: base.layer, angle, double };
}
