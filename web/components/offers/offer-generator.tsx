"use client";

import type { PDFDocument, PDFFont, PDFImage, RGB } from "pdf-lib";
import { useEffect, useMemo, useRef, useState, type RefObject } from "react";

type ProductType = "PV" | "Magazyn energii" | "PV + Magazyn energii";
type OfferStatus = "draft" | "ready";
type VatRate = 8 | 23;

type OfferTemplate = {
  id: string;
  status: OfferStatus;
  sortOrder: number | null;
  createdAt: string;
  updatedAt: string;
  name: string;
  productType: ProductType;
  priceNetPln: number;
  vatRate: VatRate;
  subsidyAmountPln: number | null;
  pvPowerKwp: string;
  storageCapacityKwh: string;
  panelBrand: string;
  panelModel: string;
  inverterBrand: string;
  inverterModel: string;
  storageBrand: string;
  storageModel: string;
  construction: string;
  protectionsAcDc: string;
  installation: string;
  monitoringEms: string;
  warranty: string;
  paymentTerms: string;
  implementationTime: string;
  validity: string;
};

type SellerProfile = {
  companyName: string;
  emailBodyTemplate: string;
  logoUrl: string | null;
};

type EmailVariable = {
  token: string;
  label: string;
  source: string;
};

type StepKey = "podstawy" | "komponenty" | "cena" | "warunki" | "tresc" | "preview";

const steps: { key: StepKey; label: string }[] = [
  { key: "podstawy", label: "Podstawy" },
  { key: "komponenty", label: "Komponenty" },
  { key: "cena", label: "Cena" },
  { key: "warunki", label: "Warunki" },
  { key: "tresc", label: "Treść" },
  { key: "preview", label: "Preview" },
];

const productTypes: ProductType[] = ["PV", "Magazyn energii", "PV + Magazyn energii"];

const defaultEmailBodyTemplate = `Dzień dobry,

przesyłam ofertę: {{Nazwa oferty}}.
Cena: {{Cena}}.

W razie pytań jestem do dyspozycji.

{{Firma}}`;

const defaultEmailVariables: EmailVariable[] = [
  { token: "{{Imię i nazwisko}}", label: "Imię i nazwisko", source: "Sheets" },
  { token: "{{Miasto}}", label: "Miasto", source: "Sheets" },
  { token: "{{Email}}", label: "Email", source: "Sheets" },
  { token: "{{Telefon}}", label: "Telefon", source: "Sheets" },
  { token: "{{Produkt}}", label: "Produkt", source: "Sheets" },
  { token: "{{Status}}", label: "Status", source: "Sheets" },
  { token: "{{Następny krok}}", label: "Następny krok", source: "Sheets" },
  { token: "{{Data następnego kroku}}", label: "Data następnego kroku", source: "Sheets" },
  { token: "{{Firma}}", label: "Firma", source: "Profil" },
  { token: "{{Nazwa oferty}}", label: "Nazwa oferty", source: "Oferta" },
  { token: "{{Cena}}", label: "Cena", source: "Oferta" },
];

const initialOffers: OfferTemplate[] = [
  {
    id: "demo-ready-pv",
    status: "ready",
    sortOrder: 10,
    createdAt: new Date("2026-05-01T09:00:00").toISOString(),
    updatedAt: new Date("2026-05-01T09:00:00").toISOString(),
    name: "PV 6,2 kWp — dom jednorodzinny",
    productType: "PV",
    priceNetPln: 31500,
    vatRate: 8,
    subsidyAmountPln: 7000,
    pvPowerKwp: "6.2",
    storageCapacityKwh: "",
    panelBrand: "Jinko",
    panelModel: "Tiger Neo",
    inverterBrand: "Huawei",
    inverterModel: "SUN2000",
    storageBrand: "",
    storageModel: "",
    construction: "Konstrukcja dachowa pod blachodachówkę",
    protectionsAcDc: "Zabezpieczenia AC/DC w komplecie",
    installation: "Montaż i uruchomienie",
    monitoringEms: "Aplikacja producenta",
    warranty: "Gwarancje zgodnie z kartami producentów.",
    paymentTerms: "40% zaliczki, 60% po montażu.",
    implementationTime: "Do 45 dni od podpisania umowy.",
    validity: "14 dni",
  },
];

const emptyDraft = (): OfferTemplate => {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    status: "draft",
    sortOrder: null,
    createdAt: now,
    updatedAt: now,
    name: "",
    productType: "PV",
    priceNetPln: 0,
    vatRate: 8,
    subsidyAmountPln: null,
    pvPowerKwp: "",
    storageCapacityKwh: "",
    panelBrand: "",
    panelModel: "",
    inverterBrand: "",
    inverterModel: "",
    storageBrand: "",
    storageModel: "",
    construction: "",
    protectionsAcDc: "",
    installation: "",
    monitoringEms: "",
    warranty: "",
    paymentTerms: "",
    implementationTime: "",
    validity: "",
  };
};

const defaultProfile: SellerProfile = {
  companyName: "Twoja firma OZE",
  emailBodyTemplate: defaultEmailBodyTemplate,
  logoUrl: null,
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";
const envUserId = process.env.NEXT_PUBLIC_OFFER_USER_ID ?? "";
const pdfFontPaths = {
  regular: "/fonts/NotoSans-Regular.ttf",
  bold: "/fonts/NotoSans-Bold.ttf",
};
const pdfAssetPaths = {
  watermark: "/offers/pv-storage-watermark.png",
};
const watermarkOpacity = 0.42;

function fromApi(row: Record<string, unknown>): OfferTemplate {
  return {
    id: String(row.id ?? crypto.randomUUID()),
    status: row.status === "ready" ? "ready" : "draft",
    sortOrder: row.sort_order === null || row.sort_order === undefined ? null : Number(row.sort_order),
    createdAt: String(row.created_at ?? new Date().toISOString()),
    updatedAt: String(row.updated_at ?? new Date().toISOString()),
    name: String(row.name ?? ""),
    productType: productTypes.includes(row.product_type as ProductType) ? row.product_type as ProductType : "PV",
    priceNetPln: Number(row.price_net_pln ?? 0),
    vatRate: Number(row.vat_rate ?? 8) === 23 ? 23 : 8,
    subsidyAmountPln: row.subsidy_amount_pln === null || row.subsidy_amount_pln === undefined ? null : Number(row.subsidy_amount_pln),
    pvPowerKwp: String(row.pv_power_kwp ?? ""),
    storageCapacityKwh: String(row.storage_capacity_kwh ?? ""),
    panelBrand: String(row.panel_brand ?? ""),
    panelModel: String(row.panel_model ?? ""),
    inverterBrand: String(row.inverter_brand ?? ""),
    inverterModel: String(row.inverter_model ?? ""),
    storageBrand: String(row.storage_brand ?? ""),
    storageModel: String(row.storage_model ?? ""),
    construction: String(row.construction ?? ""),
    protectionsAcDc: String(row.protections_ac_dc ?? ""),
    installation: String(row.installation ?? ""),
    monitoringEms: String(row.monitoring_ems ?? ""),
    warranty: String(row.warranty ?? ""),
    paymentTerms: String(row.payment_terms ?? ""),
    implementationTime: String(row.implementation_time ?? ""),
    validity: String(row.validity ?? ""),
  };
}

function toApi(offer: OfferTemplate) {
  return {
    name: offer.name,
    status: offer.status,
    product_type: offer.productType,
    price_net_pln: offer.priceNetPln || null,
    vat_rate: offer.vatRate,
    subsidy_amount_pln: offer.subsidyAmountPln,
    pv_power_kwp: offer.pvPowerKwp || null,
    storage_capacity_kwh: offer.storageCapacityKwh || null,
    panel_brand: offer.panelBrand,
    panel_model: offer.panelModel,
    inverter_brand: offer.inverterBrand,
    inverter_model: offer.inverterModel,
    storage_brand: offer.storageBrand,
    storage_model: offer.storageModel,
    construction: offer.construction,
    protections_ac_dc: offer.protectionsAcDc,
    installation: offer.installation,
    monitoring_ems: offer.monitoringEms,
    warranty: offer.warranty,
    payment_terms: offer.paymentTerms,
    implementation_time: offer.implementationTime,
    validity: offer.validity,
    sort_order: offer.sortOrder,
  };
}

function profileFromApi(row: Record<string, unknown>): SellerProfile {
  return {
    companyName: String(row.company_name ?? defaultProfile.companyName),
    emailBodyTemplate: String(row.email_body_template ?? defaultProfile.emailBodyTemplate),
    logoUrl: row.logo_data_url ? String(row.logo_data_url) : null,
  };
}

function profileToApi(profile: SellerProfile) {
  return {
    company_name: profile.companyName,
    email_body_template: profile.emailBodyTemplate,
  };
}

async function apiRequest(path: string, userId: string, init: RequestInit = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "content-type": "application/json" }),
      "x-user-id": userId,
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = "Błąd API.";
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      message = response.statusText;
    }
    throw new Error(message);
  }
  return response;
}

