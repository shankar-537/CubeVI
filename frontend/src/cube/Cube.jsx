import { forwardRef, useImperativeHandle, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { CUBIES } from './faces';
import { parseMove } from './moves';
import { COLORS, EMPTY_COLOR } from '../constants';

const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// The 2x2x2 cube itself.
// Props : colors (24 letters or null), onPaint(index), onCubeReset()
// Ref   : playMoves(moves, { getSpeed, onMoveStart }), resetPose()
const Cube = forwardRef(function Cube({ colors, onPaint, onCubeReset }, ref) {
  const rootRef = useRef();
  const pivotRef = useRef(); // temporary parent that spins the turning layer
  const cubieRefs = useRef([]);
  const anim = useRef(null); // the turn currently playing
  const busy = useRef(false);
  const dirty = useRef(false); // true once the cube has been turned

  // Put all 8 small cubes back to their starting place.
  const resetPose = () => {
    CUBIES.forEach((cubie, i) => {
      const g = cubieRefs.current[i];
      if (!g) return;
      rootRef.current.add(g);
      g.position.set(...cubie.pos);
      g.quaternion.identity();
    });
    dirty.current = false;
  };

  // Start one layer turn, resolves when it has finished.
  const turn = (move, duration) =>
    new Promise((resolve) => {
      const pivot = pivotRef.current;
      pivot.rotation.set(0, 0, 0);
      cubieRefs.current.forEach((g) => {
        if (g.position[move.axis] * move.layer > 0) pivot.attach(g);
      });
      anim.current = { ...move, duration, elapsed: 0, resolve };
    });

  const finishTurn = () => {
    const a = anim.current;
    const pivot = pivotRef.current;
    pivot.rotation[a.axis] = a.angle;
    [...pivot.children].forEach((g) => {
      rootRef.current.attach(g);
      // remove tiny rounding errors so positions stay exactly +-0.5
      g.position.set(
        Math.round(g.position.x * 2) / 2,
        Math.round(g.position.y * 2) / 2,
        Math.round(g.position.z * 2) / 2
      );
    });
    pivot.rotation.set(0, 0, 0);
    anim.current = null;
    a.resolve();
  };

  useFrame((_, delta) => {
    const a = anim.current;
    if (!a) return;
    a.elapsed += delta * 1000;
    const t = Math.min(a.elapsed / a.duration, 1);
    pivotRef.current.rotation[a.axis] = a.angle * easeInOut(t);
    if (t >= 1) finishTurn();
  });

  useImperativeHandle(ref, () => ({
    resetPose,
    async playMoves(moves, { getSpeed = () => 1, onMoveStart } = {}) {
      busy.current = true;
      dirty.current = true;
      try {
        for (let i = 0; i < moves.length; i++) {
          const move = parseMove(moves[i]);
          onMoveStart?.(i);
          await turn(move, (move.double ? 650 : 420) / getSpeed());
          await sleep(120 / getSpeed());
        }
      } finally {
        busy.current = false;
      }
    },
  }));

  const handlePaint = (index) => {
    if (busy.current) return;
    // After a solve the cube is scrambled/solved visually, so the first
    // click only puts it back to the painted state.
    if (dirty.current) {
      resetPose();
      onCubeReset?.();
      return;
    }
    onPaint(index);
  };

  return (
    <group ref={rootRef}>
      <group ref={pivotRef} />
      {CUBIES.map((cubie, i) => (
        <group
          key={cubie.key}
          ref={(el) => (cubieRefs.current[i] = el)}
          position={cubie.pos}
        >
          <mesh>
            <boxGeometry args={[0.98, 0.98, 0.98]} />
            <meshStandardMaterial color="#111111" roughness={0.7} />
          </mesh>

          {cubie.stickers.map((s) => {
            const letter = colors[s.index];
            return (
              <mesh
                key={s.index}
                position={s.localPos}
                quaternion={s.quat}
                onClick={(e) => {
                  e.stopPropagation();
                  if (e.delta > 4) return; // it was a drag (rotating), not a click
                  handlePaint(s.index);
                }}
                onPointerOver={() => (document.body.style.cursor = 'pointer')}
                onPointerOut={() => (document.body.style.cursor = 'auto')}
              >
                <planeGeometry args={[0.82, 0.82]} />
                <meshStandardMaterial
                  color={letter ? COLORS[letter].hex : EMPTY_COLOR}
                  roughness={0.6}
                />
              </mesh>
            );
          })}
        </group>
      ))}
    </group>
  );
});

export default Cube;
