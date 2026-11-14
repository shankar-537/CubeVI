// Bottom bar: move list, status text and the Speed / Reset / Solve buttons.
export default function SolutionBar({
  moves,
  activeMove,
  status,
  message,
  speed,
  onSpeed,
  onReset,
  onSolve,
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
        <div className="spacer" />
        <button className="btn" onClick={onReset} disabled={busy}>
          Reset
        </button>
        <button className="btn" onClick={onSolve} disabled={busy}>
          Solve!
        </button>
      </div>
    </section>
  );
}

