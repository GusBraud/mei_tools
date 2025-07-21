import os
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
from copy import deepcopy

class MEI_Metadata_Updater:
    """
    A class for processing and updating metadata in MEI (Music Encoding Initiative) files.
    """
    
    def __init__(self, input_folder=None, output_folder=None, namespace=None, verbose=False):
        """
        Initialize the MEI Metadata Processor.
        
        Args:
            input_folder (str, optional): Path to the folder containing MEI files to process.
            output_folder (str, optional): Path to the folder where updated MEI files will be saved.
                                          If not provided, will use input_folder.
            namespace (dict, optional): XML namespace dictionary for MEI files.
                                       Defaults to {'mei': 'http://www.music-encoding.org/ns/mei'}.
            verbose (bool, optional): Whether to print detailed processing information. Defaults to False.
        """
        self.input_folder = input_folder
        self.output_folder = output_folder if output_folder else input_folder
        
        # Ensure output folder exists
        if self.output_folder and not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
        # Set default namespace if not provided
        self.namespace = namespace if namespace else {'mei': 'http://www.music-encoding.org/ns/mei'}
        
        # Verbose mode for debugging
        self.verbose = verbose
        
        # Initialize counters for processing statistics
        self.processed_files = 0
        self.successful_updates = 0
        self.failed_updates = 0

    # now the functions
        def apply_metadata(self, mei_file_path, metadata_dict, output_folder):
        """
        Applies metadata from a dictionary to an MEI file.

        Args:
            mei_file_path (str): The path to the input MEI file.
            metadata_dict (dict): A dictionary containing the metadata.
            output_folder (str): The folder to save the updated MEI file.
        """
        if metadata_dict is None:
            print(f"No metadata found for {os.path.basename(mei_file_path)}. Skipping.")
            return

        print(f"Getting {os.path.basename(mei_file_path)}")

        parser = etree.XMLParser(remove_blank_text=True)
        try:
            tree = etree.parse(mei_file_path, parser)
            root = tree.getroot()
        except Exception as e:
            print(f"Error parsing MEI file {mei_file_path}: {e}")
            return

        ns = {'mei': 'http://www.music-encoding.org/ns/mei/4.0'}

        # Find or create the <meiHead> element
        mei_head_el = root.find('mei:meiHead', namespaces=ns)
        if mei_head_el is None:
            mei_head_el = etree.Element(etree.QName(ns['mei'], 'meiHead'), nsmap=ns)
            root.insert(0, mei_head_el) # Insert at the beginning

        # Find or create the <fileDesc> element
        fileDesc_el = mei_head_el.find('mei:fileDesc', namespaces=ns)
        if fileDesc_el is None:
            fileDesc_el = etree.Element(etree.QName(ns['mei'], 'fileDesc'), nsmap=ns)
            mei_head_el.append(fileDesc_el)

        # Find or create the <titleStmt> element
        titleStmt_el = fileDesc_el.find('mei:titleStmt', namespaces=ns)
        if titleStmt_el is None:
            titleStmt_el = etree.Element(etree.QName(ns['mei'], 'titleStmt'), nsmap=ns)
            fileDesc_el.append(titleStmt_el)

        # Add or update the <title> element
        title_el = titleStmt_el.find('mei:title', namespaces=ns)
        if title_el is None:
            title_el = etree.Element(etree.QName(ns['mei'], 'title'), nsmap=ns)
            titleStmt_el.append(title_el)
        title_el.text = metadata_dict.get('Title', '')

        # Add or update the <composer> element
        composer_el = titleStmt_el.find('mei:composer', namespaces=ns)
        if composer_el is None:
            composer_el = etree.Element(etree.QName(ns['mei'], 'composer'), nsmap=ns)
            titleStmt_el.append(composer_el)

        persName_el = composer_el.find('mei:persName', namespaces=ns)
        if persName_el is None:
            persName_el = etree.Element(etree.QName(ns['mei'], 'persName'), nsmap=ns)
            composer_el.append(persName_el)
        persName_el.text = metadata_dict.get('Composer_Name', '').replace('#265 ', '') # Remove '#265 ' prefix

        # Add or update @role="composer" to <persName> if not present
        if 'role' not in persName_el.attrib:
            persName_el.set('role', 'composer')

        # Add or update @assoc to <persName> with RDL_ID
        rdl_id = metadata_dict.get('RDL_ID', '')
        if rdl_id:
             persName_el.set('assoc', f"https://ricercardatalab.cesr.univ-tours.fr/works/{rdl_id}/")

        # Add or update @sameas with VIAF and BNF IDs
        sameas_uris = []
        composer_viaf = metadata_dict.get('Composer_VIAF', '')
        if composer_viaf:
            sameas_uris.append(composer_viaf)
        composer_bnf = metadata_dict.get('Composer_BNF_ID', '')
        if composer_bnf:
            sameas_uris.append(composer_bnf)

        if sameas_uris:
            persName_el.set('sameas', ' '.join(sameas_uris))

        # Find or create the <pubStmt> element
        pubStmt_el = fileDesc_el.find('mei:pubStmt', namespaces=ns)
        if pubStmt_el is None:
            pubStmt_el = etree.Element(etree.QName(ns['mei'], 'pubStmt'), nsmap=ns)
            fileDesc_el.append(pubStmt_el)

        # Add or update publisher information (Corrected XML string)
        try:
            pubStmt_el.append(etree.fromstring("""<publisher>Gesualdo Online  https://ricercardatalab.cesr.univ-tours.fr/fr/projects/3/</publisher>""", parser=parser))
        except Exception as e:
            print(f"Error adding publisher element: {e}")


        # Add or update the <availability> element
        availability_el = pubStmt_el.find('mei:availability', namespaces=ns)
        if availability_el is None:
             availability_el = etree.Element(etree.QName(ns['mei'], 'availability'), nsmap=ns)
             pubStmt_el.append(availability_el)

        # Add or update the <useStmt> element
        useStmt_el = availability_el.find('mei:useStmt', namespaces=ns)
        if useStmt_el is None:
             useStmt_el = etree.Element(etree.QName(ns['mei'], 'useStmt'), nsmap=ns)
             availability_el.append(useStmt_el)

        # Add or update the <licence> element
        licence_el = useStmt_el.find('mei:licence', namespaces=ns)
        if licence_el is None:
            licence_el = etree.Element(etree.QName(ns['mei'], 'licence'), nsmap=ns)
            useStmt_el.append(licence_el)

        # Add or update the @target attribute of the <licence> element
        licence_el.set('target', 'https://creativecommons.org/licenses/by-nc-sa/4.0/')

        # Add or update the text content of the <licence> element
        licence_el.text = 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License'


        # Add or update the <editor> elements
        editors = metadata_dict.get('Editor', '').split(' | ')
        editor_orcids = metadata_dict.get('Editor_ORCID', '').split(' | ')

        # Remove existing editor elements to avoid duplicates
        for existing_editor in fileDesc_el.findall('.//mei:editor', namespaces=ns):
            fileDesc_el.remove(existing_editor)

        for i, editor_name in enumerate(editors):
            if editor_name: # Check if editor_name is not empty
                editor_el = etree.Element(etree.QName(ns['mei'], 'editor'), nsmap=ns)
                fileDesc_el.append(editor_el)

                persName_el = etree.Element(etree.QName(ns['mei'], 'persName'), nsmap=ns)
                editor_el.append(persName_el)
                persName_el.text = editor_name.strip()

                # Add or update ORCID if available
                if i < len(editor_orcids) and editor_orcids[i]:
                     editor_el.set('orcid', editor_orcids[i].strip())


        # Add or update the <date> element within <fileDesc>
        date_el = fileDesc_el.find('mei:date', namespaces=ns)
        if date_el is None:
            date_el = etree.Element(etree.QName(ns['mei'], 'date'), nsmap=ns)
            fileDesc_el.append(date_el)

        # Add or update the @when attribute of the <date> element
        last_revised = metadata_dict.get('Last_Revised', '')
        if last_revised:
            date_el.set('when', last_revised)

        # Add or update the text content of the <date> element
        date_el.text = last_revised


        # Find or create the <workDesc> element
        workDesc_el = mei_head_el.find('mei:workDesc', namespaces=ns)
        if workDesc_el is None:
            workDesc_el = etree.Element(etree.QName(ns['mei'], 'workDesc'), nsmap=ns)
            mei_head_el.append(workDesc_el)

        # Find or create the <work> element
        work_el = workDesc_el.find('mei:work', namespaces=ns)
        if work_el is None:
            work_el = etree.Element(etree.QName(ns['mei'], 'work'), nsmap=ns)
            workDesc_el.append(work_el)

        # Add or update the <title> element within <work>
        work_title_el = work_el.find('mei:title', namespaces=ns)
        if work_title_el is None:
            work_title_el = etree.Element(etree.QName(ns['mei'], 'title'), nsmap=ns)
            work_el.append(work_title_el)
        work_title_el.text = metadata_dict.get('Title', '')

        # Add or update the <composer> element within <work>
        work_composer_el = work_el.find('mei:composer', namespaces=ns)
        if work_composer_el is None:
            work_composer_el = etree.Element(etree.QName(ns['mei'], 'composer'), nsmap=ns)
            work_el.append(work_composer_el)

        work_persName_el = work_composer_el.find('mei:persName', namespaces=ns)
        if work_persName_el is None:
            work_persName_el = etree.Element(etree.QName(ns['mei'], 'persName'), nsmap=ns)
            work_composer_el.append(work_persName_el)
        work_persName_el.text = metadata_dict.get('Composer_Name', '').replace('#265 ', '') # Remove '#265 ' prefix

        # Add or update @role="composer" to <persName> if not present
        if 'role' not in work_persName_el.attrib:
            work_persName_el.set('role', 'composer')

        # Add or update @sameas with VIAF and BNF IDs
        if sameas_uris:
            work_persName_el.set('sameas', ' '.join(sameas_uris))

        # Add or update the <creation> element within <work> (Corrected XML structure)
        creation_el = work_el.find('mei:creation', namespaces=ns)
        if creation_el is None:
            creation_el = etree.Element(etree.QName(ns['mei'], 'creation'), nsmap=ns)
            work_el.append(creation_el)

        # Add or update the <date> element within <creation>
        creation_date_el = creation_el.find('mei:date', namespaces=ns)
        if creation_date_el is None:
            creation_date_el = etree.Element(etree.QName(ns['mei'], 'date'), nsmap=ns)
            creation_el.append(creation_date_el)

        piece_date = metadata_dict.get('Piece_Date', '')
        if piece_date:
            creation_date_el.set('when', str(piece_date)) # Ensure date is a string
            creation_date_el.text = str(piece_date) # Add text content as well

        # Add or update the <genre> element within <work>
        genre_el = work_el.find('mei:genre', namespaces=ns)
        if genre_el is None:
            genre_el = etree.Element(etree.QName(ns['mei'], 'genre'), nsmap=ns)
            work_el.append(genre_el)
        genre_el.text = metadata_dict.get('Genre', '')


        # Find or create the <physDesc> element within <fileDesc>
        physDesc_el = fileDesc_el.find('mei:physDesc', namespaces=ns)
        if physDesc_el is None:
            physDesc_el = etree.Element(etree.QName(ns['mei'], 'physDesc'), nsmap=ns)
            fileDesc_el.append(physDesc_el)

        # Find or create the <sourceDesc> element within <physDesc>
        sourceDesc_el = physDesc_el.find('mei:sourceDesc', namespaces=ns)
        if sourceDesc_el is None:
            sourceDesc_el = etree.Element(etree.QName(ns['mei'], 'sourceDesc'), nsmap=ns)
            physDesc_el.append(sourceDesc_el)

        # Find or create the <source> element within <sourceDesc>
        source_el = sourceDesc_el.find('mei:source', namespaces=ns)
        if source_el is None:
            source_el = etree.Element(etree.QName(ns['mei'], 'source'), nsmap=ns)
            sourceDesc_el.append(source_el)

        # Add or update the <title> element within <source>
        source_title_el = source_el.find('mei:title', namespaces=ns)
        if source_title_el is None:
            source_title_el = etree.Element(etree.QName(ns['mei'], 'title'), nsmap=ns)
            source_el.append(source_title_el)
        source_title_el.text = metadata_dict.get('Source_Title', '')

        # Add or update the <date> element within <source>
        source_date_el = source_el.find('mei:date', namespaces=ns)
        if source_date_el is None:
            source_date_el = etree.Element(etree.QName(ns['mei'], 'date'), nsmap=ns)
            source_el.append(source_date_el)

        source_date = metadata_dict.get('Source_Date', '')
        if source_date:
             source_date_el.set('when', str(source_date)) # Ensure date is a string
             source_date_el.text = str(source_date) # Add text content as well

        # Add or update the <pubStmt> element within <source>
        source_pubStmt_el = source_el.find('mei:pubStmt', namespaces=ns)
        if source_pubStmt_el is None:
            source_pubStmt_el = etree.Element(etree.QName(ns['mei'], 'pubStmt'), nsmap=ns)
            source_el.append(source_pubStmt_el)

        # Add or update publisher 1 information within source pubStmt
        source_publisher1 = metadata_dict.get('Source_Publisher_1', '')
        publisher1_viaf = metadata_dict.get('Publisher_1_VIAF', '')
        publisher1_bnf = metadata_dict.get('Publisher_1_BNF_ID', '')

        if source_publisher1:
            publisher1_el = source_pubStmt_el.find(f".//mei:publisher[text()='{source_publisher1.strip()}']", namespaces=ns)
            if publisher1_el is None:
                 publisher1_el = etree.Element(etree.QName(ns['mei'], 'publisher'), nsmap=ns)
                 source_pubStmt_el.append(publisher1_el)
                 publisher1_el.text = source_publisher1.strip()

            if publisher1_viaf or publisher1_bnf:
                sameas_uris = []
                if publisher1_viaf:
                    sameas_uris.append(publisher1_viaf)
                if publisher1_bnf:
                    sameas_uris.append(publisher1_bnf)
                publisher1_el.set('sameas', ' '.join(sameas_uris))


        # Add or update publisher 2 information within source pubStmt
        source_publisher2 = metadata_dict.get('Source_Publisher_2', '')
        publisher2_viaf = metadata_dict.get('Publisher_2_VIAF', '')
        publisher2_bnf = metadata_dict.get('Publisher_2_BNF_ID', '')

        if source_publisher2:
            publisher2_el = source_pubStmt_el.find(f".//mei:publisher[text()='{source_publisher2.strip()}']", namespaces=ns)
            if publisher2_el is None:
                 publisher2_el = etree.Element(etree.QName(ns['mei'], 'publisher'), nsmap=ns)
                 source_pubStmt_el.append(publisher2_el)
                 publisher2_el.text = source_publisher2.strip()

            if publisher2_viaf or publisher2_bnf:
                sameas_uris = []
                if publisher2_viaf:
                    sameas_uris.append(publisher2_viaf)
                if publisher2_bnf:
                    sameas_uris.append(publisher2_bnf)
                publisher2_el.set('sameas', ' '.join(sameas_uris))

        # Add or update the <identifier> element within <source> for Permalink
        permalink = metadata_dict.get('Permalink', '')
        if permalink:
            identifier_el = source_el.find('mei:identifier', namespaces=ns)
            if identifier_el is None:
                identifier_el = etree.Element(etree.QName(ns['mei'], 'identifier'), nsmap=ns)
                source_el.append(identifier_el)
            identifier_el.text = permalink
            identifier_el.set('type', 'permalink')


        # Add or update the <locus> element within <source> for Source_Position
        source_position = metadata_dict.get('Source_Position', '')
        if source_position:
            locus_el = source_el.find('mei:locus', namespaces=ns)
            if locus_el is None:
                locus_el = etree.Element(etree.QName(ns['mei'], 'locus'), nsmap=ns)
                source_el.append(locus_el)
            locus_el.text = source_position


        # Add or update the <repository> element within <source> for location details
        source_location = metadata_dict.get('Source_Location', '')
        source_institution = metadata_dict.get('Source_Institution', '')
        source_shelfmark = metadata_dict.get('Source_Shelfmark', '')

        if source_location or source_institution or source_shelfmark:
            repository_el = source_el.find('mei:repository', namespaces=ns)
            if repository_el is None:
                repository_el = etree.Element(etree.QName(ns['mei'], 'repository'), nsmap=ns)
                source_el.append(repository_el)

            # Add or update <corpName> for institution
            if source_institution:
                corpName_el = repository_el.find('mei:corpName', namespaces=ns)
                if corpName_el is None:
                    corpName_el = etree.Element(etree.QName(ns['mei'], 'corpName'), nsmap=ns)
                    repository_el.append(corpName_el)
                corpName_el.text = source_institution

            # Add or update <geogName> for location
            if source_location:
                geogName_el = repository_el.find('mei:geogName', namespaces=ns)
                if geogName_el is None:
                    geogName_el = etree.Element(etree.QName(ns['mei'], 'geogName'), nsmap=ns)
                    repository_el.append(geogName_el)
                geogName_el.text = source_location

            # Add or update <shelfMark> for shelfmark
            if source_shelfmark:
                shelfMark_el = repository_el.find('mei:shelfMark', namespaces=ns)
                if shelfMark_el is None:
                    shelfMark_el = etree.Element(etree.QName(ns['mei'], 'shelfMark'), nsmap=ns)
                    repository_el.append(shelfMark_el)
                shelfMark_el.text = source_shelfmark


        # Add or update the <notes> element within <source> for Source_Reference
        source_reference = metadata_dict.get('Source_Reference', '')
        if source_reference:
            notes_el = source_el.find('mei:notes', namespaces=ns)
            if notes_el is None:
                notes_el = etree.Element(etree.QName(ns['mei'], 'notes'), nsmap=ns)
                source_el.append(notes_el)
            notes_el.text = source_reference


        # Save the updated MEI file
        output_path = os.path.join(output_folder, os.path.basename(mei_file_path))
        try:
            tree.write(output_path, pretty_print=True, xml_declaration=True, encoding='utf-8')
            print(f"Successfully updated metadata for {os.path.basename(mei_file_path)} and saved to {output_path}")
        except Exception as e:
            print(f"Error saving updated MEI file {output_path}: {e}")


