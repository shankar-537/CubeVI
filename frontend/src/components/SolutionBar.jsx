// Bottom bar: move list, status text and the Speed / Reset / Solve buttons.
export default function SolutionBar({
  moves,
  activeMove,
  status,
  isPaused,
  message,
  speed,
  onSpeed,
  onPause,
  onResume,
  onNext,
  onBack,
  onReset,
  onSolve,
  onScramble,
}) {
  const busy = status === 'solving' || status === 'playing';

  let info = 'Paint all 24 stickers, then press Solve. The moves will appear here and play on the cube.';
  if (status === 'solving') info = 'Solving...';
  if (status === 'playing') info = `Move ${activeMove + 1} of ${moves.length}`;
  if (status === 'done') info = `Done: ${moves.length} moves`;

  return (
    <section className="solution">
      <h2>2. Solution</h2>

      {moves.length > 0 && (
        <div className="moves">
          {moves.map((m, i) => (
            <span key={i} className={'move' + (i === activeMove ? ' active' : '')}>
              {m}
            </span>
          ))}
        </div>
      )}

      {message ? <p className="error">{message}</p> : <p className="info">{info}</p>}

      <div className="buttons">
        <button className="btn" onClick={onSpeed}>
          Speed {speed}x
        </button>
        

        <button
          className="btn"
          onClick={onPause}
          disabled={status !== 'playing' || isPaused}
        >
          Pause
        </button>

        <button
          className="btn"
          onClick={onResume}
          disabled={status !== 'playing' || !isPaused}
        >
          Resume
        </button>

        <button
          className="btn"
          onClick={onNext}
          disabled={moves.length === 0 || activeMove >= moves.length - 1}
        >
          Next
        </button>
        <button
          className="btn"
          onClick={onBack}
          disabled={activeMove < 0 || (status === 'playing' && !isPaused && activeMove === 0)}
        >
          Back
        </button>
        <div className="spacer" />
        <button className="btn" onClick={onReset}>
          Reset
        </button>

        <button
          className="btn"
          onClick={onScramble}
          disabled={busy}
        >
          Scramble
        </button>
        <button className="btn" onClick={onSolve} disabled={busy}>
          Solve!
        </button>
      </div>
    </section>
  );
}

