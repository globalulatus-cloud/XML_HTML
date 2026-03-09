import streamlit as st
import tempfile
import os

from converter import XMLToHTMLConverter

st.set_page_config(page_title="XML → HTML Converter")

st.title("XML to HTML Converter")

uploaded_file = st.file_uploader("Upload XML file", type=["xml"])

if uploaded_file:

    if st.button("Convert to HTML"):

        with tempfile.TemporaryDirectory() as tmpdir:

            xml_path = os.path.join(tmpdir, "input.xml")
            html_path = os.path.join(tmpdir, "output.html")

            with open(xml_path, "wb") as f:
                f.write(uploaded_file.read())

            converter = XMLToHTMLConverter(xml_path, html_path)

            success = converter.convert()

            if success:
                with open(html_path, "rb") as f:
                    html_bytes = f.read()

                st.success("Conversion complete")

                st.download_button(
                    label="Download HTML",
                    data=html_bytes,
                    file_name="converted.html",
                    mime="text/html"
                )

                st.components.v1.html(html_bytes.decode(), height=600, scrolling=True)

            else:
                st.error("Conversion failed")
