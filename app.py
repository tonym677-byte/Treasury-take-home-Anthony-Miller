"""Streamlit UI for human-in-the-loop label verification."""
import csv
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from src.ocr import extract_text
from src.verifier import verify

st.set_page_config(page_title='TTB Label Review Assistant', page_icon='🔎', layout='wide')
st.title('Alcohol Label Review Assistant')
st.caption('Standalone demonstration • Offline OCR • Decision support only — never an automated TTB approval')
st.info('Upload a label and enter the application values. Results highlight items for human review. Government warning typography must always be inspected visually.')

with st.sidebar:
    st.header('Application values')
    brand = st.text_input('Brand name', 'OLD TOM DISTILLERY')
    class_type = st.text_input('Class/type', 'Kentucky Straight Bourbon Whiskey')
    abv = st.text_input('Alcohol by volume (%)', '45')
    net_contents = st.text_input('Net contents', '750 mL')
    producer = st.text_input('Producer/bottler (optional)', '')
    address = st.text_input('Producer address (optional)', '')
    country = st.text_input('Country of origin (optional)', '')
    st.caption('Requirements differ by beverage category. Blank optional fields are not checked.')

application = dict(brand=brand, class_type=class_type, abv=abv,
                   net_contents=net_contents, producer=producer, address=address, country=country)
mode = st.radio('Review mode', ['Single label', 'Batch labels'], horizontal=True)
files = st.file_uploader('Upload label image(s) (PNG, JPG, WEBP; max 12 MB each)',
                         type=['png', 'jpg', 'jpeg', 'webp'],
                         accept_multiple_files=mode == 'Batch labels')
if files and st.button('Analyze labels', type='primary'):
    uploads = files if isinstance(files, list) else [files]
    if len(uploads) > 25:
        st.error('Maximum 25 labels per batch. Split larger submissions into batches.')
        st.stop()
    def process(item):
        name, data = item
        started = time.monotonic()
        try:
            ocr = extract_text(data)
            if not ocr.strip():
                raise ValueError('No readable text detected; upload a clearer label.')
            result = verify(ocr, application)
            return {'file': name, 'result': result, 'ocr': ocr, 'seconds': round(time.monotonic()-started, 2)}
        except (ValueError, RuntimeError) as exc:
            return {'file': name, 'error': str(exc)}
    items = [(f.name, f.getvalue()) for f in uploads]
    with st.spinner('Reading and comparing label text...'):
        with ThreadPoolExecutor(max_workers=min(4, len(items))) as pool:
            results = list(pool.map(process, items))
    st.session_state['results'] = results

results = st.session_state.get('results', [])
if results:
    st.subheader('Review results')
    rows = []
    for item in results:
        with st.expander(item['file'], expanded=len(results) == 1):
            if 'error' in item:
                st.error(item['error'])
                rows.append({'file': item['file'], 'status': 'ERROR', 'detail': item['error']})
                continue
            result = item['result']
            st.write(f"**Human review required** · OCR runtime: {item['seconds']}s · "
                     f"{result['summary']['matches']} matches · {result['summary']['review']} review items")
            st.dataframe(result['checks'], use_container_width=True, hide_index=True)
            with st.expander('Extracted OCR text'):
                st.text(item['ocr'])
            for check in result['checks']:
                rows.append({'file': item['file'], **check})
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=['file', 'field', 'expected', 'observed', 'status', 'note', 'detail'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        st.download_button('Download results (CSV)', output.getvalue(), 'label-review.csv', 'text/csv')
    st.download_button('Download full results (JSON)', json.dumps(results, indent=2), 'label-review.json', 'application/json')

st.divider()
st.caption('Prototype limitations: OCR accuracy depends on image quality; not all label regulations are evaluated; no persistent uploads; no COLA integration; no automatic legal determination. Target response time is 5 seconds per label, not guaranteed.')
