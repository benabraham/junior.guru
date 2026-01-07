#!/usr/bin/env python3
"""
Automate logo SVG processing workflow.

Replaces the manual 10-step Inkscape + SVGOMG workflow from logos/README.md:
1. Set document properties (scale=1, units=px)
2. Set width to 4980px
3. Crop to fit
4. Set final dimensions (5000px width, even height with margin)
5. Deep ungroup (preserving masks/clips)
6. Center on page
7. Minify with SVGO

Usage:
    python scripts/optimize_logo.py path/to/logo.svg
    python scripts/optimize_logo.py path/to/logo.svg --dry-run
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_inkscape(input_path, output_path, target_width=5000, margin_range=(11, 19)):
    """Run Inkscape CLI operations for geometry processing."""
    # LC_NUMERIC=C is required for decimal point handling in some locales
    env = {**os.environ, 'LC_NUMERIC': 'C'}

    # Pass 1: Ungroup and save to temp file
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
        tmp_ungrouped = Path(tmp.name)

    actions_pass1 = ';'.join([
        'select-all',
        'mcepl.ungroup-deep',
        'fit-canvas-to-selection',
        f'export-filename:{tmp_ungrouped}',
        'export-plain-svg:true',
        'export-do',
    ])

    subprocess.run(
        ['inkscape', str(input_path), '--actions', actions_pass1],
        capture_output=True,
        text=True,
        env=env,
    )

    # Query width of ungrouped file
    result = subprocess.run(
        ['inkscape', str(tmp_ungrouped), '--query-width'],
        capture_output=True,
        text=True,
        env=env,
    )

    try:
        current_width = float(result.stdout.strip())
    except ValueError:
        current_width = 0

    if current_width <= 0:
        print(f"Warning: Could not query width, using scale factor 1", file=sys.stderr)
        scale_factor = 1.0
    else:
        scale_factor = target_width / current_width

    # Pass 2: Scale and fit canvas
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
        tmp_scaled = Path(tmp.name)

    actions_pass2 = ';'.join([
        'select-all',
        f'transform-scale:{scale_factor}',
        'fit-canvas-to-selection',
        f'export-filename:{tmp_scaled}',
        'export-plain-svg:true',
        'export-do',
    ])

    subprocess.run(
        ['inkscape', str(tmp_ungrouped), '--actions', actions_pass2],
        capture_output=True,
        text=True,
        env=env,
    )

    tmp_ungrouped.unlink()

    # Query height after scaling
    result = subprocess.run(
        ['inkscape', str(tmp_scaled), '--query-height'],
        capture_output=True,
        text=True,
        env=env,
    )

    try:
        current_height = float(result.stdout.strip())
    except ValueError:
        current_height = 1000

    # Calculate new height with margin, rounded to even
    min_margin, max_margin = margin_range
    target_margin = (min_margin + max_margin) // 2
    new_height = int(current_height + target_margin)
    if new_height % 2:
        new_height += 1

    # Set document dimensions using sed
    subprocess.run([
        'sed', '-i',
        f's/width="[^"]*"/width="{target_width}"/;'
        f's/height="[^"]*"/height="{new_height}"/;'
        f's/viewBox="[^"]*"/viewBox="0 0 {target_width} {new_height}"/',
        str(tmp_scaled)
    ], check=True)

    # Pass 3: Center objects on the new page size
    actions_pass3 = ';'.join([
        'select-all',
        'object-align:hcenter vcenter page group',
        f'export-filename:{output_path}',
        'export-plain-svg:true',
        'export-do',
    ])

    result = subprocess.run(
        ['inkscape', str(tmp_scaled), '--actions', actions_pass3],
        capture_output=True,
        text=True,
        env=env,
    )

    tmp_scaled.unlink()

    if result.returncode != 0:
        print(f"Inkscape error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def run_svgo(input_path, output_path, config_path):
    """Run SVGO for final minification."""
    result = subprocess.run(
        ['npx', 'svgo', '--config', str(config_path), '-i', str(input_path), '-o', str(output_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"SVGO error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def restore_attributes(svg_path):
    """Restore attributes that SVGO strips (width, height, xmlns)."""
    import re

    content = svg_path.read_text()

    # Add xmlns if missing
    if 'xmlns="' not in content:
        content = content.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)

    # Extract viewBox dimensions and add width/height if missing
    match = re.search(r'viewBox="[^\s]+\s+[^\s]+\s+(\d+)\s+(\d+)"', content)
    if match and 'width="' not in content:
        w, h = match.groups()
        content = re.sub(
            r'(viewBox="[^"]*")',
            rf'\1 width="{w}" height="{h}"',
            content
        )

    svg_path.write_text(content)


def process_logo(input_path, dry_run=False):
    """Process a logo SVG through the full workflow."""
    input_path = Path(input_path).resolve()
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'svgo.config.logos.cjs'

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not config_path.exists():
        print(f"Error: SVGO config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {input_path}")
    size_before = input_path.stat().st_size

    # Create temp files for intermediate steps
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_inkscape = Path(tmpdir) / 'inkscape_output.svg'
        tmp_final = Path(tmpdir) / 'final.svg'

        # Step 1: Inkscape geometry operations (ungroup, scale, resize, center)
        print("  → Running Inkscape (ungroup, scale, resize, center)...")
        run_inkscape(input_path, tmp_inkscape)

        # Step 2: SVGO minification
        print("  → Running SVGO minification...")
        run_svgo(tmp_inkscape, tmp_final, config_path)

        size_after = tmp_final.stat().st_size

        if dry_run:
            print(f"  [DRY RUN] Would save: {size_before} → {size_after} bytes ({100 * size_after // size_before}%)")
        else:
            shutil.copy(tmp_final, input_path)
            print(f"  ✓ Done: {size_before} → {size_after} bytes ({100 * size_after // size_before}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Automate logo SVG processing workflow'
    )
    parser.add_argument('svg_path', help='Path to SVG file to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()
    process_logo(args.svg_path, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
