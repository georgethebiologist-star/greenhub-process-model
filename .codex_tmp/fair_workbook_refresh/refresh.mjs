import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "C:/my/Spaak/Greenhub/Model";
const workbookPath = `${root}/Greenhub/data/greenhub_feed_inputs.xlsx`;
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));

function typedCsvValues(values) {
  return values.map((row) => row.map((cell) => {
    if (typeof cell !== "string") return cell;
    const clean = cell.replace(/^\uFEFF/, "");
    const text = clean.trim();
    if (/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(text)) return Number(text);
    return clean;
  }));
}

async function readCsvMatrix(relativePath) {
  const csvText = await fs.readFile(`${root}/${relativePath}`, "utf8");
  const csvWorkbook = await Workbook.fromCSV(csvText, { sheetName: "Import" });
  return typedCsvValues(csvWorkbook.worksheets.getItem("Import").getUsedRange().values);
}

const catalogRows = await readCsvMatrix("Greenhub/data/fair_input_catalog/master_input_catalog.csv");
const recordRows = await readCsvMatrix("Greenhub/data/fair_input_catalog/master_input_records.csv");
const catalogSheet = workbook.worksheets.getItem("FAIR_Catalog");
const masterSheet = workbook.worksheets.getItem("Master_Inputs");
const previousCatalogRows = catalogSheet.getUsedRange().values.length;
const catalogHeaderRow = 6;
const masterHeaderRow = 6;
const catalogDataStartRow = catalogHeaderRow + 1;
const newCatalogLastRow = catalogHeaderRow + catalogRows.length - 1;
if (newCatalogLastRow > previousCatalogRows) {
  catalogSheet.getRange(`A${newCatalogLastRow}:W${newCatalogLastRow}`).copyFrom(
    catalogSheet.getRange(`A${previousCatalogRows}:W${previousCatalogRows}`),
    "all",
  );
}
catalogSheet.getRangeByIndexes(catalogHeaderRow - 1, 0, catalogRows.length, catalogRows[0].length).values = catalogRows;
recordRows.length && (masterSheet.getRangeByIndexes(masterHeaderRow - 1, 0, recordRows.length, recordRows[0].length).values = recordRows);
catalogSheet.getRange("A2").values = [[`Catalog urn:greenhub:catalog:master-inputs:v1 · schema 1.0.0 · ${catalogRows.length - 1} indexed source assets`]];
masterSheet.getRange("A2").values = [[`urn:greenhub:dataset:master-input-records:v1 · schema 1.0.0 · ${recordRows.length - 1} normalized records`]];

workbook.recalculate();
const validation = await workbook.inspect({ kind: "workbook,sheet,formula", maxChars: 1600 });
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "FAIR workbook formula error scan",
});
console.log(validation.ndjson);
console.log(errors.ndjson);
console.log(`catalog assets=${catalogRows.length - 1}; records=${recordRows.length - 1}; new catalog last row=${newCatalogLastRow}; previous catalog used rows=${previousCatalogRows}`);

for (const [name, range, file] of [
  ["FAIR_Catalog", "A1:W18", "fair_catalog_preview.png"],
  ["Master_Inputs", "A1:S18", "master_inputs_preview.png"],
]) {
  const preview = await workbook.render({ sheetName: name, range, scale: 1, format: "png" });
  await fs.writeFile(`${root}/.codex_tmp/fair_workbook_refresh/${file}`, new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${root}/.codex_tmp/fair_workbook_refresh/greenhub_feed_inputs.fair_refresh.xlsx`);
