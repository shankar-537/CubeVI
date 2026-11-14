import * as THREE from 'three';

// Face order used everywhere (state array, backend string): U R F D L B.
// Each face has 4 stickers, index = faceNumber * 4 + k, k = 0..3 read
// row by row as seen from OUTSIDE the cube:   0 1
//                                              2 3
// n = outward normal, r = "right" on screen, d = "down" on screen.
export const FACES = [
  { name: 'U', n: [0, 1, 0], r: [1, 0, 0], d: [0, 0, 1] },
  { name: 'R', n: [1, 0, 0], r: [0, 0, -1], d: [0, -1, 0] },
  { name: 'F', n: [0, 0, 1], r: [1, 0, 0], d: [0, -1, 0] },
  { name: 'D', n: [0, -1, 0], r: [1, 0, 0], d: [0, 0, -1] },
  { name: 'L', n: [-1, 0, 0], r: [0, 0, 1], d: [0, -1, 0] },
  { name: 'B', n: [0, 0, -1], r: [-1, 0, 0], d: [0, -1, 0] },
];

// Builds the 8 small cubes. Each one knows its start position and the
// 3 stickers on its outside (24 stickers in total).
function buildCubies() {
  const map = new Map();
  const zAxis = new THREE.Vector3(0, 0, 1);

  FACES.forEach((face, faceNo) => {
    for (let k = 0; k < 4; k++) {
      const col = k & 1 ? 1 : -1;
      const row = k >> 1 ? 1 : -1;

      // center of the small cube that owns this sticker
      const pos = face.n.map(
        (v, i) => 0.5 * v + 0.5 * col * face.r[i] + 0.5 * row * face.d[i]
      );
      const key = pos.join(',');
      if (!map.has(key)) map.set(key, { key, pos, stickers: [] });

      map.get(key).stickers.push({
        index: faceNo * 4 + k,
        localPos: face.n.map((v) => v * 0.495), // just outside the cube body
        quat: new THREE.Quaternion().setFromUnitVectors(
          zAxis,
          new THREE.Vector3(...face.n)
        ),
      });
    }
  });

  return [...map.values()];
}

export const CUBIES = buildCubies();
