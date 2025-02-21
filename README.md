# MEI Tools:  Curating Metadata and Correcting Encoding Errors

You fill find two different sets of processors here (they each consist of a collection of functions, as you can see via the github repository):

* `mei_metadata_processor.py` [takes in a csv or json file and pushes values to the MEI header]
* `mei_music_feature_processor.py` [edits the MEI body in order to correct and improve music data, including problems with slurs, musica ficta, and many features]

##  Installation

You will need to install MEI Tools in your virtual environment in order to use them with MEI files.

Here we assume that you are doing all of this in a Jupyter Notebook, which simplifies the process of working with a folder of 'source' files (the ones you want to process) and a folder of 'output' files (the files after they have been corrected).

Here is now to install the MEI Tools:

from a **terminal** in your virtual environment:

```python
pip install git+https://github.com/RichardFreedman/mei_tools
```

From a terminal in your virtual environment, check that the tools have been installed:

```python
python -c "import mei_tools; print('import successful')"
```

or open a Jupyter Notebook, create a new cell; add the following to it, and run the cell:

```python
import mei_tools
```

If there are no error messages, you are ready to go!

Next you will need to call up an instance of the processor you want. The following sections explain this in detail for each.

## MEI Metadata Updater

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
```

Now import the `MEI_Metadata_Updater` from `mei_tools`

```python
from mei_tools import MEI_Metadata_Updater
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

This should look something like this.  You might want to give the source and output folders different names than the ones shown here:

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

## MEI Music Feature Correction

The `mei_music_feature_processor.py` is a **modular tool**.  That is:  with any folder of MEI files you have the option to run various independent correction routines.  These are described in detail below, but include:

- wrapping editorial accidentals in their correct <supplied> tags
- adding voice labels to the staff definitions (for use with Verovio and CRIM Intervals)
- correction of slurs to ties (when editors mistaken encode the latter as the former)
- removal of prefatory 'incipit' staves
- removal of 'chord' elements used for ambitus in some transcriptions
- removal of empty verses (sometimes produced by conversion from other formats)
- removal of all lyrics (an extreme approach, when conversion pathways fail)
- collapsing layer elements (in which notes are mistakenly encoded as being in different voices but on the same staff)
- removal of timestamp vel attributes (the product of some conversion routines)
- removal of special editorial brackets used in The Senfl Edition files

The modules can be run as a set or singly.

We can also determine the _order_ in which they are run on each file.

It is not difficult to produce other modules for special needs.


## Step 1:  Import the Music Feature Processor and Set Up Modules and Folders


We import the **Music Featurer** from mei_tools, and define the soure and output folders.  Also note option to display a full log of the steps taken while the tool runs.

```python
from mei_tools import Music_Feature_Processor
processor = Music_Feature_Processor(source_folder="MEI", # this is your source folder 
                        output_dir="MEI_Updates", # this is the destination
                        verbose=False) # this determines whether you see full log of steps
```

## Step 2: Enable the Modules

`True` or `False` for each!  They must be `True` here to run below!

```python
processor.remove_incipit = True
processor.remove_chord = True
processor.remove_senfl_bracket = True
processor.remove_empty_verse = True
processor.remove_lyrics = False
processor.remove_tstamp_vel = True
processor.remove_chord = True
processor.collapse_layers = True
processor.remove_empty_verses = True
processor.ficta_to_supplied = True
processor.add_voice_labels = True
processor.slur_to_tie = True
```


## Step 3:  Process the Files with the Requested Modules

Note:  Items in this list must be `True` above to work!

```
results = processor.process_files([
    'fix_elisions',
    'slur_to_tie',
    'remove_incipit',
    'remove_tstamp_vel',
    'remove_chord',
    'remove_senfl_bracket',
    'remove_empty_verse',
    'collapse_layers',
    'remove_empty_verses',
    'remove_chords',
    'ficta_to_supplied',
    'add_voice_labels'
])

```
### Optional:  Progress Check

