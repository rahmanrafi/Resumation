import argparse
import json
import re
import time
import webbrowser
import logging
import jinja2.exceptions
try:
    import toml
    from toml import TomlDecodeError
    HAVE_TOML = True
except ImportError as e:
    HAVE_TOML = False
    IMP_LOG_MSG = 'toml package not found. If toml input is desired, please install it ' \
                  'from https://pypi.org/project/toml or using `pip install toml`'
from json import JSONDecodeError
from pathlib import Path
try:
    from jinja2 import Environment, FileSystemLoader
    HAVE_JINJA = True
except ImportError:
    HAVE_JINJA = False
    IMP_LOG_MSG = 'Required package module not found. Please install it from ' \
                  'https://pypi.org/project/Jinja2 or by using `pip install jinja2'
from shutil import copy

ENCODING = 'utf-8'


def _proc_url(url, index=0):
    """
    Custom filter to use with Jinja to get different components of a given URL

    :param url: the URL to process
    :param index: 0 if the template URL is wanted, 1 if the location (i.e., /foo ) is wanted
    :return: the wanted component of the URL
    """
    base_url = re.match(r'^(?:https?://)?(?:www\.)?([\w.]+)/?', url)
    if base_url:
        base_url = base_url.group(1)
    else:
        return base_url
    location = re.match(r'^(?:https?://)?(?:www\.)?.*\.\w+[/\w]*(/.+)$', url)
    if location:
        location = location.group(1)
    else:
        location = base_url

    result = (base_url, location)

    if index > 1:
        raise NotImplementedError

    return result[index]


def _fill_data(data):
    """
    Fill in missing resume data with sensible defaults, prompting the user where necessary

    :param data: dict of resume data
    :return: fully populated resume data
    """
    REQUIREMENTS = {'info': {'name', 'location', 'pdfFilename'},
                    'education': {'institution', 'location', 'start', 'end'},
                    'work': {'company', 'details', 'location', 'start', 'end'}
                    }

    for key in data.keys():
        curr_section = data[key]
        if key in REQUIREMENTS.keys():
            if key == 'info':
                contact_info = curr_section.get('contact')
                if contact_info:
                    for ci_key in contact_info:
                        curr_ci = contact_info.get(ci_key)
                        if type(curr_ci) == str or (type(curr_ci) == list and len(curr_ci) < 2):
                            icon_class = ci_key.lower()
                            icon = "fas fa-link"

                            is_url = False
                            curr_val = curr_ci if type(curr_ci) == str else curr_ci[0]
                            if re.match(r'^(?:https?://)?(?:www\.)?([\w.]+)/?', curr_val):
                                is_url = True
                            if icon_class == 'github':
                                icon = "fab fa-github"
                            elif icon_class == 'linkedin':
                                icon = "fab fa-linkedin"
                            elif icon_class in ('site', 'website', 'page', 'webpage', 'personal', 'personal page'):
                                icon = "fa fa-globe-americas"
                            elif icon_class in ('email', 'e-mail', 'mail'):
                                icon = "fa fa-at"
                            elif icon_class in ('telephone', 'cell', 'mobile', 'phone', 'tel'):
                                icon = "fas fa-phone"
                            contact_info[ci_key] = [curr_ci if type(curr_ci) == str else curr_ci[0], icon, is_url]

            if type(curr_section) != list:
                items = [curr_section]
            else:
                items = curr_section
            if key == 'work':
                for item in items:
                    work_details = item.get('details', {})
                    for role, details in work_details.items():
                        if type(details) == str:
                            work_details[role] = [details]
            continue

        elif key == 'metadata':
            metadata = data[key]
            name = data["info"]["name"]
            possessive = "'s" if name[-1] != 's' else "'"
            if not metadata.get('pageTitle'):
                metadata['pageTitle'] = f'{name} - Resume'
            if not metadata.get('pageDescription'):
                metadata['pageDescription'] = f"{name}{possessive} academics, work experience, skills, and more."

    gen_opts = data.get('options', {})
    gen_opts['contactInfoColumns'] = gen_opts.get('contactInfoColumns', 2)
    gen_opts['inlineDates'] = gen_opts.get('inlineDates', False)

    data['options'] = gen_opts

    return data


