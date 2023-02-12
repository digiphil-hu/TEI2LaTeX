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
        num_quote = len(soup.body.find_all("quote"))
        num_seg = len(soup.body.find_all("seg"))

        xml_tag_num = (num_note_critic, num_add_insert, num_add_corr, num_del_alone, num_choice, num_quote, num_seg)
        return xml_tag_num


def count_latex_body(tex):
    num_note_critic = tex.count(r"\&notecritic\&")
    num_add_insert = tex.count(r"\&addins\&")
    num_add_corr = tex.count(r"\&deladd\&")
    num_del_alone = tex.count(r"\&delalone\&")
    num_choice = tex.count(r"\&choice\&")
    num_quote = tex.count(r"\&quote\&")
    num_seg = tex.count(r"\&seg\&")

    latex_tag_num = (num_note_critic, num_add_insert, num_add_corr, num_del_alone, num_choice, num_quote, num_seg)
    return latex_tag_num


def file_list(path_in):
    filelist_in = []
    for dirpath, subdirs, files in os.walk(path_in):
        for x in files:
            if x.endswith("sz.xml"):
                filelist_in.append(os.path.join(dirpath, x))
                # pass
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    filelist_in.sort()
    return filelist_in


def change_xml_filename(xml):
    with open(xml, "r", encoding="utf8") as f_in:
        f_text = f_in.read()
        soup = BeautifulSoup(f_text, "xml")
        letter_num = soup.fileDesc.titleStmt.find("title", attrs={"type": "num"}).text
        oldfilename = xml.split("/")[-1]
        oldpath = xml.replace("XML/" + oldfilename, "")
        newxml = oldpath + "NEWNAMES/" + letter_num + "_" + oldfilename
        print(newxml)
        with open(newxml, "w", encoding="utf8") as f_out:
            f_out.write(f_text)

