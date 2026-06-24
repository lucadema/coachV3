import { jsPDF } from 'jspdf';

export type AetherGlimpsePathway = {
  title: string;
  orientation: string;
  conditions: string;
};

export type AetherGlimpsePdfData = {
  title: string;
  intro: string;
  problemDefinition: string;
  pathways: AetherGlimpsePathway[];
};

type PdfOptions = {
  filename?: string;
  logoDataUrl?: string;
  /**
   * Optional public URL for the logo. Defaults to /aether-logo.png.
   * If the logo cannot be loaded, the generator falls back to the simple text mark.
   */
  logoUrl?: string;
  generatedAt?: Date;
  /**
   * Defaults to true. The approved layout requires Inter everywhere.
   * Set to false only for local debugging when the Inter font files are unavailable.
   */
  useInterFont?: boolean;
};

type Layout = {
  pageWidth: number;
  pageHeight: number;
  marginX: number;
  marginTop: number;
  marginBottom: number;
  contentWidth: number;
};

type Rgb = [number, number, number];

type FontFamily = 'Inter' | 'helvetica';
type FontStyle = 'normal' | 'bold' | 'italic' | 'bolditalic';

const COLORS = {
  ink: [41, 73, 68] as Rgb,
  muted: [41, 73, 68] as Rgb,
  brand: [41, 73, 68] as Rgb,
  brandDark: [41, 73, 68] as Rgb,
  paleGreen: [240, 246, 245] as Rgb,
  paleGreen2: [247, 250, 249] as Rgb,
  border: [174, 194, 191] as Rgb,
  divider: [214, 226, 224] as Rgb,
  white: [255, 255, 255] as Rgb,
};

const TYPOGRAPHY = {
  titleSize: 30,
  introSize: 10,
  sectionHeadingSize: 10,
  problemBodySize: 10,
  cardTitleSize: 10,
  cardLabelSize: 10,
  cardBodySize: 10,
};

const INTER_FONT_FILES: Record<FontStyle, string> = {
  normal: 'Inter-ExtraLight.ttf',
  italic: 'Inter-ExtraLightItalic.ttf',
  bold: 'Inter-Bold.ttf',
  bolditalic: 'Inter-BoldItalic.ttf',
};

/**
 * Public entry point for the browser.
 * This creates and downloads the PDF immediately.
 */
export async function downloadAetherGlimpsePdf(
  data: AetherGlimpsePdfData,
  options: PdfOptions = {},
): Promise<void> {
  const doc = await buildAetherGlimpsePdf(data, options);
  doc.save(options.filename ?? 'aether-glimpse-session-outputs.pdf');
}

/**
 * Useful for testing: returns the jsPDF instance without saving it.
 */
export async function buildAetherGlimpsePdf(
  data: AetherGlimpsePdfData,
  options: PdfOptions = {},
): Promise<jsPDF> {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
    compress: true,
  });

  const fontFamily = options.useInterFont === false ? 'helvetica' : await initialiseFontFamily(doc);
  const layout = createLayout(doc);
  const logoDataUrl = options.logoDataUrl ?? (await loadOptionalLogoDataUrl(options.logoUrl ?? '/aether-logo.png'));
  let y = layout.marginTop;

  y = addCoverHeader(doc, layout, fontFamily, data.title, logoDataUrl, y);
  y = addIntro(doc, layout, fontFamily, data.intro, y);
  y = addSectionHeading(doc, layout, fontFamily, 'Problem definition', y + 3);
  y = addProblemDefinition(doc, layout, fontFamily, data.problemDefinition, y);
  y = addSectionHeading(doc, layout, fontFamily, 'Resolution pathways', y + 5);

  data.pathways.forEach((pathway, index) => {
    y = addPathwayCard(doc, layout, fontFamily, pathway, y + (index === 0 ? 0 : 4));
  });

  addFooters(doc, layout, fontFamily, options.generatedAt ?? new Date());
  return doc;
}


