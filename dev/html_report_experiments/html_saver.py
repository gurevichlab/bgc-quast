import json


def read_tsv_as_json(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip('\r\n').split('\t')

            for j in range(1, len(parts)):  # skip first column (labels)
                if parts[j].strip() == "":
                    parts[j] = "0"

            rows.append(parts)
    return rows



def main():
    with open('report_template.html', 'r', encoding='utf-8') as f:
        html_template = f.read()
    with open('report.css', 'r', encoding='utf-8') as f:
        style_css = f.read()
    with open('build_report.js', 'r', encoding='utf-8') as f:
        script_js = f.read()

    data_json = json.dumps(read_tsv_as_json('report.tsv'))


    html_filled = html_template.replace('{{ style_css }}', style_css)\
                               .replace('{{ script_js }}', script_js)\
                               .replace('{{ report_json }}', data_json)

    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_filled)


if __name__ == '__main__':
    main()