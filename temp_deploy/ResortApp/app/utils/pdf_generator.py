"""
PDF Bill Generation for Checkout
Generates a detailed bill PDF with all charges breakdown
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


def generate_checkout_bill_pdf(checkout, bill_details, output_path):
    """
    Generate a PDF bill for a checkout
    
    Args:
        checkout: Checkout model instance
        bill_details: Dict containing detailed breakdown
        output_path: Full path where PDF should be saved
    
    Returns:
        str: Path to the generated PDF
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    # Header
    elements.append(Paragraph("ORCHID TRAILS RESORT", title_style))
    elements.append(Paragraph("Checkout Bill", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Bill Info
    bill_info_data = [
        ['Bill ID:', str(checkout.id), 'Date:', datetime.now().strftime('%d-%m-%Y %H:%M')],
        ['Guest Name:', checkout.guest_name or 'N/A', 'Room:', checkout.room_number or 'N/A'],
    ]
    
    if checkout.invoice_number:
        bill_info_data.append(['Invoice #:', checkout.invoice_number, '', ''])
    
    bill_info_table = Table(bill_info_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 2*inch])
    bill_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(bill_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Charges breakdown
    elements.append(Paragraph("Charges Breakdown", heading_style))
    
    charges_data = [['Description', 'Amount']]
    
    # Room charges
    if checkout.room_total > 0:
        charges_data.append(['Room Charges', f'Rs.{checkout.room_total:,.2f}'])
    
    # Package charges
    if checkout.package_total > 0:
        charges_data.append(['Package Charges', f'Rs.{checkout.package_total:,.2f}'])
    
    # Food charges
    if checkout.food_total > 0:
        charges_data.append(['Food & Beverages', f'Rs.{checkout.food_total:,.2f}'])
    
    # Service charges
    if checkout.service_total > 0:
        charges_data.append(['Services', f'Rs.{checkout.service_total:,.2f}'])
    
    # Consumables
    if checkout.consumables_charges > 0:
        charges_data.append(['Consumables', f'Rs.{checkout.consumables_charges:,.2f}'])
    
    # Inventory/Rentals
    if checkout.inventory_charges > 0:
        charges_data.append(['Inventory/Rentals', f'Rs.{checkout.inventory_charges:,.2f}'])
    
    # Asset damages
    if checkout.asset_damage_charges > 0:
        charges_data.append(['Asset Damages', f'Rs.{checkout.asset_damage_charges:,.2f}'])
    
    # Late checkout
    if checkout.late_checkout_fee > 0:
        charges_data.append(['Late Checkout Fee', f'Rs.{checkout.late_checkout_fee:,.2f}'])
    
    # Key card fee
    if checkout.key_card_fee > 0:
        charges_data.append(['Key Card Fee', f'Rs.{checkout.key_card_fee:,.2f}'])
    
    # Tax
    if checkout.tax_amount > 0:
        charges_data.append(['Tax (GST)', f'Rs.{checkout.tax_amount:,.2f}'])
    
    # Discount
    if checkout.discount_amount > 0:
        charges_data.append(['Discount', f'-Rs.{checkout.discount_amount:,.2f}'])
    
    # Grand total
    charges_data.append(['', ''])
    charges_data.append(['GRAND TOTAL', f'Rs.{checkout.grand_total:,.2f}'])
    
    charges_table = Table(charges_data, colWidths=[5*inch, 2*inch])
    charges_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -3), colors.white),
        ('GRID', (0, 0), (-1, -3), 1, colors.grey),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -2), (-1, -1), 14),
        ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#EEF2FF')),
        ('TEXTCOLOR', (0, -2), (-1, -1), colors.HexColor('#4F46E5')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(charges_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Detailed items (if available)
    if bill_details:
        # Consumables details
        if bill_details.get('consumables_items'):
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Consumables Details", heading_style))
            
            consumables_data = [['Item', 'Qty', 'Rate', 'Amount']]
            for item in bill_details['consumables_items']:
                consumables_data.append([
                    item.get('item_name', 'N/A'),
                    str(item.get('quantity', item.get('actual_consumed', 0))),
                    f"Rs.{item.get('charge_per_unit', 0):,.2f}",
                    f"Rs.{item.get('total_charge', 0):,.2f}"
                ])
            
            consumables_table = Table(consumables_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1*inch])
            consumables_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(consumables_table)
        
        # Asset damages details
        if bill_details.get('asset_damages'):
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("Asset Damages", heading_style))
            
            damages_data = [['Item', 'Notes', 'Amount']]
            for item in bill_details['asset_damages']:
                damages_data.append([
                    item.get('item_name', 'N/A'),
                    item.get('notes', '-'),
                    f"Rs.{item.get('total_charge', item.get('replacement_cost', 0)):,.2f}"
                ])
            
            damages_table = Table(damages_data, colWidths=[2.5*inch, 3*inch, 1.5*inch])
            damages_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(damages_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_text = f"""
    <para align=center>
    <b>Payment Method:</b> {checkout.payment_method or 'N/A'}<br/>
    Thank you for staying with us!<br/>
    <i>Generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</i>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    return output_path
