"""Find TEI source errors that require manual correction before conversion."""

from pathlib import Path
import string

from lxml import etree


XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
VALID_HI_RENDS = {"bold", "expanded", "italic", "smallcap", "super"}


def _local_name(element):
    if element is None or not isinstance(element.tag, str):
        return None
    return etree.QName(element).localname


def _format_error(filename, line, error_type, explanation):
    return f"{filename}, line {line}: {error_type} — {explanation}"


def find_manual_corrections(xml_path):
    """Return human-readable, source-line-based errors for one TEI XML file."""
    xml_path = Path(xml_path)
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    errors = []

    def add(element, error_type, explanation, line=None):
        source_line = line if line is not None else element.sourceline
        errors.append(
            _format_error(xml_path.name, source_line, error_type, explanation)
        )

    # Report parser errors, but give empty xml:id attributes a clearer correction.
    for parser_error in parser.error_log:
        if "xml:id : attribute value  is not an NCName" not in parser_error.message:
            add(
                root,
                "INVALID_XML",
                parser_error.message,
                line=parser_error.line,
            )

    for element in tree.xpath(
        '//*[@xml:id=""]', namespaces={"xml": XML_NAMESPACE}
    ):
        add(
            element,
            "EMPTY_XML_ID",
            "remove the empty xml:id attribute or assign a valid XML name",
        )

    for note in tree.xpath('.//note[@type="translation"]'):
        if note.xpath('.//hi') and not note.xpath('.//p'):
            add(
                note,
                "TRANSLATION_NOTE_MISSING_P",
                "wrap the translation note content in a <p> element",
            )

    for quote in tree.xpath(".//quote"):
        intervening_text = (quote.tail or "").strip()
        following_element = quote.getnext()

        if intervening_text:
            if all(character in string.punctuation for character in intervening_text):
                add(
                    quote,
                    "PUNCTUATION_BETWEEN_QUOTE_AND_NOTE",
                    f'move {intervening_text!r} from after </quote> to after </note>',
                )
            else:
                add(
                    quote,
                    "TEXT_BETWEEN_QUOTE_AND_NOTE",
                    "move the intervening text after the quote's <note>",
                )

        if _local_name(following_element) != "note":
            add(
                quote,
                "QUOTE_NOTE_MISSING",
                "add a <note type=\"quote\"> immediately after </quote>",
            )
        elif following_element.get("type") != "quote":
            add(
                following_element,
                "QUOTE_NOTE_WRONG_TYPE",
                f'change note type {following_element.get("type")!r} to "quote"',
            )

    for addition in tree.xpath('.//add[@type="corr"]'):
        deletion = addition.getprevious()
        if _local_name(deletion) != "del":
            add(
                addition,
                "ADD_CORR_WITHOUT_PRECEDING_DEL",
                "place the corresponding <del> immediately before this <add>",
            )
        elif deletion.get("corresp") != addition.get("corresp"):
            add(
                addition,
                "DEL_ADD_CORRESP_MISMATCH",
                "make the adjacent <del> and <add> corresp attributes identical",
            )

    for choice in tree.xpath(".//choice"):
        if not choice.xpath("./orig"):
            add(
                choice,
                "CHOICE_MISSING_ORIG",
                "add the required <orig> child",
            )
        if not choice.xpath("./supplied"):
            add(
                choice,
                "CHOICE_MISSING_SUPPLIED",
                "add the required <supplied> child",
            )
        if any(_local_name(parent) == "persName" for parent in choice.iterancestors()):
            add(
                choice,
                "CHOICE_INSIDE_PERSNAME",
                "move <choice> outside <persName> or restructure the personal name",
            )

    for element in tree.xpath(".//orig | .//supplied"):
        if _local_name(element.getparent()) != "choice":
            element_name = _local_name(element)
            add(
                element,
                f"{element_name.upper()}_OUTSIDE_CHOICE",
                f"make <{element_name}> a direct child of <choice>",
            )

    for paragraph in tree.xpath(".//p//p"):
        add(
            paragraph,
            "NESTED_P",
            "remove the nested paragraph structure",
        )

    for deletion in tree.xpath(".//del//del"):
        add(
            deletion,
            "NESTED_DEL",
            "remove the nested deletion structure",
        )

    for highlighted in tree.xpath(".//hi"):
        rend = highlighted.get("rend")
        if rend not in VALID_HI_RENDS:
            add(
                highlighted,
                "HI_INVALID_REND",
                f"replace rend={rend!r} with a supported value",
            )

    return sorted(errors, key=lambda error: (int(error.split("line ", 1)[1].split(":", 1)[0]), error))


def write_manual_correction_report(xml_paths, output_path):
    """Write one human-readable line per manual XML correction."""
    corrections = []
    for xml_path in xml_paths:
        corrections.extend(find_manual_corrections(xml_path))

    with open(output_path, "w", encoding="utf8") as report:
        for correction in corrections:
            print(correction, file=report)

    return corrections