function formatPln(value: number) {
  return `${Math.max(0, Math.round(value)).toLocaleString("pl-PL")} PLN`;
}

function priceBreakdown(offer: OfferTemplate) {
  const net = Math.max(0, Math.round(offer.priceNetPln || 0));
  const gross = Math.round(net * (1 + offer.vatRate / 100));
  const subsidy = offer.subsidyAmountPln && offer.subsidyAmountPln > 0 ? Math.round(offer.subsidyAmountPln) : null;
  const client = subsidy === null ? gross : Math.max(0, gross - subsidy);
  return { net, gross, subsidy, client };
}

function extractEmailTokens(template: string) {
  return [...template.matchAll(/{{\s*([^{}]+?)\s*}}/g)].map((match) => match[1].trim());
}

function unknownEmailTokens(template: string, variables: EmailVariable[]) {
  const allowed = new Set(variables.map((variable) => variable.label));
  const seen = new Set<string>();
  return extractEmailTokens(template).filter((token) => {
    if (allowed.has(token) || seen.has(token)) return false;
    seen.add(token);
    return true;
  });
}

const emailTokenChipClass = [
  "mx-1 inline-flex select-none items-center gap-1 rounded-[8px] border border-[#3DFF7A]/40 bg-[#3DFF7A]/15 px-2 py-0.5",
  "align-baseline text-xs font-semibold text-[#A7FFBF] shadow-[0_0_18px_rgba(61,255,122,0.08)]",
].join(" ");

const emailTokenRemoveClass = [
  "ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-[#3DFF7A]/25",
  "bg-black/25 text-[10px] font-bold leading-none text-[#A7FFBF] hover:bg-[#3DFF7A] hover:text-black",
].join(" ");

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function emailVariableLabel(token: string, variables: EmailVariable[]) {
  return variables.find((variable) => variable.token === token)?.label ?? token.replace(/^{{\s*|\s*}}$/g, "");
}

function emailTemplateToEditorHtml(template: string, variables: EmailVariable[]) {
  return (template || "")
    .replace(/{{\s*([^{}]+?)\s*}}/g, (match) => {
      const token = match.replace(/{{\s*/, "{{").replace(/\s*}}/, "}}");
      const label = emailVariableLabel(token, variables);
      return `<span class="${emailTokenChipClass}" data-email-token="${escapeHtml(token)}" contenteditable="false" draggable="true"><span>${escapeHtml(label)}</span><button type="button" tabindex="-1" class="${emailTokenRemoveClass}" data-email-token-remove="true" aria-label="Usuń zmienną ${escapeHtml(label)}">x</button></span>`;
    })
    .replace(/\n/g, "<br>");
}

function serializeEmailEditor(root: HTMLElement) {
  const serialize = (node: Node): string => {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent ?? "";
    if (!(node instanceof HTMLElement)) return "";
    const token = node.dataset.emailToken;
    if (token) return token;
    if (node.tagName === "BR") return "\n";
    const childText = Array.from(node.childNodes).map(serialize).join("");
    return ["DIV", "P"].includes(node.tagName) ? `${childText}\n` : childText;
  };
  return Array.from(root.childNodes).map(serialize).join("").replace(/\u00a0/g, " ").replace(/\n{3,}/g, "\n\n");
}

function createEmailTokenChip(variable: EmailVariable) {
  const chip = document.createElement("span");
  chip.className = emailTokenChipClass;
  chip.dataset.emailToken = variable.token;
  chip.contentEditable = "false";
  chip.draggable = true;
  const label = document.createElement("span");
  label.textContent = variable.label;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.tabIndex = -1;
  remove.className = emailTokenRemoveClass;
  remove.dataset.emailTokenRemove = "true";
  remove.setAttribute("aria-label", `Usuń zmienną ${variable.label}`);
  remove.textContent = "x";
  chip.append(label, remove);
  return chip;
}

function removeEmailTokenChip(chip: HTMLElement, root: HTMLElement) {
  const next = chip.nextSibling;
  const previous = chip.previousSibling;
  chip.remove();
  if (next?.nodeType === Node.TEXT_NODE) {
    next.textContent = (next.textContent ?? "").replace(/^ /, "");
    if (!next.textContent) next.remove();
  } else if (previous?.nodeType === Node.TEXT_NODE) {
    previous.textContent = (previous.textContent ?? "").replace(/ $/, "");
    if (!previous.textContent) previous.remove();
  }
  root.focus();
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(root);
  range.collapse(false);
  selection?.removeAllRanges();
  selection?.addRange(range);
}

function setCaretFromDropPoint(root: HTMLElement, event: React.DragEvent<HTMLElement>) {
  const selection = window.getSelection();
  if (!selection) return;
  let range: Range | null = null;
  const doc = document as Document & {
    caretRangeFromPoint?: (x: number, y: number) => Range | null;
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
  };
  if (doc.caretRangeFromPoint) {
    range = doc.caretRangeFromPoint(event.clientX, event.clientY);
  } else if (doc.caretPositionFromPoint) {
    const position = doc.caretPositionFromPoint(event.clientX, event.clientY);
    if (position) {
      range = document.createRange();
      range.setStart(position.offsetNode, position.offset);
      range.collapse(true);
    }
  }
  if (!range || !root.contains(range.startContainer)) return;
  selection.removeAllRanges();
  selection.addRange(range);
}

function requiresPv(type: ProductType) {
  return type === "PV" || type === "PV + Magazyn energii";
}

function requiresStorage(type: ProductType) {
  return type === "Magazyn energii" || type === "PV + Magazyn energii";
}

