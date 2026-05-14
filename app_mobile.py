import streamlit as st
import pandas as pd
from streamlit_gps_location import gps_location_button
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import io
from PIL import Image as PILImage

# Page configuration
st.set_page_config(
    page_title="Field Scientist Reporter",
    layout="centered",
)

st.title("Field Scientist Reporter")
st.caption("Document and report a discovery in a structured and professional way.")

#User Inputs
st.markdown('<div class="section-header">1 · Researcher Information</div>', unsafe_allow_html=True)

researcher_name = st.text_input("Researcher name *")
discovery_title = st.text_input("Title of discovery *")
description     = st.text_area("Description / Observations *",
                               placeholder="Describe your finding in detail…",
                               height=120)
report_date = st.date_input("Date of observation", value=date.today())

#GPS Location
st.markdown('<div class="section-header">2 · GPS Location</div>', unsafe_allow_html=True)

st.subheader("Location")
location_data = gps_location_button(buttonText="Get my location")

lat, lon = None, None

if location_data is not None:
    st.write("Your location data:")
    st.json(location_data)

    if location_data.get('latitude') is not None and location_data.get('longitude') is not None:
        lat = location_data['latitude']
        lon = location_data['longitude']
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.subheader("Your location on the map")
        st.map(map_data)
else:
    st.info("Press 'Get my location' to see your location on the map.")

#Visual Evidence
st.markdown('<div class="section-header">3 · Visual Evidence</div>', unsafe_allow_html=True)

photo = st.camera_input("Take a photo")
if photo is None:
    photo = st.file_uploader("…or upload an image", type=["jpg", "jpeg", "png"])

if photo is not None:
    st.image(photo, caption="Evidence photo", use_container_width=True)

#PDF Generation
st.markdown('<div class="section-header">4 · Generate PDF Report</div>', unsafe_allow_html=True)


def build_pdf(name, title, desc, obs_date, latitude, longitude, photo_bytes):
    """Build a professional field-report PDF and return it as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    dark_green = colors.HexColor("#1e6b2e")

    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Heading1"],
        fontSize=18, textColor=colors.white,
        alignment=TA_CENTER, spaceAfter=0,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"),
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=11, textColor=colors.black, spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=12, textColor=dark_green, spaceBefore=14, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=6,
    )

    story = []

    # Title banner
    banner_table = Table([[Paragraph("FIELD REPORT", title_style)]], colWidths=[17*cm])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), dark_green),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 0.5*cm))

    coord_str = f"Lat {latitude:.5f}, Lon {longitude:.5f}" if latitude is not None else "Not captured"
    meta_table = Table([
        [Paragraph(f"<b>Researcher:</b> {name}", value_style),
         Paragraph(f"<b>Date:</b> {obs_date.strftime('%d/%m/%Y')}", value_style)],
        [Paragraph(f"<b>Coordinates:</b> {coord_str}", label_style), Paragraph("", label_style)],
    ], colWidths=[10*cm, 7*cm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3*cm))

    # Finding & observations
    story.append(Paragraph(f"Finding: {title}", heading_style))
    story.append(Paragraph("<b>Observations:</b>", label_style))
    story.append(Paragraph(desc.replace("\n", "<br/>"), body_style))

    # Photo
    if photo_bytes:
        story.append(Paragraph("Visual Evidence", heading_style))
        try:
            img_io = io.BytesIO(photo_bytes)
            pil_img = PILImage.open(img_io)
            max_w, max_h = 13*cm, 12*cm
            orig_w, orig_h = pil_img.size
            aspect = orig_h / orig_w
            img_w = max_w
            img_h = img_w * aspect
            if img_h > max_h:
                img_h = max_h
                img_w = img_h / aspect
            img_io.seek(0)
            story.append(Image(img_io, width=img_w, height=img_h))
        except Exception as e:
            story.append(Paragraph(f"[Photo could not be embedded: {e}]", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


if st.button("Generate PDF Report", use_container_width=True, type="primary"):
    # Validation
    errors = []
    if not researcher_name.strip():
        errors.append("Researcher name is required.")
    if not discovery_title.strip():
        errors.append("Title of discovery is required.")
    if not description.strip():
        errors.append("Description / Observations are required.")
    if lat is None or lon is None:
        errors.append("GPS location must be captured before generating the report.")
    if photo is None:
        errors.append("A photo must be attached as visual evidence.")

    if errors:
        for err in errors:
            st.error(f"{err}")
    else:
        with st.spinner("Building your field report…"):
            try:
                pdf_bytes = build_pdf(
                    name=researcher_name.strip(),
                    title=discovery_title.strip(),
                    desc=description.strip(),
                    obs_date=report_date,
                    latitude=lat,
                    longitude=lon,
                    photo_bytes=photo.getvalue(),
                )
                st.success(" Report generated successfully!")
                st.download_button(
                    label="Download Field Report PDF",
                    data=pdf_bytes,
                    file_name=f"field_report_{report_date.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Error generating report: {e}")
