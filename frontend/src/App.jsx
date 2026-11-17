import { useRef, useState } from 'react';
import CubeScene from './cube/CubeScene';
import Palette from './components/Palette';
import SolutionBar from './components/SolutionBar';
import { COLORS, SPEEDS } from './constants';
import { solveCube, scrambleCube } from './api';
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
  const [isPaused, setIsPaused] = useState(false);
  const [message, setMessage] = useState('');
  const [speed, setSpeed] = useState(1);

  const cubeRef = useRef(null);
  const speedRef = useRef(1); // lets the speed change while a solution is playing

  const clearSolution = () => {
    setMoves([]);
    setActiveMove(-1);
    setStatus('idle');
    setIsPaused(false);
  };

  const handlePaint = (index) => {
    setColors((prev) => {
      // No change if the sticker already has this color
      if (prev[index] === selected) return prev;

      // Check how many stickers already use this color
      const used = prev.filter((c) => c === selected).length;

      // Do not allow more than 4 stickers of one color
      if (used >= 4) return prev;

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

  const handlePause = () => {
    cubeRef.current.pausePlayback();
    setIsPaused(true);
  };

  const handleNext = () => {
    cubeRef.current.requestNext(moves);
    setIsPaused(true);
  };

  const handleBack = () => {
    cubeRef.current.requestBack(moves);
    setIsPaused(true);
  };

  const handleResume = () => {
    cubeRef.current.resumePlayback();
    setIsPaused(false);
  };

  const handleReset = () => {
    cubeRef.current.resetPose();
    setColors(emptyColors());
    clearSolution();
    setMessage('');
  };

  const handleScramble = async () => {
    try {
      setMessage('');

      cubeRef.current.resetPose();

      const data = await scrambleCube(6);

      setColors(
        ['U', 'R', 'F', 'D', 'L', 'B'].flatMap(
          (face) => data.faces[face]
        )
      );

      setMoves(data.scramble);
      setActiveMove(data.scramble.length - 1);
      setStatus('done');
      setIsPaused(false);
    } catch (err) {
      setMessage(err.message || 'Could not generate scramble.');
    }
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
    setIsPaused(false);

    try {
      const list = await solveCube(colors);
      if (list.length === 0) {
        setMessage('The cube is already solved.');
        setStatus('idle');
        return;
      }
      setMoves(list);
      setStatus('playing');
      setIsPaused(false);

      const completed = await cubeRef.current.playMoves(list, {
        getSpeed: () => speedRef.current,
        onMoveStart: setActiveMove,
      });

      if (completed) {
        setStatus('done');
      }
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
            isPaused={isPaused}
            message={message}
            speed={speed}
            onSpeed={handleSpeed}
            onPause={handlePause}
            onResume={handleResume}
            onNext={handleNext}
            onBack={handleBack}
            onReset={handleReset}
            onSolve={handleSolve}
            onScramble={handleScramble}
          />
        </main>
      </div>
    </div>
  );
}
