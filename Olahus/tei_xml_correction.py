# What tags are there under <quote>
# Milestone unit "p": where?
import os
import re
from bs4 import BeautifulSoup


def normalize_text(string):
    # Input and output: STRING!!!! [ and ] => {}
    string = re.sub("[\n\t\s]+", " ", string)
    string = re.sub('\s+', " ", string)
    return string


def main(xml):
    ch_set_onefile = set()
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")
        sp1 = normalize_text(str(sp))
        sp = BeautifulSoup(sp1, "xml")
    for elem in sp.find_all("note", attrs={"type": "critic"}):
        if elem.next_sibling is not None:
            if str(elem.next_sibling).startswith("<"):
                continue
            else:
                next = elem.next_sibling.text
                if len(next) > 0:
                    ch_set_onefile.add(next[0])
                    if next[0] == "/" or next[0] == ")":
                        print(xml, elem)
    return ch_set_onefile


if __name__ == '__main__':
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("KUTYAFÜLE"):
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    ch_set_global = set()
    for i in filelist_in:
        s = main(i)
        ch_set_global = ch_set_global.union(s)
    print(ch_set_global)