async function loadOptionalLogoDataUrl(url: string): Promise<string | undefined> {
  try {
    const response = await fetch(url);
    if (!response.ok) return undefined;

    const blob = await response.blob();
    if (!blob.type.startsWith('image/')) return undefined;

    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(reader.error ?? new Error(`Could not read logo image: ${url}`));
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.warn(`Could not load logo image from ${url}. Falling back to text mark.`, error);
    return undefined;
  }
}

async function initialiseFontFamily(doc: jsPDF): Promise<FontFamily> {
  try {
    await Promise.all(
      Object.entries(INTER_FONT_FILES).map(async ([style, filename]) => {
        const base64 = await fetchFontAsBase64(`/fonts/${filename}`);
        doc.addFileToVFS(filename, base64);
        doc.addFont(filename, 'Inter', style as FontStyle);
      }),
    );
    return 'Inter';
  } catch (error) {
    console.error('Could not initialise Inter for the PDF:', error);
    throw new Error(
      'The approved PDF layout requires Inter font files in public/fonts. ' +
        'Add Inter-ExtraLight.ttf, Inter-ExtraLightItalic.ttf, Inter-Bold.ttf and Inter-BoldItalic.ttf, then restart the dev server.',
      { cause: error },
    );
  }
}

async function fetchFontAsBase64(url: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load font: ${url}`);
  }

  const buffer = await response.arrayBuffer();
  const bytes = new Uint8Array(buffer);

  // Vite can return index.html with a 200 status for a missing public asset.
  // That looks like a successful fetch but is not a font file, and jsPDF will fail later.
  // TrueType/OpenType fonts usually start with 0x00010000, "OTTO", "ttcf", or "true".
  const signature = String.fromCharCode(...bytes.slice(0, 4));
  const isLikelyFont =
    (bytes[0] === 0x00 && bytes[1] === 0x01 && bytes[2] === 0x00 && bytes[3] === 0x00) ||
    signature === 'OTTO' ||
    signature === 'ttcf' ||
    signature === 'true';

  if (!isLikelyFont) {
    throw new Error(`Fetched asset is not a valid TTF/OTF font: ${url}`);
  }

  let binary = '';
  const chunkSize = 0x8000;

  for (let index = 0; index < bytes.length; index += chunkSize) {
    const chunk = bytes.subarray(index, index + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return btoa(binary);
}

function setPdfFont(doc: jsPDF, fontFamily: FontFamily, style: FontStyle): void {
  doc.setFont(fontFamily, style);
}

function drawSquareBox(
  doc: jsPDF,
  x: number,
  y: number,
  width: number,
  height: number,
  fillColor: Rgb,
  borderColor: Rgb,
  lineWidth = 0.25,
): void {
  // Draw the fill and each border side explicitly. This avoids any rounded-corner
  // rendering artefacts and makes the problem and pathway containers definitely square.
  doc.setFillColor(...fillColor);
  doc.rect(x, y, width, height, 'F');

  doc.setDrawColor(...borderColor);
  doc.setLineWidth(lineWidth);
  doc.line(x, y, x + width, y);
  doc.line(x + width, y, x + width, y + height);
  doc.line(x + width, y + height, x, y + height);
  doc.line(x, y + height, x, y);
}

function createLayout(doc: jsPDF): Layout {
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const marginX = 18;
  const marginTop = 18;
  const marginBottom = 18;

  return {
    pageWidth,
    pageHeight,
    marginX,
    marginTop,
    marginBottom,
    contentWidth: pageWidth - marginX * 2,
  };
}

function addCoverHeader(
  doc: jsPDF,
  layout: Layout,
  fontFamily: FontFamily,
  title: string,
  logoDataUrl: string | undefined,
  y: number,
): number {
  if (logoDataUrl) {
    const logoWidth = 42;
    const logoHeight = 10.75;
    doc.addImage(logoDataUrl, 'PNG', layout.pageWidth - layout.marginX - logoWidth, y - 2, logoWidth, logoHeight);
  } else {
    doc.setDrawColor(...COLORS.brand);
    doc.setFillColor(...COLORS.paleGreen);
    doc.rect(layout.pageWidth - layout.marginX - 31, y - 2, 31, 11, 'FD');
    setPdfFont(doc, fontFamily, 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(...COLORS.brandDark);
    doc.text('AETHER', layout.pageWidth - layout.marginX - 15.5, y + 5.2, { align: 'center' });
  }
  
  const titleDown = 8;
  setPdfFont(doc, fontFamily, 'normal');
  doc.setFontSize(TYPOGRAPHY.titleSize);
  doc.setTextColor(...COLORS.brandDark);
  doc.text(clean(title), layout.marginX, y + 20 + titleDown);

  return y + 33 + titleDown;
}

function addContinuationHeader(doc: jsPDF, layout: Layout, fontFamily: FontFamily): number {
  const y = 12;

  setPdfFont(doc, fontFamily, 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(...COLORS.brand);
  doc.text('Aether Glimpse', layout.marginX, y);

  return y + 8;
}

function addIntro(doc: jsPDF, layout: Layout, fontFamily: FontFamily, intro: string, y: number): number {
  setPdfFont(doc, fontFamily, 'bold');
  doc.setFontSize(TYPOGRAPHY.introSize);
  doc.setTextColor(...COLORS.brandDark);

  const lines = split(doc, intro, layout.contentWidth);
  doc.text(lines, layout.marginX, y, { lineHeightFactor: 1.26 });

  return y + blockHeight(TYPOGRAPHY.introSize, lines.length, 1.26) + 3;
}

function addSectionHeading(
  doc: jsPDF,
  layout: Layout,
  fontFamily: FontFamily,
  heading: string,
  y: number,
): number {
  y = ensureSpace(doc, layout, fontFamily, y, 16);

  setPdfFont(doc, fontFamily, 'bold');
  doc.setFontSize(TYPOGRAPHY.sectionHeadingSize);
  doc.setTextColor(...COLORS.brand);
  doc.text(clean(heading), layout.marginX, y);

  return y + 6;
}

function addProblemDefinition(
  doc: jsPDF,
  layout: Layout,
  fontFamily: FontFamily,
  text: string,
  y: number,
): number {
  const padding = 4;
  const fontSize = TYPOGRAPHY.problemBodySize;
  const width = layout.contentWidth - padding * 2;

  setPdfFont(doc, fontFamily, 'italic');
  doc.setFontSize(fontSize);
  doc.setTextColor(...COLORS.ink);
  const lines = split(doc, text, width);
  const height = padding * 2 + blockHeight(fontSize, lines.length, 1.30);

  y = ensureSpace(doc, layout, fontFamily, y, height + 2);

  drawSquareBox(doc, layout.marginX, y - 4, layout.contentWidth, height, COLORS.paleGreen2, COLORS.divider, 0.25);

  doc.text(lines, layout.marginX + padding, y + padding, { lineHeightFactor: 1.30 });

  return y + height;
}

function addPathwayCard(
  doc: jsPDF,
  layout: Layout,
  fontFamily: FontFamily,
  pathway: AetherGlimpsePathway,
  y: number,
): number {
  const x = layout.marginX;
  const width = layout.contentWidth;
  const paddingX = 5;
  const headerHeight = 10;
  const titleSize = TYPOGRAPHY.cardTitleSize;
  const labelSize = TYPOGRAPHY.cardLabelSize;
  const bodySize = TYPOGRAPHY.cardBodySize;
  const bodyWidth = width - paddingX * 2;

  setPdfFont(doc, fontFamily, 'normal');
  doc.setFontSize(bodySize);
  const orientationLines = split(doc, pathway.orientation, bodyWidth);
  const conditionLines = split(doc, pathway.conditions, bodyWidth);

  const bodyTopPadding = 6;
  const bodyBottomPadding = 2;
  const labelHeight = blockHeight(labelSize, 1, 1.1);
  const orientationHeight = blockHeight(bodySize, orientationLines.length, 1.28);
  const conditionHeight = blockHeight(bodySize, conditionLines.length, 1.28);
  const gapBetweenSections = 3;

  const bodyHeight =
    bodyTopPadding +
    labelHeight +
    1.5 +
    orientationHeight +
    gapBetweenSections +
    labelHeight +
    1.5 +
    conditionHeight +
    bodyBottomPadding;

  const cardHeight = headerHeight + bodyHeight;
  y = ensureSpace(doc, layout, fontFamily, y, cardHeight + 4);

  // Outer card.
  drawSquareBox(doc, x, y, width, cardHeight, COLORS.white, COLORS.border, 0.35);

  // Header band.
  doc.setFillColor(...COLORS.paleGreen);
  doc.rect(x, y, width, headerHeight, 'F');
  setPdfFont(doc, fontFamily, 'bold');
  doc.setFontSize(titleSize);
  doc.setTextColor(...COLORS.brandDark);
  doc.text(clean(pathway.title.toUpperCase()), x + paddingX, y + 6.8);

  let textY = y + headerHeight + bodyTopPadding;

  setPdfFont(doc, fontFamily, 'bold');
  doc.setFontSize(labelSize);
  doc.setTextColor(...COLORS.brand);
  doc.text('Orientation:', x + paddingX, textY);
  textY += labelHeight + 1.1;

  setPdfFont(doc, fontFamily, 'normal');
  doc.setFontSize(bodySize);
  doc.setTextColor(...COLORS.ink);
  doc.text(orientationLines, x + paddingX, textY, { lineHeightFactor: 1.28 });
  textY += orientationHeight + gapBetweenSections;

  setPdfFont(doc, fontFamily, 'bold');
  doc.setFontSize(labelSize);
  doc.setTextColor(...COLORS.brand);
  doc.text('Conditions:', x + paddingX, textY);
  textY += labelHeight + 1.1;

  setPdfFont(doc, fontFamily, 'normal');
  doc.setFontSize(bodySize);
  doc.setTextColor(...COLORS.ink);
  doc.text(conditionLines, x + paddingX, textY, { lineHeightFactor: 1.28 });

  return y + cardHeight;
}

function addFooters(doc: jsPDF, layout: Layout, fontFamily: FontFamily, generatedAt: Date): void {
  const pageCount = doc.getNumberOfPages();
  const dateText = generatedAt.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });

  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    const y = layout.pageHeight - 10;

    setPdfFont(doc, fontFamily, 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.muted);
    doc.text(`Generated ${dateText}`, layout.marginX, y);
    doc.text(`Page ${page} of ${pageCount}`, layout.pageWidth / 2, y, { align: 'center' });
    doc.text('Aether Glimpse', layout.pageWidth - layout.marginX, y, { align: 'right' });
  }
}

function ensureSpace(
  doc: jsPDF,
  layout: Layout,
  fontFamily: FontFamily,
  y: number,
  neededHeight: number,
): number {
  const bottomLimit = layout.pageHeight - layout.marginBottom - 10;
  if (y + neededHeight <= bottomLimit) return y;

  doc.addPage();
  return addContinuationHeader(doc, layout, fontFamily);
}

function split(doc: jsPDF, text: string, maxWidth: number): string[] {
  return doc.splitTextToSize(clean(text), maxWidth) as string[];
}

function blockHeight(fontSizePt: number, lineCount: number, lineHeightFactor: number): number {
  return fontSizePt * 0.352778 * lineHeightFactor * Math.max(lineCount, 1);
}

function clean(value: string): string {
  // Keeps normal punctuation, including curly quotes and dashes, but removes control characters
  // that can create odd PDF output when data comes from user input.
  return Array.from(value)
    .filter((character) => {
      const code = character.charCodeAt(0);
      return code === 9 || code === 10 || code === 13 || (code >= 32 && code !== 127);
    })
    .join('')
    .trim();
}
