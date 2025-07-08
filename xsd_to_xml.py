import argparse
from lxml import etree
import random
import datetime


# --- Helper Functions for Sample Data Generation ---
def generate_sample_value(xsd_type_name):
    """Generates a sample value based on the XSD data type."""
    type_map = {
        # Basic XML Schema Built-in Types (all lowercase keys)
        "string": "sample_string",
        "normalizedstring": "sample_normalized_string",
        "token": "sample_token",
        "boolean": random.choice(["true", "false"]),
        "decimal": f"{random.uniform(1.0, 1000.0):.2f}",  # Format to 2 decimal places
        "integer": str(random.randint(1, 1000)),
        "long": str(random.randint(1000, 100000)),
        "int": str(random.randint(1, 1000)),
        "short": str(random.randint(1, 100)),
        "byte": str(random.randint(0, 127)),
        "nonnegativeinteger": str(random.randint(0, 1000)),
        "positiveinteger": str(random.randint(1, 1000)),
        "nonpositiveinteger": str(random.randint(-1000, 0)),
        "negativeinteger": str(random.randint(-1000, -1)),
        "double": f"{random.uniform(1.0, 1000.0):.4f}",
        "float": f"{random.uniform(1.0, 1000.0):.4f}",
        "duration": "P1Y2M3DT4H5M6S",  # Example duration
        "datetime": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),  # UTC time
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "date": datetime.date.today().isoformat(),
        "gyearmonth": datetime.datetime.now().strftime("%Y-%m"),
        "gyear": datetime.datetime.now().strftime("%Y"),
        "gmonthday": datetime.datetime.now().strftime("--%m-%d"),
        "gday": datetime.datetime.now().strftime("---%d"),
        "gmonth": datetime.datetime.now().strftime("--%m--"),
        "hexbinary": "0FB7",
        "base64binary": "AQIDBA==",
        "anyuri": "http://example.com/resource",
        "qname": "tns:sampleQName",
        "notation": "sample_notation",
        "id": "id" + str(random.randint(1000, 9999)),
        "idref": "idref" + str(random.randint(1000, 9999)),
        "idrefs": "idrefs_1 idrefs_2",
        "nmtoken": "sample_NMTOKEN",
        "nmtokens": "sample_NMTOKEN_1 sample_NMTOKEN_2",
        "name": "sample_Name",
        "ncname": "sampleNCName",
        "language": "en-US",
        "entity": "entity_name",
        "entities": "entity_name_1 entity_name_2",
        "notations": "notation_1 notation_2",
        "anysimpletype": "any_simple_type_value",  # Generic fallback
    }
    # Convert the input type name to lowercase for consistent lookup
    return type_map.get(xsd_type_name.lower(), f"UNKNOWN_TYPE_{xsd_type_name}")


# --- Core XML Generation Logic ---

