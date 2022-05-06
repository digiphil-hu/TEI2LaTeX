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


        # Delete <ref> tags
        for i in sp.find_all("ref"):
            i.extract()

        # Error check
        for d in sp.find_all("del"):
            if str(d.next_sibling).startswith("<add"):
                d_cor = d["corresp"]
                a_cor = d.next_sibling["corresp"]
                if d_cor != a_cor:
                    print("File name: " + xml + "Del corresp: " + d_cor + "Add corrsp: " + a_cor)

        # p in p
        for p_p in sp.p.find_all("p"):
            print(p_p)

        # Quote
        for q in sp.find_all("quote", recursive="not"):
            for q_sub in sp.quote.find_all(re.compile("[a-zA-Z]+")):
                print(q_sub, ",", xml)



if __name__ == '__main__':
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))

    for i in filelist_in:
        main(i)
