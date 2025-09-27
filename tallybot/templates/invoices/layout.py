"""Invoice layout."""
import enum
import datetime
import decimal as d

from reportlab import platypus as p
from reportlab.rl_config import defaultPageSize
from reportlab.lib import colors
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import schema


pdfmetrics.registerFont(
    TTFont("Font", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(
    TTFont("Font-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"))

c = d.getcontext()
c.traps[d.FloatOperation] = True

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]

# Define styles used in invoice document
DEFAULT_FONT = "Font"
DEFAULT_FONT_BOLD = "Font-Bold"
COLOR_GREY = colors.Color(0.9, 0.9, 0.9)


def get_style_book():
    """Prepare all styles used for invoice document."""
    style_book = StyleSheet1()
    style_book.add(ParagraphStyle(
        "default",
        fontName=DEFAULT_FONT,
    ))
    style_book.add(ParagraphStyle(
        "default-bold",
        fontName=DEFAULT_FONT_BOLD,
    ))
    style_book.add(ParagraphStyle(
        "HeaderLeft",
        style_book["default"],
        alignment=TA_LEFT,
    ))
    style_book.add(ParagraphStyle(
        "HeaderLeftBold",
        style_book["default-bold"],
        alignment=TA_LEFT,
    ))
    style_book.add(ParagraphStyle(
        "HeaderRight",
        style_book["default"],
        alignment=TA_RIGHT,
    ))
    style_book.add(ParagraphStyle(
        "HeaderRightBold",
        style_book["default-bold"],
        alignment=TA_RIGHT,
    ))
    style_book.add(ParagraphStyle(
        "HeaderTitle",
        style_book["default-bold"],
        alignment=TA_CENTER,
        fontSize=12,
    ))
    style_book.add(ParagraphStyle(
        "TableHeader",
        style_book["default-bold"],
    ))
    style_book.add(ParagraphStyle(
        "TableHeaderCenter",
        style_book["TableHeader"],
        alignment=TA_CENTER,
    ))
    style_book.add(ParagraphStyle(
        "Table",
        style_book["default"],
    ))
    style_book.add(ParagraphStyle(
        "TableCenter",
        style_book["Table"],
        alignment=TA_CENTER,
    ))
    style_book.add(ParagraphStyle(
        "Footer",
        style_book["default"],
        fontSize=6,
    ))
    return style_book


STYLES = get_style_book()


class FirstPage(int, enum.Enum):
    """First page of the invoice.

    First page contains 4 frames:
    - Biller info & Payer info
    - Invoice header
    - Invoice table
    - Invoice payment info

    +----------+      +-----------+
    |          |      |           |
    |  BILLER  |      |  HEADER   |
    |          |      |           |
    +----------+      +-----------+

    +-----------------------------+
    |                             |
    |           TABLE             |
    |                             |
    +-----------------------------+

    +---------------+
    |     PAYTO     |
    +---------------+

    +----------FOOTER-------------+
    """

    HEIGHT = defaultPageSize[1]
    WIDTH = defaultPageSize[0]
    TOP_MARGIN = 60
    LEFT_MARGIN = 30
    RIGHT_MARGIN = 30
    BOTTOM_MARGIN = 5


class Biller(int, enum.Enum):
    """Positions of payer and biller frame.

    +----------+   +-----------+
    |  BILLER  |   |           |
    +----------+   |  DETAILS  |
                   |           |
                   |           |
                   +-----------+
    +----------+   +-----------+
    |  PAYER   |   |           |
    +----------+   |  DETAILS  |
                   |           |
                   |           |
                   +-----------+
    """

    TOP_MARGIN = FirstPage.TOP_MARGIN + 20
    LEFT_MARGIN = FirstPage.LEFT_MARGIN + 0
    DETAILS_HEIGHT = 100
    DETAILS_WIDTH = 170
    TITLE_HEIGHT = 30
    TITLE_WIDTH = 55
    SPACE = 10


def get_biller_frame():
    """Return biller frame."""
    return frame_left_corner(
        Biller.LEFT_MARGIN,
        Biller.TOP_MARGIN,
        Biller.TITLE_WIDTH + Biller.DETAILS_WIDTH,
        2 * Biller.DETAILS_HEIGHT + Biller.SPACE
    )


def create_biller_info(biller_text, payer_text):
    """Create a biller and payer info.

    Args:
        biller_text: iterator of strings
        payer_text: iterator of strings

    Return list of shapes(flowables) that should be added in biller frame.
    """
    b_head = p.Paragraph("From:", STYLES["HeaderLeftBold"])
    p_head = p.Paragraph("Bill to:", STYLES["HeaderLeftBold"])
    biller = p.Paragraph("<br/>".join(biller_text), STYLES["default"])
    payer = p.Paragraph("<br/>".join(payer_text), STYLES["default"])
    return [p.Table(
        [[b_head, biller], [p.Spacer(1, 0), p.Spacer(1, 0)], [p_head, payer]],
        colWidths=[Biller.TITLE_WIDTH, Biller.DETAILS_WIDTH],
        rowHeights=[
            Biller.DETAILS_HEIGHT, Biller.SPACE, Biller.DETAILS_HEIGHT],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
    )]


class Header(int, enum.Enum):
    """Invoice header frame positions.

    Invoice header is divided into 3 columns:
     +-----------------------------+
     |           TITLE             |
     +-----------------------------+

      +-----------+ +-------------+
      |           | |             |
      | LEFT_COL  | |  RIGHT_COL  |
      |           | |             |
      |           | |             |
      +-----------+ +-------------+
    """

    TOP_MARGIN = FirstPage.TOP_MARGIN + 30
    RIGHT_MARGIN = FirstPage.RIGHT_MARGIN + 0
    HEIGHT = 100
    WIDTH = 200
    TITLE_HEIGHT = 30
    SPACE_AFTER_TITLE = 10
    RIGHT_COL_WIDTH = 100
    MARGIN_COL = 10


def get_invoice_header_frame():
    """Return invoice header frame."""
    return frame_right_corner(
        Header.RIGHT_MARGIN,
        Header.TOP_MARGIN,
        Header.WIDTH,
        Header.HEIGHT)


def create_invoice_heading(i: schema.InvoiceData):
    """Create an invoice heading.

    Args:
       values: list of strings

    Invoice header contains information:
    - Invoice number
    - Invoice date
    - Invoice due date
    - Invoice total amount
    - Invoice total due

    Return a list of shapes(flowables) that should be added in header frame.
    """
    date = datetime.date.today()
    due_date = date + datetime.timedelta(days=i.terms)
    values = [
        i.no,
        date.strftime("%d %b %Y"),
        due_date.strftime("%d %b %Y"),
        i.currency + ' ' + i.total,
        i.currency + ' ' + i.total]
    shapes = []
    title = p.Paragraph("I N V O I C E", STYLES["HeaderTitle"])
    bold_ind = [2, 4]
    headings = [
        "INVOICE #", "INVOICE DATE", "DUE DATE", "TOTAL AMOUNT", "TOTAL DUE"]
    left_col = apply_style_to_list(
        headings, STYLES["HeaderLeft"], STYLES["HeaderLeftBold"], bold_ind)
    right_col = apply_style_to_list(
        values, STYLES["HeaderRight"], STYLES["HeaderRightBold"], bold_ind)
    shapes.append(p.Table(
        [[title]],
        colWidths=[Header.WIDTH],
        rowHeights=[Header.TITLE_HEIGHT],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    ))
    shapes.append(p.Spacer(0, Header.SPACE_AFTER_TITLE))
    row_t_height =\
        Header.HEIGHT\
        - Header.TITLE_HEIGHT\
        - Header.SPACE_AFTER_TITLE
    shapes.append(p.Table(
        list(zip(left_col, right_col)),
        colWidths=[
            Header.WIDTH - Header.RIGHT_COL_WIDTH - 2*Header.MARGIN_COL,
            Header.RIGHT_COL_WIDTH
        ],
        rowHeights=row_t_height/len(left_col),
        style=[
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
    ))
    return shapes


class Table(int, enum.Enum):
    """Invoice table frame positions.

    +-------------------------------+
    | MEMO    | HOURS | RATE | TOTAL|
    +-------------------------------+
    |         |       |      |      |
    |         |       |      |      |
    |         |       |      |      |
    +-------------------------------+
    """

    TOP_MARGIN = Biller.TOP_MARGIN + 2 * Biller.DETAILS_HEIGHT + Biller.SPACE
    SPACE_BEFORE = 70
    LEFT_MARGIN = FirstPage.LEFT_MARGIN + 0
    HEIGHT = 300
    WIDTH = FirstPage.WIDTH - FirstPage.LEFT_MARGIN - FirstPage.RIGHT_MARGIN
    HOURS_WIDTH = 50
    RATE_WIDTH = 50
    TOTAL_WIDTH = 65


def get_table_frame():
    """Return invoice table frame."""
    return frame_left_corner(
        Table.LEFT_MARGIN,
        Table.TOP_MARGIN + Table.SPACE_BEFORE,
        Table.WIDTH,
        Table.HEIGHT)


def create_table(rows, rate, total):
    """Create an invoice table."""
    style = [
        ('GRID', (0, 0), (-1, -1), 0.1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    cells = [[
        p.Paragraph("DESCRIPTION", STYLES["TableHeader"]),
        p.Paragraph("HOURS", STYLES["TableHeaderCenter"]),
        p.Paragraph("RATE", STYLES["TableHeaderCenter"]),
        p.Paragraph("TOTAL", STYLES["TableHeaderCenter"]),
    ]]
    for item in rows:
        cells.append([
            p.Paragraph(item.description, STYLES["Table"]),
            p.Paragraph(str(item.hours), STYLES["TableCenter"]),
            p.Paragraph(str(rate), STYLES["TableCenter"]),
            p.Paragraph(str(item.total), STYLES["TableCenter"]),
        ])
    cells.append([
        p.Paragraph("TOTAL", STYLES["Table"]),
        p.Paragraph("", STYLES["TableCenter"]),
        p.Paragraph("", STYLES["TableCenter"]),
        p.Paragraph(str(total), STYLES["TableCenter"]),
    ])
    return [p.Table(
        cells,
        style=style,
        colWidths=[
            Table.WIDTH
            - Table.HOURS_WIDTH
            - Table.RATE_WIDTH
            - Table.TOTAL_WIDTH,
            Table.HOURS_WIDTH,
            Table.RATE_WIDTH,
            Table.TOTAL_WIDTH],
        rowHeights=25)]


class PayInfo(int, enum.Enum):
    """Invoice pay info frame positions.

    +--------------------------------+
    |           PAY TO               |
    +--------+-----------------------+
    |        |                       |
    |        |                       |
    | LABEL  |  INFORMATION          |
    |        |                       |
    |        |                       |
    |        |                       |
    +--------+-----------------------+
    """

    BOTTOM_MARGIN = 70
    LEFT_MARGIN = FirstPage.LEFT_MARGIN + 0
    TITLE_HEIGHT = 40
    ROW_HEIGHT = 20
    WIDTH = 250
    LABEL_WIDTH = 40


def get_pay_info_frame():
    """Return invoice pay info frame."""
    return blank_frame(
        PayInfo.LEFT_MARGIN,
        PayInfo.BOTTOM_MARGIN,
        PayInfo.WIDTH,
        3*PayInfo.ROW_HEIGHT + PayInfo.TITLE_HEIGHT)


def create_pay_info(bank: schema.BankInfo):
    """Create an invoice pay info frame."""
    style = [
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]
    cells = [[
        p.Paragraph("Bank:", STYLES["Table"]),
        p.Paragraph(bank.name, STYLES["Table"]),
    ]]
    cells.append([
        p.Paragraph("IBAN:", STYLES["Table"]),
        p.Paragraph(bank.iban, STYLES["Table"]),
    ])
    cells.append([
        p.Paragraph("BIC:", STYLES["Table"]),
        p.Paragraph(bank.bic, STYLES["Table"]),
    ])
    return [
        p.Table(
            [[p.Paragraph("PAY BY BANK TRANSFER", STYLES["TableHeader"])]],
            style=[
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_GREY)],
            colWidths=PayInfo.WIDTH,
            rowHeights=PayInfo.TITLE_HEIGHT),
        p.Table(
            cells,
            style=style,
            colWidths=[
                PayInfo.LABEL_WIDTH,
                PayInfo.WIDTH - PayInfo.LABEL_WIDTH],
            rowHeights=PayInfo.ROW_HEIGHT)
    ]


def get_footer_frame():
    """Return invoice footer frame."""
    return blank_frame(
        FirstPage.LEFT_MARGIN,
        FirstPage.BOTTOM_MARGIN,
        FirstPage.WIDTH - FirstPage.LEFT_MARGIN - FirstPage.RIGHT_MARGIN,
        15)


def create_footer():
    """Add footer with thanks to."""
    msg = "*This invoice was generated automatically using "
    msg += "open source software (Python, ReportLab)"
    return [p.Paragraph(
        msg,
        STYLES["Footer"],
    )]


def apply_style_to_list(lst, n_style, b_style, b_rows):
    """Apply style.

    Args:
        lst: list of strings
        n_style: normal Paragraph style
        b_style: bold style
        b_rows: indexes to apply bold style
        kwargs: additional arguments to ParagraphStyle
    """
    applied_style = []
    for i, item in enumerate(lst):
        if i in b_rows:
            applied_style.append(p.Paragraph(item, style=b_style))
        else:
            applied_style.append(p.Paragraph(item, style=n_style))
    return applied_style


def blank_frame(*args, **kwargs):
    """Create a blank frame.

    Remove default padding from the frame.
    """
    for pad in ["leftPadding", "rightPadding", "topPadding", "bottomPadding"]:
        if pad not in kwargs:
            kwargs[pad] = 0
    return p.Frame(*args, **kwargs)


def frame_left_corner(x, y, width, height):
    """Create a frame in top left corner.

    Args:
        x: margin from the left
        y: margin from the top
        width: width of the frame
        height: height of the frame
    """
    return blank_frame(x, PAGE_HEIGHT - y - height, width, height)


def frame_right_corner(x, y, width, height):
    """Create a frame in top right corner.

    Args:
        x: margin from the right
        y: margin from the top
        width: width of the frame
        height: height of the frame
    """
    return blank_frame(
        PAGE_WIDTH - x - width,
        PAGE_HEIGHT - y - height,
        width,
        height)


def get_invoice_template(bytes_io):
    """Generate an invoice document template with empty frames.

    Args:
        bytes_io: BytesIO object to write the binary document to
    """
    template = p.PageTemplate(
        frames=[
            get_biller_frame(),
            get_invoice_header_frame(),
            get_table_frame(),
            get_pay_info_frame(),
            get_footer_frame(),],
    )
    doc = p.BaseDocTemplate(
        bytes_io, pageTemplates=[template])
    return doc


def strnum(num):
    """Return a number with leading zeros."""
    return f"{num:,.2f}"


def write_invoice(bytes_io, inv: schema.InvoiceData):
    """Write invoice to a file.

    Args:
        bytes_io: BytesIO object to write the binary document to
    """
    total = d.Decimal(0)
    for item in inv.rows:
        total += d.Decimal(item.hours) * d.Decimal(inv.rate)
        item.total = strnum(d.Decimal(item.hours) * d.Decimal(inv.rate))
    inv.total = strnum(total)
    elements = []
    for item in [
            create_biller_info(inv.biller, inv.payer),
            create_invoice_heading(inv),
            create_table(
                inv.rows,
                rate=strnum(d.Decimal(inv.rate)),
                total=strnum(total)),
            create_pay_info(inv.biller_bank),
            create_footer()]:
        elements += item
        elements.append(p.FrameBreak())
    doc = get_invoice_template(bytes_io)
    doc.author = "Juris Kaminskis"
    doc.creator = "Juris Kaminskis"
    doc.title = "Invoice"
    doc.subject = "Invoice"
    doc.build(elements)


if __name__ == "__main__":
    """Create an invoice document 'invoice.pdf' in the current directory."""
    from io import BytesIO
    data = schema.InvoiceData(
        "EXN987",
        [
            "ICO Reklamation",
            "Forest street 21",
            "Alembotan",
        ],
        schema.BankInfo("Bank name", "Bank account", "Bank code"),
        ["John Doe", "New York", " USA+1 123456789"],
        (
            schema.InvoiceRow("Some meaningfull text on the invoice", "21"),
            schema.InvoiceRow("Other services", "20")),
        40,
        "50.1",
        "EUR"
    )
    # Write pdf out
    writer = BytesIO()
    write_invoice(writer, data)
    with open("invoice.pdf", "wb") as f:
        f.write(writer.getvalue())
