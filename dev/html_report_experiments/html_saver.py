import json


def read_tsv_as_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip().split('\t') for line in f if line.strip()]
    return lines


def main():
    with open('report_template.html', 'r', encoding='utf-8') as f:
        html_template = f.read()
    with open('report.css', 'r', encoding='utf-8') as f:
        style_css = f.read()
    with open('build_report.js', 'r', encoding='utf-8') as f:
        script_js = f.read()

    data_json = json.dumps(read_tsv_as_json('report_data2.tsv'))

    html_filled = html_template.replace('{{ style_css }}', style_css)\
                               .replace('{{ script_js }}', script_js)\
                               .replace('{{ report_json }}', data_json)

    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_filled)


if __name__ == '__main__':
    main()