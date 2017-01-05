import os
import sys
import time
import shutil
import urllib
import docraptor

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
