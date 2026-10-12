import re
import subprocess
import os

def md_to_html(md_text, title):
    # Basic markdown to clean HTML conversion
    lines = md_text.split("\n")
    html_lines = []
    in_code = False
    code_block = []
    in_table = False
    table_lines = []
    in_list = False

    html_lines.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292e;
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
}}
h1 {{
    color: #1a365d;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 8px;
    margin-top: 24px;
}}
h2 {{
    color: #2b6cb0;
    border-bottom: 1px solid #edf2f7;
    padding-bottom: 6px;
    margin-top: 24px;
}}
h3 {{
    color: #2d3748;
    margin-top: 20px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
}}
th, td {{
    border: 1px solid #cbd5e0;
    padding: 8px 12px;
    text-align: left;
}}
th {{
    background-color: #f7fafc;
    font-weight: bold;
}}
pre {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    font-family: "Courier New", Courier, monospace;
    font-size: 13px;
}}
code {{
    background-color: #edf2f7;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: "Courier New", Courier, monospace;
    font-size: 13px;
}}
blockquote {{
    border-left: 4px solid #4299e1;
    margin: 0;
    padding-left: 16px;
    color: #4a5568;
}}
ul, ol {{
    padding-left: 24px;
}}
li {{
    margin-bottom: 4px;
}}
hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 24px 0;
}}
</style>
</head>
<body>
""")

    def process_inline(text):
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    def flush_table(t_lines):
        if not t_lines:
            return ""
        out = ["<table>"]
        # Header
        headers = [c.strip() for c in t_lines[0].strip("|").split("|")]
        out.append("<thead><tr>" + "".join(f"<th>{process_inline(h)}</th>" for h in headers) + "</tr></thead>")
        out.append("<tbody>")
        for row in t_lines[2:]:  # skip divider
            cols = [c.strip() for c in row.strip("|").split("|")]
            out.append("<tr>" + "".join(f"<td>{process_inline(c)}</td>" for c in cols) + "</tr>")
        out.append("</tbody></table>")
        return "\n".join(out)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block
        if line.startswith("```"):
            if in_code:
                in_code = False
                escaped = "\n".join(code_block).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_lines.append(f"<pre><code>{escaped}</code></pre>")
                code_block = []
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_block.append(line)
            i += 1
            continue

        # Table
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if not in_table:
                in_table = True
                table_lines = [line]
            else:
                table_lines.append(line)
            i += 1
            continue
        elif in_table:
            html_lines.append(flush_table(table_lines))
            table_lines = []
            in_table = False

        # Lists
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            if not in_list:
                in_list = True
                html_lines.append("<ul>")
            html_lines.append(f"<li>{process_inline(line.strip()[2:])}</li>")
            i += 1
            continue
        elif in_list and line.strip() != "":
            # Check if continuation or end of list
            if not (line.strip().startswith("- ") or line.strip().startswith("* ") or line.strip().startswith("1. ")):
                in_list = False
                html_lines.append("</ul>")

        if in_list and line.strip() == "":
            in_list = False
            html_lines.append("</ul>")

        # Headers
        if line.startswith("# "):
            html_lines.append(f"<h1>{process_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{process_inline(line[3:])}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{process_inline(line[4:])}</h3>")
        elif line.startswith("#### "):
            html_lines.append(f"<h4>{process_inline(line[5:])}</h4>")
        elif line.strip() == "---":
            html_lines.append("<hr>")
        elif line.strip() == "":
            pass
        else:
            html_lines.append(f"<p>{process_inline(line)}</p>")

        i += 1

    if in_table:
        html_lines.append(flush_table(table_lines))
    if in_list:
        html_lines.append("</ul>")

    html_lines.append("</body></html>")
    return "\n".join(html_lines)


def convert_doc(md_path, base_name):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = md_to_html(md_content, base_name)
    html_path = f"{base_name}.html"
    docx_path = f"{base_name}.docx"
    doc_path = f"{base_name}.doc"
    pdf_path = f"{base_name}.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Convert to docx
    subprocess.run(["textutil", "-convert", "docx", html_path, "-output", docx_path], check=True)
    print(f"Generated: {docx_path}")

    # Convert to doc
    subprocess.run(["textutil", "-convert", "doc", html_path, "-output", doc_path], check=True)
    print(f"Generated: {doc_path}")

    # Convert to pdf via cupsfilter
    with open(pdf_path, "wb") as pf:
        subprocess.run(["/usr/sbin/cupsfilter", md_path], stdout=pf, stderr=subprocess.DEVNULL)
    print(f"Generated: {pdf_path}")

    # Cleanup intermediate HTML
    if os.path.exists(html_path):
        os.remove(html_path)

if __name__ == "__main__":
    convert_doc("DEVELOPMENT_TECHNICAL_DOCUMENT.md", "Technical_Document_1_Application_Development")
    convert_doc("DOCKER_JENKINS_TECHNICAL_DOCUMENT.md", "Technical_Document_2_Docker_and_Jenkins")
    print("All documents generated successfully!")
