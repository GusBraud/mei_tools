from bs4 import BeautifulSoup
from typing import Optional
from pathlib import Path

class MEI_Definition_Processor:
    def __init__(self, source_folder: Optional[str] = None, output_dir: Optional[str] = None):
        self.source_folder = Path(source_folder) if source_folder else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else Path("updated_MEI_files")
        self.soup = None
    
    def add_mei_declaration(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Adds MEI XML model declarations to the beginning of an XML document."""
        try:
            # Create the XML model declarations
            rng_declaration = '<?xml-model href="https://music-encoding.org/schema/4.0.1/mei-CMN.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
            sch_declaration = '<?xml-model href="https://music-encoding.org/schema/4.0.1/mei-CMN.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>\n'
            
            # Get the original XML declaration
            xml_decl = soup.prettify().split('\n')[0] + '\n'
            
            # Combine all declarations and content
            result = xml_decl + rng_declaration + sch_declaration + soup.prettify().split('\n', 1)[1]
            
            return BeautifulSoup(result, features='lxml-xml')
        except Exception as e:
            print(f"Error adding declarations: {str(e)}")
            raise

    def process_files(self, metadata_dict_list: list) -> dict:
        """Process MEI files and add declarations."""
        try:
            file_paths = self.get_source_files()
            results = {}
            
            for file_path in file_paths:
                try:
                    # Load the MEI file
                    self.soup = self.load_mei_file(file_path)
                    
                    # Add MEI declarations
                    self.soup = self.add_mei_declaration(self.soup)
                    
                    # Process metadata
                    metadata_dict = self._get_matching_dict(file_path.name, metadata_dict_list)
                    if metadata_dict:
                        self._apply_metadata_updates(metadata_dict)
                        
                        if self.output_dir:
                            output_path = self.output_dir / Path(file_path).relative_to(self.source_folder)
                            self.save_processed_file(self.soup, str(output_path))
                        
                        results[file_path] = "success"
                    else:
                        results[file_path] = "no_match"
                        
                except Exception as e:
                    results[file_path] = f"error: {str(e)}"
                    
            return results
        except Exception as e:
            print(f"Error processing files: {str(e)}")
            raise
