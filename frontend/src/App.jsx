import { useRef, useState } from 'react';
import CubeScene from './cube/CubeScene';
import Palette from './components/Palette';
import SolutionBar from './components/SolutionBar';
import { COLORS, SPEEDS } from './constants';
import { solveCube } from './api';
import './App.css';

const emptyColors = () => Array(24).fill(null);

// Returns an error text, or '' when the painted cube is OK to send.
function validate(colors) {
  const empty = colors.filter((c) => !c).length;
  if (empty) return `Paint all 24 stickers first (${empty} left).`;

  for (const letter of Object.keys(COLORS)) {
    const n = colors.filter((c) => c === letter).length;
    if (n !== 4) {
      return `Each color must be used exactly 4 times (${COLORS[letter].name} is used ${n}).`;
    }
  }
  return '';
}

export default function App() {
  const [colors, setColors] = useState(emptyColors);
  const [selected, setSelected] = useState('R');
  const [moves, setMoves] = useState([]);
  const [activeMove, setActiveMove] = useState(-1);
  const [status, setStatus] = useState('idle'); // idle | solving | playing | done
  const [message, setMessage] = useState('');
  const [speed, setSpeed] = useState(1);

  const cubeRef = useRef(null);
  const speedRef = useRef(1); // lets the speed change while a solution is playing

  const clearSolution = () => {
    setMoves([]);
    setActiveMove(-1);
    setStatus('idle');
  };

  const handlePaint = (index) => {
    setColors((prev) => {
      const next = [...prev];
      next[index] = selected;
      return next;
    });
    setMessage('');
  };

  const handleSpeed = () => {
    const next = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length];
    setSpeed(next);
    speedRef.current = next;
  };

  const handleReset = () => {
    cubeRef.current.resetPose();
    setColors(emptyColors());
    clearSolution();
    setMessage('');
  };

  const handleSolve = async () => {
    const error = validate(colors);
    if (error) {
      setMessage(error);
      return;
    }

    setMessage('');
    cubeRef.current.resetPose(); // start from the painted cube (also for a 2nd solve)
    setMoves([]);
    setActiveMove(-1);
    setStatus('solving');

    try {
      const list = await solveCube(colors);
      if (list.length === 0) {
        setMessage('The cube is already solved.');
        setStatus('idle');
        return;
      }
      setMoves(list);
      setStatus('playing');
      await cubeRef.current.playMoves(list, {
        getSpeed: () => speedRef.current,
        onMoveStart: setActiveMove,
      });
      setStatus('done');
    } catch (err) {
      setMessage(err.message || 'Something went wrong.');
      clearSolution();
    }
  };

  return (
    <div className="app">
      <header className="header">Cube Solver</header>

      <div className="body">
        <Palette colors={colors} selected={selected} onSelect={setSelected} />

        <main className="main">
          <div className="stage">
            <div className="canvas-wrap">
              <CubeScene
                ref={cubeRef}
                colors={colors}
                onPaint={handlePaint}
                onCubeReset={clearSolution}
              />
            </div>
            <div className="stage-hint">Drag to rotate · click a sticker to paint it</div>
          </div>

          <SolutionBar
            moves={moves}
            activeMove={activeMove}
            status={status}
            message={message}
            speed={speed}
            onSpeed={handleSpeed}
            onReset={handleReset}
            onSolve={handleSolve}
          />
        </main>
      </div>
    </div>
  );
}
