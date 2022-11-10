from bs4 import BeautifulSoup
from normalize import normalize_text


def header2latex(soup):
    header_str = ""

    # Response to, has response
    resp_to = ""
    has_resp = ""
    if soup.find("relatedItem", attrs={"type": "responseTo"}) is not None:
        resp_to = soup.find("relatedItem", attrs={"type": "responseTo"}).bibl.ref.text
    if soup.find("relatedItem", attrs={"type": "hasResponse"}) is not None:
        has_resp = soup.find("relatedItem", attrs={"type": "hasResponse"}).bibl.ref.text

    # Insert title
    title_num = soup.fileDesc.titleStmt.find("title", attrs={"type": "num"})
    title_num = normalize_text(title_num, {"all"}).text
    title_main = soup.fileDesc.titleStmt.find("title", attrs={"type": "main"})
    title_main = normalize_text(title_main, {"all"}).text

    header_str += r"\section*{\textsubscript{" + resp_to + "}" + title_num + r"\textsubscript{" + has_resp + r"}\\~\\" \
                  + title_main + r"}\addcontentsline{toc}{section}{" + r".~" + title_main + "}" + "\n\n"

    # Insert manuscript description
    institution = soup.institution.text
    repository = soup.repository.text
    folio = soup.measure.text
    header_str += r"\textit{Manuscript used}: " + institution + ", " + repository + ", fol. " + folio + "\n\n"

    # Insert critIntro (Photo copy). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for photo in elem.find_all("p"):
            if photo.text.startswith("Photo copy:") and photo.text != "Photo copy:":
                photo = normalize_text(photo, {"all"}).text
                print(photo)
                header_str += r"\textit{" + photo + "}" + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        if publication.text == "" or publication.text == " ":
            continue
        else:
            publication = normalize_text(publication, {"all"})
            header_str += "\\textit{" + "Published: " + "}" + publication.text + "\n\n"

    # Insert translation
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        if translation.text == "" or translation.text == " ":
            continue
        else:
            translation = normalize_text(translation, {"all"})
            header_str += translation.text + "\n\n"

    # Insert critIntro (Notes:). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Notes:") and p.text != "Notes:":
                p = normalize_text(p, {"all"}).text
                header_str += p + "\n\n"

    header_str += r"\end{center}" + "\n\n"
    return header_str
