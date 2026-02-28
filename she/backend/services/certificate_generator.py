from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
import uuid

class CertificateGenerator:
    def __init__(self):
        self.output_dir = 'static/certificates'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_certificate(self, user_name, course_name, completion_date):
        """Generate a PDF certificate for course completion"""
        
        # Generate unique filename
        filename = f"cert_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(letter),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=36,
            textColor=colors.HexColor('#ff1493'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#ff69b4'),
            spaceAfter=30,
            alignment=1
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )
        
        name_style = ParagraphStyle(
            'Name',
            parent=styles['Normal'],
            fontSize=28,
            textColor=colors.HexColor('#ff1493'),
            spaceAfter=20,
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("Certificate of Completion", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        story.append(Paragraph("This is to certify that", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Name
        story.append(Paragraph(user_name, name_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Body
        story.append(Paragraph(
            f"has successfully completed the course",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Course name
        story.append(Paragraph(
            f"<b>{course_name}</b>",
            ParagraphStyle(
                'CourseName',
                parent=styles['Normal'],
                fontSize=20,
                textColor=colors.HexColor('#ff69b4'),
                alignment=1
            )
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Date
        story.append(Paragraph(
            f"Completed on: {completion_date.strftime('%B %d, %Y')}",
            body_style
        ))
        
        # Build PDF
        doc.build(story)
        
        return filename
    
    def generate_bulk_certificates(self, completions):
        """Generate certificates for multiple users"""
        certificates = []
        for completion in completions:
            filename = self.generate_certificate(
                completion['user_name'],
                completion['course_name'],
                completion['completion_date']
            )
            certificates.append({
                'user_id': completion['user_id'],
                'certificate_file': filename
            })
        return certificates

# Simple certificate generator without reportlab (fallback)
class SimpleCertificateGenerator:
    def generate_certificate(self, user_name, course_name, completion_date):
        """Generate a simple HTML certificate"""
        from jinja2 import Template
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #fff0f5, #ffe4e9);
                }
                .certificate {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border: 10px solid #ff69b4;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 0 30px rgba(255,105,180,0.3);
                }
                h1 {
                    color: #ff1493;
                    font-size: 48px;
                    margin-bottom: 20px;
                }
                h2 {
                    color: #ff69b4;
                    font-size: 32px;
                }
                .name {
                    font-size: 40px;
                    color: #ff1493;
                    margin: 30px 0;
                    font-weight: bold;
                }
                .course {
                    font-size: 28px;
                    color: #ff69b4;
                    margin: 20px 0;
                }
                .date {
                    font-size: 18px;
                    color: #666;
                    margin-top: 40px;
                }
            </style>
        </head>
        <body>
            <div class="certificate">
                <h1>Certificate of Completion</h1>
                <h2>This is to certify that</h2>
                <div class="name">{{ user_name }}</div>
                <h2>has successfully completed the course</h2>
                <div class="course">{{ course_name }}</div>
                <div class="date">Completed on: {{ completion_date }}</div>
            </div>
        </body>
        </html>
        """)
        
        html_content = template.render(
            user_name=user_name,
            course_name=course_name,
            completion_date=completion_date.strftime('%B %d, %Y')
        )
        
        # Generate unique filename
        filename = f"cert_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join('static/certificates', filename)
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        return filename