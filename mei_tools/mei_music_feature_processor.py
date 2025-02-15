from typing import List, Dict, Optional, Callable
from bs4 import BeautifulSoup
import os
from pathlib import Path
from functools import partial
import random

class Music_Feature_Processor:
    def __init__(
        self,
        source_folder: Optional[str] = None,
        output_dir: Optional[str] = None,
        verbose: bool = True
    ):
        """Initialize the Music_Feature_Processor with optional parameters."""
        self.source_folder = Path(source_folder) if source_folder else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else Path("MEI_Updates")
        self.soup = None
        self._modules: Dict[str, Callable] = {}
        self.verbose = verbose
        self._register_modules()

    def _log(self, message: str) -> None:
        """Helper method to control logging output.  Verbose is True by default."""
        if self.verbose:
            print(message)

    def _register_modules(self) -> None:
        """Register available transformation modules."""
        self._modules = {
            'fix_elisions': partial(self._fix_elisions),
            'slur_to_tie': partial(self._slur_to_tie),
            'remove_incipit': partial(self._remove_incipit),
            'remove_tstamp_vel': partial(self._remove_tstamp_vel),
            'remove_senfl_bracket': partial(self._remove_senfl_bracket),
            'remove_empty_verse': partial(self._remove_empty_verse),
            'remove_lyrics': partial(self._remove_lyrics),
            'collapse_layers': partial(self._collapse_layers),
            'remove_empty_verses': partial(self._remove_empty_verses),
            'remove_chords': partial(self._remove_chords),
            'ficta_to_supplied': partial(self._ficta_to_supplied),
            'add_voice_labels': partial(self._add_voice_labels),
            'remove_variants': partial(self._remove_variants),
            'remove_anchored_text': partial(self._remove_anchored_text)
        }
    def get_source_files(self) -> List[str]:
        """Get list of MEI files in the source folder."""
        try:
            files = list(self.source_folder.glob("*.mei"))
            if not files:
                self._log(f"No MEI files found in {self.source_folder}")
            return [str(f) for f in files]
        except Exception as e:
            self._log(f"Error listing files: {str(e)}")
            raise

    def load_mei_file(self, file_path: str) -> BeautifulSoup:
        """
        Load and parse MEI XML file, handling both UTF-8 and UTF-16 encodings.
        
        Args:
            file_path (str): Path to the MEI XML file
            
        Returns:
            BeautifulSoup: Parsed XML content
            
        Raises:
            FileNotFoundError: If the file does not exist
            Exception: If the file cannot be decoded with either UTF-8 or UTF-16
        """
        if not os.path.exists(file_path):
            self._log(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try UTF-8 first (most common)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return BeautifulSoup(content, features='lxml-xml')
                
        except UnicodeDecodeError:
            # If UTF-8 fails, try UTF-16
            try:
                with open(file_path, 'r', encoding='utf-16') as file:
                    content = file.read()
                    return BeautifulSoup(content, features='lxml-xml')
                    
            except UnicodeDecodeError:
                self._log(f"Could not decode file {file_path} with either UTF-8 or UTF-16")
                raise Exception(f"Unable to decode file {file_path}. Please verify the file encoding.")
    
        
    def _fix_elisions(self) -> BeautifulSoup:
        """Fix syllable elisions in the MEI files.  When exported from Sibelius the elisions results in two syllable elements per note.  This module finds the double syllable notes, then reformats the two syllables as a single
        tag for that note.  The two syllables are connected with an underscore, which renders correctly in Verovio, and is valid MEI.
        """
        try:
            self._log("=== Starting elision fix ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            verses = self.soup.find_all('verse')
            # self._log(f"Found {len(verses)} verses")
            for i, verse in enumerate(verses):
                # self._log(f"\nVerse {i+1}:")
                # self._log(f"Verse attributes: {dict(verse.attrs)}")
                syllables = verse.find_all('syl')
                # self._log(f"Found {len(syllables)} syllables")
                if len(syllables) <= 1:
                    # self._log("Skipping verse - not enough syllables")
                    continue
                first_syllable = syllables[0]
                second_syllable = syllables[1]
                # self._log(f"First syllable text: {first_syllable.text}")
                # self._log(f"Second syllable text: {second_syllable.text}")
                if not (first_syllable.string and second_syllable.string):
                    # self._log("Skipping verse - missing syllable text")
                    continue
                new_text = f"{first_syllable.text}_{second_syllable.text}"
                first_syllable.string.replace_with(new_text)
                first_syllable['con'] = 'd'
                first_syllable['wordpos'] = 'm'
                second_syllable.decompose()
                # self._log("Elision fix applied successfully")
                # self._log(f"Modified verse structure: {verse.prettify()[:200]}...")
            self._log("=== Elision fix complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error in elision fix: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise

    def _slur_to_tie(self) -> BeautifulSoup:
        """Replace slurs with ties in MEI files.  Occasionally editors mistakenly encode ties as slurs.  This module checks for these and fixes them."""
        try:
            self._log("=== Starting slur to tie conversion ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            slurs = self.soup.find_all('slur')
            # self._log(f"Found {len(slurs)} slurs")
            for i, slur in enumerate(slurs):
                # self._log(f"\nSlur {i+1}:")
                # self._log(f"Slur attributes before: {dict(slur.attrs)}")
                del slur['layer']
                del slur['tstamp']
                del slur['tstamp2']
                del slur['staff']
                slur.name = 'tie'
                # self._log(f"Slur attributes after: {dict(slur.attrs)}")
                # self._log(f"Modified slur structure: {slur.prettify()[:200]}...")
            self._log("=== Slur to tie conversion complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error in slur to tie conversion: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise

   

    def _ficta_to_supplied(self) -> BeautifulSoup:
        """Convert ficta to supplied.  With the Sib_MEI export module, musica ficta is stored as text and not as a supplied element.  This module fixes such errors, provided that the note to which the ficta appliesis given the color 'red' in the original Sibelius file.  The function looks for accid elements associated with red notes and converts them into proper MEI supplied elements."""
        try:
            self._log("=== Starting ficta to supplied conversion ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            # Remove 'dir' tags
            dir_tags = self.soup.find_all('dir')
            for tag in dir_tags:
                tag.decompose()
            
            # Process color notes
            color_notes = self.soup.find_all('note', attrs={'color': True})
            
            for note in color_notes:
                if note.find('accid') is not None:
                    note_with_accid_ges = note.find('accid', attrs={'accid.ges': True})
                    if note_with_accid_ges:
                        # Rename the accid.ges attribute to accid
                        note_with_accid_ges['accid'] = note_with_accid_ges.get('accid.ges')
                        del note_with_accid_ges['accid.ges']
                    del note['color']
                    accid_tag = note.find('accid')
                    
                    # Extract the 'accid' attribute value
                    accid_value = accid_tag.get('accid')
                    
                    # Create new supplied tag
                    random_id = random.randint(10000, 99999)
                    xml_string = f"m-{random_id}"
                    supplied_tag = self.soup.new_tag('supplied', attrs={'reason': 'edit', 'xml:id': xml_string})
                    
                    # Create the new accid tag
                    random_id = random.randint(10000, 99999)
                    xml_string = f"m-{random_id}"
                    new_accid_tag = self.soup.new_tag('accid', attrs={'accid': accid_value, 'func': "edit", 'place': "above", 'xml:id': xml_string})
                    
                    # Replace the old accid tag with the supplied + accid
                    accid_tag.replace_with(supplied_tag)
                    supplied_tag.append(new_accid_tag)
            
            self._log("=== Ficta to supplied conversion complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error in ficta to supplied conversion: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _remove_variants(self) -> BeautifulSoup:
        """Remove variant elements and their contents.  Files with <app> elements include variant readings. There are some cases in which we want to preserve only the lemma (for example:  analysis).This module removes the <app> elements."""
        try:
            self._log("=== Starting variant removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            apps = self.soup.find_all('app')
            for app in apps:
                parent_layer = app.parent
                notes = app.find('lem').find_all('note')
                # Add notes to the correct position
                for note in notes:
                    parent_layer.append(note)
                
                readings = app.find_all('rdg')
                for reading in readings:
                    reading.decompose()
                
                app.decompose()
            
            self._log("=== Variant removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error in variant removal: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _remove_chords(self) -> BeautifulSoup:
        """Remove chord elements.  These are sometimes found in XML files, and this module removes them."""
        try:
            self._log("=== Starting chord removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            if hasattr(self, 'remove_chord') and self.remove_chord:
                chords = self.soup.find_all('chord')
                for chord in chords:
                    chord.decompose()
                
                self._log(f"Removed {len(chords)} chord elements")
            
            self._log("=== Chord removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error removing chords: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _collapse_layers(self) -> BeautifulSoup:
        """Collapse layers within staff elements.  Again, some files put notes on different MEI layers.  This module combines those layers."""
        try:
            self._log("=== Starting layer collapse ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            # Find all staff elements
            staff_elements = self.soup.find_all('staff')
            
            # self._log(f"Found {len(staff_elements)} staff elements")
            
            for staff in staff_elements:
                n = staff.get('n')
                if n and n.isdigit():  # Check if n attribute exists and is numeric
                    n = int(n)
                    
                    # Find all layer tags within the staff element
                    layers = staff.find_all('layer')
                    
                    # Identify the layer tag with n="1"
                    target_layer = next((layer for layer in layers if layer.get('n') == '1'), None)
                    
                    if target_layer:
                        # Combine contents of other layers into the target layer
                        for layer in layers:
                            if layer.get('n') != '1' and layer.contents:
                                target_layer.extend(layer.contents)
                        
                        # Remove now-empty layer tags with n > 1
                        for layer in layers:
                            if layer.get('n') != '1' and not layer.contents:
                                layer.extract()
                        
                        # Update the n attribute of the target layer
                        target_layer['n'] = '1'
                        
                        # self._log(f"Collapsed layers in staff {n}")
                        # self._log(f"Modified staff structure: {staff.prettify()[:200]}...")
                    # else:
                        # self._log(f"No layer with n='1' found in staff {n}")
            
            self._log("=== Layer collapse complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error collapsing layers: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _remove_empty_verses(self) -> BeautifulSoup:
        """Remove empty verse elements.  In some cases we find extra verse elements that nevertheless lack content.  These create problems for layout with Verovio, and so we can remove them."""
        try:
            self._log("=== Starting empty verse removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            if hasattr(self, 'remove_empty_verse') and self.remove_empty_verses:
                verse_elements = self.soup.find_all('verse')
                verse_elements_without_children = [verse for verse in verse_elements
                                                if not any(child.name for child in verse.contents)]
                
                for verse in verse_elements_without_children:
                    verse.decompose()
                
                # self._log(f"Removed {len(verse_elements_without_children)} empty verse elements")
            
            self._log("=== Empty verse removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error removing empty verses: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _remove_anchored_text(self) -> BeautifulSoup:
        """Remove anchoredText elements.  Anchored text elements can create strange effects when we render files with Verovio.  We can remove them with this module."""
        try:
            self._log("=== Starting anchoredText removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            anchored_texts = self.soup.find_all('anchoredText')
            for tag in anchored_texts:
                tag.decompose()
            
            self._log("=== AnchoredText removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error in anchoredText removal: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _remove_incipit(self) -> BeautifulSoup:
        """Process measure numbers after removing incipit.  Some early music files include incipits (prefatory staves) that include information about original clefs and noteheads.  These are normally given a lable of "0" in the original file.  But they can disrupt the regular measure numbers throughout the remainder of the score.  This module removes the incipit and renumbers the remaining bars so that the labels and bar numbers are the same, and start with "1". """
        try:
            self._log("=== Starting incipit removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            if hasattr(self, 'remove_incipit') and self.remove_incipit:
                # Find and remove measure labeled '0'
                incipit = self.soup.find('measure', attrs={'label': '0', 'n': '1'})
                if incipit:
                    incipit.decompose()
                    # self._log("Removed incipit measure")
            
            # Renumber remaining measures
            remaining_measures = self.soup.find_all('measure')
            # self._log(f"Found {len(remaining_measures)} measures to renumber")
            
            for measure in remaining_measures:
                current_number = measure['n']
                new_number = int(current_number) - 1
                measure['n'] = str(new_number)
                # self._log(f"Renumbered measure from {current_number} to {new_number}")
            
            self._log("=== Measure number processing complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error processing measure numbers: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise

    def _remove_tstamp_vel(self) -> BeautifulSoup:
        """Remove timestamp and velocity attributes from notes, rests, and mRests.  The tstamp.real attribute might be a problem in some contexts, and so we remove it. 
        """
        try:
            self._log("=== Starting timestamp and velocity removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            # Remove from notes
            notes_time = self.soup.find_all('note', attrs={'tstamp.real': True})
            notes_vel = self.soup.find_all('note', attrs={'vel': True})
            for note in notes_time:
                del note['tstamp.real']
            for note in notes_vel:
                del note['vel']
            # self._log(f"Processed {len(notes_time)} notes with timestamps and {len(notes_vel)} notes with velocity")
            
            # Remove from rests
            rests_time = self.soup.find_all('rest', attrs={'tstamp.real': True})
            rests_vel = self.soup.find_all('rest', attrs={'vel': True})
            for rest in rests_time:
                del rest['tstamp.real']
            for rest in rests_vel:
                del rest['vel']
            # self._log(f"Processed {len(rests_time)} rests with timestamps and {len(rests_vel)} rests with velocity")
            
            # Remove from mRests
            mrests_time = self.soup.find_all('mRest', attrs={'tstamp.real': True})
            mrests_vel = self.soup.find_all('mRest', attrs={'vel': True})
            for mrest in mrests_time:
                del mrest['tstamp.real']
            for mrest in mrests_vel:
                del mrest['vel']
            # self._log(f"Processed {len(mrests_time)} mRests with timestamps and {len(mrests_vel)} mRests with velocity")
            
            # Remove tstamp2 from ties
            ties = self.soup.find_all("tie")
            for tie in ties:
                if 'tstamp' in tie.attrs:
                    del tie['tstamp']
                if 'tstamp2' in tie.attrs:
                    del tie['tstamp2']
            # self._log(f"Processed {len(ties)} ties")
            
            self._log("=== Timestamp and velocity removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error removing timestamps and velocities: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise


    def _remove_senfl_bracket(self) -> BeautifulSoup:
        """Remove Senfl bracket elements. This module removes some special brackets inserted by editors of the Senfl edition."""
        try:
            self._log("=== Starting Senfl bracket removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            if hasattr(self, 'remove_senfl_bracket') and self.remove_senfl_bracket:
                brackets = self.soup.find_all('line', attrs={'type': 'bracket'})
                for bracket in brackets:
                    bracket.decompose()
                # self._log(f"Removed {len(brackets)} Senfl bracket elements")
            
            self._log("=== Senfl bracket removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error removing Senfl brackets: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise

    def _remove_empty_verse(self) -> BeautifulSoup:
        """Remove empty verse elements.  Some verse elements are in fact empty, and can distort formatting with Verovio.  We remove them with this module."""
        try:
            self._log("=== Starting empty verse removal ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            if hasattr(self, 'remove_empty_verse') and self.remove_empty_verse:
                verse_elements = self.soup.find_all('verse')
                verse_elements_without_children = [verse for verse in verse_elements
                                                 if not any(child.name for child in verse.contents)]
                for verse in verse_elements_without_children:
                    verse.decompose()
                # self._log(f"Removed {len(verse_elements_without_children)} empty verse elements")
            
            self._log("=== Empty verse removal complete ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            return self.soup
        except Exception as e:
            self._log(f"Error removing empty verses: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise

    def _remove_lyrics(self) -> BeautifulSoup:
        """Remove all lyrics, including nested verse elements.  Some files imported from XML or other sources have corrupted lyrics.  Sometimes it is simply better to start over with text underlay in this case, and so this module removes all lyrics.  The files can then be opened with MuseScore for further updates."""
        try:
            self._log("=== Starting lyrics removal ===")
            
            # Get initial state
            initial_verses = self.soup.find_all('verse')
            initial_notes = self.soup.find_all('note')
            
            # Log initial state with detailed information
            # self._log(f"Initial verse count: {len(initial_verses)}")
            # self._log(f"Initial note count: {len(initial_notes)}")
            
            # Store original XML structure for comparison
            original_structure = self.soup.prettify()
            
            if hasattr(self, 'remove_lyrics') and self.remove_lyrics:
                # Find all verse elements
                verses = self.soup.find_all(lambda tag: tag.name == 'verse')
                
                # Track removed elements
                removed_count = 0
                removed_locations = []
                
                # Remove each verse element
                for verse in verses:
                    parent = verse.parent
                    parent_name = parent.name if parent else 'root'
                    verse_id = verse.get('xml:id', 'no-id')
                    
                    # Log detailed information
                    removed_locations.append(
                        f"Verse (xml:id='{verse_id}') in {parent_name} "
                        f"(xml:id='{parent.get('xml:id', 'no-id')}')"
                    )
                    
                    # Verify verse contents before removal
                    # self._log(f"\nRemoving verse with attributes: {dict(verse.attrs)}")
                    # self._log(f"Verse text content: {verse.text.strip()[:100]}...")
                    
                    # Perform removal
                    verse.decompose()
                    removed_count += 1
                
                # Verify changes
                # final_verses = self.soup.find_all('verse')
                # final_notes = self.soup.find_all('note')
                
                # Log verification results
                # self._log("\nVerification Results:")
                # self._log(f"Initial verses: {len(initial_verses)}")
                # self._log(f"Final verses: {len(final_verses)}")
                self._log(f"Verses removed: {removed_count}")
                
                # Compare XML structures
                final_structure = self.soup.prettify()
                if len(original_structure) != len(final_structure):
                    self._log("XML structure changed after lyrics removal")
                else:
                    self._log("Warning: XML structure lengths match after removal")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error removing lyrics: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def _add_voice_labels(self) -> BeautifulSoup:
        """Add voice labels to staff definitions.  It is helpful for Verovio and  CRIM intervals to have voice names as 'label' attributes in our files.  This module takes care of that."""
        try:
            self._log("=== Adding voice labels ===")
            # self._log(f"Initial XML structure: {self.soup.prettify()[:200]}...")
            
            staff_defs = self.soup.find_all('staffDef')
            
            for staff_def in staff_defs:
                # Find the nested <label> tag
                label = staff_def.find('label')
                # Extract the text content of the <label> tag
                label_text = label.get_text() if label else None
                # Add the extracted text as an attribute 'label' to the <staffDef> tag
                if label_text:
                    staff_def['label'] = label_text
            
            # Capitalize the first letter of each voice label
            for staff_def in staff_defs:
                label = staff_def.find('label')
                label_text = label.get_text() if label else None
                if label_text:
                    first_letter = label_text[0].upper()
                    label_abbr = staff_def.find('labelAbbr')
                    if label_abbr:
                        label_abbr.string = first_letter + '.'
            
            self._log("=== Voice labels added ===")
            # self._log(f"Final XML structure: {self.soup.prettify()[:200]}...")
            
            return self.soup
        
        except Exception as e:
            self._log(f"Error adding voice labels: {str(e)}")
            self._log(f"Current XML state: {self.soup.prettify()[:200]}...")
            raise
    
    def process_files(self, modules_to_apply: List[str]) -> Dict[str, str]:
        """Process multiple MEI files with specified transformation modules.  """
        file_paths = self.get_source_files()
        if not isinstance(file_paths, list):
            raise TypeError("file_paths must be a list of strings")
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
        results = {}
        for file_path in file_paths:
            try:
                relative_path = str(Path(file_path).relative_to(self.source_folder))
                if self.output_dir:
                    output_path = self.output_dir / Path(relative_path)
                self.soup = self.load_mei_file(file_path)
                processed_soup = self.soup
                self._log(f"\nProcessing {relative_path}")
                self._log(f"Applying modules: {modules_to_apply}")
                for module_name in modules_to_apply:
                    if module_name not in self._modules:
                        self._log(f"Warning: Unknown module {module_name}")
                        continue
                    module = self._modules[module_name]
                    self._log(f"Applying {module_name}...")
                    processed_soup = module()
                    self._log(f"{module_name} applied successfully")
                if self.output_dir:
                    self.save_processed_file(processed_soup, str(output_path))
                results[file_path] = "success"
                self._log(f"Successfully processed {relative_path}")
            except Exception as e:
                results[file_path] = f"error: {str(e)}"
                self._log(f"Processing failed for {relative_path}: {str(e)}")
        return results
    
    def save_processed_file(self, soup: BeautifulSoup, output_path: str) -> None:
        """Save processed MEI file with proper formatting and UTF-8 encoding.
        Note that we handle xml, mxml and mei files uniformly with UTF-8 encoding."""
        try:
            # Add _rev_ to the filename
            path = Path(output_path)
            base = path.stem
            suffix = path.suffix
            new_path = path.parent / f"{base}_rev{suffix}"

            # Use consistent UTF-8 encoding for all file types
            encoding = 'utf-8'
            
            # Create XML declaration with UTF-8 encoding
            xml_decl = '<?xml version="1.0" encoding="UTF-8"?>'
            
            # Ensure proper XML formatting
            pretty_xml = soup.prettify()
            
            # Add XML declaration if missing
            if not pretty_xml.startswith('<?xml'):
                pretty_xml = xml_decl + '\n' + pretty_xml
                
            # Write file with UTF-8 encoding
            with open(new_path, 'w', encoding=encoding) as f:
                f.write(pretty_xml)

            # Verify file was saved
            saved_file = Path(new_path)
            if saved_file.exists():
                self._log(f"File saved successfully: {new_path}")
                return new_path
            else:
                raise FileNotFoundError(f"File not saved: {new_path}")
                
        except Exception as e:
            self._log(f"Error saving processed file: {str(e)}")
            raise

    