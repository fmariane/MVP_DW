"""Publica versões HTML dos documentos locais, preservando os arquivos fonte.

Dependência: Markdown 3.8.2. Executar a partir de qualquer diretório.
"""
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import html
import json
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = "https://fmariane.github.io/MVP_DW/"
REPO = "https://github.com/fmariane/MVP_DW/blob/main/"

STYLE = """
:root{color-scheme:light;--ink:#203244;--accent:#086a80;--line:#d9e3ec}
*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:var(--ink);font:17px/1.7 system-ui,sans-serif}
header{border-bottom:1px solid var(--line);background:#fff;padding:18px max(24px,calc((100vw - 1180px)/2))}
nav{display:flex;gap:22px;flex-wrap:wrap}a{color:var(--accent);text-underline-offset:3px}
main{max-width:1180px;margin:32px auto;padding:32px;background:#fff;border:1px solid var(--line);border-radius:12px}
h1,h2,h3{line-height:1.3;color:#183044}h1{font-size:2rem}h2{margin-top:2em}h3{margin-top:1.6em}
img{display:block;max-width:100%;height:auto;margin:24px auto}pre{padding:18px;background:#f0f4f8;overflow:auto;border-radius:8px}
code{font-family:ui-monospace,monospace;font-size:.88em;overflow-wrap:anywhere}pre code{overflow-wrap:normal}
.tablewrap{overflow-x:auto;margin:24px 0}table{width:100%;border-collapse:collapse;font-size:.94em}
th,td{text-align:left;padding:11px 14px;border:1px solid var(--line);vertical-align:top}th{background:#eef5f7}
tbody tr:nth-child(even){background:#fafcfd}.toc{padding:12px 24px;background:#f4f8fa;border-radius:8px}
.mermaid{overflow-x:auto;margin:24px 0}.mermaid svg{height:auto}summary{cursor:pointer;font-weight:600}
.note,footer{color:#526779;font-size:.9em}footer{max-width:1180px;margin:24px auto;padding:0 24px}
@media(max-width:720px){main{margin:12px;padding:18px}h1{font-size:1.65rem}header{padding:16px}}
@media print{header,.toc{display:none}main{border:0;margin:0;max-width:none;padding:0}pre{white-space:pre-wrap}}
"""


def page(title, body, source=None, diagram=False):
    source_link = f'<a href="{REPO}{quote(source)}">Arquivo original</a>' if source else ""
    script = """<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs';
mermaid.initialize({startOnLoad:true,securityLevel:'strict',theme:'neutral'});
</script>""" if diagram else ""
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | MVP DW</title><style>{STYLE}</style></head>
<body><header><nav><a href="{SITE}">Início</a><a href="{SITE}docs/index.html">Documentação</a>
<a href="https://github.com/fmariane/MVP_DW#readme">Relatório completo</a>{source_link}</nav></header>
<main>{body}</main><footer>Documentação do MVP de Minas Gerais, 2025. Foram preservados os arquivos fonte no repositório.</footer>{script}</body></html>
'''


def rewrite_href(match):
    href = html.unescape(match.group(1))
    parsed = urlsplit(href)
    if parsed.scheme or href.startswith(("#", "//")):
        return match.group(0)
    target = (DOCS / unquote(parsed.path)).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError(f"Link fora do projeto: {href}")
    rel = target.relative_to(ROOT).as_posix()
    if target.parent == DOCS and target.suffix in (".md", ".json"):
        url = SITE + quote(str(Path(rel).with_suffix(".html")).replace("\\", "/"))
    elif rel == "README.md":
        url = "https://github.com/fmariane/MVP_DW#readme"
    elif target.suffix in (".py", ".sql", ".md", ".txt"):
        url = REPO + quote(rel)
    else:
        url = SITE + quote(rel)
    if parsed.fragment and rel != "README.md":
        url += "#" + parsed.fragment
    return 'href="' + html.escape(url, quote=True) + '"'


def json_view(value):
    if isinstance(value, dict):
        rows = ''.join(f'<tr><th>{html.escape(str(k))}</th><td>{json_view(v)}</td></tr>' for k, v in value.items())
        return f'<div class="tablewrap"><table><tbody>{rows}</tbody></table></div>'
    if isinstance(value, list):
        return '<ol>' + ''.join(f'<li>{json_view(v)}</li>' for v in value) + '</ol>'
    return html.escape(str(value))


def main():
    entries = []
    for source in sorted(DOCS.iterdir()):
        if source.suffix not in (".md", ".json"):
            continue
        text = source.read_text(encoding="utf-8-sig")
        diagram = False
        if source.suffix == ".md":
            title = next(line.lstrip("# ") for line in text.splitlines() if line.startswith("# "))
            diagrams = []

            def capture(m):
                diagrams.append(m.group(1))
                return f'\n\n<div id="diagram{len(diagrams)-1}"></div>\n\n'

            text = re.sub(r"```mermaid\s*\n(.*?)```", capture, text, flags=re.S)
            renderer = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
            body = renderer.convert(text)
            for i, code in enumerate(diagrams):
                body = body.replace(f'<div id="diagram{i}"></div>',
                    '<div class="mermaid">' + html.escape(code) + '</div>'
                    '<details><summary>Definição textual do diagrama</summary><pre>' + html.escape(code) + '</pre></details>')
            diagram = bool(diagrams)
            body = re.sub(r'href="([^"]+)"', rewrite_href, body)
            body = body.replace('<table>', '<div class="tablewrap"><table>').replace('</table>', '</table></div>')
            body = '<details><summary>Navegação nesta página</summary>' + renderer.toc + '</details>' + body
        else:
            title = "Verificação da modelagem"
            body = f'<h1>{title}</h1><p>São apresentados os valores registrados na verificação local do modelo. Esta evidência não substitui a execução na nuvem.</p>' + json_view(json.loads(text))
        output = source.with_suffix(".html")
        output.write_text(page(title, body, source.relative_to(ROOT).as_posix(), diagram), encoding="utf-8")
        entries.append((title, output.name))
    body = '<h1>Documentação do projeto</h1><p>Foram disponibilizadas versões HTML para leitura no navegador, com tabelas, imagens, código e navegação entre documentos.</p><ol>'
    body += ''.join(f'<li><a href="{SITE}docs/{quote(name)}">{html.escape(title)}</a></li>' for title, name in entries)
    body += '</ol><p class="note">Nos documentos com diagramas, a renderização gráfica é realizada pelo Mermaid. Sua definição textual também é disponibilizada para consulta.</p>'
    (DOCS / "index.html").write_text(page("Documentação", body), encoding="utf-8")
    print(f"Gerados {len(entries)} documentos HTML e um índice.")


if __name__ == "__main__":
    main()
