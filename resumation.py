import argparse
import json
import logging
import re
import time
from json import JSONDecodeError
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from shutil import copy
import webbrowser

ENCODING = 'utf-8'


def _proc_url(url, index=0):
    """
    Custom filter to use with Jinja to get different components of a given URL

    :param url: the URL to process
    :param index: 0 if the base URL is wanted, 1 if the location (i.e., /foo ) is wanted
    :return: the wanted component of the URL
    """
    base_url = re.sub(r'^(?:https?://)?(?:www\.)?', '', url)
    location = re.match(r'^.*/(.*)/?$', url)
    if location:
        location = location.group(1)
    else:
        location = base_url
    result = (base_url, location)

    if index > 1:
        raise NotImplementedError

    return result[index]


def main():
    """
    Main entry point into this script

    :return: None
    """
    # General housekeeping/config
    args = parse_args()
    resume_data = None
    fail_read = False
    jenv = Environment(loader=FileSystemLoader('base', encoding=ENCODING))
    jenv.filters['proc_url'] = _proc_url

    # Read the JSON input and try sub it into the base template
    try:
        with open(args.json, encoding=ENCODING) as json_fp:
            resume_data = json.load(json_fp)
    except (FileNotFoundError, JSONDecodeError) as e:
        fail_read = e
    if fail_read or not resume_data:
        logging.error(f'Could not read json file at {args.json.resolve()}')
        logging.debug(f'{fail_read}')
        exit(1)
    template = jenv.get_template('base.html')
    render = template.render(resume_data)

    # Output the generated resume files
    out_dir = Path('out')
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        Path('out/res/css').mkdir(parents=True, exist_ok=True)
        Path('out/res/js').mkdir(parents=True, exist_ok=True)
        with open('out/resume.html', mode='w', encoding=ENCODING) as out:
            out.write(render)
        if not Path('out/res/css/resume.css').exists() or args.overwrite:
            copy('base/base.css', 'out/res/css/resume.css')
    except IOError as e:
        logging.error(f'Could not write to destination {out_dir.resolve()}: {e}')
        exit(1)

    # Ask the user if they want to open the generated page in their web browser so as to defer PDF generation to that
    user_prompt = input('Would you like to open your browser now? (y/N): ')
    while user_prompt and user_prompt.lower()[0] not in ('y', 'n'):
        user_prompt = input('Would you like to open your browser now to print to a .PDF? (y/N): ')
    js_template = jenv.get_template('base.js')
    if user_prompt and user_prompt.lower()[0] == 'y':
        js_template = jenv.get_template('base.js')
        js = js_template.render({'should_print': 'window.print()'})
        with open('out/res/js/resume.js', mode='w', encoding=ENCODING) as out_js:
            out_js.write(js)
        webbrowser.open(f'file://{Path("out/resume.html").resolve()}')
        # Throw in a delay to have the browser window that opens cache this temporary version before overwriting it
        time.sleep(5)

    # Write the final resume.js to the output directory
    with open('out/res/js/resume.js', mode='w', encoding=ENCODING) as out_js:
        js = js_template.render({'should_print': ''})
        out_js.write(js)

    print('Resume generation was successful. If you did not elect to export a .PDF, please use your browser')
    exit(0)


def parse_args():
    """
    Parse CLI arguments, if any

    :return: parsed argument namespace
    """
    parser = argparse.ArgumentParser(description='Generate a stylized HTML/PDF resume from JSON')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--json', type=Path, default=Path('resume.json'), help='path to resume JSON data')
    parser.add_argument('--overwrite', action='store_true', help='overwrite existing files in output directory')

    args = parser.parse_args()
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%H:%M:%S', level=log_level)
    return parser.parse_args()


if __name__ == '__main__':
    main()
