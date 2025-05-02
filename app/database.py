import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

SQLALCHEMY_DATABASE_URL = "sqlite:///./giraffe_tracker.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    original_image = Column(String)
    processed_image = Column(String)
    giraffe_count = Column(Integer)
    processing_time = Column(Float)
    is_video = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


def save_to_history(result):
    db = SessionLocal()
    try:
        db_item = DetectionHistory(
            original_image=result.original_image,
            processed_image=result.processed_image,
            giraffe_count=result.giraffe_count,
            processing_time=result.processing_time
        )
        db.add(db_item)
        db.commit()
    finally:
        db.close()


def get_history(limit: int = 100):
    db = SessionLocal()
    try:
        return db.query(DetectionHistory).order_by(DetectionHistory.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def clear_history():
    db = SessionLocal()
    try:
        db.query(DetectionHistory).delete()
        db.commit()
    finally:
        db.close()



def generate_report(report_type: str):
    history = get_history(limit=1000)

    if not history:
        return None

    data = []
    for item in history:
        data.append([
            item.timestamp.strftime("%d.%m.%Y %H:%M"),
            f"Original: {item.original_image}\nResult: {item.processed_image}",
            str(item.giraffe_count),
            f"{item.processing_time:.2f} sec"
        ])

    report_dir = "static/reports"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if report_type == "excel":
        filename = f"{report_dir}/report_{timestamp}.xlsx"
        df = pd.DataFrame(data, columns=[
            "Date and time",
            "Images",
            "Amount",
            "Processing time"
        ])
        df.to_excel(filename, index=False)
    elif report_type == "pdf":
        filename = f"{report_dir}/report_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
            title="Giraffe Tracking Report"
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='HeaderStyle',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        styles.add(ParagraphStyle(
            name='FooterStyle',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            spaceBefore=20
        ))

        elements = []

        elements.append(Paragraph("GIRAFFE TRACKING REPORT", styles['HeaderStyle']))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 15))

        table_data = [
            [
                Paragraph("Date and time", styles['Normal']),
                Paragraph("Images/Videos", styles['Normal']),
                Paragraph("Amount", styles['Normal']),
                Paragraph("Processing time", styles['Normal'])
            ]
        ]

        for item in history:
            table_data.append([
                item.timestamp.strftime("%d.%m.%Y %H:%M"),
                f"Original: {item.original_image}\nResult: {item.processed_image}",
                str(item.giraffe_count),
                f"{item.processing_time:.2f} sec"
            ])

        table = Table(
            table_data,
            colWidths=[40*mm, 100*mm, 20*mm, 30*mm],
            repeatRows=1
        )

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c956c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEADING', (0, 0), (-1, -1), 12),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        total_giraffes = sum(item.giraffe_count for item in history)
        avg_time = sum(item.processing_time for item in history)/len(history) if history else 0
        elements.append(Paragraph(
            f"<b>Total giraffes detected:</b> {total_giraffes}<br/>"
            f"<b>Average processing time:</b> {avg_time:.2f} sec",
            styles['Normal']
        ))

        elements.append(Paragraph(
            "Automatically generated by Giraffe Tracking System",
            styles['FooterStyle']
        ))

        doc.build(elements)
    else:
        return None

    return filename