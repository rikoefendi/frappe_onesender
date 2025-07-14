import copy
import cssutils
import asyncio
import frappe


from io import BytesIO
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from typing import Literal
from frappe.utils import cstr, scrub_urls
from werkzeug.wrappers import Response
from frappe.website.serve import get_response_without_exception_handling
from frappe.utils.print_utils import get_print
from frappe.translate import print_language
from frappe.www.printview import validate_print_permission
@frappe.whitelist(allow_guest=True)
def download_pdf(
	doctype: str,
	name: str,
	format=None,
	doc=None,
	no_letterhead=0,
	language=None,
	letterhead=None,
	pdf_generator: Literal["wkhtmltopdf", "chrome"] | None = None,
    filename: str = None
):
    doc = doc or frappe.get_doc(doctype, name)
    validate_print_permission(doc)

    with print_language(language):
        pdf_file = frappe.get_print(
            doctype,
            name,
            format,
            doc=doc,
            as_pdf=True,
            letterhead=letterhead,
            no_letterhead=no_letterhead,
            pdf_generator=pdf_generator,
        )
    filename = filename or name
    frappe.local.response.filename = "{name}.pdf".format(name=filename.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf_file
    frappe.local.response.type = "pdf"

def get_pdf(
        doctype: str,
        name: str,
        format=None,
        doc=None,
        no_letterhead=0,
        language=None,
        letterhead=None,
        pdf_generator: Literal["wkhtmltopdf", "chrome"] | None = None,
    ): 
    with print_language(language):
        pdf_file = frappe.get_print(
            doctype,
            name,
            format,
            doc=doc,
            as_pdf=True,
            letterhead=letterhead,
            no_letterhead=no_letterhead,
            pdf_generator=pdf_generator,
        )
    return pdf_file

@frappe.whitelist(allow_guest=True)
def download_image(
    doctype=None,
	name=None,
	print_format=None,
	style=None,
	doc=None,
	no_letterhead=0,
	letterhead=None,
    filename = None
):
    stream = get_image(
        doctype,
        name,
        print_format,
        style,
        doc,
        no_letterhead,
        letterhead,
    )

    filename = filename or name
    filename = f"{filename.replace(' ', '-').replace('/', '-')}.jpeg"
    response = Response()
    response.headers.add("Content-Disposition", "inline", filename=filename)
    response.data = stream.getvalue()
    response.mimetype = "image/jpg"
    return response

def get_image(
    doctype=None,
	name=None,
	print_format=None,
	style=None,
	doc=None,
	no_letterhead=0,
	letterhead=None
):
    local = frappe.local

    original_form_dict = copy.deepcopy(local.form_dict)
    try:
        local.form_dict.doctype = doctype
        local.form_dict.name = name
        local.form_dict.format = print_format
        local.form_dict.style = style
        local.form_dict.doc = doc
        local.form_dict.no_letterhead = no_letterhead
        local.form_dict.letterhead = letterhead


        response = get_response_without_exception_handling("printview", 200)
        html = str(response.data, "utf-8")
    finally:
        local.form_dict = original_form_dict

    html = scrub_urls(html)
    soup = BeautifulSoup(html, "html5lib")
    options = read_options_from_html(soup)
    options =  get_page_size_doc(options)

    page_width = options.get("page-width")
    page_height = options.get("page-height")
    page_size = options.get("page-size")
    if not page_width or not page_height:
        size = PageSize.get(page_size or "A4")
        page_width = f"{size["width"]}mm"
        page_height = f"{size["height"]}mm"

    for el in soup.select("pre"):
        el["style"] = "white-space: break-spaces; "
    el = soup.select_one(".print-format")

    el["style"] = f"min-height: {page_height}; width: {page_width}"
    return generate_pdf_from_html(str(soup))


def get_page_size_doc(options):
    pdf_page_size = (
		options.get("page-size") or frappe.db.get_single_value("Print Settings", "pdf_page_size") or "A4"
	)

    if pdf_page_size == "Custom":
        options["page-height"] = options.get("page-height") or frappe.db.get_single_value(
            "Print Settings", "pdf_page_height"
        )
        options["page-width"] = options.get("page-width") or frappe.db.get_single_value(
            "Print Settings", "pdf_page_width"
        )
    else:
        options["page-size"] = pdf_page_size
    return options

def generate_pdf_from_html(html_content: str) -> BytesIO:
    async def _inner():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="load")
            

            el = await page.query_selector(".print-format")
            bytes = await el.screenshot(type="jpeg", path=None, quality=100)
            await browser.close()
            return BytesIO(bytes)

    return asyncio.run(_inner())

