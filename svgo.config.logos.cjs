/**
 * SVGO config for logo optimization.
 *
 * Matches the SVGOMG settings from src/jg/coop/images/logos/README.md:
 * - Number and Transform precision: 0
 * - Features all ON except:
 *   - remove xmlns (keep it)
 *   - Remove viewBox (keep it)
 *   - Prefer viewBox to width/height (keep dimensions)
 *   - Replace duplicate elements with links (disabled)
 *   - Replace xlink with native SVG (disabled)
 */
module.exports = {
  floatPrecision: 0,
  transformPrecision: 0,
  js2svg: {
    indent: 2,
    pretty: true,
  },
  plugins: [
    // ON - cleanup and minification
    'cleanupAttrs',
    'cleanupEnableBackground',
    'cleanupIds',
    'cleanupListOfValues',
    'cleanupNumericValues',
    'collapseGroups',
    'convertColors',
    'convertEllipseToCircle',
    'convertOneStopGradients',
    'convertPathData',
    'convertShapeToPath',
    'convertStyleToAttrs',
    'convertTransform',
    'inlineStyles',
    'mergePaths',
    'mergeStyles',
    'minifyStyles',
    'moveElemsAttrsToGroup',
    'moveGroupAttrsToElems',
    'removeComments',
    'removeDeprecatedAttrs',
    'removeDesc',
    'removeDoctype',
    'removeEditorsNSData',
    'removeEmptyAttrs',
    'removeEmptyContainers',
    'removeEmptyText',
    'removeHiddenElems',
    'removeMetadata',
    'removeNonInheritableGroupAttrs',
    'removeTitle',
    'removeUnusedNS',
    'removeUselessDefs',
    'removeUselessStrokeAndFill',
    'removeXMLProcInst',
    'sortAttrs',
    'sortDefsChildren',
    // ON - useful for logos (disabled by default in SVGO)
    'removeRasterImages',
    'removeScripts',
    'removeStyleElement',
  ],
}
