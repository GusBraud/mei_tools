from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime
# import os
from pathlib import Path
import logging
from lxml import etree

class MEI_Metadata_Updater:
    def __init__(self, source_folder: Optional[str] = None, output_dir: Optional[str] = None, metadata_dict_list: List[Dict] = None):
        self.source_folder = Path(source_folder) if source_folder else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else Path("updated_MEI_files")
        self.soup = None
        self.metadata_dict_list = metadata_dict_list if metadata_dict_list else []
        self._load_metadata_from_dict_list()


    def _log(self, message):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.info(message)
    
    def get_source_files(self) -> List[str]:
        if self.source_folder.is_dir():
            return sorted([f for f in self.source_folder.iterdir() if f.is_file()])
        else:
            raise ValueError("Source folder is not a valid directory.")
    
    def _load_metadata_from_dict_list(self):
        if not self.metadata_dict_list:
            raise ValueError("No metadata dictionary list provided.")
    
        # You can add any additional processing logic here if needed
        self._log(f"Loaded {len(self.metadata_dict_list)} metadata dictionaries.")
    
    def process_files(self, metadata_dict_list: List[Dict], modules_to_apply: List[str]) -> Dict[str, str]:
        file_paths = self.get_source_files()
        if not isinstance(file_paths, list):
            raise TypeError("file_paths must be a list of strings")

        results = {}
        for file_path in file_paths:
            try:
                self.file_path = file_path  # Add this line to set the file_path attribute
                relative_path = str(Path(file_path).relative_to(self.source_folder))
                self.soup = self.load_mei_file(file_path)

                # Split the file path to get just the file name
                file_name = Path(file_path).name
                
                # Find the corresponding metadata dictionary
                metadata_dict = next((md for md in metadata_dict_list if md['MEI_Name'].strip() == file_name), None)
                if not metadata_dict:
                    raise ValueError(f"No matching metadata found for file: {file_name}")

                self._apply_metadata_updates(metadata_dict)

                if self.output_dir:
                    output_path = self.output_dir / Path(relative_path)
                    self.save_processed_file(self.soup, str(output_path))

                results[file_path] = "success"
            except Exception as e:
                results[file_path] = f"error: {str(e)}"

        return results

    def load_mei_file(self, file_path: str) -> BeautifulSoup:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return BeautifulSoup(content, features='lxml-xml')

    def _apply_metadata_updates(self, metadata_dict: Dict):
        self._log(f"Updating metadata for file: {self.file_path}")

        # Clear out all elements from meiHead
        mei_head = self.soup.find('meiHead')
        if mei_head:
            for child in mei_head.find_all(recursively=False):
                child.decompose()

        # Rebuild meiHead with required tags
        file_desc = self.soup.new_tag('fileDesc')
        title_stmt = self.soup.new_tag('titleStmt')
        title = self.soup.new_tag('title')
        title_stmt.append(title)

        resp_stmt = self.soup.new_tag('respStmt')
        title_stmt.append(resp_stmt)

        pub_stmt = self.soup.new_tag('pubStmt')
        publisher = self.soup.new_tag('publisher')
        distributor = self.soup.new_tag('distributor')
        date = self.soup.new_tag('date')
        availability = self.soup.new_tag('availability')
        tag_list = [publisher, distributor, date, availability]
        for tag in tag_list:
            pub_stmt.append(tag)

        tag_list = [title_stmt, pub_stmt]
        for tag in tag_list:
            file_desc.append(tag)

        mei_head.append(file_desc)

        # Set metadata values
        title.string = metadata_dict.get('Title', '')
        composer = self.soup.new_tag('composer')
        composer.string = metadata_dict.get('Composer_Name', '')
        composer['auth'] = 'VIAF'
        composer['auth.uri'] = metadata_dict.get('Composer_VIAF', '')
        resp_stmt.append(composer)

        editors = metadata_dict.get('Editor', '').split('|')
        for editor in editors:
            editor_tag = self.soup.new_tag('persName')
            editor_tag.string = editor.strip()
            editor_tag['role'] = 'editor'
            resp_stmt.append(editor_tag)

        publisher.string = metadata_dict.get('Publisher', '')

        rights_statement = metadata_dict.get('Rights_Statement', '')
        availability.string = rights_statement

        copyright_owner = metadata_dict.get('Copyright_Owner', '').split('|')
        for owner in copyright_owner:
            owner_tag = self.soup.new_tag('persName') if 'person' in owner.lower() else self.soup.new_tag('corpName')
            owner_tag.string = owner.strip()
            distributor.append(owner_tag)

        current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        date.string = current_date

        app_info = self.soup.new_tag('appInfo')
        application = self.soup.new_tag('application')
        name = self.soup.new_tag('name')
        application.append(name)
        name.string = "MEI Soup Updater 2025"
        app_info.append(application)

        mei_head.append(app_info)

        # Work list
        work_list = self.soup.new_tag('workList')
        work = self.soup.new_tag('work')
        title_work = self.soup.new_tag('title')
        title_work.string = metadata_dict.get('Title', '')
        work.append(title_work)
        work.append(composer)
        work_list.append(work)
        mei_head.append(work_list)

        # Manifestation list
        manifestation_list = self.soup.new_tag('manifestationList')
        manifestation = self.soup.new_tag('manifestation')
        identifier = self.soup.new_tag('identifier')
        identifier.string = metadata_dict.get('Source_Reference', '')
        manifestation.append(identifier)
        manifestation_list.append(manifestation)
        mei_head.append(manifestation_list)

        # Source details
        source_details = self.soup.new_tag('sourceDetails')
        manifestation.append(source_details)
        source_title = self.soup.new_tag('title')
        source_title.string = metadata_dict.get('Source_Title', '')
        source_details.append(source_title)

        # Source publication
        source_pub = self.soup.new_tag('pubStmt')
        source_publisher = self.soup.new_tag('publisher')
        source_publisher.string = metadata_dict.get('Source_Publisher_1', '')
        source_pub.append(source_publisher)
        manifestation.append(source_pub)

        # Source date
        source_date = self.soup.new_tag('date')
        source_date.string = metadata_dict.get('Source_Date', '')
        manifestation.append(source_date)

        # Source location
        source_location = self.soup.new_tag('geogName')
        source_location.string = metadata_dict.get('Source_Location', '')
        repository = self.soup.new_tag('repository')
        repository.append(source_location)
        manifestation.append(repository)

        # Source institution
        source_institution = self.soup.new_tag('corpName')
        source_institution.string = metadata_dict.get('Source_Institution', '')
        repository.append(source_institution)

        # Source shelfmark
        source_shelvemark = self.soup.new_tag('identifier')
        source_shelvemark.string = metadata_dict.get('Source_Shelfmark', '')
        repository.append(source_shelvemark)

        self._log("Metadata updates applied successfully")

    def save_processed_file(self, soup: BeautifulSoup, output_path: str) -> None:
        """Save processed MEI file with proper formatting and encoding. Note that we handle xml, mxml and mei somewhat differently."""
        try:
            # Add _rev_ to the filename
            path = Path(output_path)
            base = path.stem
            suffix = path.suffix
            new_path = path.parent / f"{base}_rev{suffix}"

            # Determine the appropriate encoding based on the output file
            if suffix.lower() == '.xml':
                encoding = 'utf-16'  # Assuming .xml files are UTF-16
            elif suffix.lower() == '.mxml':
                encoding = 'utf-8'   # Assuming .mxml files are UTF-8
            else:
                encoding = 'utf-8'   # Default to UTF-8

            xml_decl = '<?xml version="1.0" encoding="UTF-8"?>'
            pretty_xml = soup.prettify()
            if not pretty_xml.startswith('<?xml'):
                pretty_xml = xml_decl + '\n' + pretty_xml

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