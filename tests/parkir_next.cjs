const fs = require("fs");

const [, , jalurTs, jalurSumber, jalurData] = process.argv;
const ts = require(jalurTs);
const hasil = ts.transpileModule(fs.readFileSync(jalurSumber, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
});
const modul = { exports: {} };
new Function("module", "exports", "require", hasil.outputText)(modul, modul.exports, require);
const h = modul.exports;
const data = JSON.parse(fs.readFileSync(jalurData, "utf8"));
const masuk = JSON.parse(fs.readFileSync(0, "utf8"));

process.stdout.write(
  JSON.stringify({
    kawasan: masuk.titik.map(([lat, lon]) => {
      const r = h.cariKawasan(data, lat, lon);
      return [r.kawasan, r.ruas, r.luar];
    }),
    tarif: masuk.kombinasi.map(([a, b, c, d]) => {
      const t = h.hitungTarif(data, a, b, c, d);
      return t ? t.total : null;
    }),
  }),
);
