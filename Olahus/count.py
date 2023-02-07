import os

from bs4 import BeautifulSoup


def count_xml_body(xml):
    with open(xml, "r", encoding="utf8") as f_xml:
        soup = BeautifulSoup(f_xml, "xml")
        num_note_critic = len(soup.body.find_all("note", {"type": "critic"}))
        num_add_insert = len(soup.body.find_all("add", {"type": "insert"}))
        num_add_corr = len(soup.body.find_all("add", {"type": "corr"}))
        num_del_alone = len(soup.body.find_all("del")) - num_add_corr
        num_choice = len(soup.body.find_all("choice"))

        xml_tag_num = (num_note_critic, num_add_insert, num_add_corr, num_del_alone, num_choice)
        return xml_tag_num


def count_latex_body(tex):
    num_note_critic = tex.count(r"\&notecritic\&")
    num_add_insert = tex.count(r"\&addins\&")
    num_add_corr = tex.count(r"\&deladd\&")
    num_del_alone = tex.count(r"&delalone\&")
    num_choice = tex.count(r"&choice\&")

    latex_tag_num = (num_note_critic, num_add_insert, num_add_corr, num_del_alone, num_choice)
    return latex_tag_num


def file_list(path_in):
    filelist_in = []
    for dirpath, subdirs, files in os.walk(path_in):
        for x in files:
            if x.endswith("sz.xml"):
                # filelist_in.append(os.path.join(dirpath, x))
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    return filelist_in.sort()
