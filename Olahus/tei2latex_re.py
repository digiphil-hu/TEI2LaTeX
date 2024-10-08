# This script converts letters encoded in XML to LaTeX files.
# Author: https://github.com/gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal


import time
from bs4 import BeautifulSoup
from Olahus.count import count_xml_body, count_latex_body, file_list, change_xml_filename
from normalize import normalize_text, latex_escape, remove_xml_tags_from_latex
from paragraph import paragraph
from header import header2latex
import lxml


def text2latex(soup, letternum, filename):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for float_p in soup.floatingText.find_all("p"):
        float_p = normalize_text(float_p, {"all"}).text
        text_latex += r"\noindent{}\textit{\small " + float_p + "}"
    soup.floatingText.extract()

    text_latex += "\n\n" + r"\medskip{}" + "\n"

    # Letter text
    text_latex += "\n" \
                  + r"\selectlanguage{latin}" + "\n" \
                  + r"\makeatletter" + "\n" \
                  + r"\renewcommand*{\footfootmarkA}{" + letternum + r"\,\textsuperscript{\@nameuse{@thefnmarkA}\,}}" \
                  + r"\makeatother" + "\n" \
                  + r"\beginnumbering" + "\n" \
                  + r"\firstlinenum{5}" + "\n" \
                  + r"\linenumincrement{5}" + "\n" \
                  + r"\Xtxtbeforenumber[A]{" + letternum + ",}" + "\n" \
                  + r"\Xtxtbeforenumber[B]{" + letternum + ",}" + "\n"

    # Paragraph
    for p in soup.body.div.find_all("p"):
        p = paragraph(p, filename=filename)
        if len(p.text.replace(" ", "")) > 0:
            text_latex += "\n" \
                          + r"\pstart" + "\n" \
                          + p.text + "\n" \
                          + r"\pend" + "\n"

    # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head, {"all"})

        for index_p, p in enumerate(div.find_all("p")):
            p = paragraph(p, filename=filename)
            if len(p.text.replace(" ", "")) > 0:
                if index_p == 0:
                    text_latex += "\n" \
                                  + r"\pstart" + "\n" \
                                  + r"[" + verso_head.text + "]" + "\n" \
                                  + p.text + "\n" \
                                  + r"\pend" + "\n"
                else:
                    text_latex += "\n" \
                              + r"\pstart" + "\n" \
                              + p.text + "\n" \
                              + r"\pend" + "\n"

    text_latex += "\n" \
                  + r"\endnumbering" + "\n\n" \
                  + r"\selectlanguage{english}" + "\n"
    # text_latex += "\n" + r"\pagebreak" + "\n\n"

    text_latex = latex_escape(text_latex)

    return text_latex


def transform_header_body(xml, num):
    file_name = xml.split("/")[-1]
    # print(file_name)
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Normalize xml: removes tab, linebreak, double space
        sp = normalize_text(sp, {"xml"})

        # Delete <ref> tags from body and from header note type critIntro
        for item in sp.body.find_all("ref"):
            item.extract()
        for item in sp.teiHeader.find_all("note", {"type": "critIntro"}):
            for r in item.find_all("ref"):
                r.extract()

        # Delete milestone unit pagebreak
        for pb in sp.body.find_all("milestone", {"unit": "pb"}):
            pb.extract()

        # Remove <persName> if it contains <add> or <del> tags.
        for pers in sp.body.find_all("persName"):
            for nested in pers.find_all():
                try:
                    if nested.name == "add" or nested.name == "del":
                        pers.unwrap()
                    if nested.name == "choice":
                        print("ERROR: <choice> as child of <persName>")
                except ValueError:
                    pass

        # If <quote> not under <p> => <p><quote>
        for q in sp.find_all("quote"):
            par = q.find_parent()
            if par.name == "div":
                note_q = q.next_sibling
                p_q_note = BeautifulSoup("<p>" + str(q) + str(note_q) + "</p>", "xml")
                q.replace_with(p_q_note)
                note_q.extract()

        # List note type translation if it has <hi> but no <p>
        for translation in sp.notesStmt.find_all("note", attrs={"type": "translation"}):
            if len(translation.find_all("hi")) > 0 and len(translation.find_all("p")) == 0:
                print("Missing <p> in translation: ", xml)

        # Do the job!
        with open("latex2.tex", "a", encoding="utf8") as f_latex:
            with open("xml_latex_log.tsv", "a", encoding="utf8") as f_log:
                # Write header
                h = header2latex(sp.teiHeader, num)
                f_latex.write(h[0])
                title_num = h[1]

                # Write text
                t = text2latex(sp.find("text"), letternum=title_num, filename=file_name)
                t = remove_xml_tags_from_latex(t)
                f_latex.write(t)

                # Write log
                xml_tup = count_xml_body(xml)
                latex_tup = count_latex_body(t)
                num_set = set()
                for i in range(7):
                    num_set.add(latex_tup[i] - xml_tup[i])
                if len(num_set) == 1 and 0 in num_set:
                    pass
                else:
                    print(f"{file_name}\t{latex_tup[0]-xml_tup[0]}\t{latex_tup[1]-xml_tup[1]}\t"
                          f"{latex_tup[2]-xml_tup[2]}\t{latex_tup[3]-xml_tup[3]}\t{latex_tup[4]-xml_tup[4]}"
                          f"\t{latex_tup[5]-xml_tup[5]}\t{latex_tup[6]-xml_tup[6]}",
                          file=f_log)


def main(dir_name_in, dir_name_out):
    with open("xml_latex_log.tsv", "w", encoding="utf8") as f:
        print("filename", "\t", "num_note_critic", "\t", "num_add_insert", "\t", "num_add_corr", "\t",
              "num_del_alone", "\t", "num_choice", "\t", "num_quote", "\t", "num_seg", file=f)
    with open("latex2.tex", "w", encoding="utf8") as f_w:
        with open("begin.txt", "r", encoding="utf8") as f_r:
            start = f_r.read()
            f_w.write(start)
    f_list = file_list(dir_name_in)
    begin = time.time()

    for num, i in enumerate(f_list):
        print(i)
        out = i.replace(dir_name_in, dir_name_out).replace(".xml", ".tex")
        transform_header_body(i, num)
    with open("latex2.tex", "a", encoding="utf8") as f_w:
        # End of latex doc
        f_w.write(r"\end{document}")
    end = time.time()
    print(end - begin)


def rename_files():
    dir_name_in = "/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML"
    f_list = file_list(dir_name_in)
    for i in f_list:
        change_xml_filename(i)


if __name__ == '__main__':
    # rename_files()
    dir_name_in = "XML"
    dir_name_out = "LaTeX"
    main(dir_name_in, dir_name_out)

