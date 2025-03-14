import os
import random
from lxml import etree
import xml.etree.ElementTree as ET

class MEI_Music_Feature_Processor:
    """
    A class for processing MEI XML files to correct various music features.
    """
    
    def __init__(self):
        """Initialize the MEI Music Feature Processor."""
        pass

    def process_music_features(self, mei_path,
                               output_folder,
                               remove_incipit=True,
                               remove_pb=True,
                               remove_sb=True,
                               remove_annotation=True,
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
                               voice_labels=True):
        """ 
        This function will correct various music feature problems in MEI files.  
        All the subfunctions have default values, but these can be changed by passing in a Boolean, 
        such as `remove_incipit = False`.

        Be sure to pass a directory for the output folder, such as `output_folder = MEI_Updates`

        To run the function, pass a list of mei_paths to the function. For example:

        output_folder = 'MEI_Updates'
        for mei_path in mei_paths:
            process_music_features(mei_path, output_folder)

        You can also specify which modules to use, via Booleans, for example:

        output_folder = 'MEI_Updates'
        for mei_path in mei_paths:
            process_music_features(mei_path, 
            remove_incipit=True,
            remove_variants=True,
            output_folder)



        """
        # get the file and build revised name
        full_path = os.path.basename(mei_path)
        basename = os.path.splitext(os.path.basename(full_path))[0]
        revised_name = basename + "_rev.mei"
        print('Getting ' + basename)
        
        # new
        try:
            # Use lxml.etree instead of xml.etree.ElementTree
            mei_doc = etree.parse(mei_path)
            root = mei_doc.getroot()
        except etree.ParseError as e:
            print(f"Error parsing {mei_path}: {e}")
            return f"Error: Could not parse {mei_path}. Make sure it contains valid XML."
        

        # Define the MEI namespace
        ns = {'mei': 'http://www.music-encoding.org/ns/mei'}

        # inicipt removal
        if remove_incipit == True:
            # Find measure with label="0" and n="1"
            incipit_xpath = '//mei:measure[@label="0"][@n="1"]'
            measures = root.xpath(incipit_xpath, namespaces=ns)
            
            if measures:
                incipit = measures[0]
                
                # Remove measure
                parent = incipit.getparent()
                if parent is not None:
                    parent.remove(incipit)
                    print("Measure removed successfully!")
                    
                    # Renumber remaining measures starting at 1
                    measures = root.xpath('//mei:measure', namespaces=ns)
                    print("\nRenumbering measures...")
                    for idx, measure in enumerate(measures, 1):  # Start enumeration at 1
                        old_label = measure.get('label')
                        old_num = measure.get('n')
                        
                        # Set both n and label to match the current position
                        new_number = str(idx)
                        measure.set('n', new_number)
                        measure.set('label', new_number)
                    
        # page break removal
        # pb removal
        if remove_pb == True:
            # Find pb elements
            pb_elements = root.findall('.//mei:pb', namespaces=ns)
            count = len(pb_elements)
            print(f"Found {count} page breaks to remove.")
            for pb in pb_elements:
                pb.getparent().remove(pb)
            
        # sb removal
        if remove_sb == True:
            # Find sb elements
            sb_elements = root.findall('.//mei:sb', namespaces=ns)
            count = len(sb_elements)
            print(f"Found {count} section breaks to remove.")
            for sb in sb_elements:
                sb.getparent().remove(sb)
              
        # remove annotation
        if remove_annotation == True:
            annotations = root.findall('.//mei:annot', namespaces=ns)
            count = len(annotations)
            print(f"Found {count} annotations to remove.")
            for annotation in annotations:
                annotation.getparent().remove(annotation)
                
        # variants
        if remove_variants == True:
            # Find all app elements (variant apparatus)
            apps = root.findall('.//mei:app', namespaces=ns)
            count = len(apps)
            print(f"Found {count} variants to correct.")
            for app in apps:
                # Get the parent layer
                app_parent_layer = app.getparent()
                
                # Find all lem elements containing notes
                lems = app.findall('.//mei:lem', namespaces=ns)
            
                # Move notes to parent layer
                for lem in lems:
                    notes = lem.findall('.//mei:note', namespaces=ns)
                    for note in notes:
                        # Remove note from current position
                        lem.remove(note)
                        # Add note to parent layer
                        app_parent_layer.append(note)
                
                # Remove all rdg elements
                rdgs = app.findall('.//mei:rdg', namespaces=ns)
                count = len(rdgs)
                # print(f"Found {count} readings to remove.")
                for rdg in rdgs:
                    rdg_parent_layer = rdg.getparent()
                    rdg_parent_layer.remove(rdg)
                
                # Finally, remove the app element itself
                app_parent_layer.remove(app)
        
        # remove anchored text tags
        if remove_anchored_text == True:
            # find all anchored
            anchored = root.findall('.//mei:anchoredText', namespaces=ns)

            # remove the anchors
            for anchor in anchored:
                # find parent of those anchors and remove the anchored text
                parent_layer = anchor.getparent()
                if parent_layer is not None:
                    parent_layer.remove(anchor)
                    print("Anchored text removed successfully!")
            
        # remove timestamp and velocity
        if remove_timestamp == True:
            # for notes
            print('Checking and Removing timestamp.')
            notes = root.findall('.//mei:note', namespaces=ns)
            for note in notes:
                # Remove timestamp attribute
                if 'tstamp.real' in note.attrib:
                    del note.attrib['tstamp.real']
                # Remove velocity attribute
                if 'vel' in note.attrib:
                    del note.attrib['vel']
            
            # Remove timestamp and velocity attributes from rests
            rests = root.findall('.//mei:rest', namespaces=ns)
            for rest in rests:
                if 'tstamp.real' in rest.attrib:
                    del rest.attrib['tstamp.real']
                if 'vel' in rest.attrib:
                    del rest.attrib['vel']
            
            # Remove timestamp and velocity attributes from mRests
            mrests = root.findall('.//mei:mRest', namespaces=ns)
            for mrest in mrests:
                if 'tstamp.real' in mrest.attrib:
                    del mrest.attrib['tstamp.real']
                if 'vel' in mrest.attrib:
                    del mrest.attrib['vel']
            
            # Remove tstamp2 from ties for Verovio compatibility
            ties = root.findall('.//mei:tie', namespaces=ns)
            for tie in ties:
                if 'tstamp' in tie.attrib:
                    del tie.attrib['tstamp']
                if 'tstamp2' in tie.attrib:
                    del tie.attrib['tstamp2']    
        
        # Remove chord elements
        if remove_chord == True:
            chords = root.findall('.//mei:chord', namespaces=ns)
            count = len(chords)
            print(f"Found {count} chord elements to remove.")

            for chord in chords:
                parent = chord.getparent()
                parent.remove(chord)
        
        # Remove Senfl brackets
        if remove_senfl_bracket == True:
            brackets = root.findall('.//mei:line[@type="bracket"]', namespaces=ns)
            count = len(brackets)
            print(f"Found {count} bracket elements to remove.")
            for bracket in brackets:
                parent = bracket.getparent()
                parent.remove(bracket)
        
        # Remove empty verse elements
        if remove_empty_verse == True:
            if remove_empty_verse:
                # Find all parent elements that might contain verses
                for parent in root.findall('.//mei:syllable', namespaces=ns):
                    # Find all verses within this parent
                    verses = parent.findall('mei:verse', namespaces=ns)
                    # Create a list of verses to keep
                    verses_to_keep = []
                    for verse in verses:
                        if list(verse):  # If verse has children
                            verses_to_keep.append(verse)
                    
                    # If we found empty verses, clear the parent and add back only non-empty verses
                    if len(verses_to_keep) < len(verses):
                        # Remove all verses from parent
                        for verse in verses:
                            parent.remove(verse)
                        # Add back only non-empty verses
                        for verse in verses_to_keep:
                            parent.append(verse)
        
        # Remove all lyrics
        if remove_lyrics == True:
            verses = root.findall('.//mei:verse', namespaces=ns)
            count = len(verses)
            print(f"Found {count} lyric elements to remove.")
            for verse in verses:
                parent = verse.getparent()
                parent.remove(verse)
        
        # Fix elisions
        if fix_elisions == True:
            verses = root.findall('.//mei:verse', namespaces=ns)
            for verse in verses:
                # Set all v numbers to 1
                verse.set('n', '1')
                
                # Find all syl elements
                syllables = verse.findall('.//mei:syl', namespaces=ns)
                
                # Check if there are more than one syl elements
                if len(syllables) > 1:
                    print(f"Found elided syllables to correct.")
                    
                    # Get the text of the first and second syllables
                    first_syllable = syllables[0].text or ""
                    second_syllable = syllables[1].text or ""
                    
                    # Concatenate the text with "=" as separator
                    new_text = f"{first_syllable}={second_syllable}"
                    
                    # Update the text of the first syllable
                    syllables[0].text = new_text
                    
                    # Set attributes for the first syllable
                    syllables[0].set('con', 'd')
                    syllables[0].set('wordpos', 'm')
                    
                    # Remove the second syllable
                    parent = syllables[1].getparent()
                    parent.remove(syllables[1])
        
        # Replace slurs with ties
        if slur_to_tie == True:
            slurs = root.findall('.//mei:slur', namespaces=ns)
            count = len(slurs)
            print(f"Found {count} slurs to correct as ties.")
            for slur in slurs:
                # Remove specific attributes
                for attr in ['layer', 'tstamp', 'tstamp2', 'staff']:
                    if attr in slur.attrib:
                        del slur.attrib[attr]
                
                # Change element name to 'tie'
                slur.tag = f"{{{ns['mei']}}}tie"

        #  combine layers
        if collapse_layers == True:

            staves = root.findall('.//mei:staff', namespaces=ns)
            for staff in staves:
                layers = staff.findall('.//mei:layer', namespaces=ns)
                for layer in layers:
                    if layer.get('n') != '1':  # Only process non-layer-1 elements
                        target_layer = staff.find('.//mei:layer[@n="1"]', namespaces=ns)
                        if target_layer is not None:
                            if layer.text or len(layer) > 0:  # Check for any content
                                # Move all children to target layer
                                for child in list(layer):
                                    target_layer.append(child)
                                # Remove the empty layer
                                layer.getparent().remove(layer)
                            

        
        # correcting ficta as supplied
        if correct_ficta == True:
            # remove 'dir' tags - try both with and without namespace
            dir_tags = root.findall('.//dir', namespaces=ns) + root.findall('.//mei:dir', namespaces=ns)
            print(f"Found {len(dir_tags)} dir tags to remove")
            for tag in dir_tags:
                tag.getparent().remove(tag)
        
            # Try both approaches to find notes with color attributes
            color_notes = root.findall('.//mei:note[@color]', namespaces=ns)
            color_count = len(color_notes) 
            print(f"Found {color_count} total color notes to correct as supplied.")
            
            if color_count > 0:
                for note in color_notes:
                    # Try both namespace approaches for finding accid elements
                    accid = note.find('mei:accid', namespaces=ns)
                    
                    if accid is not None:
                        # Handle accid.ges attributes
                        if 'accid.ges' in accid.attrib:
                            accid.set('accid', accid.get('accid.ges'))
                            del accid.attrib['accid.ges']
                            # print('deleted accid.ges')
                        
                        # Remove color attribute
                        del note.attrib['color']
                        # print('deleted color')
                        
                        # Get accid value
                        accid_value = accid.get('accid')
                        
                        # Generate unique IDs
                        note_random_id = random.randint(1000000, 9999999)
                        accid_random_id = random.randint(1000000, 9999999)
                        
                        
                        # ns for xml ids
                        XML_NS = 'http://www.w3.org/XML/1998/namespace'

                        # Create new supplied parent tag
                        supplied_tag = etree.SubElement(
                            note, 
                            'supplied',
                            attrib={
                                'reason': 'edit',
                                f'{{{XML_NS}}}id': f"m-{note_random_id}"  # Use Clark notation for xml:id
                            }
                        )
                        
                    
                        # Update the accid tag creation
                        new_accid_tag = etree.SubElement(
                            supplied_tag, 
                            'accid',
                            attrib={
                                'accid': accid_value,
                                'func': "edit",
                                'place': "above",
                                f'{{{XML_NS}}}id': f"m-{accid_random_id}"  # Use Clark notation for xml:id
                            }
                        )
                        
                        # Replace old accid tag with new structure
                        note.remove(accid)
                        # print("updated note with new supplied accidental")
                        
        # fix voice labels
        if voice_labels == True:
            # revert staffDef/label to staffDef/@label
            staffDefs = root.findall('.//mei:staffDef', namespaces=ns)
            count = len(staffDefs)
            print(f"Found {count} staff labels to correct.")
            
            for staffDef in staffDefs:
                label_elem = staffDef.find('mei:label', namespaces=ns)
                if label_elem is not None and label_elem.text:
                    staffDef.set('label', label_elem.text)
        
        
        # save the result
        output_file_path = os.path.join(output_folder, revised_name)
        
        # Get the MEI namespace
        mei_ns = "http://www.music-encoding.org/ns/mei"
        
        # Get the meiversion attribute from the root
        meiversion = root.get("meiversion", "4.0.0")
        xml_id = root.get("{http://www.w3.org/XML/1998/namespace}id", "m-1")
        
        # Convert to string and parse with lxml for better control
        # xml_string = ET.tostring(root)
        xml_string = etree.tostring(root)
        parser = etree.XMLParser(remove_blank_text=True)
        root_lxml = etree.fromstring(xml_string, parser)
        
        # Create a new XML tree with the proper namespace setup
        new_root = etree.Element("mei", 
                                nsmap={None: mei_ns},  # Default namespace without prefix
                                attrib={"meiversion": meiversion,
                                        "{http://www.w3.org/XML/1998/namespace}id": xml_id})
        
        # Copy the content from the original tree
        for child in root_lxml:
            new_root.append(child)
        
        # Remove namespace prefixes from all elements except the root
        for elem in new_root.iter():
            if elem is not new_root:  # Skip the root element
                if not hasattr(elem.tag, 'find') or elem.tag.find('}') == -1:
                    continue
                elem.tag = elem.tag.split('}', 1)[1]  # Remove namespace prefix
        
        # Format the XML with proper indentation
        etree.indent(new_root, space="    ")
        
        # Serialize to string with XML declaration
        formatted_xml = etree.tostring(
            new_root,
            pretty_print=True,
            encoding='utf-8',
            xml_declaration=True
        )
        
        # Write to file
        with open(output_file_path, 'wb') as f:
            f.write(formatted_xml)
        
        print(f'Saved updated {revised_name}')
        return formatted_xml

