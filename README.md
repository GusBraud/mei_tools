# Music Encoding Initiative Files:  Curating Metadata and Correcting Encoding Errors

You fill find two different scripts here:

* `mei_metadata_processor.py` 
* `mei_music_feature_processor.py`


## MEI Metadata Updater

Remember that this python file must be in the same directory as your notebook!

The processor takes in:

- A `source_folder` of MEI files to be updated (and also asks you specify an `output_dir` where the processed files will go)
- A `list of metadata dictionaries` that provide the new data.  One convenient way to do this is by publishing a **[Google Sheet as CSV](https://docs.google.com/spreadsheets/d/1ctSIhNquWlacXQNLg92N_DV1H4lUJeXLn7iqKyLlhng/edit?gid=422384819#gid=422384819)**, then importing that sheet to Pandas and then converting it to a list of dictionaries (in which each row is a dictionary). Here is what one of our dictionary entries looks like.  The `keys` are the columns of our spreadsheet.  The `values` are the contents of each cell for a given row.

```python
{'CRIM_ID': 'CRIM_Model_0001',
 'MEI_Name': 'CRIM_Model_0001.mei',
 'Title': 'Veni speciosam',
 'Mass Title': '',
 'Genre': 'motet ',
 'Composer_Name': 'Johannes Lupi',
 'CRIM_Person_ID': 'CRIM_Person_0004',
 'Composer_VIAF': 'http://viaf.org/viaf/42035469',
 'Composer_BNF_ID': 'https://data.bnf.fr/ark:/12148/cb139927263',
 'Piece_Date': ' before 1542',
 'Source_ID': 'CRIM_Source_0003',
 'Source_Short_Title': 'Musicae Cantiones',
 'Source_Title': 'Chori Sacre Virginis Marie Cameracensis Magistri, Musicae Cantiones (quae vulgo motetta nuncupantur) noviter omni studio ac diligentia in lucem editae. (8, 6, 5, et 4 vocum.) Index quindecim Cantionum. Liber tertius.',
 'Source_Publisher_1': 'Pierre Attaingnant',
 'Publisher_1_VIAF': 'http://viaf.org/viaf/59135590',
 'Publisher_1_BNF_ID': 'https://data.bnf.fr/ark:/12148/cb12230232k',
 'Source_Publisher_2': '',
 'Publisher_2_VIAF': '',
 'Publisher_2_BNF_ID': '',
 'Source_Date': '1542',
 'Source_Reference': 'RISM A I, L 3089',
 'Source_Location': 'Wien',
 'Source_Institution': 'Österreichische Nationalbibliothek',
 'Source_Shelfmark': 'SA.78.C.1/3/1-4 Mus 19',
 'Editor': 'Marco Gurrieri | Bonnie Blackburn | Vincent Besson | Richard Freedman',
 'Last_Revised': '2020_07_10',
 'Rights_Statement': 'This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License',
 'Copyright_Owner': "Centre d'Études Supérieures de la Renaissance | Haverford College | Marco Gurrieri | Bonnie Blackburn | Vincent Besson | Richard Freedman"}
 ```

The processor takes in each file in turn, then matches it against the list of dictionaries to find the one it needs.

Our first step with the MEI file itself is to rebuild the `head` element.  Depending on the particular pathway used to create the MEI file (Sibelius to MEI exporter, MEI Friend, Verovio Viewer, or MuseScore) the results will be quite different.  Not all exporters create the head tags in the same way, although each is valid MEI.

We rebuild the MEI to include key elements:

- **fileDesc** (with information about what is contained here, including composer, title, editors, modern publisher, and rights statement)
- **appInfo** (how we created the file, with the MEI Updater)
- **workList** (repeating information about the composer and title of the music)
- **manifestationList** (the details of the original source, including title, date, location)


Each of these tags is being created, populated with data from the matching **metadata_dict**, and appended to the appropriate parent element in the MEI structure. Some tags are nested within others, creating a hierarchical structure for the metadata.

### Step 1: Import the Required Libraries

This is the first step before running the processor.

```python
#  Import necessary libraries
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import logging
import os
import pandas as pd

# the following refers to 'mei_metadata_processor.py` file, and needs to be in the same folder as this NB
from mei_metadata_processor import MEI_Metadata_Updater 
```

#### Optional Error Logging

You can also opt to show a log of errors:

```python
# logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```


### Step 2: Load the Metadata from the Google Sheet; Create List of Dictionaries

```python
# Load metadata CSV
metadata_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSspBYGhjx-UJb-lIcy8Dmxjj3c1EuBqX_IWhi2aT1MvybZ_RAn8eq7gXfjzQ_NEfEq2hCZY5y-sHx/pub?output=csv"
df = pd.read_csv(metadata_csv_url).fillna('')
crim_metadata_dict_list = df.to_dict(orient='records')
```


### Step 3: Set Up the Updater with Source Folder, Output Folder, and Metadata List

This should look something like this.  You might want to give the source and output folderrs different names than the ones shown here:

```python
updater = MEI_Metadata_Updater(
    source_folder="MEI",
    output_dir="MEI_Updates",
    metadata_dict_list=crim_metadata_dict_list
)
```
### Step 4: Process the Files

Here we declare the results and run the updater, passing in the metadata dictionary list:

```python
results = updater.process_files(crim_metadata_dict_list)
```

#### Option to Print Summary Report of the Process


```python
file_path, status in results.items():
    print(f"Processed {status}: {file_path}")
```

