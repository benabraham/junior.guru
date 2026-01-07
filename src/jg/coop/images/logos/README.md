# Logos

Various logos of companies and communities used throughout the project (HTML images, website…). Ideally SVGs.

## Automated workflow (recommended)

Requires Inkscape installed (`inkscape --version` to verify).

```bash
# Single logo
uv run jg tidy optimize-logo src/jg/coop/images/logos/foo.svg

# Dry run (see what would change)
python scripts/optimize_logo.py src/jg/coop/images/logos/foo.svg --dry-run

# All logos (batch)
for f in src/jg/coop/images/logos/*.svg; do
  python scripts/optimize_logo.py "$f"
done
```

What it does:
- Deep ungroup (preserves masks/clips)
- Scale to 4980px, crop to fit, center on page
- Set viewBox to 5000px width, even height with ~15px margin
- Minify with SVGO (precision 0)

Config: `svgo.config.logos.cjs` in project root.

## Simple workflow for adding SVGs

1. Open in Inkscape.
2. Ctrl+Shift+R (crop to fit)

## Full manual workflow for adding SVGs that are minified and easier to work with later

1. Open in Inkscape.
2. Ctrl+Shift+D (document properties)
3. Check if: 
   - Scale is 1, change to 1 if not
   - Units are px, change to px if not
4. Select all and set width to 4980 px
5. Ctrl+Shift+R (crop to fit)
6. Ctrl+Shift+D (document properties)
   - set width to 5000 px
   - set height to nearest higher even number that gives the logo about 11 to 19 more pixels (1356 to 1370) 
7. Select all and Ungroup (Ctrl+Shift+G)
8. Optional: you can ungroup all down and merge elements (Ctrl++) with the same color. If masks and such is used this might get complex, ask Dan Srb to do it then. 
9. Align and Distribute (Ctrl+Shift+A)
   - check Move/align selection as group
   - set Relative to: "Page"
   - click center icons, both vertical and horizontal
10. Use https://jakearchibald.github.io/svgomg/ to get minified version.
   - set Number and Transform precision to 0
     - Do not forget to test with "Show original" if the shape didn't change too much. Normally it shouldn't but there are special cases in which setting one of the precisions to 1 makes difference.
   - Features all on except for:
     - remove xmlns
     - Remove viewBox
     - Prefer viewBox to width/height
     - Replace duplicate elements with links
     - Replace xlink with native SVG
