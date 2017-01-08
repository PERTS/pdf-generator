import os
import sys
import time
import shutil
import urllib
import docraptor

# Parser from https://github.com/lxml/lxml
from lxml import etree
from lxml.html import fromstring, tostring

# Function builds Table of Contents based on an HTML string
# Returns HTML with adjustments for Table of Contents
def build_toc(html):
    new_html = html
    # First make sure this html has a place for the html
    if 'id="toc"' not in html:
        return html

    # Then find all header elements
    # Create a regex to find any <h1> <h2> <h3>
    # For each, 
    # - fetch the title-string and
    # - construct a parameterized string for the ID
    # - Check the number following the h and,
    # - adjust the TOC html accordingly 

    # @todo: remove this, it's just for testing
    toc = etree.Element("div", id="toc")

    # parsed_html = etree.fromstring(html)
    event_types = ("start", "end", "start-ns", "end-ns")
    parser = etree.XMLPullParser(event_types)
    events = parser.read_events()
    parser.feed(html)
    # Increases as we get deeper, helps construct TOC
    header_level = 0
    current_list = toc # append list items to main div
    last_item = toc

    for action, obj in events:
        classes = obj.get('class')
        if classes and any(x in classes for x in ['title', 'no-toc']):
            continue
        if action == 'start':
            if obj.tag == 'h1':
                if header_level > 1:
                    # Need to return to top level
                    current_list = toc
                header_level = 1
            elif obj.tag == 'h2':
                if header_level < 2:
                    # Add new level to the TOC
                    current_list = etree.SubElement(last_item, "ol")
                elif header_level > 2:
                    # Need to close current level and go up
                    current_list = current_list.getparent().getparent()
                header_level = 2
            elif obj.tag == 'h3':
                if header_level < 3:
                    # Add new level to the TOC
                    current_list = etree.SubElement(last_item, "ol")
                elif header_level > 3:
                    # Need to close current level and go up
                    current_list = current_list.getparent().getparent()
                header_level = 3
            # For any header level, we append to the header list position
            if obj.tag in ('h1', 'h2', 'h3'):
                header_text = obj.text.strip()
                # Parameterize text AND CHANGE BELOW
                param_header = header_text.lower().replace(' ', '-');
                obj.set("id", param_header)
                # Append li a with href and text to the TOC
                list_item = etree.SubElement(current_list, "li")
                anchor = etree.SubElement(
                    list_item, "a", href="#%s" % param_header)
                anchor.text = header_text
                last_item = list_item

    root = parser.close()
    new_html = tostring(root).replace('<div id="toc"></div>', tostring(toc))
    # print(new_html)
    return new_html


docraptor.configuration.username = "ONweg0Cg51Sb6erdp9"
doc_api = docraptor.DocApi()

# Determine testing or production (paid) from arguments
# Default to 'test' because why waste money?
if '--production' in sys.argv:
    print('Running script for PRODUCTION')
    is_test = False
else:
    print('Running script for TESTING')
    is_test = True

# Determine if default styles should be embedded or not
# Default to True because our styles are bomb
if '--ignore-styles' in sys.argv:
    print('Ignoring awesome pre-built styles...')
    should_use_default_styles = False
else:
    print('Using awesome pre-built styles...')
    should_use_default_styles = True

# Determine if Table of Contents should be generated or not
# Default to False because it requires some HTML finess
should_generate_toc = False
if '--toc' in sys.argv:
    should_generate_toc = True

# Loops through all files in the "inbox" folder
for html_file in os.listdir("inbox"):

    # Determine if file is the correct format
    if html_file.split('.')[1] == 'html':
        filename = html_file.split('.')[0]
        html = urllib.urlopen("inbox/{}".format(html_file)).read()

        ##########################

        html = build_toc(html)

        #########################

        # Check if style embedder is checked
        if should_use_default_styles:
            print('Embedding default styles for PDF...')
            # Eembed CSS from 'templates/reports/_styles.html'
            # -- before the </head> element in the document
            # -- or create <head></head> and inject in there
            if '</head>' in html:
                print('Head found.')
            else:
                print('No head found, creating...')
                # Find <body> and inject before that
                body_loc = html.index('<body>')
                html = "{}<head></head>{}".format(
                    html[:body_loc], html[body_loc:])

            # Fetch styles html
            styles_template = 'templates/reports/_styles.html'
            styles_html = urllib.urlopen(styles_template).read()

            # Find </head> and inject styles before that
            head_loc = html.index("</head>")
            html = "{}{}{}".format(
                html[:head_loc], styles_html, html[head_loc:])

        if should_generate_toc:
            print('Generating TOC for document...')
            # @todo: Generate the TOC by finding h1, h2, h3 tags

        print("Converting file \"{}\"...".format(html_file))

        # Variables for tracking generation time
        time_counter = 0
        sleep_increment = 0.1  # in seconds

        try:
            create_response = doc_api.create_async_doc({
                "test": is_test,     # test documents are free but watermarked
                "document_content": html,           # supply content directly
                "name": "{}.pdf".format(filename),  # help find document later
                "document_type": "pdf",             # pdf or xls or xlsx
                "prince_options": {
                    "javascript": True              # generated content in js
                    # 'baseurl': 'https://s3.amazonaws.com'
                }
            })

            while True:
                status_response = doc_api.get_async_doc_status(create_response.status_id)
                if status_response.status == "completed":
                    doc_response = doc_api.get_async_doc(status_response.download_id)
                    file = open("outbox/{}.pdf".format(filename), "wb")
                    file.write(doc_response)
                    file.close
                    print("PDF generated at \"/outbox/{}.pdf\"".format(
                        filename))
                    print("PDF generated in ~{}ms".format(
                        time_counter * sleep_increment * 1000))
                    break
                elif status_response.status == "failed":
                    print("FAILED")
                    print(status_response)
                    break
                else:
                    time_counter += 1
                    time.sleep(sleep_increment)

        except docraptor.rest.ApiException as error:
            print(error)
            print(error.message)
            print(error.code)
            print(error.response_body)

    else:
        print('\"{}\" is not a valid HTML file. Skipping.'.format(html_file))