function validateReady(offer: OfferTemplate) {
  const errors: string[] = [];
  if (!offer.name.trim()) errors.push("Brakuje nazwy oferty.");
  if (!offer.priceNetPln || offer.priceNetPln <= 0) errors.push("Brakuje ceny netto zestawu.");
  if (offer.vatRate !== 8 && offer.vatRate !== 23) errors.push("VAT musi wynosić 8% albo 23%.");
  if (requiresPv(offer.productType)) {
    if (!offer.pvPowerKwp.trim()) errors.push("Brakuje mocy PV kWp.");
    if (!offer.panelBrand.trim()) errors.push("Brakuje marki paneli.");
    if (!offer.panelModel.trim()) errors.push("Brakuje modelu paneli.");
    if (!offer.inverterBrand.trim()) errors.push("Brakuje marki falownika.");
    if (!offer.inverterModel.trim()) errors.push("Brakuje modelu falownika.");
  }
  if (requiresStorage(offer.productType)) {
    if (!offer.storageCapacityKwh.trim()) errors.push("Brakuje pojemności magazynu kWh.");
    if (!offer.storageBrand.trim()) errors.push("Brakuje marki magazynu.");
    if (!offer.storageModel.trim()) errors.push("Brakuje modelu magazynu.");
  }
  return errors;
}

function hasPdfMinimum(offer: OfferTemplate) {
  return Boolean(offer.name.trim() && offer.priceNetPln > 0 && (offer.vatRate === 8 || offer.vatRate === 23));
}

function readyWithNumbers(offers: OfferTemplate[]) {
  return offers
    .filter((offer) => offer.status === "ready")
    .sort((a, b) => (a.sortOrder ?? 999999) - (b.sortOrder ?? 999999))
    .map((offer, index) => ({ ...offer, number: index + 1 }));
}

function draftsNewest(offers: OfferTemplate[]) {
  return offers
    .filter((offer) => offer.status === "draft")
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

function componentLines(offer: OfferTemplate) {
  return [
    offer.pvPowerKwp ? `Moc PV: ${offer.pvPowerKwp} kWp` : "",
    offer.panelBrand || offer.panelModel ? `Panele: ${offer.panelBrand} ${offer.panelModel}`.trim() : "",
    offer.inverterBrand || offer.inverterModel ? `Falownik: ${offer.inverterBrand} ${offer.inverterModel}`.trim() : "",
    offer.storageCapacityKwh ? `Magazyn: ${offer.storageCapacityKwh} kWh` : "",
    offer.storageBrand || offer.storageModel ? `Model magazynu: ${offer.storageBrand} ${offer.storageModel}`.trim() : "",
    offer.construction ? `Konstrukcja: ${offer.construction}` : "",
    offer.protectionsAcDc ? `Zabezpieczenia AC/DC: ${offer.protectionsAcDc}` : "",
    offer.installation ? `Montaż: ${offer.installation}` : "",
    offer.monitoringEms ? `Monitoring/EMS: ${offer.monitoringEms}` : "",
    offer.warranty ? `Gwarancja: ${offer.warranty}` : "",
  ].filter(Boolean);
}

function updateOfferField<K extends keyof OfferTemplate>(
  offer: OfferTemplate,
  key: K,
  value: OfferTemplate[K],
): OfferTemplate {
  return { ...offer, [key]: value, updatedAt: new Date().toISOString() };
}

function wrapPdfText(value: string, maxChars: number) {
  const words = value.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });
  if (current) lines.push(current);
  return lines;
}

function wrapPdfTextByWidth(value: string, font: PDFFont, size: number, maxWidth: number) {
  const words = value.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (current && font.widthOfTextAtSize(next, size) > maxWidth) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });
  if (current) lines.push(current);
  return lines;
}

