"""Rewrite the chart specs in a compact, readable layout: anything short (a list of numbers, a small
{"field": ..., "type": ...} object) stays on one line; longer things are spread over several lines.
The content is unchanged - only the whitespace. Run from the DV2 folder:  python3 scripts/format_specs.py [files...]
"""
import json, sys, glob

WIDTH = 100   # longest line (including indent) that may stay on one line

def fmt(v, indent=0, prefix=0):
    # prefix = width of the key text in front of this value on its line ("key": )
    one = json.dumps(v, ensure_ascii=False)
    if not isinstance(v, (dict, list)) or len(one) + indent + prefix <= WIDTH:
        return one
    pad, inner = ' ' * indent, ' ' * (indent + 2)
    if isinstance(v, list):
        return '[\n' + ',\n'.join(inner + fmt(x, indent + 2) for x in v) + '\n' + pad + ']'
    return '{\n' + ',\n'.join(f'{inner}{json.dumps(k, ensure_ascii=False)}: {fmt(x, indent + 2, len(json.dumps(k, ensure_ascii=False)) + 2)}' for k, x in v.items()) + '\n' + pad + '}'

if __name__ == '__main__':
    for path in sys.argv[1:] or sorted(glob.glob('specs/*.json')):
        spec = json.load(open(path, encoding='utf-8'))
        text = fmt(spec) + '\n'
        assert json.loads(text) == spec                      # safety check: same content
        open(path, 'w', encoding='utf-8').write(text)
        print(f'{path}: {text.count(chr(10))} lines')
