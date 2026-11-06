// Curated vibrant neon palette matching backend
export const COLOR_PALETTE = [
  '#00f0ff', // Electric Cyan
  '#ff0080', // Neon Magenta
  '#00ff88', // Neon Mint
  '#ffb400', // Bright Amber
  '#8c00ff', // Electric Violet
  '#ff3c3c', // Coral Red
  '#00b4ff', // Sky Blue
  '#ffe600', // Neon Yellow
  '#00ffc8', // Turquoise
  '#ff64c8', // Pink
];

export function getColorForId(id: number): string {
  return COLOR_PALETTE[id % COLOR_PALETTE.length];
}