async function fetchFont(path: string) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Nie udało się pobrać fontu PDF: ${path}`);
  }
  return response.arrayBuffer();
}

async function imageBlobToPngBytes(blob: Blob) {
  const bitmap = await createImageBitmap(blob);
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const context = canvas.getContext("2d");
  if (!context) {
    bitmap.close();
    throw new Error("Nie udało się przygotować logo do PDF.");
  }
  context.drawImage(bitmap, 0, 0);
  bitmap.close();
  const dataUrl = canvas.toDataURL("image/png");
  const response = await fetch(dataUrl);
  return response.arrayBuffer();
}

async function embedPdfImage(pdfDoc: PDFDocument, imageUrl: string | null): Promise<PDFImage | null> {
  if (!imageUrl) return null;
  try {
    const response = await fetch(imageUrl);
    if (!response.ok) return null;
    const blob = await response.blob();
    const bytes = await blob.arrayBuffer();
    const type = blob.type.toLowerCase();
    if (type.includes("png")) {
      return pdfDoc.embedPng(bytes);
    }
    if (type.includes("jpeg") || type.includes("jpg")) {
      return pdfDoc.embedJpg(bytes);
    }
    const pngBytes = await imageBlobToPngBytes(blob);
    return pdfDoc.embedPng(pngBytes);
  } catch {
    return null;
  }
}

async function buildPdfBlob(offer: OfferTemplate, profile: SellerProfile) {
  const [{ PDFDocument, rgb }, fontkitModule] = await Promise.all([
    import("pdf-lib"),
    import("@pdf-lib/fontkit"),
  ]);
  const pdfDoc = await PDFDocument.create();
  pdfDoc.registerFontkit(fontkitModule.default);
  const [regularBytes, boldBytes] = await Promise.all([
    fetchFont(pdfFontPaths.regular),
    fetchFont(pdfFontPaths.bold),
  ]);
  const regularFont = await pdfDoc.embedFont(regularBytes);
  const boldFont = await pdfDoc.embedFont(boldBytes);
  const [logoImage, watermarkImage] = await Promise.all([
    embedPdfImage(pdfDoc, profile.logoUrl),
    embedPdfImage(pdfDoc, pdfAssetPaths.watermark),
  ]);
  const page = pdfDoc.addPage([595, 842]);
  const price = priceBreakdown(offer);
  const components = componentLines(offer);
  const terms = [
    offer.paymentTerms ? `Warunki płatności: ${offer.paymentTerms}` : "",
    offer.implementationTime ? `Termin realizacji: ${offer.implementationTime}` : "",
    offer.validity ? `Ważność oferty: ${offer.validity}` : "",
  ].filter(Boolean);
  const pdfDarkBackground = rgb(0.08, 0.1, 0.09);
  const pdfDarkOverlay = rgb(0.06, 0.07, 0.07);
  const pdfTextWhite = rgb(0.96, 0.98, 0.96);
  const muted = rgb(0.68, 0.71, 0.69);
  const quiet = rgb(0.46, 0.49, 0.47);
  const rule = rgb(0.25, 0.28, 0.26);
  const text = (
    value: string,
    x: number,
    y: number,
    size = 10,
    font = regularFont,
    color = pdfTextWhite,
  ) => {
    page.drawText(value, { x, y, size, font, color });
  };
  const line = (x1: number, y1: number, x2: number, y2: number, color = rule) => {
    page.drawLine({ start: { x: x1, y: y1 }, end: { x: x2, y: y2 }, thickness: 0.8, color });
  };
  const fill = (x: number, y: number, width: number, height: number, color: RGB, opacity = 1) => {
    page.drawRectangle({ x, y, width, height, color, opacity });
  };

  fill(0, 0, 595, 842, pdfDarkBackground);
  if (watermarkImage) {
    page.drawImage(watermarkImage, {
      x: 0,
      y: 0,
      width: 595,
      height: 842,
      opacity: watermarkOpacity,
    });
    fill(0, 0, 595, 842, pdfDarkOverlay, 0.58);
  }
  text(profile.companyName || "OZE Agent", 48, 760, 11, boldFont);
  if (logoImage) {
    const logoSize = logoImage.scaleToFit(72, 42);
    const logoX = 547 - logoSize.width;
    const logoY = 742;
    const logoClearArea = {
      x: logoX - 8,
      y: logoY - 8,
      width: logoSize.width + 16,
      height: logoSize.height + 16,
    };
    fill(logoClearArea.x, logoClearArea.y, logoClearArea.width, logoClearArea.height, pdfDarkBackground, 0.78);
    page.drawImage(logoImage, {
      x: logoX,
      y: logoY,
      width: logoSize.width,
      height: logoSize.height,
    });
  }
  const titleLines = wrapPdfTextByWidth(offer.name || "Oferta", boldFont, 22, 310);
  titleLines.forEach((lineText, index) => {
    text(lineText, 48, 716 - index * 27, 22, boldFont);
  });

  text("Cena", 48, 666, 9, boldFont, muted);
  text(formatPln(price.client), 48, 638, 24, boldFont);

  const priceRows = [
    ["Cena netto", formatPln(price.net)],
    ["VAT", `${offer.vatRate}%`],
    ["Cena brutto", formatPln(price.gross)],
    ...(price.subsidy !== null
      ? [["Szacowane dofinansowanie", formatPln(price.subsidy)], ["Cena po dopłacie", formatPln(price.client)]]
      : []),
  ];
  let y = 604;
  priceRows.forEach(([label, value]) => {
    text(label, 48, y, 10, regularFont, muted);
    text(value, 430, y, 10, regularFont, pdfTextWhite);
    y -= 18;
  });

  y -= 14;
  text("Dane klienta", 48, y, 12, boldFont);
  y -= 14;
  line(48, y, 547, y);
  y -= 20;
  text("Klient", 48, y, 9, boldFont, muted);
  text("Jan Testowy", 165, y, 10);
  y -= 19;
  text("Miasto", 48, y, 9, boldFont, muted);
  text("Warszawa", 165, y, 10);
  y -= 19;
  text("Data", 48, y, 9, boldFont, muted);
  text(new Date().toLocaleDateString("pl-PL"), 165, y, 10);

  if (components.length) {
    y -= 34;
    text("Zakres zestawu", 48, y, 12, boldFont);
    y -= 14;
    line(48, y, 547, y);
    y -= 20;
    components.slice(0, 10).forEach((item) => {
      const lines = wrapPdfTextByWidth(`• ${item}`, regularFont, 9.5, 475);
      lines.forEach((wrapped) => {
        text(wrapped, 58, y, 9.5);
        y -= 15;
      });
    });
  }

  if (terms.length && y > 130) {
    y -= 8;
    text("Warunki", 48, y, 12, boldFont);
    y -= 14;
    line(48, y, 547, y);
    y -= 20;
    terms.forEach((item) => {
      wrapPdfTextByWidth(`• ${item}`, regularFont, 9.5, 475).forEach((wrapped) => {
        text(wrapped, 58, y, 9.5);
        y -= 15;
      });
    });
  }

  line(48, 82, 547, 82);
  wrapPdfText(
    "Oferta ma charakter informacyjny. Szczegóły techniczne, dostępność komponentów i warunki realizacji wymagają potwierdzenia z handlowcem.",
    100,
  ).forEach((wrapped, index) => text(wrapped, 48, 62 - index * 13, 8.5, regularFont, quiet));

  const bytes = await pdfDoc.save();
  const pdfBytes = bytes.slice().buffer as ArrayBuffer;
  return new Blob([pdfBytes], { type: "application/pdf" });
}

async function downloadTestPdf(offer: OfferTemplate, profile: SellerProfile) {
  const blob = await buildPdfBlob(offer, profile);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `Oferta-test-${offer.name.trim() || "szkic"}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}

