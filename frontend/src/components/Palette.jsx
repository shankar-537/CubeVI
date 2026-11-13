import { COLORS } from '../constants';

// Left column: pick a color, then click a sticker on the cube.
export default function Palette({ colors, selected, onSelect }) {
  const painted = colors.filter(Boolean).length;

  return (
    <aside className="palette">
      <h2>1. Pick a color</h2>
      <p className="sub">then click a sticker</p>

      {Object.entries(COLORS).map(([letter, c]) => {
        const used = colors.filter((x) => x === letter).length;
        return (
          <button
            key={letter}
            className={'swatch' + (selected === letter ? ' selected' : '')}
            style={{ background: c.hex, color: c.text }}
            onClick={() => onSelect(letter)}
          >
            <span>{c.name}</span>
            <small>{used} / 4</small>
          </button>
        );
      })}

      <p className="painted">{painted} / 24 painted</p>
    </aside>
  );
}
