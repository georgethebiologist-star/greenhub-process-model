import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const inPath = path.join(root, "Greenhub", "results", "economic_inventory_catalog.json");
const outPath = path.join(root, "Greenhub", "results", "economic_inventory_catalog.xlsx");

const payload = JSON.parse(await fs.readFile(inPath, "utf8"));

const workbook = Workbook.create();

function rowsToMatrix(rows) {
  if (!rows || rows.length === 0) {
    return [["No rows"]];
  }
  const columns = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set()),
  );
  return [
    columns,
    ...rows.map((row) => columns.map((column) => row[column] ?? "")),
  ];
}

function objectToRows(obj) {
  return Object.entries(obj).map(([key, value]) => ({
    metric: key,
    value: typeof value === "object" ? JSON.stringify(value) : value,
  }));
}

function addSheet(name, rowsOrMatrix) {
  const sheet = workbook.worksheets.add(name);
  const matrix = Array.isArray(rowsOrMatrix?.[0])
    ? rowsOrMatrix
    : rowsToMatrix(rowsOrMatrix);
  sheet.getCell(0, 0).write(matrix);
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines = true;
  return sheet;
}

addSheet("ReadMe", [
  ["topic", "value"],
  ...payload.readme.map((row) => [row.topic, row.value]),
]);
addSheet("Summary", rowsToMatrix(objectToRows(payload.summary)));
addSheet("Inventory_Catalog", rowsToMatrix(payload.inventory_cost_catalog));
addSheet("Known_Costs_Scaling", rowsToMatrix(payload.known_costs_scaling));
addSheet("Missing_Cost_Items", rowsToMatrix(payload.missing_cost_items));
addSheet("Process_Scenarios", rowsToMatrix(payload.process_scenarios));
addSheet("Code_Units_Utilities", rowsToMatrix(payload.code_units_utilities));
addSheet("Source_Files", rowsToMatrix(payload.source_files));
addSheet("Global_Notes", rowsToMatrix(payload.global_notes));

await fs.mkdir(path.dirname(outPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outPath);
console.log(outPath);
