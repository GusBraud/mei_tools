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

## A. MEI Metadata Updater

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


We now create or update each of these tags in turn, populating them with data from the matching **metadata_dict**, and appended to the appropriate parent element in the MEI structure. Some tags are nested within others, creating a hierarchical structure for the metadata.

### Step 1: Import the Required Libraries

This is the first step before running the processor.

```python
#  Import necessary libraries
import mei_tools
from mei_tools import MEI_Metadata_Updater
from mei_tools import MEI_Music_Feature_Processor
import glob
import os
import pandas as pd
```

### Step 2: Load the Metadata from the Google Sheet; Create List of Dictionaries

```python
# Load metadata CSV
metadata_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSspBYGhjx-UJb-lIcy8Dmxjj3c1EuBqX_IWhi2aT1MvybZ_RAn8eq7gXfjzQ_NEfEq2hCZY5y-sHx/pub?output=csv"
df = pd.read_csv(metadata_csv_url).fillna('')
crim_metadata_dict_list = df.to_dict(orient='records')
```

#### Step 3.  Specify Input and Output Folders


For example:

```python
mei_paths = glob.glob('MEI_raw/*')
output_folder = 'MEI_Updates'
```

#### Step 4. Create an instance of the processor.  

```python
metadata_updater = MEI_Metadata_Updater()
```


- Optionally you can use `dir(metadata_updater)` to see all the available methods.  In fact there is only one that interests us:  `apply_metadata`


#### Step 5:  Build Tuples for Processor

Here we make 'pairs' of each mei file and its corresponding metadata dictionary:

```python
pairs_to_process = []
for mei_path in mei_paths:
    mei_file_name = os.path.basename(mei_path)
    matching_dict = next((item for item in metadata_dicts if item['MEI_Name'] == mei_file_name), None)
    tup = mei_path, matching_dict
    pairs_to_process.append(tup)
```

#### Step 6: Process the Files

Here we declare the results and run the updater, passing in the metadata dictionary list:

```python
for mei_file_name, matching_dict in pairs_to_process:
    metadata_updater.apply_metadata(mei_file_name, matching_dict, output_folder)
```


## B. MEI Music Feature Correction

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

It is not difficult to produce other modules for special needs.


## Step 1:  Create an instance of the processor

`music_feature_processor = MEI_Music_Feature_Processor()`

Optionally you can also see a list of the functions within it:

`dir(music_feature_processor)`

We are only interested in `process_music_features`.


### Step 2: Now specify the input and ouput folders

For example:

```python
mei_paths = glob.glob('MEI_Updates/*')
output_folder = "MEI_Final"
```

### Step 3:  Process the Files



```python
for mei_path in mei_paths:
    music_feature_processor.process_music_features(mei_path,
                                                  output_folder="MEI_Final",
                                                  remove_incipit=True,
                                                  remove_variants=True,
                                                  remove_anchored_text=True,
                                                  remove_timestamp=True,
                                                  remove_chord=True,
                                                  remove_senfl_bracket=False,
                                                  remove_empty_verse=False,
                                                  remove_lyrics=False,
                                                  fix_elisions=True,
                                                  slur_to_tie=True,
                                                  collapse_layers=False,
                                                  correct_ficta=True,
                                                  voice_labels=True)



# Then, call the method on the instance
for mei_path in mei_paths:
    music_feature_processor.process_music_features(mei_path,
                                                  output_folder="MEI_Final",
                                                  remove_incipit=True,
                                                  remove_variants=True,
                                                  remove_anchored_text=True,
                                                  remove_timestamp=True,
                                                  remove_chord=True,
                                                  remove_senfl_bracket=False,
                                                  remove_empty_verse=False,
                                                  remove_lyrics=False,
                                                  fix_elisions=True,
                                                  slur_to_tie=True,
                                                  collapse_layers=False,
                                                  correct_ficta=True,
                                                  voice_labels=True)```




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