export function OfferGenerator() {
  const [offers, setOffers] = useState<OfferTemplate[]>(initialOffers);
  const [profile, setProfile] = useState<SellerProfile>(defaultProfile);
  const [emailVariables, setEmailVariables] = useState<EmailVariable[]>(defaultEmailVariables);
  const [apiUserId] = useState(envUserId);
  const [apiError, setApiError] = useState("");
  const [selectedId, setSelectedId] = useState(initialOffers[0]?.id ?? "");
  const [editor, setEditor] = useState<OfferTemplate>(initialOffers[0] ?? emptyDraft());
  const [activeStep, setActiveStep] = useState<StepKey>("podstawy");
  const [errors, setErrors] = useState<string[]>([]);
  const [profileErrors, setProfileErrors] = useState<string[]>([]);
  const [logoError, setLogoError] = useState("");
  const emailEditorRef = useRef<HTMLDivElement | null>(null);

  const ready = useMemo(() => readyWithNumbers(offers), [offers]);
  const drafts = useMemo(() => draftsNewest(offers), [offers]);
  const selected = offers.find((offer) => offer.id === selectedId) ?? null;
  const price = priceBreakdown(editor);
  const pdfAllowed = hasPdfMinimum(editor);
  const apiReady = Boolean(apiBase && apiUserId);
  const emailUnknownTokens = unknownEmailTokens(profile.emailBodyTemplate, emailVariables);

  useEffect(() => {
    if (!apiBase || !apiUserId) return;
    let cancelled = false;
    async function load() {
      try {
        setApiError("");
        const [templatesResponse, profileResponse, variablesResponse] = await Promise.all([
          apiRequest("/offers/templates", apiUserId),
          apiRequest("/offers/profile", apiUserId),
          apiRequest("/offers/email-variables", apiUserId),
        ]);
        const templatesBody = await templatesResponse.json();
        const profileBody = await profileResponse.json();
        const variablesBody = await variablesResponse.json();
        if (cancelled) return;
        const loadedOffers = (templatesBody.templates ?? []).map((row: Record<string, unknown>) => fromApi(row));
        if (loadedOffers.length) {
          setOffers(loadedOffers);
          setSelectedId(loadedOffers[0].id);
          setEditor(loadedOffers[0]);
        }
        if (profileBody.profile) {
          setProfile((current) => ({ ...current, ...profileFromApi(profileBody.profile) }));
        }
        if (Array.isArray(variablesBody.variables) && variablesBody.variables.length) {
          setEmailVariables(variablesBody.variables);
        }
      } catch (error) {
        if (!cancelled) setApiError(error instanceof Error ? error.message : "Nie udało się pobrać ofert.");
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [apiUserId]);

  function selectOffer(offer: OfferTemplate) {
    setSelectedId(offer.id);
    setEditor(offer);
    setErrors([]);
  }

  async function createDraft() {
    const draft = emptyDraft();
    if (apiReady) {
      try {
        setApiError("");
        const response = await apiRequest("/offers/templates", apiUserId, {
          method: "POST",
          body: JSON.stringify({ data: toApi(draft) }),
        });
        const body = await response.json();
        const created = fromApi(body.template);
        setOffers((current) => [created, ...current]);
        selectOffer(created);
        return;
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Nie udało się utworzyć szkicu.");
      }
    }
    setOffers((current) => [draft, ...current]);
    selectOffer(draft);
  }

  async function saveEditor() {
    const blocking = editor.status === "ready" ? validateReady(editor) : [];
    if (blocking.length) {
      setErrors(blocking);
      return;
    }
    if (apiReady) {
      try {
        setApiError("");
        const response = await apiRequest(`/offers/templates/${editor.id}`, apiUserId, {
          method: "PATCH",
          body: JSON.stringify({ data: toApi(editor) }),
        });
        const body = await response.json();
        const saved = fromApi(body.template);
        setEditor(saved);
        setOffers((current) => current.map((offer) => (offer.id === saved.id ? saved : offer)));
        setErrors([]);
        return;
      } catch (error) {
        setErrors([error instanceof Error ? error.message : "Nie udało się zapisać oferty."]);
        return;
      }
    }
    setOffers((current) => current.map((offer) => (offer.id === editor.id ? editor : offer)));
    setErrors([]);
  }

  async function publishEditor() {
    const blocking = validateReady(editor);
    if (blocking.length) {
      setErrors(blocking);
      return;
    }
    if (apiReady) {
      try {
        setApiError("");
        await apiRequest(`/offers/templates/${editor.id}`, apiUserId, {
          method: "PATCH",
          body: JSON.stringify({ data: toApi(editor) }),
        });
        const response = await apiRequest(`/offers/templates/${editor.id}/publish`, apiUserId, { method: "POST" });
        const body = await response.json();
        const published = fromApi(body.template);
        setEditor(published);
        setSelectedId(published.id);
        setOffers((current) => current.map((offer) => (offer.id === published.id ? published : offer)));
        setErrors([]);
        return;
      } catch (error) {
        setErrors([error instanceof Error ? error.message : "Nie udało się opublikować oferty."]);
        return;
      }
    }
    const maxOrder = Math.max(0, ...offers.filter((offer) => offer.status === "ready").map((offer) => offer.sortOrder ?? 0));
    const next = { ...editor, status: "ready" as const, sortOrder: maxOrder + 10, updatedAt: new Date().toISOString() };
    setEditor(next);
    setSelectedId(next.id);
    setOffers((current) => current.map((offer) => (offer.id === next.id ? next : offer)));
    setErrors([]);
  }

  async function deleteOffer(id: string) {
    if (apiReady) {
      try {
        setApiError("");
        await apiRequest(`/offers/templates/${id}`, apiUserId, { method: "DELETE" });
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Nie udało się usunąć oferty.");
        return;
      }
    }
    setOffers((current) => {
      const remaining = current.filter((offer) => offer.id !== id);
      const reindexedReady = readyWithNumbers(remaining).map((offer) => ({
        ...offer,
        sortOrder: offer.number * 10,
      }));
      const reindexedIds = new Set(reindexedReady.map((offer) => offer.id));
      return remaining.map((offer) => reindexedReady.find((item) => item.id === offer.id) ?? (reindexedIds.has(offer.id) ? offer : offer));
    });
    if (selectedId === id) {
      const next = offers.find((offer) => offer.id !== id);
      if (next) selectOffer(next);
    }
  }

  async function duplicateOffer(offer: OfferTemplate) {
    if (apiReady) {
      try {
        setApiError("");
        const response = await apiRequest(`/offers/templates/${offer.id}/duplicate`, apiUserId, { method: "POST" });
        const body = await response.json();
        const draft = fromApi(body.template);
        setOffers((current) => [draft, ...current]);
        selectOffer(draft);
        return;
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Nie udało się zduplikować oferty.");
        return;
      }
    }
    const draft = {
      ...offer,
      id: crypto.randomUUID(),
      status: "draft" as const,
      sortOrder: null,
      name: `${offer.name || "Oferta"} — kopia`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setOffers((current) => [draft, ...current]);
    selectOffer(draft);
  }

  async function moveReady(id: string, direction: -1 | 1) {
    const ordered = ready.map((offer) => offer.id);
    const index = ordered.indexOf(id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ordered.length) return;
    [ordered[index], ordered[target]] = [ordered[target], ordered[index]];
    setOffers((current) =>
      current.map((offer) => {
        const nextIndex = ordered.indexOf(offer.id);
        return nextIndex === -1 ? offer : { ...offer, sortOrder: (nextIndex + 1) * 10 };
      }),
    );
    if (apiReady) {
      try {
        setApiError("");
        await apiRequest("/offers/templates/reorder", apiUserId, {
          method: "POST",
          body: JSON.stringify({ ordered_template_ids: ordered }),
        });
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Nie udało się zmienić kolejności.");
      }
    }
  }

  async function handleLogo(file: File | null) {
    setLogoError("");
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
      setLogoError("Logo musi być PNG, JPG albo WebP.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setLogoError("Logo może mieć maksymalnie 2 MB.");
      return;
    }
    if (apiReady) {
      try {
        setApiError("");
        const form = new FormData();
        form.append("file", file);
        const response = await apiRequest("/offers/profile/logo", apiUserId, {
          method: "POST",
          body: form,
        });
        const body = await response.json();
        if (body.profile) {
          setProfile((current) => ({ ...current, ...profileFromApi(body.profile) }));
          return;
        }
      } catch (error) {
        setApiError(error instanceof Error ? error.message : "Nie udało się wysłać logo.");
        return;
      }
    }
    const url = URL.createObjectURL(file);
    setProfile((current) => ({ ...current, logoUrl: url }));
  }

  async function saveProfile() {
    if (!apiReady) return;
    const unknownTokens = unknownEmailTokens(profile.emailBodyTemplate, emailVariables);
    if (unknownTokens.length) {
      setProfileErrors(unknownTokens.map((token) => `Nieznana zmienna emaila: ${token}`));
      return;
    }
    try {
      setApiError("");
      setProfileErrors([]);
      await apiRequest("/offers/profile", apiUserId, {
        method: "PUT",
        body: JSON.stringify({ data: profileToApi(profile) }),
      });
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Nie udało się zapisać profilu.");
    }
  }

  function insertEmailToken(token: string) {
    const editor = emailEditorRef.current;
    const variable = emailVariables.find((item) => item.token === token);
    if (!editor || !variable) {
      setProfile((current) => ({ ...current, emailBodyTemplate: `${current.emailBodyTemplate}${token}` }));
      return;
    }
    editor.focus();
    const selection = window.getSelection();
    const range = selection && selection.rangeCount > 0 && selection.anchorNode && editor.contains(selection.anchorNode)
      ? selection.getRangeAt(0)
      : document.createRange();
    if (!editor.contains(range.startContainer)) {
      range.selectNodeContents(editor);
      range.collapse(false);
    }
    range.deleteContents();
    const chip = createEmailTokenChip(variable);
    const spacer = document.createTextNode(" ");
    const fragment = document.createDocumentFragment();
    fragment.append(chip, spacer);
    range.insertNode(fragment);
    range.setStartAfter(spacer);
    range.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(range);
    setProfile((current) => ({ ...current, emailBodyTemplate: serializeEmailEditor(editor) }));
  }

  async function downloadPdf(offer: OfferTemplate, currentProfile: SellerProfile) {
    try {
      setApiError("");
      await downloadTestPdf(offer, currentProfile);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Nie udało się pobrać PDF.");
    }
  }

  const rows = (items: (OfferTemplate & { number?: number })[], numbered: boolean) =>
    items.map((offer) => (
      <tr key={offer.id} className={selectedId === offer.id ? "bg-[#3DFF7A]/[0.07]" : "bg-white/[0.04]"}>
        <td className="h-12 border-b border-white/10 px-3 text-sm tabular-nums text-zinc-400">
          {numbered ? offer.number : ""}
        </td>
        <td className="border-b border-white/10 px-3">
          <button
            className="text-left text-sm font-medium text-white hover:text-[#3DFF7A]"
            onClick={() => selectOffer(offer)}
          >
            {offer.name || "Bez nazwy"}
          </button>
          <div className="text-xs text-zinc-500">{offer.productType}</div>
        </td>
        <td className="border-b border-white/10 px-3 text-sm text-zinc-300">
          {offer.priceNetPln ? formatPln(priceBreakdown(offer).client) : "Brak ceny"}
        </td>
        <td className="border-b border-white/10 px-3 text-right">
          <div className="flex justify-end gap-1">
            {numbered ? (
              <>
                <button className="h-8 w-8 rounded-[8px] border border-white/10 text-sm" onClick={() => void moveReady(offer.id, -1)} aria-label="Przesuń w górę">
                  ↑
                </button>
                <button className="h-8 w-8 rounded-[8px] border border-white/10 text-sm" onClick={() => void moveReady(offer.id, 1)} aria-label="Przesuń w dół">
                  ↓
                </button>
              </>
            ) : null}
            <button className="rounded-[8px] border border-white/10 px-2 text-xs" onClick={() => void duplicateOffer(offer)}>
              Duplikuj
            </button>
            <button className="rounded-[8px] border border-red-400/30 bg-red-500/10 px-2 text-xs text-red-300" onClick={() => void deleteOffer(offer.id)}>
              Usuń
            </button>
          </div>
        </td>
      </tr>
    ));

  return (
    <div className="oze-offers mx-auto grid w-full max-w-[1500px] gap-5 px-4 py-5 xl:grid-cols-[minmax(560px,1fr)_520px]">
      <section className="min-w-0">
        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-end">
          <div className="sm:col-start-2">
            <h1 className="text-2xl font-semibold tracking-[0] text-white">Generator ofert</h1>
          </div>
          <button
            onClick={() => void createDraft()}
            className="h-10 rounded-[8px] bg-[#3DFF7A] px-4 text-sm font-semibold text-black shadow-[0_0_28px_rgba(61,255,122,0.18)] hover:bg-[#6DFF98] sm:col-start-3 sm:justify-self-end"
          >
            Nowy szkic
          </button>
        </div>
        {apiError ? (
          <div className="mb-4 rounded-[8px] border border-red-400/30 bg-red-950/30 p-3 text-sm text-red-300">
            {apiError}
          </div>
        ) : null}

        <OfferTable title="Gotowe oferty" empty="Brak gotowych ofert." rows={rows(ready, true)} />
        <div className="h-5" />
        <OfferTable title="Szkice" empty="Brak szkiców." rows={rows(drafts, false)} />
      </section>

      <aside className="min-w-0 rounded-[8px] border border-white/10 bg-white/[0.04]">
        <div className="border-b border-white/10 p-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_150px]">
            <label className="text-xs font-medium uppercase text-[#3DFF7A]">
              Firma
              <input
                className="mt-1 h-10 w-full rounded-[8px] border border-white/10 bg-black/30 px-3 text-sm text-white"
                value={profile.companyName}
                onChange={(event) => setProfile((current) => ({ ...current, companyName: event.target.value }))}
              />
            </label>
            <label className="text-xs font-medium uppercase text-[#3DFF7A]">
              Logo
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="mt-1 block h-10 w-full text-xs text-zinc-400 file:mr-2 file:h-9 file:rounded-[8px] file:border-0 file:bg-white/[0.08] file:text-zinc-200 file:px-3 file:text-xs file:font-medium"
                onChange={(event) => void handleLogo(event.target.files?.[0] ?? null)}
              />
            </label>
          </div>
          {logoError ? <p className="mt-2 text-sm text-red-300">{logoError}</p> : null}
        </div>

        {selected ? (
          <div>
            <div className="flex gap-1 overflow-x-auto border-b border-white/10 p-2">
              {steps.map((step) => (
                <button
                  key={step.key}
                  data-active={activeStep === step.key ? "true" : "false"}
                  onClick={() => setActiveStep(step.key)}
                  className={[
                    "h-9 rounded-[8px] px-3 text-sm font-medium",
                    activeStep === step.key ? "bg-[#3DFF7A] text-black" : "text-zinc-400 hover:bg-white/[0.06]",
                  ].join(" ")}
                >
                  {step.label}
                </button>
              ))}
            </div>

            <div className="p-4">
              {activeStep === "podstawy" ? (
                <BasicsStep
                  editor={editor}
                  setEditor={setEditor}
                />
              ) : null}
              {activeStep === "komponenty" ? <ComponentsStep editor={editor} setEditor={setEditor} /> : null}
              {activeStep === "cena" ? <PriceStep editor={editor} setEditor={setEditor} price={price} /> : null}
              {activeStep === "warunki" ? <TermsStep editor={editor} setEditor={setEditor} /> : null}
              {activeStep === "tresc" ? (
                <EmailContentStep
                  profile={profile}
                  setProfile={setProfile}
                  emailVariables={emailVariables}
                  emailEditorRef={emailEditorRef}
                  insertEmailToken={insertEmailToken}
                  emailUnknownTokens={emailUnknownTokens}
                  profileErrors={profileErrors}
                  apiReady={apiReady}
                  saveProfile={saveProfile}
                />
              ) : null}
              {activeStep === "preview" ? <PreviewStep editor={editor} profile={profile} price={price} /> : null}

              {errors.length ? (
                <div className="mt-4 rounded-[8px] border border-red-400/30 bg-red-950/30 p-3 text-sm text-red-300">
                  {errors.map((error) => (
                    <div key={error}>{error}</div>
                  ))}
                </div>
              ) : null}

              <div className="mt-5 flex flex-wrap gap-2">
                <button
                  onClick={() => void saveEditor()}
                  className="h-10 rounded-[8px] border border-white/12 px-4 text-sm font-semibold text-zinc-200 hover:bg-white/[0.06]"
                >
                  Zapisz
                </button>
                {editor.status === "draft" ? (
                  <button
                    onClick={() => void publishEditor()}
                    className="h-10 rounded-[8px] bg-[#3DFF7A] px-4 text-sm font-semibold text-black shadow-[0_0_28px_rgba(61,255,122,0.18)] hover:bg-[#6DFF98]"
                  >
                    Publikuj
                  </button>
                ) : null}
                <button
                  disabled={!pdfAllowed}
                  onClick={() => void downloadPdf(editor, profile)}
                  className="h-10 rounded-[8px] border border-white/12 px-4 text-sm font-semibold text-zinc-200 hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Test PDF
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-5 text-sm text-zinc-400">Wybierz ofertę albo utwórz szkic.</div>
        )}
      </aside>
    </div>
  );
}

function OfferTable({ title, rows, empty }: { title: string; rows: React.ReactNode[]; empty: string }) {
  return (
    <section className="rounded-[8px] border border-white/10 bg-white/[0.04]">
      <div className="flex h-12 items-center border-b border-white/10 px-4">
        <h2 className="text-sm font-semibold text-white">{title}</h2>
      </div>
      {rows.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] table-fixed">
            <thead>
              <tr className="bg-white/[0.06]">
                <th className="w-14 border-b border-white/10 px-3 py-2 text-left text-xs font-semibold uppercase text-[#3DFF7A]">Nr</th>
                <th className="border-b border-white/10 px-3 py-2 text-left text-xs font-semibold uppercase text-[#3DFF7A]">Oferta</th>
                <th className="w-36 border-b border-white/10 px-3 py-2 text-left text-xs font-semibold uppercase text-[#3DFF7A]">Cena</th>
                <th className="w-64 border-b border-white/10 px-3 py-2 text-right text-xs font-semibold uppercase text-[#3DFF7A]">Akcje</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      ) : (
        <div className="p-4 text-sm text-zinc-500">{empty}</div>
      )}
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-xs font-medium uppercase text-[#3DFF7A]">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  );
}

function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className="h-10 w-full rounded-[8px] border border-white/10 bg-black/30 px-3 text-sm text-white" />;
}

function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className="min-h-20 w-full resize-y rounded-[8px] border border-white/10 bg-black/30 px-3 py-2 text-sm text-white" />;
}

function BasicsStep({
  editor,
  setEditor,
}: {
  editor: OfferTemplate;
  setEditor: (offer: OfferTemplate) => void;
}) {
  return (
    <div className="grid gap-3">
      <Field label="Nazwa">
        <TextInput value={editor.name} onChange={(event) => setEditor(updateOfferField(editor, "name", event.target.value))} />
      </Field>
      <Field label="Typ zestawu">
        <select
          className="h-10 w-full rounded-[8px] border border-white/10 bg-black/30 px-3 text-sm text-white"
          value={editor.productType}
          onChange={(event) => setEditor(updateOfferField(editor, "productType", event.target.value as ProductType))}
        >
          {productTypes.map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
      </Field>
    </div>
  );
}

function ComponentsStep({ editor, setEditor }: { editor: OfferTemplate; setEditor: (offer: OfferTemplate) => void }) {
  return (
    <div className="grid gap-4">
      {requiresPv(editor.productType) ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Moc PV kWp">
            <TextInput value={editor.pvPowerKwp} onChange={(event) => setEditor(updateOfferField(editor, "pvPowerKwp", event.target.value))} />
          </Field>
          <Field label="Panele marka">
            <TextInput value={editor.panelBrand} onChange={(event) => setEditor(updateOfferField(editor, "panelBrand", event.target.value))} />
          </Field>
          <Field label="Panele model">
            <TextInput value={editor.panelModel} onChange={(event) => setEditor(updateOfferField(editor, "panelModel", event.target.value))} />
          </Field>
          <Field label="Falownik marka">
            <TextInput value={editor.inverterBrand} onChange={(event) => setEditor(updateOfferField(editor, "inverterBrand", event.target.value))} />
          </Field>
          <Field label="Falownik model">
            <TextInput value={editor.inverterModel} onChange={(event) => setEditor(updateOfferField(editor, "inverterModel", event.target.value))} />
          </Field>
        </div>
      ) : null}
      {requiresStorage(editor.productType) ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Pojemność kWh">
            <TextInput value={editor.storageCapacityKwh} onChange={(event) => setEditor(updateOfferField(editor, "storageCapacityKwh", event.target.value))} />
          </Field>
          <Field label="Magazyn marka">
            <TextInput value={editor.storageBrand} onChange={(event) => setEditor(updateOfferField(editor, "storageBrand", event.target.value))} />
          </Field>
          <Field label="Magazyn model">
            <TextInput value={editor.storageModel} onChange={(event) => setEditor(updateOfferField(editor, "storageModel", event.target.value))} />
          </Field>
        </div>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Konstrukcja">
          <TextInput value={editor.construction} onChange={(event) => setEditor(updateOfferField(editor, "construction", event.target.value))} />
        </Field>
        <Field label="Zabezpieczenia AC/DC">
          <TextInput value={editor.protectionsAcDc} onChange={(event) => setEditor(updateOfferField(editor, "protectionsAcDc", event.target.value))} />
        </Field>
        <Field label="Montaż">
          <TextInput value={editor.installation} onChange={(event) => setEditor(updateOfferField(editor, "installation", event.target.value))} />
        </Field>
        <Field label="Monitoring/EMS">
          <TextInput value={editor.monitoringEms} onChange={(event) => setEditor(updateOfferField(editor, "monitoringEms", event.target.value))} />
        </Field>
      </div>
      <Field label="Gwarancja">
        <TextArea value={editor.warranty} onChange={(event) => setEditor(updateOfferField(editor, "warranty", event.target.value))} />
      </Field>
    </div>
  );
}

function PriceStep({ editor, setEditor, price }: { editor: OfferTemplate; setEditor: (offer: OfferTemplate) => void; price: ReturnType<typeof priceBreakdown> }) {
  return (
    <div className="grid gap-3">
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Cena netto zestawu">
          <TextInput type="number" value={editor.priceNetPln || ""} onChange={(event) => setEditor(updateOfferField(editor, "priceNetPln", Number(event.target.value)))} />
        </Field>
        <Field label="VAT">
          <select
            className="h-10 w-full rounded-[8px] border border-white/10 bg-black/30 px-3 text-sm text-white"
            value={editor.vatRate}
            onChange={(event) => setEditor(updateOfferField(editor, "vatRate", Number(event.target.value) as VatRate))}
          >
            <option value={8}>8%</option>
            <option value={23}>23%</option>
          </select>
        </Field>
        <Field label="Dofinansowanie">
          <TextInput type="number" value={editor.subsidyAmountPln ?? ""} onChange={(event) => setEditor(updateOfferField(editor, "subsidyAmountPln", event.target.value ? Number(event.target.value) : null))} />
        </Field>
      </div>
      <div className="grid gap-2 rounded-[8px] border border-white/10 bg-white/[0.06] p-3 text-sm text-zinc-300">
        <div>Netto: {formatPln(price.net)}</div>
        <div>Brutto: {formatPln(price.gross)}</div>
        {price.subsidy !== null ? <div>Po dopłacie: {formatPln(price.client)}</div> : null}
      </div>
    </div>
  );
}

function TermsStep({ editor, setEditor }: { editor: OfferTemplate; setEditor: (offer: OfferTemplate) => void }) {
  return (
    <div className="grid gap-3">
      <Field label="Warunki płatności">
        <TextInput value={editor.paymentTerms} onChange={(event) => setEditor(updateOfferField(editor, "paymentTerms", event.target.value))} />
      </Field>
      <Field label="Termin realizacji">
        <TextInput value={editor.implementationTime} onChange={(event) => setEditor(updateOfferField(editor, "implementationTime", event.target.value))} />
      </Field>
      <Field label="Ważność oferty">
        <TextInput value={editor.validity} onChange={(event) => setEditor(updateOfferField(editor, "validity", event.target.value))} />
      </Field>
    </div>
  );
}

function EmailTemplateEditor({
  editorRef,
  value,
  variables,
  onChange,
  insertEmailToken,
}: {
  editorRef: RefObject<HTMLDivElement | null>;
  value: string;
  variables: EmailVariable[];
  onChange: (value: string) => void;
  insertEmailToken: (token: string) => void;
}) {
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || document.activeElement === editor) return;
    editor.innerHTML = emailTemplateToEditorHtml(value, variables);
  }, [editorRef, value, variables]);

  function emitChange() {
    const editor = editorRef.current;
    if (editor) onChange(serializeEmailEditor(editor));
  }

  function insertPlainText(text: string) {
    const editor = editorRef.current;
    if (!editor) return;
    editor.focus();
    const selection = window.getSelection();
    const range = selection && selection.rangeCount > 0 && selection.anchorNode && editor.contains(selection.anchorNode)
      ? selection.getRangeAt(0)
      : document.createRange();
    if (!editor.contains(range.startContainer)) {
      range.selectNodeContents(editor);
      range.collapse(false);
    }
    range.deleteContents();
    const textNode = document.createTextNode(text);
    range.insertNode(textNode);
    range.setStartAfter(textNode);
    range.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(range);
    emitChange();
  }

  return (
    <div
      ref={editorRef}
      role="textbox"
      aria-label="Treść emaila"
      contentEditable
      suppressContentEditableWarning
      className="mt-1 min-h-[360px] w-full overflow-auto rounded-[8px] border border-white/10 bg-black/30 px-3 py-2 text-sm leading-6 text-white outline-none focus:border-[#3DFF7A]/60"
      style={{ whiteSpace: "pre-wrap" }}
      onInput={emitChange}
      onBlur={emitChange}
      onClick={(event) => {
        const remove = event.target instanceof HTMLElement ? event.target.closest("[data-email-token-remove]") : null;
        if (!(remove instanceof HTMLElement)) return;
        event.preventDefault();
        const chip = remove.closest("[data-email-token]");
        if (!(chip instanceof HTMLElement)) return;
        removeEmailTokenChip(chip, event.currentTarget);
        emitChange();
      }}
      onPaste={(event) => {
        event.preventDefault();
        insertPlainText(event.clipboardData.getData("text/plain"));
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragStart={(event) => {
        const target = event.target instanceof HTMLElement ? event.target.closest("[data-email-token]") : null;
        const token = target instanceof HTMLElement ? target.dataset.emailToken : "";
        if (token) event.dataTransfer.setData("text/plain", token);
      }}
      onDrop={(event) => {
        event.preventDefault();
        const token = event.dataTransfer.getData("text/plain");
        if (!token) return;
        setCaretFromDropPoint(event.currentTarget, event);
        insertEmailToken(token);
      }}
    />
  );
}

function EmailContentStep({
  profile,
  setProfile,
  emailVariables,
  emailEditorRef,
  insertEmailToken,
  emailUnknownTokens,
  profileErrors,
  apiReady,
  saveProfile,
}: {
  profile: SellerProfile;
  setProfile: (updater: (current: SellerProfile) => SellerProfile) => void;
  emailVariables: EmailVariable[];
  emailEditorRef: RefObject<HTMLDivElement | null>;
  insertEmailToken: (token: string) => void;
  emailUnknownTokens: string[];
  profileErrors: string[];
  apiReady: boolean;
  saveProfile: () => Promise<void>;
}) {
  return (
    <div className="grid gap-3">
      <div>
        <div className="text-xs font-medium uppercase text-[#3DFF7A]">Treść emaila</div>
        <EmailTemplateEditor
          editorRef={emailEditorRef}
          value={profile.emailBodyTemplate}
          variables={emailVariables}
          onChange={(value) => setProfile((current) => ({ ...current, emailBodyTemplate: value }))}
          insertEmailToken={insertEmailToken}
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {emailVariables.map((variable) => (
          <button
            key={variable.token}
            type="button"
            draggable
            onClick={() => insertEmailToken(variable.token)}
            onDragStart={(event) => event.dataTransfer.setData("text/plain", variable.token)}
            className="rounded-[8px] border border-white/10 bg-white/[0.06] px-2.5 py-1.5 text-xs font-medium text-zinc-200 hover:border-[#3DFF7A]/50 hover:text-white"
            title={variable.source}
          >
            {variable.label}
          </button>
        ))}
      </div>
      {emailUnknownTokens.length ? (
        <div className="rounded-[8px] border border-red-400/30 bg-red-950/30 p-3 text-sm text-red-300">
          {emailUnknownTokens.map((token) => (
            <div key={token}>Nieznana zmienna emaila: {token}</div>
          ))}
        </div>
      ) : null}
      {apiReady ? (
        <button
          onClick={() => void saveProfile()}
          className="h-9 w-fit rounded-[8px] border border-white/12 px-3 text-sm font-semibold text-zinc-200 hover:bg-white/[0.06]"
        >
          Zapisz profil
        </button>
      ) : null}
      {profileErrors.length ? (
        <div className="rounded-[8px] border border-red-400/30 bg-red-950/30 p-3 text-sm text-red-300">
          {profileErrors.map((error) => (
            <div key={error}>{error}</div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PreviewStep({ editor, profile, price }: { editor: OfferTemplate; profile: SellerProfile; price: ReturnType<typeof priceBreakdown> }) {
  const lines = componentLines(editor);
  return (
    <div className="offer-preview-card rounded-[8px] border border-white/10 bg-white/[0.04] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">{profile.companyName}</div>
          <h2 className="mt-4 text-xl font-semibold tracking-[0] text-white">{editor.name || "Bez nazwy"}</h2>
          <p className="mt-1 text-sm text-zinc-400">{editor.productType}</p>
        </div>
        {profile.logoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={profile.logoUrl} alt="" className="h-12 max-w-32 object-contain" />
        ) : null}
      </div>
      <div className="mt-5 border-l-4 border-[#3DFF7A] pl-4">
        <div className="text-xs font-semibold uppercase text-[#3DFF7A]">Cena</div>
        <div className="mt-1 text-3xl font-semibold tracking-[0] text-white">{formatPln(price.client)}</div>
      </div>
      <dl className="mt-5 grid gap-2 text-sm text-zinc-300">
        <div className="flex justify-between gap-3"><dt>Netto</dt><dd>{formatPln(price.net)}</dd></div>
        <div className="flex justify-between gap-3"><dt>Brutto</dt><dd>{formatPln(price.gross)}</dd></div>
        {price.subsidy !== null ? <div className="flex justify-between gap-3"><dt>Szacowane dofinansowanie</dt><dd>{formatPln(price.subsidy)}</dd></div> : null}
      </dl>
      {lines.length ? (
        <ul className="mt-5 space-y-1 text-sm text-zinc-300">
          {lines.map((line) => <li key={line}>{line}</li>)}
        </ul>
      ) : null}
      <p className="mt-5 text-xs leading-5 text-zinc-500">
        Oferta ma charakter informacyjny. Szczegóły techniczne, dostępność komponentów i warunki realizacji wymagają potwierdzenia z handlowcem.
      </p>
    </div>
  );
}
