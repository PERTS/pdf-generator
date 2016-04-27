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

# Loops through all files in the "inbox" folder
for html_file in os.listdir("inbox"):
    # Determine if file is the correct format
    if html_file.split('.')[1] == 'html':
        filename = html_file.split('.')[0]
        html = urllib.urlopen("inbox/{}".format(html_file)).read()

        print("Converting file \"{}\"...".format(html_file))

        try:
            create_response = doc_api.create_async_doc({
                "test": is_test,
                "document_content": html,
                # "document_url": "inbox/{}".format(pdf),
                "name": "docraptor-python.pdf",
                "document_type": "pdf",
            })

            while True:
                status_response = doc_api.get_async_doc_status(create_response.status_id)
                if status_response.status == "completed":
                    doc_response = doc_api.get_async_doc(status_response.download_id)
                    file = open("outbox/{}.pdf".format(filename), "wb")
                    file.write(doc_response)
                    file.close
                    print("PDF generated at \"/outbox/{}.pdf\"".format(filename))
                    break
                elif status_response.status == "failed":
                    print("FAILED")
                    print(status_response)
                    break
                else:
                    time.sleep(1)

        except docraptor.rest.ApiException as error:
            print(error)
            print(error.message)
            print(error.code)
            print(error.response_body)

    else:
        print('\"{}\" is not a valid HTML file. Skipping.'.format(html_file))