Note that this is distinct from the `verbose` setting above, which reports each step for each file!

```
for file_path, status in results.items():
    if status == "success":
        print(f"Successfully processed: {file_path}")
    else:
        print(f"Error processing {file_path}: {status}")
```

### Optional:  Run Just One Module?


```python
# Create an instance of the processor
processor = XMLProcessor(
    source_folder="MEI testing",  # Optional: defaults to current directory
    output_dir="MEI_Updates_2",   # Optional: defaults to "MEI_Updates"
    verbose=True
)

# set module to `True`

processor.remove_lyrics = True

# rocess files with lyrics removal
results = processor.process_files(['remove_lyrics'])
```



#### Notes
- the `verbose=True` option provides detailed output, which is useful for debugging but may slow down processing.
- `results` dictionary will contain the outcome for each file processed.
- Ensure that your `source_folder` contains the MEI files you want to process.
- The `output_dir` designates where processed files will be saved.
- Adjust the list of modules in `process_files()` based on your needs.


## Detailed Explanation of the Modules

Note:  We can easily add more modules based on your experience with particular MEI files.


#### _fix_elisions

Fix syllable elisions in the MEI files.  When exported from Sibelius the elisions results in two syllable elements per note.  This module finds the double syllable notes, then reformats the two syllables as a single
tag for that note.  The two syllables are connected with an underscore, which renders correctly in Verovio, and is valid MEI.

---

#### _slur_to_tie

Replace slurs with ties in MEI files.  Occasionally editors mistakenly encode ties as slurs.  This module checks for these and fixes them.

---

#### _ficta_to_supplied

Convert ficta to supplied.  With the Sib_MEI export module, musica ficta is stored as text and not as a supplied element.  This module fixes such errors, provided that the note to which the ficta appliesis given the color 'red' in the original Sibelius file.  The function looks for accid elements associated with red notes and converts them into proper MEI supplied elements.

---

#### _remove_variants

Remove variant elements and their contents.  Files with <app> elements include variant readings. There are some cases in which we want to preserve only the lemma (for example:  analysis).This module removes the <app> elements.

---

#### _remove_chords

Remove chord elements.  These are sometimes found in XML files, and this module removes them.

---

#### _collapse_layers

Collapse layers within staff elements.  Again, some files put notes on different MEI layers.  This module combines those layers.

---

#### _remove_empty_verses

Remove empty verse elements.  In some cases we find extra verse elements that nevertheless lack content.  These create problems for layout with Verovio, and so we can remove them.

---

#### _remove_anchored_text

Remove anchoredText elements.  Anchored text elements can create strange effects when we render files with Verovio.  We can remove them with this module.

---

#### _remove_incipit

Process measure numbers after removing incipit.  Some early music files include incipits (prefatory staves) that include information about original clefs and noteheads.  These are normally given a lable of "0" in the original file.  But they can disrupt the regular measure numbers throughout the remainder of the score.  This module removes the incipit and renumbers the remaining bars so that the labels and bar numbers are the same, and start with "1". 

---

#### _remove_tstamp_vel

Remove timestamp and velocity attributes from notes, rests, and mRests.  The tstamp.real attribute might be a problem in some contexts, and so we remove it. 
        

---

#### _remove_senfl_bracket

Remove Senfl bracket elements. This module removes some special brackets inserted by editors of the Senfl edition.

---

#### _remove_empty_verse

Remove empty verse elements.  Some verse elements are in fact empty, and can distort formatting with Verovio.  We remove them with this module.

---

#### _remove_lyrics

Remove all lyrics, including nested verse elements.  Some files imported from XML or other sources have corrupted lyrics.  Sometimes it is simply better to start over with text underlay in this case, and so this module removes all lyrics.  The files can then be opened with MuseScore for further updates.

---

#### _add_voice_labels

Add voice labels to staff definitions.  It is helpful for Verovio and  CRIM intervals to have voice names as 'label' attributes in our files.  This module takes care of that.



