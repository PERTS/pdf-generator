# pdf-generator
Generates PDFs from HTML files using DocRaptor

Put the html files you want to convert in subdirectory `inbox`

Then from the root directory run:

```
python generate.py
```

PDF files will be generated in a `outbox` subdirectory.

## Production v. Testing

By default PDF files are generated in 'testing' mode with DocRaptor. These are
free for PERTS and do not count against the quota we pay for each month.

To make PDFs for production (something you would want to send to schools) you
will need to add a `production` flag to the python command:

```
python generate.py --production
```
