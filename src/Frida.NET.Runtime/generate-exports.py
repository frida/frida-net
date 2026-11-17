import argparse
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-header", required=True, type=Path)
    parser.add_argument("--glib-exports", required=True, type=Path)
    parser.add_argument("--nm")
    parser.add_argument("--archive", action="append", default=[], type=Path)
    parser.add_argument("--output-def", required=True, type=Path)
    parser.add_argument("--output-version-script", required=True, type=Path)
    parser.add_argument("--output-symbol-list", required=True, type=Path)
    parser.add_argument("--output-references", required=True, type=Path)
    args = parser.parse_args()

    frida_symbols = sorted(set(re.findall(r"\b(frida_[a-z0-9_]+)\s*\(", args.core_header.read_text(encoding="utf-8"))))
    glib_symbols = args.glib_exports.read_text(encoding="utf-8").split()
    if args.archive:
        defined = query_defined_symbols(args.nm, args.archive)
        glib_symbols = [symbol for symbol in glib_symbols if symbol in defined]
    symbols = frida_symbols + glib_symbols

    args.output_def.write_text(generate_def(symbols), encoding="utf-8")
    args.output_version_script.write_text(generate_version_script(symbols), encoding="utf-8")
    args.output_symbol_list.write_text(generate_symbol_list(symbols), encoding="utf-8")
    args.output_references.write_text(generate_references(symbols), encoding="utf-8")


def query_defined_symbols(nm, archives):
    output = subprocess.run([nm, "-g", "--defined-only", *archives], capture_output=True, text=True, check=True).stdout
    names = {line.split()[-1] for line in output.splitlines() if len(line.split()) == 3}
    return names | {name[1:] for name in names if name.startswith("_")}


def generate_def(symbols):
    return "EXPORTS\n" + "".join(f"{symbol}\n" for symbol in symbols)


def generate_version_script(symbols):
    entries = "".join(f"    {symbol};\n" for symbol in symbols)
    return f"""{{
  global:
{entries}
  local:
    *;
}};
"""


def generate_symbol_list(symbols):
    return "".join(f"_{symbol}\n" for symbol in symbols)


def generate_references(symbols):
    declarations = "".join(f"extern void {symbol} (void);\n" for symbol in symbols)
    entries = "".join(f"  {symbol},\n" for symbol in symbols)
    return f"""{declarations}
void (* const frida_net_exports[]) (void) =
{{
{entries}}};
"""


if __name__ == "__main__":
    main()