class XSDToXMLGenerator:
    """
    Generates an XML instance document based on an XSD schema.
    Handles nested elements, attributes, data types, and occurrences.
    """
    XSD_NAMESPACE = "{http://www.w3.org/2001/XMLSchema}"

    def __init__(self, xsd_path):
        try:
            self.schema_doc = etree.parse(xsd_path)
            # etree.XMLSchema handles imports/includes internally when parsing the schema
            self.xmlschema = etree.XMLSchema(self.schema_doc)
            self.target_namespace = self.schema_doc.getroot().get('targetNamespace')
            # The namespace map for the root element will typically map the default namespace
            # to the targetNamespace of the schema.
            self.namespace_map = {None: self.target_namespace} if self.target_namespace else {}

            # For complex types defined globally, we need a lookup.
            # This uses findall() which correctly uses the namespace syntax.
            self.complex_types = self._get_global_definitions("complexType")
            self.simple_types = self._get_global_definitions("simpleType")

        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XSD syntax: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"XSD file not found: {xsd_path}")
        except Exception as e:
            # Catch any other lxml parsing errors during __init__
            raise Exception(f"Failed to load or parse XSD: {e}")

    def _get_global_definitions(self, tag_name):
        """Helper to get global complexType or simpleType definitions."""
        definitions = {}
        # Use findall with the correct namespace prefix for robust parsing
        for definition in self.schema_doc.getroot().findall(f"{self.XSD_NAMESPACE}{tag_name}"):
            name = definition.get("name")
            if name:
                definitions[name] = definition
        return definitions

    def _get_type_definition(self, type_name):
        """Resolves a type name to its XSD definition (complex or simple)."""
        if type_name is None:
            return None  # No explicit type defined

        # Check if it's a built-in XSD type (starts with xs:)
        if type_name.startswith("xs:"):
            return None  # No specific definition needed for built-in types, handle by name

        # Check if it's a custom type defined in the current schema's global definitions
        # This covers types defined directly in the main XSD file.
        if type_name in self.complex_types:
            return self.complex_types[type_name]

        if type_name in self.simple_types:
            return self.simple_types[type_name]

        # For types imported from other namespaces (e.g., iso20022_DRAFT_types.xsd),
        # their definitions aren't typically direct children of this schema document.
        # The XSD SchemaSet knows about them, but simple 'find' won't get them.
        # For this utility, we'll assume string if not found, but a more complex
        # solution might try to traverse the schemaSet or imported documents.
        # print(f"Warning: Could not find definition for custom type '{type_name}' in the current schema's global definitions. Assuming string type.")
        return None  # Fallback to handling by name as a simple type

    def _get_xsd_type_name(self, xsd_element):
        """
        Determines the effective XSD type name for an element or attribute.
        Handles direct type attributes, references, and inline complexType/simpleType definitions.
        """
        # Direct type attribute (e.g., <xs:element name="age" type="xs:int"/>)
        type_attr = xsd_element.get("type")
        if type_attr:
            if type_attr.startswith("xs:"):
                return type_attr.split(":")[1]  # Return 'int', 'string' etc.
            # If it's a custom type like 'tns:MyType', return 'MyType'
            if ":" in type_attr:
                return type_attr.split(":")[-1]
            return type_attr  # Custom type name

        # Check for reference to a global element or attribute
        ref_attr = xsd_element.get("ref")
        if ref_attr:
            # Resolving refs is complex; for elements, it usually means copying type info.
            # For this utility, we'll just treat it as a string placeholder if type isn't explicit.
            # A full implementation would look up the referenced element/attribute definition.
            # For now, let's assume if it's a ref and no type, it defaults to string.
            return "string"  # Fallback for referenced elements/attributes without explicit type

        # Inline complexType/simpleType definition
        complex_type_def = xsd_element.find(f"{self.XSD_NAMESPACE}complexType")
        if complex_type_def is not None:
            # Check for simpleContent within inline complexType
            simple_content_def = complex_type_def.find(f"{self.XSD_NAMESPACE}simpleContent")
            if simple_content_def is not None:
                extension_def = simple_content_def.find(f"{self.XSD_NAMESPACE}extension")
                if extension_def is not None:
                    base_type = extension_def.get("base")
                    if base_type and base_type.startswith("xs:"):
                        return base_type.split(":")[1]
                    # If base is a custom type, return its name. Otherwise, default.
                    if ":" in base_type:
                        return base_type.split(":")[-1]
                    return base_type if base_type else "string"  # Fallback if base not xs: type
            return None  # Inline complex type, not a named type we can map directly

        simple_type_def = xsd_element.find(f"{self.XSD_NAMESPACE}simpleType")
        if simple_type_def is not None:
            restriction = simple_type_def.find(f"{self.XSD_NAMESPACE}restriction")
            if restriction is not None:
                base_type = restriction.get("base")
                if base_type and base_type.startswith("xs:"):
                    return base_type.split(":")[1]
                # If base is a custom type, return its name. Otherwise, default.
                if ":" in base_type:
                    return base_type.split(":")[-1]
                return base_type if base_type else "string"
            return None  # Inline simple type, not a named type we can map directly

        # Fallback for elements without explicit type or inline definition (defaults to xs:anyType, often implies string)
        return "string"

    def _get_occurrence(self, xsd_node):
        """Gets minOccurs and maxOccurs for an XSD element."""
        min_occurs = int(xsd_node.get("minOccurs", 1))
        max_occurs_str = xsd_node.get("maxOccurs", "1")
        max_occurs = float('inf') if max_occurs_str == "unbounded" else int(max_occurs_str)
        return min_occurs, max_occurs

    def _process_content_model(self, parent_xml_element, content_model_element, path=""):
        """
        Recursively processes complexType content models (sequence, all, choice, complexContent, simpleContent).
        `content_model_element` can be xs:sequence, xs:all, xs:choice, xs:complexContent, xs:simpleContent.
        """
        current_path = path

        if content_model_element is None:
            return

        # Handle xs:sequence, xs:all
        if content_model_element.tag in [f"{self.XSD_NAMESPACE}sequence", f"{self.XSD_NAMESPACE}all"]:
            for child_xsd_element in content_model_element.findall(f"{self.XSD_NAMESPACE}element"):
                self._generate_xml_element(parent_xml_element, child_xsd_element, current_path)
            # Also handle groups if present (xs:group ref="...")
            for group_ref in content_model_element.findall(f"{self.XSD_NAMESPACE}group"):
                # This is a simplification. Full group resolution would require looking up global groups.
                # For now, we'll just log a warning.
                print(
                    f"Warning: xs:group reference '{group_ref.get('ref')}' at {current_path} is not fully resolved. Skipping group content.")
        elif content_model_element.tag == f"{self.XSD_NAMESPACE}choice":
            # For simplicity, pick the first element in a choice
            # You could extend this to randomly pick one or offer user choice
            first_choice = content_model_element.find(f"{self.XSD_NAMESPACE}element")
            if first_choice is not None:
                # print(f"Info: Processing first element in xs:choice at {current_path}/{first_choice.get('name')}")
                self._generate_xml_element(parent_xml_element, first_choice, current_path)
            else:
                print(f"Warning: xs:choice at {current_path} contains no elements.")
        elif content_model_element.tag == f"{self.XSD_NAMESPACE}complexContent":
            extension = content_model_element.find(f"{self.XSD_NAMESPACE}extension")
            restriction = content_model_element.find(f"{self.XSD_NAMESPACE}restriction")

            if extension is not None:
                base_type_name = extension.get("base")
                base_type_def = self._get_type_definition(
                    base_type_name)  # Will be None for built-in or types from other namespaces

                # Process attributes and content from the base type if found
                if base_type_def:
                    self._process_attributes(parent_xml_element, base_type_def)
                    base_content_model = base_type_def.find(f"{self.XSD_NAMESPACE}sequence") or \
                                         base_type_def.find(f"{self.XSD_NAMESPACE}all") or \
                                         base_type_def.find(f"{self.XSD_NAMESPACE}choice") or \
                                         base_type_def.find(f"{self.XSD_NAMESPACE}complexContent")
                    if base_content_model is not None:
                        self._process_content_model(parent_xml_element, base_content_model, current_path)
                elif base_type_name:
                    # If base type is not found (e.g., from an imported schema), assume basic processing for it.
                    # This is a heuristic.
                    # print(f"Info: Base type '{base_type_name}' for extension at {current_path} not found among global types. Attributes/content might be incomplete.")
                    pass  # Attributes within extension are still processed below

                # Process attributes and sequence specifically defined in the extension
                self._process_attributes(parent_xml_element, extension)
                sequence = extension.find(f"{self.XSD_NAMESPACE}sequence")
                if sequence is not None:
                    self._process_content_model(parent_xml_element, sequence, current_path)
            elif restriction is not None:
                # Handle complexContent restriction (less common for full content model)
                print(
                    f"Warning: xs:complexContent with restriction at {current_path} found. This is a complex case and might not be fully generated.")
                self._process_attributes(parent_xml_element, restriction)
                sequence = restriction.find(f"{self.XSD_NAMESPACE}sequence")
                if sequence is not None:
                    self._process_content_model(parent_xml_element, sequence, current_path)
            else:
                print(f"Warning: xs:complexContent at {current_path} has no extension or restriction.")

        elif content_model_element.tag == f"{self.XSD_NAMESPACE}simpleContent":
            extension = content_model_element.find(f"{self.XSD_NAMESPACE}extension")
            restriction = content_model_element.find(f"{self.XSD_NAMESPACE}restriction")

            if extension is not None:
                base_type_name = extension.get("base")
                # The text content comes from the base type of the extension
                if base_type_name:
                    if base_type_name.startswith("xs:"):
                        parent_xml_element.text = generate_sample_value(base_type_name.split(":")[1])
                    else:
                        # Custom base type for simple content
                        parent_xml_element.text = generate_sample_value(base_type_name.split(":")[-1])
                else:
                    parent_xml_element.text = generate_sample_value("string")  # Fallback
                # Handle attributes defined within the simpleContent extension
                self._process_attributes(parent_xml_element, extension)
            elif restriction is not None:
                base_type_name = restriction.get("base")
                if base_type_name:
                    if base_type_name.startswith("xs:"):
                        parent_xml_element.text = generate_sample_value(base_type_name.split(":")[1])
                    else:
                        # If there are enumerations or other facets, handle them
                        enum_values = [e.get("value") for e in restriction.findall(f"{self.XSD_NAMESPACE}enumeration")]
                        if enum_values:
                            parent_xml_element.text = random.choice(enum_values)
                        else:
                            # Custom base type, but no enums - generate generic sample
                            parent_xml_element.text = generate_sample_value(base_type_name.split(":")[-1])
                else:
                    # No base type, check for enums directly under restriction
                    enum_values = [e.get("value") for e in restriction.findall(f"{self.XSD_NAMESPACE}enumeration")]
                    if enum_values:
                        parent_xml_element.text = random.choice(enum_values)
                    else:
                        parent_xml_element.text = generate_sample_value("string")  # Fallback
                # Handle attributes defined within the simpleContent restriction
                self._process_attributes(parent_xml_element, restriction)
            else:
                print(f"Warning: simpleContent at {current_path} has no extension or restriction.")
        else:
            print(
                f"Warning: Unhandled content model tag: {content_model_element.tag} at {current_path}. Skipping content generation for this part.")

    def _process_attributes(self, xml_element, xsd_definition):
        """Processes attributes for an XML element from an XSD definition (element or complexType)."""
        # Find attributes directly defined within the xsd_definition (e.g., <xs:element> or <xs:complexType>)
        for attr in xsd_definition.findall(f"{self.XSD_NAMESPACE}attribute"):
            attr_name = attr.get("name")
            if attr_name:
                attr_type = self._get_xsd_type_name(attr)
                attr_value = generate_sample_value(attr_type)
                xml_element.set(attr_name, attr_value)
            else:
                # Handle attribute references (e.g., <xs:attribute ref="tns:myAttribute"/>)
                ref_attr = attr.get("ref")
                if ref_attr:
                    # This is a simplification. Resolving attribute refs requires looking up global attributes.
                    # For now, we'll just set a placeholder.
                    # A full solution would parse the ref, find the global attribute, and get its type.
                    resolved_name = ref_attr.split(":")[-1]  # Simple extraction of local name
                    xml_element.set(resolved_name, f"ref_value_for_{resolved_name}")
                else:
                    print(
                        f"Warning: Attribute definition without 'name' or 'ref' found in {xsd_definition.tag}. Skipping.")

        # Handle attributeGroup references
        for attr_group_ref in xsd_definition.findall(f"{self.XSD_NAMESPACE}attributeGroup"):
            ref_name = attr_group_ref.get("ref")
            if ref_name:
                # This is a simplification. Resolving attributeGroup refs requires looking up global attributeGroups
                # and then processing their contained attributes.
                print(
                    f"Warning: xs:attributeGroup reference '{ref_name}' found. This is not fully resolved. Skipping group content.")

    def _generate_xml_element(self, parent_xml_node, xsd_element_def, current_path=""):
        """
        Recursively generates an XML element based on its XSD definition.
        `xsd_element_def` is an lxml element representing an <xs:element>.
        """
        element_name = xsd_element_def.get("name")
        if not element_name:
            print(f"Warning: Skipping unnamed element in XSD at {current_path}")
            return

        current_path = f"{current_path}/{element_name}"

        min_occurs, max_occurs = self._get_occurrence(xsd_element_def)

        if min_occurs == 0 and max_occurs == 0:
            return  # Don't generate if minOccurs=0 and maxOccurs=0

        # Determine how many times to generate this element
        num_occurrences = 1  # Default to 1 occurrence
        if max_occurs == float('inf'):
            # Generate at least min_occurs, up to a small random number for unbounded
            num_occurrences = random.randint(min_occurs, min(min_occurs + 1, 2))
            if num_occurrences == 0 and min_occurs == 0:  # Ensure at least one if minOccurs=0 but maxOccurs=unbounded
                num_occurrences = 1
        elif max_occurs > 1:
            num_occurrences = random.randint(min_occurs, max_occurs)
            if num_occurrences == 0 and min_occurs == 0:  # Ensure at least one if minOccurs=0 but maxOccurs>1
                num_occurrences = 1
        elif min_occurs == 0 and random.random() < 0.5:  # 50% chance to skip optional elements (minOccurs=0)
            num_occurrences = 0

        if num_occurrences == 0:
            return  # Skip if randomly decided not to generate optional element

        for _ in range(num_occurrences):
            xml_element = etree.SubElement(parent_xml_node, element_name, nsmap=self.namespace_map)

            # --- Determine Element's Type and Process ---
            xsd_type_name = self._get_xsd_type_name(xsd_element_def)
            xsd_type_def = self._get_type_definition(xsd_type_name)  # Will be None for built-in or inline types

            if xsd_type_def is not None:
                # This element refers to a globally defined complexType or simpleType
                # Process attributes defined directly on the type definition
                self._process_attributes(xml_element, xsd_type_def)

                # Process content model (sequence, all, choice, complexContent, simpleContent) if it's a complex type
                complex_type_content = xsd_type_def.find(f"{self.XSD_NAMESPACE}sequence") or \
                                       xsd_type_def.find(f"{self.XSD_NAMESPACE}all") or \
                                       xsd_type_def.find(f"{self.XSD_NAMESPACE}choice") or \
                                       xsd_type_def.find(f"{self.XSD_NAMESPACE}complexContent") or \
                                       xsd_type_def.find(f"{self.XSD_NAMESPACE}simpleContent")

                if complex_type_content is not None:
                    self._process_content_model(xml_element, complex_type_content, current_path)
                elif xsd_type_def.tag == f"{self.XSD_NAMESPACE}simpleType":
                    # If it's a globally defined simple type, generate text content directly
                    restriction = xsd_type_def.find(f"{self.XSD_NAMESPACE}restriction")
                    if restriction is not None:
                        base_type = restriction.get("base")
                        if base_type and base_type.startswith("xs:"):
                            xml_element.text = generate_sample_value(base_type.split(":")[1])
                        else:
                            # Handle enums if present
                            enum_values = [e.get("value") for e in
                                           restriction.findall(f"{self.XSD_NAMESPACE}enumeration")]
                            if enum_values:
                                xml_element.text = random.choice(enum_values)
                            else:
                                xml_element.text = f"SIMPLE_TYPE_NO_BASE_OR_ENUM_{xsd_type_name}"
                    else:
                        xml_element.text = f"SIMPLE_TYPE_NO_RESTRICTION_{xsd_type_name}"
                else:
                    # Complex type with no explicit content model (e.g., empty complex type or only attributes)
                    pass

            else:
                # Element has an inline definition or is a built-in type
                # Process attributes defined directly on the element definition
                self._process_attributes(xml_element, xsd_element_def)

                # Check for inline complexType definition
                inline_complex_type = xsd_element_def.find(f"{self.XSD_NAMESPACE}complexType")
                if inline_complex_type is not None:
                    # Process content model of the inline complex type
                    content_model = inline_complex_type.find(f"{self.XSD_NAMESPACE}sequence") or \
                                    inline_complex_type.find(f"{self.XSD_NAMESPACE}all") or \
                                    inline_complex_type.find(f"{self.XSD_NAMESPACE}choice") or \
                                    inline_complex_type.find(f"{self.XSD_NAMESPACE}complexContent") or \
                                    inline_complex_type.find(f"{self.XSD_NAMESPACE}simpleContent")
                    if content_model is not None:
                        self._process_content_model(xml_element, content_model, current_path)
                    elif inline_complex_type.find(f"{self.XSD_NAMESPACE}simpleContent") is None:
                        # If it's a complex type but without any sequence/all/choice/simpleContent, it might be empty or just has attributes.
                        pass  # Attributes are already processed.
                else:
                    # Element is a simple type (either built-in or inline simpleType)
                    inline_simple_type = xsd_element_def.find(f"{self.XSD_NAMESPACE}simpleType")
                    if inline_simple_type is not None:
                        restriction = inline_simple_type.find(f"{self.XSD_NAMESPACE}restriction")
                        if restriction is not None:
                            base_type = restriction.get("base")
                            if base_type and base_type.startswith("xs:"):
                                xml_element.text = generate_sample_value(base_type.split(":")[1])
                            else:
                                enum_values = [e.get("value") for e in
                                               restriction.findall(f"{self.XSD_NAMESPACE}enumeration")]
                                if enum_values:
                                    xml_element.text = random.choice(enum_values)
                                else:
                                    xml_element.text = f"INLINE_SIMPLE_TYPE_NO_BASE_OR_ENUM"
                        else:
                            xml_element.text = f"INLINE_SIMPLE_TYPE_NO_RESTRICTION"
                    else:
                        # Default to text content for simple elements without inline definitions
                        xml_element.text = generate_sample_value(xsd_type_name)

    def generate_xml(self, root_element_name=None):
        """
        Generates the root XML element and recursively populates it.
        For schemas like camt.053.001.08, the root element 'Document' is often
        the only direct child of xs:schema.
        """
        # Find the main root element definition in the XSD
        # For camt.xsd, this is typically <xs:element name="Document">
        selected_root_xsd_element = None

        if root_element_name:
            # If a specific root name is given, try to find it among global elements
            # Use direct find for elements that are direct children of the schema root
            selected_root_xsd_element = self.schema_doc.getroot().find(
                f"{self.XSD_NAMESPACE}element[@name='{root_element_name}']")
            if selected_root_xsd_element is None:
                raise ValueError(f"Root element '{root_element_name}' not found in XSD.")
        else:
            # If no specific root name, assume the first global element is the intended root.
            # This is common for single-document schemas like camt.053.
            selected_root_xsd_element = self.schema_doc.getroot().find(f"{self.XSD_NAMESPACE}element")
            if selected_root_xsd_element is None:
                raise ValueError("No global element definition found in the XSD to start XML generation.")
            print(
                f"Info: No specific root element specified. Using first global element: '{selected_root_xsd_element.get('name')}'")

        root_name = selected_root_xsd_element.get("name")

        # Ensure the target namespace is correctly associated with the root element
        # The 'None' key sets the default namespace.
        root_element = etree.Element(root_name, nsmap=self.namespace_map)

        # Process the selected root element's definition
        self._generate_xml_element(root_element, selected_root_xsd_element)

        return etree.tostring(root_element, pretty_print=True, encoding='utf-8', xml_declaration=True)


### Command Line Interface and Example Usage

def main():
    parser = argparse.ArgumentParser(
        description="Generate an XML instance document from an XSD schema.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("xsd_file", help="Path to the input XSD schema file.")
    parser.add_argument("-o", "--output", default="output.xml",
                        help="Path to the output XML file (default: output.xml).")
    parser.add_argument("-r", "--root", help="Name of the root element to start generation from "
                                             "(if XSD has multiple global elements). "
                                             "If not specified, the first global element is used.")

    args = parser.parse_args()

    try:
        generator = XSDToXMLGenerator(args.xsd_file)
        xml_output = generator.generate_xml(root_element_name=args.root)

        with open(args.output, "wb") as f:
            f.write(xml_output)

        print(f"\nXML generated successfully and saved to: {args.output}")

    except (ValueError, FileNotFoundError, Exception) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
