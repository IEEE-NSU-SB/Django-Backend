from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

class BudgetPDF:

    def create_pdf(title, cost_data, revenue_data):
        # Create a BytesIO buffer to hold the PDF data
        buffer = BytesIO()

        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, title)
        c.setTitle(title)

        # Cost Breakdown (First)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 90, "Cost Breakdown")

        cost_header = {-1 : ["ITEM", "QUANTITY", "PRICE PER UNIT (BDT)", "TOTAL PRICE (BDT)"]}
        cost_header.update(cost_data)
        # Draw cost table and get final Y position
        new_y = BudgetPDF.draw_table(c, cost_header, x=50, y=height - 120, col_widths=[180, 80, 120, 120])

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

        c.setFont("Helvetica", 10)
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
        styleN = styles["Normal"]

        # Convert long text cells to Paragraph objects for wrapping
        wrapped_data = [[Paragraph(str(cell), styleN) for cell in columns] for row, columns in data.items()]

        table = Table(wrapped_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        table.wrapOn(canvas, x, y)
        table.drawOn(canvas, x, y - (len(data) * 20))

        # Return new Y position after drawing the table
        return y - (len(data) * 20) - 20  # Adding extra spacing