class PageSize:
	page_sizes = {
		"A10": (26, 37),
		"A1": (594, 841),
		"A0": (841, 1189),
		"A3": (297, 420),
		"A2": (420, 594),
		"A5": (148, 210),
		"A4": (210, 297),
		"A7": (74, 105),
		"A6": (105, 148),
		"A9": (37, 52),
		"A8": (52, 74),
		"B10": (44, 31),
		"B1+": (1020, 720),
		"B4": (353, 250),
		"B5": (250, 176),
		"B6": (176, 125),
		"B7": (125, 88),
		"B0": (1414, 1000),
		"B1": (1000, 707),
		"B2": (707, 500),
		"B3": (500, 353),
		"B2+": (720, 520),
		"B8": (88, 62),
		"B9": (62, 44),
		"C10": (40, 28),
		"C9": (57, 40),
		"C8": (81, 57),
		"C3": (458, 324),
		"C2": (648, 458),
		"C1": (917, 648),
		"C0": (1297, 917),
		"C7": (114, 81),
		"C6": (162, 114),
		"C5": (229, 162),
		"C4": (324, 229),
		"Legal": (216, 356),
		"Junior Legal": (127, 203),
		"Letter": (216, 279),
		"Tabloid": (279, 432),
		"Ledger": (432, 279),
		"ANSI C": (432, 559),
		"ANSI A (letter)": (216, 279),
		"ANSI B (ledger & tabloid)": (279, 432),
		"ANSI E": (864, 1118),
		"ANSI D": (559, 864),
	}

	@classmethod
	def get(cls, name):
		if name in cls.page_sizes:
			width, height = cls.page_sizes[name]
			return {"width": width, "height": height}
		else:
			return None  # Return None if the page size is not found


def read_options_from_html(soup: BeautifulSoup):
    options = {}
    
    valid_styles = get_print_format_styles(soup)
    attrs = (
        "margin-top",
        "margin-bottom",
        "margin-left",
        "margin-right",
        "page-size",
        "header-spacing",
        "orientation",
        "page-width",
        "page-height",
    )
    options |= {style.name: style.value for style in valid_styles if style.name in attrs}
    return options

def get_print_format_styles(soup: BeautifulSoup) -> list[cssutils.css.Property]:
    """
    Extract only the CSS properties directly applied to `.print-format`,
    excluding child/descendant selectors.

    Returns:
        List[cssutils.css.Property]: List of CSS Property objects
    """
    stylesheet = ""
    style_tags = soup.find_all("style")

    # Concatenate all <style> tag contents
    for style_tag in style_tags:
        stylesheet += cstr(style_tag.string)

    # Parse all styles
    parsed_sheet = cssutils.parseString(stylesheet)
    valid_styles = []

    for rule in parsed_sheet:
        if not isinstance(rule, cssutils.css.CSSStyleRule):
            continue

        # Accept selectors that directly target `.print-format`
        # Allow: `.print-format`, `.print-format, p`, `p, .print-format`
        # Reject: `.print-format p`, `.print-format > div`, `.print-format #abc`, etc.
        selectors = [s.strip() for s in rule.selectorText.split(",")]

        for selector in selectors:
            if selector == ".print-format":
                # Accept all properties from this rule
                valid_styles.extend(prop for prop in rule.style)
                break  # one match is enough

    return valid_styles