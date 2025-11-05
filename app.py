from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from invoice_generator import InvoiceGenerator
import os
import io
from datetime import datetime


app = Flask(__name__)
CORS(app)   


# Use current directory for invoices
INVOICES_DIR = os.path.join(os.getcwd(), 'invoices')
os.makedirs(INVOICES_DIR, exist_ok=True)


@app.route('/api/generate-invoice', methods=['POST'])
def generate_invoice():
    """
    Receive invoice data and generate PDF
    Expected JSON structure from frontend
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('company_info') or not data.get('buyer_info') or not data.get('items'):
            return jsonify({'error': 'Missing required fields: company_info, buyer_info, items'}), 400
        
        # Create safe filename without spaces
        safe_invoice_number = data['invoice_number'].replace(' ', '_').replace('/', '_')
        pdf_filename = f'Invoice_{safe_invoice_number}.pdf'
        pdf_filepath = os.path.join(INVOICES_DIR, pdf_filename)
        
        # Create invoice generator
        invoice = InvoiceGenerator(
            output_filename=pdf_filepath,
            logo_path=r"C:\Users\risha\OneDrive\Documents\Programs\Invoice Generator\fascinoai.png"
        )
        
        # Add logo and invoice details
        invoice.add_logo_and_invoice_details(
            company_info=data['company_info'],
            invoice_number=data['invoice_number'],
            invoice_date=data['invoice_date'],
            po_number=data.get('po_number'),
            agreement=data.get('agreement')
        )
        
        # Add party details
        invoice.add_party_details(
            seller_info=data['company_info'],
            buyer_info=data['buyer_info']
        )
        
        # Add items
        invoice.add_items(data['items'])
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['rate'] for item in data['items'])
        
        # Handle discount
        discount_type = data.get('discount_type', 'none')
        discount_value = float(data.get('discount_value', 0))
        discount_amount = 0
        
        if discount_type == 'percentage':
            discount_amount = subtotal * (discount_value / 100)
        elif discount_type == 'amount':
            discount_amount = discount_value
        
        # Subtotal after discount
        subtotal_after_discount = subtotal - discount_amount
        
        # Calculate tax on discounted amount
        cgst_rate, cgst_amt, sgst_rate, sgst_amt, igst_rate, igst_amt = \
            InvoiceGenerator.calculate_tax(
                subtotal=subtotal_after_discount,
                seller_state=data['company_info']['state'],
                buyer_state=data['buyer_info']['state'],
                cgst_rate=float(data.get('cgst_rate', 9)),
                sgst_rate=float(data.get('sgst_rate', 9)),
                igst_rate=float(data.get('igst_rate', 18))
            )
        
        shipping_charges = float(data.get('shipping_charges', 0))
        total = subtotal_after_discount + cgst_amt + sgst_amt + igst_amt + shipping_charges
        
        # Add totals with NEW discount support
        invoice.add_totals(
            subtotal=subtotal,
            discount_type=discount_type,
            discount_value=discount_value,
            discount_amount=discount_amount,
            cgst_rate=cgst_rate,
            cgst_amount=cgst_amt,
            sgst_rate=sgst_rate,
            sgst_amount=sgst_amt,
            igst_rate=igst_rate,
            igst_amount=igst_amt,
            shipping_amount=shipping_charges,
            total_amount=total
        )
        
        # Generate PDF
        pdf_path = invoice.generate()
        
        # Check if file was created
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Failed to generate PDF file'}), 500
        
        # Read PDF file into memory
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = io.BytesIO(pdf_file.read())
            
            pdf_data.seek(0)
            
            # Return PDF file from memory
            response = send_file(
                pdf_data,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=pdf_filename
            )
            
            # Clean up file after sending (optional)
            try:
                os.remove(pdf_path)
            except:
                pass  # File in use, will be cleaned up later
            
            return response
        
        except Exception as file_error:
            print(f"File error: {str(file_error)}")
            return jsonify({'error': f'Error reading PDF file: {str(file_error)}'}), 500
        
    except Exception as e:
        print(f"Error: {str(e)}")  # Print to console for debugging
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
