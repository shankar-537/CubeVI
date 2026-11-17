"""Script to pre-compute and dump Pattern Databases (PDB) to disk.

Building pattern databases at worker startup takes ~19 seconds of CPU time
and allocates large BFS queues, which causes timeouts and OOM kills on cheap cloud
tiers (e.g. 512MB RAM, shared vCPU).

This script pre-computes the databases offline and dumps them to disk (e.g. pdb.pickle)
so the worker can load them on boot in < 100ms.

Usage:
    python -m app.solver.build_pdb [--output path/to/pdb.pickle]
    python app/solver/build_pdb.py [--output path/to/pdb.pickle]
"""

import argparse
import logging
from pathlib import Path
import sys
import time

# Ensure backend root is on sys.path if run directly
current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.cube.state import CubeState
from app.solver.heuristics import (
    DEFAULT_PDB_PATH,
    CornerPatternDatabase,
    dump_pdb_file,
    load_pdb_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cubevi.build_pdb")


def build_and_dump_pdbs(output_path: str | Path | None = None) -> Path:
    """Pre-compute the standard corner pattern databases and dump them to disk.

    Args:
        output_path: Destination path for the pickled PDB. Defaults to DEFAULT_PDB_PATH.

    Returns:
        Path to the generated pickle file.
    """
    target_path = Path(output_path) if output_path else DEFAULT_PDB_PATH
    logger.info(f"Starting Pattern Database pre-computation...")
    total_start = time.perf_counter()

    # 1. Build PDB 1: corners (0, 1, 2, 3)
    logger.info("Building PDB 1 for corners (0, 1, 2, 3)...")
    t0 = time.perf_counter()
    pdb1 = CornerPatternDatabase(pattern_pieces=(0, 1, 2, 3), autoload=False)
    t_pdb1 = time.perf_counter() - t0
    logger.info(
        f"PDB 1 built in {t_pdb1:.2f}s ({len(pdb1.distances)} states)"
    )

    # 2. Build PDB 2: corners (4, 5, 6, 7)
    logger.info("Building PDB 2 for corners (4, 5, 6, 7)...")
    t0 = time.perf_counter()
    pdb2 = CornerPatternDatabase(pattern_pieces=(4, 5, 6, 7), autoload=False)
    t_pdb2 = time.perf_counter() - t0
    logger.info(
        f"PDB 2 built in {t_pdb2:.2f}s ({len(pdb2.distances)} states)"
    )

    # 3. Assemble payload with tuple keys and string aliases
    data = {
        (0, 1, 2, 3): pdb1.distances,
        (4, 5, 6, 7): pdb2.distances,
        "pdb1": pdb1.distances,
        "pdb2": pdb2.distances,
    }

    # 4. Dump to disk
    logger.info(f"Dumping PDB to {target_path}...")
    t0 = time.perf_counter()
    saved_path = dump_pdb_file(target_path, data)
    t_dump = time.perf_counter() - t0

    file_size_mb = saved_path.stat().st_size / (1024 * 1024)
    total_time = time.perf_counter() - total_start
    logger.info(
        f"Dumped {file_size_mb:.2f} MB in {t_dump:.2f}s. "
        f"Total pre-computation took {total_time:.2f}s."
    )

    # 5. Verify integrity and benchmark load speed
    logger.info("Verifying pickled PDB integrity and measuring load time...")
    t0 = time.perf_counter()
    loaded = load_pdb_file(saved_path)
    t_load_ms = (time.perf_counter() - t0) * 1000
    assert (0, 1, 2, 3) in loaded, "Key (0, 1, 2, 3) missing from loaded PDB!"
    assert (4, 5, 6, 7) in loaded, "Key (4, 5, 6, 7) missing from loaded PDB!"
    assert len(loaded[(0, 1, 2, 3)]) == 136080, f"Unexpected PDB1 size: {len(loaded[(0, 1, 2, 3)])}"
    assert len(loaded[(4, 5, 6, 7)]) == 136080, f"Unexpected PDB2 size: {len(loaded[(4, 5, 6, 7)])}"

    solved = CubeState.solved()
    test_pdb = CornerPatternDatabase((0, 1, 2, 3), db_path=saved_path)
    assert test_pdb.heuristic(solved) == 0

    logger.info(
        f"Verification successful! Load time from disk: {t_load_ms:.2f}ms (< 100ms)."
    )
    return saved_path


def main():
    parser = argparse.ArgumentParser(
        description="Pre-compute and dump Pattern Databases (PDB) to disk."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"Target file path for the pickled database (default: {DEFAULT_PDB_PATH})",
    )
    args = parser.parse_args()
    build_and_dump_pdbs(output_path=args.output)


if __name__ == "__main__":
    main()
