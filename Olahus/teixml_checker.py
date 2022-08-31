# What tags are there under <quote>
# Milestone unit "p": where?
import os
import re
from bs4 import BeautifulSoup

def normalize_text(string):
    # Input and output: STRING!!!! [ and ] => {}
    string = re.sub("[\n\t\s]+", " ", string)
    string = re.sub('\s+', " ", string)
    string = re.sub("\[", "{[}", string)
    string = re.sub("\]", "{]}", string)
    return string


def main(xml):
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")
        sp1 = normalize_text(str(sp))
        sp = BeautifulSoup(sp1, "xml")
        print(xml)

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

        #<choice> <orig> és <supplied> check
        for ch in sp.find_all("choice"):
            if len(ch.find_all("orig")) == 0:
                print(ch, xml)
            if len(ch.find_all("supplied")) == 0:
                print(ch, xml)

        #<orig><supplied> under <choice>
        for sup in sp.find_all("supplied"):
            parent = sup.find_parent(re.compile("[a-z]+"))
            if parent.name != "choice":
                print(parent.name, xml)
        for orig in sp.find_all("orig"):
            parent = sup.find_parent(re.compile("[a-z]+"))
            if parent.name != "choice":
                print(parent.name, xml)

        # p in p
        for p_p in sp.p.find_all("p"):
            print("<p> alatt <p>: ", xml)

        # <quote><p>; <quote><quote>; <quote> + MISSING sibling
        for q in sp.find_all("quote"):
            if q.next_sibling is None:
                print("Quote next tag missing: ", xml)
            if q.next_sibling is not None and q.next_sibling.name != "note":
                print(f"Quote but no note, but: {q.next_sibling.name}", xml)
            for q_sub in sp.quote.findChildren(re.compile("[a-zA-Z]+")):
                if q_sub.name == "p":
                    print("Quote alatt: " , xml)
        # <quote> in verso?
        for div in sp.find_all("div", attrs={"type": "verso"}):
            for elem in div.find_all("quote"):
                print("Quote in verso: ", xml)

        # del alatt del
        for d1 in sp.find_all("del"):
            for d2 in d1.find_all("del"):
                print("Del alatt del: ", xml)

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
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("KUTYAFÜLE"):
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))

    for i in filelist_in:
        main(i)
