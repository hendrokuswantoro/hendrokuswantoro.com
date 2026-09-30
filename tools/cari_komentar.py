from __future__ import annotations

import io
import json
import pathlib
import re
import subprocess
import sys
import tokenize

AKAR = pathlib.Path(__file__).resolve().parent.parent
LEWATI = ("node_modules", ".next", "next/out", "dist", "assets/vendor", "next/public/assets/vendor",
          "backend/db/migrations", ".git", "cadangan", "unggahan", "hasil-uji-keamanan",
          "next/next-env.d.ts", ".pytest_cache", ".ruff_cache", ".claude", ".venv")


def _dilewati(p: pathlib.Path) -> bool:
    jalur = p.relative_to(AKAR).as_posix()
    return any(jalur == x or jalur.startswith(x + "/") or f"/{x}/" in f"/{jalur}" for x in LEWATI)


NAMA_PAGAR = ("Dockerfile", ".gitignore", ".gitattributes", "_headers", "_redirects", ".env.example")


def _cocok(p: pathlib.Path, akhiran: tuple[str, ...], nama: tuple[str, ...]) -> bool:
    return p.suffix in akhiran or p.name in nama or (
        "requirements" in nama and p.name.startswith("requirements") and p.suffix == ".txt"
    )


def berkas(akhiran: tuple[str, ...], nama: tuple[str, ...] = ()) -> list[pathlib.Path]:
    hasil = []
    for p in AKAR.rglob("*"):
        if p.is_file() and _cocok(p, akhiran, nama) and not _dilewati(p):
            hasil.append(p)
    return sorted(hasil)


def python(p: pathlib.Path) -> list[tuple[int, str]]:
    temuan = []
    sumber = p.read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(sumber).readline):
        if tok.type == tokenize.COMMENT:
            teks = tok.string
            if tok.start[0] == 1 and teks.startswith("#!"):
                continue
            temuan.append((tok.start[0], teks))
    return temuan


PEMINDAI_TS = r"""
const ts = require(process.argv[1]);
const fs = require("fs");
const hasil = {};
for (const berkas of JSON.parse(fs.readFileSync(0, "utf8"))) {
  const teks = fs.readFileSync(berkas, "utf8");
  const jenis = berkas.endsWith(".tsx") ? ts.ScriptKind.TSX : berkas.endsWith(".ts") ? ts.ScriptKind.TS : ts.ScriptKind.JSX;
  const sumber = ts.createSourceFile(berkas, teks, ts.ScriptTarget.Latest, true, jenis);
  const lihat = new Map();
  const catat = (daftar) => { for (const r of daftar || []) lihat.set(r.pos, r); };
  const telusuri = (simpul) => {
    catat(ts.getLeadingCommentRanges(teks, simpul.pos));
    catat(ts.getTrailingCommentRanges(teks, simpul.end));
    for (const anak of simpul.getChildren(sumber)) telusuri(anak);
  };
  telusuri(sumber);
  const temuan = [];
  for (const r of [...lihat.values()].sort((a, b) => a.pos - b.pos)) {
    const isi = teks.slice(r.pos, r.end);
    const baris = teks.slice(0, r.pos).split("\n").length;
    if (!(baris === 1 && isi.startsWith("#!"))) temuan.push([baris, isi.slice(0, 120)]);
  }
  if (temuan.length) hasil[berkas] = temuan;
}
process.stdout.write(JSON.stringify(hasil));
"""


def skrip(daftar: list[pathlib.Path]) -> dict[pathlib.Path, list[tuple[int, str]]]:
    ts = AKAR / "next" / "node_modules" / "typescript"
    node = "node"
    for calon in ("node", "C:/Program Files/nodejs/node.exe"):
        try:
            subprocess.run([calon, "--version"], capture_output=True, check=True)
            node = calon
            break
        except (OSError, subprocess.CalledProcessError):
            continue
    keluar = subprocess.run(
        [node, "-e", PEMINDAI_TS, str(ts)], input=json.dumps([str(p) for p in daftar]),
        capture_output=True, text=True, check=True,
    )
    mentah = json.loads(keluar.stdout or "{}")
    return {
        pathlib.Path(b): isi
        for b, isi in mentah.items()
    }


def css(p: pathlib.Path) -> list[tuple[int, str]]:
    teks = p.read_text(encoding="utf-8")
    temuan = []
    for m in re.finditer(r"/\*.*?\*/", teks, re.S):
        isi = m.group(0)
        temuan.append((teks.count("\n", 0, m.start()) + 1, isi[:120]))
    return temuan


def html(p: pathlib.Path) -> list[tuple[int, str]]:
    teks = p.read_text(encoding="utf-8")
    return [(teks.count("\n", 0, m.start()) + 1, m.group(0)[:120])
            for m in re.finditer(r"<!--.*?-->", teks, re.S)]


def pagar(p: pathlib.Path) -> list[tuple[int, str]]:
    temuan = []
    di_heredoc = None
    for nomor, baris in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if di_heredoc:
            if baris.strip() == di_heredoc:
                di_heredoc = None
            continue
        tanda = re.search(r"<<-?\s*'?\"?([A-Z_]+)'?\"?", baris)
        if tanda and p.suffix in (".sh", ".yml"):
            di_heredoc = tanda.group(1)
        bersih = baris.strip()
        if not bersih.startswith("#"):
            continue
        if nomor == 1 and bersih.startswith("#!"):
            continue
        temuan.append((nomor, bersih[:120]))
    return temuan


def batch(p: pathlib.Path) -> list[tuple[int, str]]:
    temuan = []
    for nomor, baris in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        bersih = baris.strip()
        if bersih.lower().startswith(("rem ", "::")) or bersih.lower() == "rem":
            temuan.append((nomor, bersih[:120]))
    return temuan


def ts_ada() -> bool:
    return (AKAR / "next" / "node_modules" / "typescript" / "package.json").exists()


def semua(dengan_skrip: bool = True) -> dict[pathlib.Path, list[tuple[int, str]]]:
    hasil: dict[pathlib.Path, list[tuple[int, str]]] = {}
    for p in berkas((".py",)):
        if t := python(p):
            hasil[p] = t
    if dengan_skrip:
        hasil.update(skrip(berkas((".js", ".mjs", ".cjs", ".ts", ".tsx"))))
    for p in berkas((".css",)):
        if t := css(p):
            hasil[p] = t
    for p in berkas((".html",)):
        if t := html(p):
            hasil[p] = t
    lain = berkas((".sh", ".yml", ".yaml", ".conf", ".toml", ".service", ".timer", ".ps1"),
                  NAMA_PAGAR + ("requirements",))
    for p in lain:
        if t := pagar(p):
            hasil[p] = t
    for p in berkas((".cmd", ".bat")):
        if t := batch(p):
            hasil[p] = t
    return {p: t for p, t in hasil.items() if t}


def main() -> int:
    if not ts_ada():
        print("next/node_modules/typescript tidak ada: jalankan npm ci di next/ dulu", file=sys.stderr)
        return 2
    hasil = semua()
    for p, temuan in sorted(hasil.items()):
        for nomor, teks in temuan:
            print(f"{p.relative_to(AKAR).as_posix()}:{nomor}: {teks}")
    if hasil:
        print(f"\n{sum(len(t) for t in hasil.values())} komentar di {len(hasil)} berkas")
        return 1
    print("tidak ada komentar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