def main():
    """
    Main entry point into this script

    :return: None
    """
    # General housekeeping/config
    args = parse_args()
    resume_data = None

    # Read the input and try sub it into the template template
    fail_read = False
    fail_msg = None
    try:
        with open(args.data, encoding=ENCODING) as data_fp:
            try:
                resume_data = json.load(data_fp)
                logging.debug(f'Parsed resume data: {resume_data}')
            except JSONDecodeError as _e:
                fail_read = True
                fail_msg = f'Data input could not be parsed as a valid JSON. Please check for syntax errors. {_e}'
    except FileNotFoundError:
        fail_read = True
        fail_msg = f'Failed to access file {args.data.resolve()}'
    if fail_read:
        logging.error(f'Unable to continue with resume generation... {fail_msg}')
        exit(1)

    resume_data = _fill_data(resume_data)

    logging.info('Generating resume...')
    jenv = Environment(loader=FileSystemLoader('template', encoding=ENCODING))
    jenv.filters['proc_url'] = _proc_url

    html_template = jenv.get_template('template.html')
    render = None
    try:
        render = html_template.render(resume_data)
        logging.info('Successfully generated resume template!')
    except jinja2.exceptions.TemplateError:
        logging.error('Failed to generate resume template. Please ensure your data input contains '
                      'all required fields. For more information, refer to resume.schema.json')
        exit(1)

    # Output the generated resume files
    out_dir = Path('out')
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        Path('out/res/css').mkdir(parents=True, exist_ok=True)
        Path('out/res/js').mkdir(parents=True, exist_ok=True)
        with open('out/resume.html', mode='w', encoding=ENCODING) as out:
            out.write(render)

        if not Path('out/res/css/resume.css').exists() or args.overwrite:
            css_template = jenv.get_template('template.css')
            try:
                css_render = css_template.render(resume_data['options'])
                with open('out/res/css/resume.css', mode='w', encoding=ENCODING) as out_css:
                    out_css.write(css_render)
                logging.info('Successfully generated resume CSS!')

            except jinja2.exceptions.TemplateError as je:
                logging.debug(je)
                copy('template/template_d.css', 'out/res/css/resume.css')

    except IOError as _e:
        logging.error(f'Could not write to destination {out_dir.resolve()}: {_e}')
        exit(1)

    # Ask the user if they want to open the generated page in their web browser so as to defer PDF generation to that
    # user_prompt = input('Would you like to open your browser now to print to a .PDF? (y/N): ')
    # while user_prompt and user_prompt.lower()[0] not in ('y', 'n'):
    #     user_prompt = input('Would you like to open your browser now to print to a .PDF? (y/N): ')
    # js_template = jenv.get_template('template.js')
    # if user_prompt and user_prompt.lower()[0] == 'y':
    js_template = jenv.get_template('template.js')
    js = js_template.render({'should_print': ''})
    with open('out/res/js/resume.js', mode='w', encoding=ENCODING) as out_js:
        out_js.write(js)
    webbrowser.open(f'file://{Path("out/resume.html").resolve()}')
    # Throw in a delay to have the browser window that opens cache this temporary version before overwriting it
    # time.sleep(2)

    # Write the final resume.js to the output directory
    with open('out/res/js/resume.js', mode='w', encoding=ENCODING) as out_js:
        js = js_template.render({'should_print': ''})
        out_js.write(js)

    print(f'\n'
          f'Your generated resume is now available at {out_dir.joinpath("resume.html").resolve()}.\n'
          f'If you did not elect to export a .PDF, open this file in your web browser and print to a .PDF')
    exit(0)


def parse_args():
    """
    Parse CLI arguments, if any

    :return: parsed argument namespace
    """
    parser = argparse.ArgumentParser(description='Generate a stylized HTML/PDF resume from JSON')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--data', type=Path, default=Path('resume.json'), help='path to resume data (.json/.toml)')
    parser.add_argument('--overwrite', action='store_true', help='overwrite existing files in output directory')

    args = parser.parse_args()
    logging.basicConfig(format='[%(levelname)s] [%(asctime)s]: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not HAVE_JINJA:
        logging.critical(IMP_LOG_MSG)
        exit(1)
    elif not HAVE_TOML:
        logging.warning(IMP_LOG_MSG)

    return parser.parse_args()


if __name__ == '__main__':
    main()
