import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(".");
const resultsDir = path.join(projectRoot, "Greenhub", "results");
const previewRoot = path.join(projectRoot, ".codex_tmp", "phase7_report_previews");
const filenames = [
  "phase7_nutrient_recovery_report.xlsx",
  "phase7_scenario_comparison.xlsx",
  "phase7_limitations_and_data_needs.xlsx",
];

await fs.mkdir(previewRoot, { recursive: true });
for (const filename of filenames) {
  const workbookPath = path.join(resultsDir, filename);
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
  const stem = path.parse(filename).name;
  const previewDir = path.join(previewRoot, stem);
  await fs.mkdir(previewDir, { recursive: true });
  const sheetNames = workbook.worksheets.items.map((sheet) => sheet.name);
  for (const sheet of workbook.worksheets.items) {
    const safeName = sheet.name.replace(/[^A-Za-z0-9_-]+/g, "_");
    const preview = await workbook.render({
      sheetName: sheet.name,
      range: "A1:O40",
      scale: 1,
      format: "png",
    });
    await fs.writeFile(
      path.join(previewDir, `${safeName}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    maxChars: 12000,
  });
  console.log(JSON.stringify({ filename, sheetNames, formulaErrors: errors.ndjson }));
}
