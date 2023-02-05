# What tags are there under <quote>
# Milestone unit "p": where?
import os
import re
from bs4 import BeautifulSoup


def normalize_text(string):
    # Input and output: STRING!!!! [ and ] => {}
    string = string.replace("\n\t", "")
    string = re.sub('\s+', " ", string)
    string = re.sub("\[", "{[}", string)
    string = re.sub("\]", "{]}", string)
    string = re.sub(r'''(</del>)\s+(<add corresp="[a-zA-Z]+" type="corr")''', r"\1\2", string)
    return string


def main(xml):
    filename = xml.lstrip("/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML")
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")
        sp1 = normalize_text(str(sp))
        sp = BeautifulSoup(sp1, "xml")

        # Delete <ref> tags
        for i in sp.find_all("ref"):
            i.extract()

        # Error check <del><add>
        for d in sp.find_all("del"):
            if str(d.next_sibling).startswith("<add"):
                d_cor = d["corresp"]
                a_cor = d.next_sibling["corresp"]
                if d_cor != a_cor:
                    print("File name: " + xml + "Del corresp: " + d_cor + "Add corrsp: " + a_cor)

        # <choice> <orig> és <supplied> check
        for ch in sp.find_all("choice"):
            if len(ch.find_all("orig")) == 0:
                print(ch, xml)
            if len(ch.find_all("supplied")) == 0:
                print(ch, xml)

        # <orig><supplied> under <choice>
        for sup in sp.find_all("supplied"):
            parent = sup.find_parent(re.compile("[a-zA-Z]+"))
            if parent.name != "choice":
                print(parent.name, xml)
        for orig in sp.find_all("orig"):
            parent = sup.find_parent(re.compile("[a-zA-Z]+"))
            if parent.name != "choice":
                print(parent.name, xml)

        # p in p
        for p_p in sp.p.find_all("p"):
            print("ERROR: p\p: ", xml)

        # <quote><p>; <quote><quote>; <quote> + MISSING sibling
        for q in sp.find_all("quote"):
            if q.next_sibling is None:
                print("Quote next tag missing: ", xml)
            if q.next_sibling is not None and q.next_sibling.name != "note":
                if q.next_sibling != " ":
                    print(f"Quote but no note, but: {q.next_sibling.name}", xml)
            for q_sub in sp.quote.findChildren(re.compile("[a-zA-Z]+")):
                if q_sub.name == "p":
                    print("Quote alatt: ", xml)

        # <quote> in verso?
        for div in sp.find_all("div", attrs={"type": "verso"}):
            for elem in div.find_all("quote"):
                print("Quote in verso: ", xml)

        # del alatt del
        for d1 in sp.find_all("del"):
            for d2 in d1.find_all("del"):
                print("ERROR: del/del: ", xml)

        for para in sp.find_all("p"):
            para_parent = para.find_parent()
            if para_parent.name == "body" and para_parent.find_parent().name != "floatingText":
                print("ERROR: text/body/p in:", filename)

        # Remove <persName> if it contains <add> or <del> tags.
        for pers in sp.body.find_all("persName"):
            for nested in pers.find_all():
                try:
                    if nested.name == "add" or nested.name == "del":
                        pers.unwrap()
                    if nested.name == "choice":
                        print("ERROR: <choice> as child of <persName>")
                except ValueError:
                    continue


        # for n in sp.body.find_all("note"):
        #     try:
        #         if n["type"] == "critic":
        #             father = n.find_parent()
        #             if father.name != "p":
        #                 print(father.name)
        #                 if father.name == "quote":
        #                     print("quote", n, xml)
        #     except KeyError:
        #         print(n, "\t", xml)
        # taglist = ["persName", "placeName", "add"]
        # for del_alone in sp.body.find_all("del"):
        #     if not str(del_alone.next_sibling).startswith("<add"):
        #         if del_alone.previous_element.name is None:
        #             if del_alone.previous_element.text.replace(" ", "") == "":
        #                 try:
        #                     prev_prev = del_alone.find_previous_sibling()
        #                     # print(prev_prev.name)
        #                     if prev_prev.name in taglist:
        #                         raw_text = prev_prev.text
        #                         print("Name, Add", raw_text)
        #                     if prev_prev.name == "choice":
        #                         raw_text = prev_prev.supplied.text
        #                         print("Choice", raw_text)
        #                     if prev_prev.name == "note":
        #                         raw_text = prev_prev.previous_element.text
        #                         print("note", raw_text)
        #                 except AttributeError:
        #                     raw_text = "VEZÉRSZÓ"
        #                     print("NINCS előző tag!")
        #             else:
        #                 raw_text = del_alone.previous_element.text
        #                 print("Szöveg, tele.", raw_text)
        #         else:
        #             # print(xml.lstrip("/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML"))
        #             # print(del_alone.previous_element.name)
        #             if del_alone.previous_element.name == "add":
        #                 raw_text = del_alone.previous_element.text
        #                 print("Add", raw_text)
        #             if del_alone.previous_element.name == "milestone":
        #                 prev_elem = del_alone.previous_element
        #                 raw_text = prev_elem.previous_element.text
        #                 print("Milestone", raw_text)
        #             if del_alone.previous_element.name == "p":
        #                 raw_text = "VEZÉRSZÓ"
        #                 print("p", raw_text)
        #
        #             # if del_alone.find_previous_sibling() is None:
        #             #     print("miafasz?")
        #             # else:
        #             #     print(del_alone.find_previous_sibling().name, "-", del_alone.find_previous_sibling().text)

        # for para in sp.body.find_all("p"):
        #     for add_in in para.find_all("add", attrs={"type": "insert"}):
        #         if add_in.find_parent().name == "p" or add_in.find_parent().name == "quote":
        #             print(filename, add_in.find_parent().name)
        #         else:
        #             continue
        #             # print("Parent different")

        # for name in sp.body.find_all("add", {"type": "corr"}):
        #     name_prev = name.find_previous("del")
        #     print(name_prev.name)
        #     for nested in name_prev.find_all():
        #         print(nested)

        # for nam in sp.body.find_all("add", {"type": "corr"}):
        #     for nested in nam.find_all():
        #         if nested.name == "del":
        #             print(filename, nam)

        for ch in sp.body.find_all("choice"):
            if ch.find_parent().name != "p" and ch.find_parent().name != "quote" and ch.find_parent().name != "l":
                print(filename, "\t", ch.find_parent())


        """
        # Quote print
        xml_short = xml.split("/")[-1]
        with open("quote.txt", "a", encoding="utf8") as f_doc:
            for q in sp.find_all("quote"):
                for orig in q.find_all("orig"):
                    orig.string = "[Orig: " + orig.text + "]"
                    orig.unwrap()
                for sup in q.find_all("supplied"):
                    sup.string = "[Supplied: " + sup.text + "]"
                    sup.unwrap
                quote = q.text
                if str(q.next_sibling).startswith("<note"):
                    note = q.next_sibling.text
                    f_doc.write("Filename: " + xml_short + "\n" + "Quote: " + quote + "\n" + "Note: " + note + "\n\n")
                else:
                    f_doc.write("Filename: " + xml_short + "\n" + "Quote: " + quote + "\n" + "Note missing!" + "\n\n")
        """


if __name__ == '__main__':
    dir_name_in = "/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    filelist_in.sort()
    for i in filelist_in:
        main(i)
