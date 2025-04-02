from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
import xlwt

from insb_port import settings
from main_website.models import Toolkit

class BudgetPDF:

    def create_pdf(sc_ag_primary, title, cost_data, revenue_data):
        # Create a BytesIO buffer to hold the PDF data
        buffer = BytesIO()

        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        branch_logo = Toolkit.objects.get(title=BudgetPDF.get_sc_ag_logo_name(1)).picture
        branch_logo_path = settings.MEDIA_ROOT+str(branch_logo)
        sc_ag_logo_path = None

        if sc_ag_primary == 1:
            # Watermark Logo (Behind the Text)
            c.setFillAlpha(0.1)  # Make watermark logo faint
            c.drawImage(branch_logo_path, 60, 230, width=470, height=470, mask='auto')
        else:
            sc_ag_logo = Toolkit.objects.get(title=BudgetPDF.get_sc_ag_logo_name(sc_ag_primary)).picture
            sc_ag_logo_path = settings.MEDIA_ROOT+str(sc_ag_logo)
            # Watermark Logo (Behind the Text)
            c.setFillAlpha(0.1)  # Make watermark logo faint
            c.drawImage(sc_ag_logo_path, 70, 230, width=470, height=470, mask='auto')
        
        # Top Left Logo
        c.setFillAlpha(1)  # Ensure logos are fully opaque
        c.drawImage(branch_logo_path, 50, height - 70, width=40, height=40, mask='auto')

        if sc_ag_primary != 1:
            # Top Right Logo
            c.drawImage(sc_ag_logo_path, width - 90, height - 70, width=40, height=40, mask='auto')

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 90, title)
        c.setTitle(title)

        # Cost Breakdown (First)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 130, "Cost Breakdown")

        cost_header = {-1 : ["ITEM", "QUANTITY", "PRICE PER UNIT (BDT)", "TOTAL PRICE (BDT)"]}
        cost_header.update(cost_data)
        # Draw cost table and get final Y position
        new_y = BudgetPDF.draw_table(c, cost_header, x=50, y=height - 160, col_widths=[180, 80, 120, 120])

        # Revenue Breakdown (Positioned Below Cost Breakdown)
        c.setFont("Helvetica-Bold", 12)
        revenue_y = new_y - 50  # Provide extra space
        c.drawString(50, revenue_y, "Total Revenue")

        revenue_header = {-1 : ["Revenue Type", "Quantity", "Revenue / Unit (BDT)", "Revenue Generated (BDT)"]}
        revenue_header.update(revenue_data)
        BudgetPDF.draw_table(c, revenue_header, x=50, y=revenue_y - 30, col_widths=[180, 80, 120, 120])

        # Signatures
        c.line(50, 100, 250, 100)
        c.line(300, 100, 500, 100)

        c.setFont("Times-Roman", 12)
        c.drawString(50, 85, "Dr. Fariah Mahzabeen")
        c.drawString(50, 70, "Assistant Professor")
        c.drawString(50, 55, "Dept. of ECE, North South University")
        c.drawString(50, 40, "Faculty Advisor, IEEE NSU SB WIE AG")

        c.drawString(300, 85, "Shaira Imtiaz Aurchi")
        c.drawString(300, 70, "Chair, IEEE NSU SB WIE AG")
        c.drawString(300, 55, "North South University")

        # Save the PDF
        c.save()

        # Move buffer cursor to the beginning
        buffer.seek(0)

        return buffer

    def draw_table(canvas, data, x, y, col_widths):

        styles = getSampleStyleSheet()   
        
        # Convert long text cells to Paragraph objects for wrapping
        wrapped_data = []
        for i, row in enumerate(data.values()):
            if i == 0:
                # Bold style for the first row
                style = ParagraphStyle(name="Header", parent=styles["Normal"])
                style.fontName = 'Helvetica-Bold'
                # style.textColor = colors.black
                # style.alignment = 1

            else:
                # Default style for normal text
                style = ParagraphStyle(name="Normal", parent=styles["Normal"])
                style.fontName = 'Helvetica'
                # style.textColor = colors.black

            wrapped_row = [Paragraph(str(cell), style) for cell in row]
            wrapped_data.append(wrapped_row)

        table = Table(wrapped_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        table.wrapOn(canvas, x, y)
        table.drawOn(canvas, x, y - (len(data) * 20))

        # Return new Y position after drawing the table
        return y - (len(data) * 20) - 20  # Adding extra spacing

    def export_budget_sheet_to_excel(sc_ag_primary, title, cost_data, revenue_data):

        # Create a workbook and add a worksheet
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Budget Sheet")

        # Define styles
        header_style = xlwt.easyxf(
            "font: bold on; align: horiz center, vert center; borders: bottom medium"
        )
        subheader_style = xlwt.easyxf("font: bold on; align: horiz left")
        data_style = xlwt.easyxf(
            "align: wrap on, horiz center, vert center; borders: left thin, right thin, top thin, bottom thin"
        )
        
        # Set column widths
        ws.col(0).width = 7500  # "ITEM" column (wider for better readability)
        ws.col(1).width = 4000  # "QUANTITY" column
        ws.col(2).width = 6000  # "PRICE PER UNIT (BDT)" column
        ws.col(3).width = 6000  # "TOTAL PRICE (BDT)" column

        # Write sheet title
        ws.write_merge(0, 0, 0, 3, title, header_style)

        # Section: Revenue Breakdown
        ws.write(2, 0, "Cost Breakdown", subheader_style)
        ws.write(3, 0, "ITEM", header_style)
        ws.write(3, 1, "QUANTITY", header_style)
        ws.write(3, 2, "PRICE PER UNIT (BDT)", header_style)
        ws.write(3, 3, "TOTAL PRICE (BDT)", header_style)

        row = 4
        for data in cost_data.values():
            ws.write(row, 0, data[0], data_style)
            ws.write(row, 1, data[1], data_style)
            ws.write(row, 2, data[2], data_style)
            ws.write(row, 3, data[3], data_style)
            row += 1
        
        ws.write(row, 2, "Total Cost:", subheader_style)
        # ws.write(row, 3, budget_data.get("total_revenue", 0.0), data_style)

        # Section: Cost Breakdown
        row += 2
        ws.write(row, 0, "Revenue Breakdown", subheader_style)
        row += 1
        ws.write(row, 0, "Revenue Type", header_style)
        ws.write(row, 1, "QUANTITY", header_style)
        ws.write(row, 2, "Revenue / Unit (BDT)", header_style)
        ws.write(row, 3, "Revenue Generated (BDT)", header_style)

        row += 1
        for data in revenue_data.values():
            ws.write(row, 0, data[0], data_style)
            ws.write(row, 1, data[1], data_style)
            ws.write(row, 2, data[2], data_style)
            ws.write(row, 3, data[3], data_style)
            row += 1
        
        ws.write(row, 2, "Total Revenue:", subheader_style)
        # ws.write(row, 3, budget_data.get("total_cost", 0.0), data_style)

        # Approval Section
        row += 3
        ws.write(row, 0, "Approved by:", subheader_style)
        # ws.write(row + 1, 0, budget_data.get("approval", ""), data_style)
        
        # Save the file to a buffer instead of disk
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)  # Move the cursor to the beginning of the buffer

        return buffer
    
    def get_sc_ag_logo_name(primary):
        if primary == 1:
            return 'IEEE NSU SB Logo'
        elif primary == 2:
            return 'IEEE NSU PES SBC Logo'
        elif primary == 3:
            return 'IEEE NSU RAS SBC Logo'
        elif primary == 4:
            return 'IEEE NSU IAS SBC Logo'
        elif primary == 5:
            return 'IEEE NSU SB WIE AG Logo'