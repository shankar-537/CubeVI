
// Handles all communication between the frontend and backend.
//
// Frontend sticker order:
// U: 0-3, R: 4-7, F: 8-11,
// D: 12-15, L: 16-19, B: 20-23.
//
// Backend expects:
// {
//   faces: { U: [...], R: [...], F: [...], D: [...], L: [...], B: [...] },
//   constraint: ""
// }

const API_URL = import.meta.env.VITE_API_URL ?? '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Convert the frontend's 24-element array into the backend's face format.
function convertToFaces(colors) {
  const faceNames = ['U', 'R', 'F', 'D', 'L', 'B'];
  const faces = {};

  for (let i = 0; i < 6; i++) {
    faces[faceNames[i]] = colors.slice(i * 4, i * 4 + 4);
  }

  return faces;
}

export async function solveCube(colors) {
  if (USE_MOCK) {
    // Temporary fake solution for testing the animation.
    await delay(600);
    return ['R', 'U', "R'", "U'", "R'", 'F', 'R2', "U'", "R'"];
  }

  const requestBody = {
    faces: convertToFaces(colors),
    constraint: '',
  };

  const res = await fetch(`${API_URL}/solve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

const responseText = await res.text();

let data;

try {
  data = JSON.parse(responseText);
} catch {
  throw new Error(
    `Backend returned an empty or invalid response. Status: ${res.status}. Response: ${responseText || '(empty)'}`
  );
}

  if (!res.ok) {
    throw new Error(data.detail || `Solver error (${res.status})`);
  }

  if (!Array.isArray(data.moves)) {
    throw new Error('Unexpected reply from solver.');
  }

  if (data.valid === false) {
    throw new Error(data.explanation || 'Invalid cube state.');
  }

  return data.moves;
}
