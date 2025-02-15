from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import logging
from lxml import etree

class MEI_Metadata_Updater:
    def __init__(self, source_folder: Optional[str] = None, output_dir: Optional[str] = None, metadata_dict_list: List[Dict] = None):
        self.source_folder = Path(source_folder) if source_folder else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else Path("updated_MEI_files")
        self.soup = None
        self.metadata_dict_list = metadata_dict_list if metadata_dict_list else []
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


    def _log(self, message):
        """Creates optional log of errors and processes."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.info(message)
    
    def get_source_files(self) -> List[str]:
        """Looks to the designated local folder and creates a list of all .mei files for processing."""
        if self.source_folder.is_dir():
            # Debug: Print the contents of the source folder
            print(f"Contents of {self.source_folder}:")
            for item in self.source_folder.iterdir():
                print(f"- {item}")

            # Get all .mei files in the directory
            files = [f for f in self.source_folder.glob('*.mei')]
            # Debug: Print the number of .mei files found
            print(f"Found {len(files)} .mei files in total")

            # Sort the files alphabetically
            return sorted(files)
        else:
            raise ValueError("Source folder is not a valid directory.")
    
    def _load_metadata_from_dict_list(self):
        """Loads a list of dictionaries or json that contain the metadata.  The names of the keys correspond to the keys used to update the various MEI elements."""
        if not self.metadata_dict_list:
            raise ValueError("No metadata dictionary list provided.")
    
        # You can add any additional processing logic here if needed
        self._log(f"Loaded {len(self.metadata_dict_list)} metadata dictionaries.")
    
    def _get_matching_dict(self, file_name_with_extension: str, metadata: List[Dict]) -> Optional[Dict]:
        """
        Find matching metadata dictionary. This is used for updating MEI with metadata from a csv or json file
        """
        try:
            matching_dict = next(item for item in metadata if item.get('MEI_Name') == file_name_with_extension)
            if matching_dict is None:
                self.logger.warning(f"No matching metadata dictionary found for {file_name_with_extension}")
                return None
            return matching_dict
        except StopIteration:
            self.logger.warning(f"No matching metadata dictionary found for {file_name_with_extension}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding matching dict for {file_name_with_extension}: {str(e)}")
            return None
    
    def process_files(self, metadata_dict_list: List[Dict]) -> Dict[str, str]:
        file_paths = self.get_source_files()
        if not isinstance(file_paths, list):
            raise TypeError("file_paths must be a list of strings")

        results = {}
        for file_path in file_paths:
            try:
                self.file_path = file_path  # Set the file_path attribute
                relative_path = str(Path(file_path).relative_to(self.source_folder))
                
                # Load the MEI file
                self.soup = self.load_mei_file(file_path)

                # Find the corresponding metadata dictionary
                metadata_dict = self._get_matching_dict(file_path.name, metadata_dict_list)
                
                if metadata_dict:
                    # Apply metadata updates
                    self._apply_metadata_updates(metadata_dict)
                    
                    if self.output_dir:
                        output_path = self.output_dir / Path(relative_path)
                        self.save_processed_file(self.soup, str(output_path))
                    
                    results[file_path] = "success"
                else:
                    # Handle cases where no matching metadata is found
                    self.logger.warning(f"No matching metadata dictionary found for file: {file_path.name}")
                    results[file_path] = "no_match"

            except Exception as e:
                results[file_path] = f"error: {str(e)}"

        return results

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

    def _apply_metadata_updates(self, metadata_dict: Dict):
        """Updates the metadata, using one file and its matching metadata dictionary."""
        self._log(f"Updating metadata for file: {self.file_path}")

        # Clear out all elements from meiHead
        mei_head = self.soup.find('meiHead')
        if mei_head:
            for child in mei_head.find_all(recursively=False):
                child.decompose()

        # create new fileDesc
        file_desc = self.soup.new_tag('fileDesc')

        # create new titleStmt
        title_stmt = self.soup.new_tag('titleStmt')
        title = self.soup.new_tag('title')
        title_stmt.append(title)

        # create new respStmt and add to titleStmt
        resp_stmt = self.soup.new_tag('respStmt')
        title_stmt.append(resp_stmt)

        # create new pubStmt
        pub_stmt = self.soup.new_tag('pubStmt')
        publisher = self.soup.new_tag('publisher')
        distributor = self.soup.new_tag('distributor')
        # latest update of the MEI file
        date = self.soup.new_tag('date')
        current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        date['isodate'] = current_date
        availability = self.soup.new_tag('availability')
        # add all the tags to the pub_stmt
        tag_list = [publisher, distributor, date, availability]
        for tag in tag_list:
            pub_stmt.append(tag)

        # add titleStmt and pubStmt to fileDesc 
        tag_list = [title_stmt, pub_stmt]
        for tag in tag_list:
            file_desc.append(tag)

        # add fileDesc to meiHead
        mei_head.append(file_desc)

         # build encodingDesc and add to head
        encodingDesc = self.soup.new_tag('encodingDesc')
        
        # build appInfo
        appInfo = self.soup.new_tag('appInfo')
        application = self.soup.new_tag('application')
        name = self.soup.new_tag('name')
        application.append(name)
        appInfo.append(application)
        encodingDesc.append(appInfo)
        name.string = "mei metadata processor: url:  https://github.com/RichardFreedman/mei_tools" 
        # add fileDesc to meiHead
        mei_head.append(encodingDesc)

        # build workList and add to head
        workList = self.soup.new_tag('workList')
        work = self.soup.new_tag('work')
        title = self.soup.new_tag('title')
        composer = self.soup.new_tag('composer')
        classification = self.soup.new_tag('classification')
        termList = self.soup.new_tag('termList')
        term = self.soup.new_tag('term')
        termList.append(term)
        classification.append(termList)
        tag_list = [title, composer, classification]
        for tag in tag_list:
            work.append(tag)
        workList.append(work)
        mei_head.append(workList)
        
        # build manifestationList and add to head
        manifestationList = self.soup.new_tag('manifestationList')
        # optional identifier for source--could be RISM
        manifestation = self.soup.new_tag('manifestation')
        identifier = self.soup.new_tag('identifier')
        # title of source publication
        titleStmt = self.soup.new_tag('titleStmt')
        title = self.soup.new_tag('title')
        titleStmt.append(title)
        
        # build pubStmt for original source in manifestationList
        pubStmt = self.soup.new_tag('pubStmt')
        publisher = self.soup.new_tag('publisher')
        # this is to be the date of the original publication
        date = self.soup.new_tag('date')
        
        # adding publisher and date to the pubStmt
        tag_list = [publisher, date]
        for tag in tag_list:
            pubStmt.append(tag)
            
        # build physLoc
        physLoc = self.soup.new_tag('physLoc')
        repository = self.soup.new_tag('repository')
        corpName = self.soup.new_tag('corpName')
        settlement = self.soup.new_tag('settlement')
        identifier = self.soup.new_tag('identifier')
        # adding corpName, settlement, and identifier to physLoc
        tag_list = [corpName, settlement, identifier]
        for tag in tag_list:
            repository.append(tag)
        physLoc.append(repository)
        
        # add titleStmt, pubStmt and physLoc to manifestation
        tag_list = [titleStmt, pubStmt, physLoc]
        for tag in tag_list:
            manifestation.append(tag)
        
        # add manifestation to manifestationList and then to meihead
        manifestationList.append(manifestation)
        mei_head.append(manifestationList)

        # Now that the head is in place, add the metadata values based on the matching metadata dict
        
        # add title to fileDesc and workList
        title = metadata_dict.get('Title', '')
        self.soup.find('fileDesc').find('titleStmt').find('title').string = title
        self.soup.find('workList').find('work').find('title').string = title

        # add composer to fileDesc and workList
        composer_name = metadata_dict.get('Composer_Name', '')
        composer_viaf = metadata_dict.get('Composer_VIAF', '')
        respStmt = self.soup.find('fileDesc').find('respStmt')
        # add a persName for the composer, plus string and attributes
        persName = self.soup.new_tag('persName')
        persName.string = composer_name
        persName['role'] = 'composer'
        persName['auth'] = 'VIAF'
        persName['auth.uri'] = composer_viaf
        respStmt.append(persName)
        
        # also add composer in the workList, too
        comp_tag = self.soup.find('workList').find('work').find('composer')
        comp_tag.string = composer_name
        comp_tag['auth'] = 'VIAF'
        comp_tag['auth.uri'] = composer_viaf

        # add editors to respStmt
        editors = metadata_dict.get('Editor', '').split('|') # splits list at "|"
        for editor in editors:
            editor_tag = self.soup.new_tag('persName')
            editor_tag.string = editor.strip()
            editor_tag['role'] = 'editor'
            resp_stmt.append(editor_tag)

        # add publisher, copyright and rights info for THIS file
        pub_tag = self.soup.find('fileDesc').find('pubStmt').find('publisher')
        pub_tag.string = metadata_dict.get('Publisher', '')
        rights_tag = self.soup.find('fileDesc').find('pubStmt').find('availability')
        rights_tag.string = metadata_dict.get('Rights_Statement', '')
        # cc owners
        dist_tag = self.soup.find('fileDesc').find('pubStmt').find('distributor')
        owners = metadata_dict.get('Copyright_Owner')
        owner_list = owners.split("|") # Splits the string at "|"
        owner_names = [name.strip() for name in owner_list]
        for owner in owner_names:
            if "Centre" in owner:
                owner_tag = self.soup.new_tag('corpName')
                owner_tag.string = owner
                dist_tag.append(owner_tag)
            elif "College" in owner:
                owner_tag = self.soup.new_tag('corpName')
                owner_tag.string = owner
                dist_tag.append(owner_tag)
            else: 
                owner_tag = self.soup.new_tag('persName')
                owner_tag.string = owner
                dist_tag.append(owner_tag)

    
        # genre for workList (composer and title already added)
        genre = metadata_dict.get('Genre', '')
        self.soup.find('workList').find('work').find('classification').find('termList').find('term').string = genre

        # Manifestation list
        # authority id
        source_ref = metadata_dict.get('Source_Reference')
        self.soup.find('manifestation').find('identifier').string = source_ref
        
        # source title
        source_title = metadata_dict.get('Source_Title', '')
        self.soup.find('manifestation').find('titleStmt').find('title').string = source_title
        
        pub_tag = self.soup.find('manifestation').find('pubStmt').find('publisher')
        
        # now deal with pub 1 and metadata
        if len(metadata_dict.get('Source_Publisher_1')) > 0:
            source_pub_1_csv = metadata_dict.get('Source_Publisher_1')
            pub_1_tag = self.soup.new_tag('persName')
            pub_1_tag.string = source_pub_1_csv
            # Now, safely attempt to add the 'auth_uri' attribute
            if isinstance(pub_1_tag, str):
                print("Error: pub_1_tag should be a BeautifulSoup Tag object, not a string.")
            else:
                auth_uri_value = metadata_dict.get('Publisher_1_VIAF', '')
                pub_1_tag['auth'] = 'VIAF'
                pub_1_tag['auth.uri'] = auth_uri_value
        
            # append pub 1 to the publisher tag in the pubStmt of the manifestation
            pub_tag.append(pub_1_tag)
        
        # now deal with pub 2 and metadata
        if len(metadata_dict.get('Source_Publisher_2')) > 0:
            source_pub_2_csv = metadata_dict.get('Source_Publisher_2')
            pub_2_tag = self.soup.new_tag('persName')
            pub_2_tag.string = source_pub_2_csv
            # Now, safely attempt to add the 'auth_uri' attribute
            if isinstance(pub_1_tag, str):
                print("Error: pub_2_tag should be a BeautifulSoup Tag object, not a string.")
            else:
                auth_uri_value = metadata_dict.get('Publisher_2_VIAF', '')
                pub_2_tag['auth'] = 'VIAF'
                pub_2_tag['auth.uri'] = auth_uri_value
            # append pub 2 to the publisher tag in the pubStmt of the manifestation
            pub_tag.append(pub_2_tag)
        
        # source date--not the current date!
        if metadata_dict.get('Source_Date') is not None:
            source_date_csv = metadata_dict.get('Source_Date')
            date_tag = self.soup.find('manifestationList').find('pubStmt').find('date')
            date_tag.string = source_date_csv
            
        # source location
        source_location = metadata_dict.get('Source_Location')
        repository_tag = self.soup.find('manifestationList').find('manifestation').find('physLoc').find('repository')
        repository_tag.append(self.soup.new_tag('geogName'))
        repository_tag.find('geogName').string = source_location
        
        # source institution
        source_institution = metadata_dict.get('Source_Institution')
        self.soup.find('manifestationList').find('manifestation').find('physLoc').find('repository').find('corpName').string = source_institution
        
        # source shelfmark
        source_shelfmark = metadata_dict.get('Source_Shelfmark')
        self.soup.find('repository').find('identifier').string = source_shelfmark

        self._log("Metadata updates applied successfully")

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
