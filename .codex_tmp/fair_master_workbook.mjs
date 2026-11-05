import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from 'file:///C:/Users/katrb/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root = 'C:/my/Spaak/Greenhub/Model';
const workbookPath = `${root}/.codex_tmp/greenhub_feed_inputs_original.xlsx`;
const catalogPath = `${root}/Greenhub/data/fair_input_catalog/master_input_catalog.json`;
const outputPath = `${root}/.codex_tmp/greenhub_feed_inputs_fair.xlsx`;
const payload = JSON.parse(await fs.readFile(catalogPath, 'utf8'));
const inputs = JSON.parse(await fs.readFile(`${root}/Greenhub/data/fair_input_catalog/master_input_records.json`, 'utf8'));
const internalAssets = payload.assets.map(row => row.relative_path === 'Greenhub/data/greenhub_feed_inputs.xlsx'
  ? {...row, dataset_id:'urn:greenhub:asset:greenhub-feed-input-workbook', sha256:'See external master_input_catalog.csv/json; self-checksum is intentionally not embedded to avoid recursive hashing.', provenance:'Workbook self-reference; the external FAIR catalog carries the current content hash.'}
  : row);
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const before = await workbook.inspect({kind:'sheet', include:'id,name', maxChars:4000});
if (String(before.ndjson).includes('FAIR_Catalog')) throw new Error('FAIR_Catalog already exists; stop instead of replacing it.');
const originalSheetCount = before.ndjson.trim().split('\n').length;
const originalSnapshots = Array.from({length:originalSheetCount}, (_, index) => {
  const range = workbook.worksheets.getItemAt(index).getUsedRange();
  return {values:range.values, formulas:range.formulas};
});
const readmeUpdates = {
  10: 'A = measured/verified; B = directly traceable literature, official data or supplier evidence; C = project engineering estimate; D = uncertain/quarantined and not a runtime quality tier; E = explicit assumption or structural placeholder. B does not imply high transferability; do not describe unknown as zero.',
  17: 'Class E inputs are explicit assumptions/placeholders. They may support screening only when the applicable structural-test gate allows them; reports must retain the assumption label and affected limitations.',
  23: 'Keep class E values visibly identified as assumptions/placeholders. Replace or validate before design-grade, investment-grade TEA/LCA, permitting or performance claims.',
  28: 'Phase 4 supplied values are class E assumptions/placeholders unless individually source-validated. Screening outputs must retain this status; do not present them as measurements.',
  31: 'Phase 5 supplied values are class E assumptions/placeholders unless individually source-validated. They support screening/code checks only and are not equipment-design or performance evidence.',
  36: 'Phase 6 supplied process values are class E assumptions/placeholders unless individually source-validated. Screening results remain conditional and are not permitting or performance claims.',
  42: 'Phase 7 supplied values are class E assumptions/placeholders unless individually source-validated. They do not establish TEA/LCA completeness, fertilizer eligibility, water reuse or configuration evidence.',
};
const readme = workbook.worksheets.getItem('ReadMe');
for (const [rowText, value] of Object.entries(readmeUpdates)) {
  const row = Number(rowText);
  readme.getRange(`B${row}`).values = [[value]];
  originalSnapshots[0].values[row - 1][1] = value;
}
const sheet = workbook.worksheets.add('FAIR_Catalog');
sheet.showGridLines = false;
sheet.tabColor = '#2F6B55';
const headers = Object.keys(internalAssets[0]);
const lastCol = String.fromCharCode(64 + headers.length);
for (let row = 1; row <= 4; row++) sheet.mergeCells(`A${row}:${lastCol}${row}`);
sheet.getRange('A1').values = [[payload.title]];
sheet.getRange('A2').values = [[`Catalog ${payload.catalog_id} · schema ${payload.schema_version} · ${payload.counts.assets} indexed source assets`]];
sheet.getRange('A3').values = [[payload.authoritative_value_policy]];
sheet.getRange('A4').values = [[`Override precedence: ${payload.override_precedence}`]];
sheet.getRangeByIndexes(5, 0, internalAssets.length + 1, headers.length).values = [headers, ...internalAssets.map(row => headers.map(key => row[key] ?? ''))];
sheet.getRange(`A1:${lastCol}1`).format = {fill:'#153D36',font:{bold:true,color:'#FFFFFF',size:16},verticalAlignment:'center'};
sheet.getRange(`A2:${lastCol}4`).format = {fill:'#EAF1EC',font:{color:'#153D36',size:10},wrapText:true,verticalAlignment:'center'};
sheet.getRange(`A6:${lastCol}6`).format = {fill:'#2F6B55',font:{bold:true,color:'#FFFFFF',size:10},wrapText:true,verticalAlignment:'center'};
sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 28;
sheet.getRange('A2:W2').format.rowHeight = 30;
sheet.getRange('A3:W3').format.rowHeight = 38;
sheet.getRange('A4:W4').format.rowHeight = 38;
sheet.getRange(`A6:${lastCol}6`).format.rowHeight = 44;
sheet.getRange(`A7:${lastCol}${payload.assets.length + 6}`).format = {font:{size:9,color:'#1F302B'},wrapText:true,verticalAlignment:'top'};
sheet.getRange('A:A').format.columnWidth = 48;
sheet.getRange('B:B').format.columnWidth = 28;
sheet.getRange('C:C').format.columnWidth = 55;
sheet.getRange('D:F').format.columnWidth = 18;
sheet.getRange('G:G').format.columnWidth = 68;
sheet.getRange('H:I').format.columnWidth = 28;
sheet.getRange('J:K').format.columnWidth = 38;
sheet.getRange('L:Q').format.columnWidth = 24;
sheet.getRange('R:W').format.columnWidth = 34;
sheet.freezePanes.freezeRows(6);
const master = workbook.worksheets.add('Master_Inputs');
master.showGridLines = false;
master.tabColor = '#72946C';
const recordHeaders = Object.keys(inputs.records[0]);
const recordLastCol = String.fromCharCode(64 + recordHeaders.length);
for (let row = 1; row <= 4; row++) master.mergeCells(`A${row}:${recordLastCol}${row}`);
master.getRange('A1').values = [[inputs.title]];
master.getRange('A2').values = [[`${inputs.dataset_id} · schema ${inputs.schema_version} · ${inputs.record_count} normalized records`]];
master.getRange('A3').values = [[inputs.authority_note]];
master.getRange('A4').values = [['Generated snapshot only; edit the authoritative source file and rebuild. UI/request overrides retain their existing precedence.']];
master.getRangeByIndexes(5, 0, inputs.records.length + 1, recordHeaders.length).values = [recordHeaders, ...inputs.records.map(row => recordHeaders.map(key => row[key] ?? ''))];
master.getRange(`A1:${recordLastCol}1`).format = {fill:'#153D36',font:{bold:true,color:'#FFFFFF',size:16},verticalAlignment:'center'};
master.getRange(`A2:${recordLastCol}4`).format = {fill:'#EAF1EC',font:{color:'#153D36',size:10},wrapText:true,verticalAlignment:'center'};
master.getRange(`A6:${recordLastCol}6`).format = {fill:'#72946C',font:{bold:true,color:'#FFFFFF',size:10},wrapText:true,verticalAlignment:'center'};
master.getRange(`A1:${recordLastCol}1`).format.rowHeight = 28;
master.getRange(`A2:${recordLastCol}2`).format.rowHeight = 24;
master.getRange(`A3:${recordLastCol}4`).format.rowHeight = 38;
master.getRange(`A6:${recordLastCol}6`).format.rowHeight = 42;
master.getRange(`A7:${recordLastCol}${inputs.records.length + 6}`).format = {font:{size:9,color:'#1F302B'},wrapText:true,verticalAlignment:'top'};
for (const [column,width] of [['A',28],['B',62],['C',32],['D',18],['E',20],['F',54],['G',16],['H',30],['I',52],['J',32],['K',58],['L',34],['M',24],['N',16],['O',58],['P',48],['Q',58],['R',58],['S',68]]) {
  master.getRange(`${column}:${column}`).format.columnWidth = width;
}
master.freezePanes.freezeRows(6);
// These catalog sheets contain static values only. Avoid workbook-wide recalculation:
// it would materialize cached formula outputs in untouched legacy control sheets.
const audit = await workbook.inspect({kind:'sheet',include:'id,name',maxChars:5000});
for (let index = 0; index < originalSheetCount; index++) {
  const range = workbook.worksheets.getItemAt(index).getUsedRange();
  const current = range.values, formulas = range.formulas, snapshot = originalSnapshots[index], mismatch = [];
  for (let row = 0; row < Math.max(current.length, snapshot.values.length); row++) {
    for (let col = 0; col < Math.max(current[row]?.length || 0, snapshot.values[row]?.length || 0); col++) {
      const beforeFormula = snapshot.formulas[row]?.[col] || '';
      const afterFormula = formulas[row]?.[col] || '';
      if (beforeFormula || afterFormula) {
        if (beforeFormula !== afterFormula) mismatch.push({row:row+1,col:col+1,beforeFormula,afterFormula});
      } else if (JSON.stringify(current[row]?.[col]) !== JSON.stringify(snapshot.values[row]?.[col])) {
        mismatch.push({row:row+1,col:col+1,before:snapshot.values[row]?.[col],after:current[row]?.[col]});
      }
      if (mismatch.length >= 5) break;
    }
    if (mismatch.length >= 5) break;
  }
  if (mismatch.length) throw new Error(`Existing workbook sheet ${index} inputs/formulas changed during the additive catalog edit: ${JSON.stringify(mismatch)}`);
}
const preview = await workbook.render({sheetName:'FAIR_Catalog',range:'A1:W12',scale:0.7,format:'png'});
await fs.writeFile(`${root}/.codex_tmp/fair_catalog_preview.png`, new Uint8Array(await preview.arrayBuffer()));
const inputPreview = await workbook.render({sheetName:'Master_Inputs',range:'A1:S12',scale:0.7,format:'png'});
await fs.writeFile(`${root}/.codex_tmp/master_inputs_preview.png`, new Uint8Array(await inputPreview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({before:before.ndjson,after:audit.ndjson,outputPath,assetCount:internalAssets.length,inputRecordCount:inputs.record_count}));
