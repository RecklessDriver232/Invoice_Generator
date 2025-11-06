from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import Image
import os
from datetime import datetime


class InvoiceGenerator:
    def __init__(self, output_filename=None, logo_path=None):
        if output_filename is None:
            output_filename = f'invoice_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        self.output_filename = output_filename
        self.logo_path = logo_path
        
        self.doc = SimpleDocTemplate(
            output_filename, 
            pagesize=A4,
            rightMargin=40, 
            leftMargin=40,
            topMargin=70,
            bottomMargin=50
        )
        
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        self.small_style = ParagraphStyle(
            'SmallNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=3
        )
        
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke
        )
        
        self.invoice_label_style = ParagraphStyle(
            'InvoiceLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2C3E50')
        )
        
        self.invoice_value_style = ParagraphStyle(
            'InvoiceValue',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2C3E50')
        )
    
    def _add_header(self, canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4
        bar_height = 12
        bar_y = page_height - 70
        bar_x_start = 40
        bar_x_end = page_width - 40
        canvas_obj.setFillColor(colors.HexColor('#B02415'))
        canvas_obj.rect(bar_x_start, bar_y, bar_x_end - bar_x_start, bar_height, fill=1, stroke=0)
        canvas_obj.restoreState()
    
    def _add_footer(self, canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4
        footer_bar_height = 12
        footer_y = 40
        bar_x_start = 40
        bar_x_end = page_width - 40
        canvas_obj.setFillColor(colors.HexColor('#B02415'))
        canvas_obj.rect(bar_x_start, footer_y, bar_x_end - bar_x_start, footer_bar_height, fill=1, stroke=0)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        footer_text = "© 2025 Fascino. All rights reserved. | Invoice Generated on " + datetime.now().strftime("%d/%m/%Y")
        text_width = canvas_obj.stringWidth(footer_text, "Helvetica", 8)
        canvas_obj.drawString((page_width - text_width) / 2, 2, footer_text)
        canvas_obj.restoreState()
    
    def add_logo_and_invoice_details(self, company_info, invoice_number, invoice_date, po_number=None, agreement=None):

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # Small logo - 0.4 inch (about 28-30 pixels like your reference)
                logo = Image(self.logo_path, width=0.4*inch, height=0.4*inch)
                logo.hAlign = 'CENTER'
                
                # Center the logo at the top
                self.elements.append(logo)
                self.elements.append(Spacer(1, 0.15*inch))
            except Exception as e:
                print(f"Warning: Could not load logo - {e}")
    
        # Company info and invoice details
        left_column_data = [
            Paragraph(company_info['name'], self.heading_style),
            Paragraph(company_info['address'], self.small_style),
            Paragraph(f"{company_info['city']}, {company_info['state']}. {company_info['pincode']}", self.small_style),
            Paragraph(f"GST NO: {company_info['gstin']}", self.small_style),
            Paragraph(company_info['email'], self.small_style),
        ]

        right_column_data = [
            Paragraph(f'<u>{self._format_date(invoice_date)}</u>', self.normal_style),
            Spacer(1, 0.15*inch),
            Paragraph(f'INVOICE {invoice_number}', self.invoice_value_style),
        ]

        if po_number:
            right_column_data.append(Spacer(1, 0.15*inch))
            right_column_data.append(Paragraph('PO NUMBER', self.invoice_label_style))
            right_column_data.append(Paragraph(po_number, self.normal_style))

        if agreement:
            right_column_data.append(Spacer(1, 0.15*inch))
            right_column_data.append(Paragraph('AGREEMENT', self.invoice_label_style))
            right_column_data.append(Paragraph(agreement, self.normal_style))

        top_section_table = Table(
            [[left_column_data, right_column_data]], 
            colWidths=[3.25*inch, 3.25*inch]
        )
        top_section_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        self.elements.append(top_section_table)
        self.elements.append(Spacer(1, 0.25*inch))

    
    def add_party_details(self, seller_info, buyer_info):
        seller_text = f"{seller_info['name']}\n{seller_info['address']}\n{seller_info['city']}, {seller_info['state']} - {seller_info['pincode']}"
        buyer_text = f"{buyer_info['name']}\n{buyer_info['address']}\n{buyer_info['city']}, {buyer_info['state']} - {buyer_info['pincode']}"
        
        seller_gstin = f"GST NUMBER: {seller_info['gstin']}"
        buyer_gstin = f"GST NUMBER: {buyer_info.get('gstin', 'N/A')}"
        
        info_data = [
            [Paragraph('BILL TO', self.heading_style), Paragraph('SHIP TO', self.heading_style)],
            [Paragraph(seller_text, self.normal_style), Paragraph(buyer_text, self.normal_style)],
            [Paragraph(seller_gstin, self.normal_style), Paragraph(buyer_gstin, self.normal_style)],
        ]
        
        info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.grey),
        ]))
        self.elements.append(info_table)
        self.elements.append(Spacer(1, 0.3*inch))
    
    def add_items(self, items):
        items_data = [
            [Paragraph('S.No', self.table_header_style), 
            Paragraph('Name of Product', self.table_header_style), 
            Paragraph('HSN/SAC', self.table_header_style),
            Paragraph('Qty', self.table_header_style), 
            Paragraph('Rate', self.table_header_style), 
            Paragraph('Amount', self.table_header_style)]
        ]
        
        for idx, item in enumerate(items, 1):
            amount = item['quantity'] * item['rate']
            items_data.append([
                Paragraph(str(idx), self.normal_style),
                Paragraph(item['description'], self.normal_style),
                Paragraph(item.get('hsn_code', ''), self.normal_style),
                Paragraph(f'{int(item["quantity"])}', self.normal_style),
                Paragraph(f'{item["rate"]:.2f}', self.normal_style),
                Paragraph(f'{amount:.2f}', self.normal_style)
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 2.8*inch, 0.9*inch, 0.6*inch, 0.9*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#A23034")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9F9F9")),   
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        self.elements.append(items_table)
        self.elements.append(Spacer(1, 0.2*inch))
    
    def _number_to_words(self, number):
        ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
        teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", 
                "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
        tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
        
        def convert_below_thousand(num):
            if num == 0:
                return ""
            elif num < 10:
                return ones[num]
            elif num < 20:
                return teens[num - 10]
            elif num < 100:
                return tens[num // 10] + ("" if num % 10 == 0 else " " + ones[num % 10])
            else:
                return ones[num // 100] + " HUNDRED" + ("" if num % 100 == 0 else " " + convert_below_thousand(num % 100))
        
        if number == 0:
            return "ZERO"
        
        num = int(number)
        words = ""
        if num >= 10000000:
            words += convert_below_thousand(num // 10000000) + " CRORE "
            num %= 10000000
        if num >= 100000:
            words += convert_below_thousand(num // 100000) + " LAKH "
            num %= 100000
        if num >= 1000:
            words += convert_below_thousand(num // 1000) + " THOUSAND "
            num %= 1000
        if num > 0:
            words += convert_below_thousand(num)
        return words.strip() + " RUPEES ONLY"
    
    def add_totals(self, subtotal, discount_type, discount_value, discount_amount, 
                   cgst_rate, cgst_amount, sgst_rate, sgst_amount, igst_rate, igst_amount, 
                   shipping_amount, total_amount):
        total_in_words = self._number_to_words(total_amount)
        left_column_text = Paragraph(
            f'TOTAL AMOUNT IN WORDS:<br/>{total_in_words}',
            self.normal_style
        )
        
        totals_data = [
            [Paragraph('SUBTOTAL', self.normal_style), Paragraph(f'{subtotal:.2f}', self.normal_style)],
        ]
        
        # Add discount row if applicable
        if discount_amount > 0:
            if discount_type == 'percentage':
                totals_data.append([
                    Paragraph(f'DISCOUNT ({discount_value}%)', self.normal_style), 
                    Paragraph(f'-{discount_amount:.2f}', self.normal_style)
                ])
            else:
                totals_data.append([
                    Paragraph('DISCOUNT', self.normal_style), 
                    Paragraph(f'-{discount_amount:.2f}', self.normal_style)
                ])
            
            subtotal_after_discount = subtotal - discount_amount
            totals_data.append([
                Paragraph('AFTER DISCOUNT', self.normal_style), 
                Paragraph(f'{subtotal_after_discount:.2f}', self.normal_style)
            ])
        
        # Add tax rows
        if cgst_rate > 0:
            totals_data.append([Paragraph(f'CGST ({cgst_rate}%)', self.normal_style), Paragraph(f'{cgst_amount:.2f}', self.normal_style)])
        
        if sgst_rate > 0:
            totals_data.append([Paragraph(f'SGST ({sgst_rate}%)', self.normal_style), Paragraph(f'{sgst_amount:.2f}', self.normal_style)])
        
        if igst_rate > 0:
            totals_data.append([Paragraph(f'IGST ({igst_rate}%)', self.normal_style), Paragraph(f'{igst_amount:.2f}', self.normal_style)])
        
        # Add shipping
        totals_data.append([Paragraph('SHIPPING/HANDLING', self.normal_style), Paragraph(f'{shipping_amount:.2f}', self.normal_style)])
        
        # Add total
        grand_total_style = ParagraphStyle(
            'GrandTotal',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold'
        )
        
        totals_data.append([
            Paragraph('TOTAL', grand_total_style), 
            Paragraph(f'{total_amount:.2f}', grand_total_style)
        ])
        
        right_table = Table(totals_data, colWidths=[1.8*inch, 1*inch])
        right_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (1, -1), 10),
            ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (1, -1), 12),
            ('LINEABOVE', (0, -1), (1, -1), 2, colors.black),
            ('TOPPADDING', (0, 0), (1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (1, -1), 6),
        ]))
        
        main_table = Table(
            [[left_column_text, right_table]],
            colWidths=[3.25*inch, 2.75*inch]
        )
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        self.elements.append(main_table)
        self.elements.append(Spacer(1, 0.4*inch))
        
        left_column_text = Paragraph("THIS IS A COMPUTER GENERATED INVOICE THUS SIGNATURE MAY NOT BE REQUIRED", self.normal_style)
        right_column_text = Paragraph("FOR FASCINO HEALTH CARE", self.normal_style)
        notes_table = Table(
            [[left_column_text, right_column_text]],
            colWidths=[3.25*inch, 3.25*inch]
        )
        notes_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        self.elements.append(notes_table)
        self.elements.append(Spacer(1, 0.2*inch))
        self.elements.append(Paragraph("AUTHORIZED SIGNATORY", self.heading_style))
    
    def generate(self):
        self.doc.build(self.elements, onFirstPage=self._add_header_and_footer, 
                       onLaterPages=self._add_header_and_footer)
        return self.output_filename
    
    def _add_header_and_footer(self, canvas_obj, doc):
        self._add_header(canvas_obj, doc)
        self._add_footer(canvas_obj, doc)
    
    @staticmethod
    def _format_date(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return str(date_str)
    
    @staticmethod
    def calculate_tax(subtotal, seller_state, buyer_state, cgst_rate=9, sgst_rate=9, igst_rate=18):
        is_same_state = seller_state.strip().lower() == buyer_state.strip().lower()
        
        if is_same_state:
            cgst_amt = subtotal * (cgst_rate / 100)
            sgst_amt = subtotal * (sgst_rate / 100)
            return cgst_rate, cgst_amt, sgst_rate, sgst_amt, 0, 0
        else:
            igst_amt = subtotal * (igst_rate / 100)
            return 0, 0, 0, 0, igst_rate, igst_amt
