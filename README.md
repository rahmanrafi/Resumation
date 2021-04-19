# Resumation
### An automated, simple, clean resume generator

## Dependencies
- `>= python 3.6`
- `jinja2`

## Getting Started
Clone or download this repository. If you don't already have `>= python 3.6` set up on your platform, please do that first.

The only dependency required for this to work is jinja2, which can be installed using 
`pip3 install jinja2` or alternatively `python3 -m pip install jinja2`.

## Usage
The main functionality for this tool exists in `resumation.py`. You are required to supply a .json file that provides the data to use
when generating the resume. The expected schema for this .json file can be seen in `resume.schema.json`. Alternatively, 
refer to `resume.json` for an example, which in turn generates [this resume](https://rafirahman.com/resume).

By default, the tool will look for a file called `resume.json` in the current working directory. You can override 
this behavior by providing a different path when running the script, using the `--json <PATH_TO_JSON>` option. 

By default, the tool will not overwrite `./out/res/css/resume.css`. This is primarily done to preserve
any customization(s) that may be done to the stylesheet used for the generated resume page. If you don't care about 
this, you can disable this behavior using the `--overwrite` option.

Generated artifacts will be placed in `./out` relative to the current working directory.

### .PDF Exporting
In order to keep the tool simple, dependency-free, and platform-agnostic, it ***is not*** currently able to export the
generated resume to a .PDF file. 

After generation, the script will prompt you if you want to open `resume.html` that was generated in your default
browser. If you choose to do so, you can use your browser's "print to PDF" functionality to export the resume 
as a .PDF file (you may however need to play around with the print margins to get the layout the way you want it however).