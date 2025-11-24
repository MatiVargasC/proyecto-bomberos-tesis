#!/usr/bin/env python3
"""Convert SVG files in a directory to PNG using cairosvg.

Usage:
  python scripts/convert_svgs_to_png.py --input static/images --overwrite

Requires: cairosvg (pip install cairosvg)

This script is lightweight and intended for local development to produce
PNG fallbacks for SVGs that may not render correctly inside some components.
"""
import argparse
import os
import sys

try:
    import cairosvg
except Exception:
    print("Error: cairosvg is required. Install with: pip install cairosvg")
    sys.exit(1)


def convert_file(svg_path, png_path, scale=1.0):
    try:
        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
        print(f"Converted: {os.path.basename(svg_path)} -> {os.path.basename(png_path)}")
    except Exception as e:
        print(f"Failed to convert {svg_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert SVGs to PNGs in a directory.")
    parser.add_argument('--input', '-i', required=True, help='Input directory containing .svg files')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing PNGs')
    parser.add_argument('--scale', type=float, default=1.0, help='Scale factor for output PNGs')
    parser.add_argument('--dry-run', action='store_true', help="List files that would be converted without writing")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    if not os.path.isdir(input_dir):
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)

    svgs = [f for f in os.listdir(input_dir) if f.lower().endswith('.svg')]
    if not svgs:
        print("No SVG files found in the input directory.")
        return

    for name in svgs:
        svg_path = os.path.join(input_dir, name)
        png_name = os.path.splitext(name)[0] + '.png'
        png_path = os.path.join(input_dir, png_name)

        if os.path.exists(png_path) and not args.overwrite:
            print(f"Skipping (exists): {png_name}")
            continue

        if args.dry_run:
            print(f"Would convert: {name} -> {png_name}")
            continue

        convert_file(svg_path, png_path, scale=args.scale)


if __name__ == '__main__':
    main()
