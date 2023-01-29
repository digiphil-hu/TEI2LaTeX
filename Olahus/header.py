from bs4 import BeautifulSoup
from normalize import normalize_text, latex_escape


def header2latex(soup):
    header_str = ""

    header_str += r"\begin{center}" + "\n\n"

    # Title, letter metadata
    title_num = soup.fileDesc.titleStmt.find("title", attrs={"type": "num"})
    title_num = normalize_text(title_num, {"header"}).text
    title_main = soup.fileDesc.titleStmt.find("title", attrs={"type": "main"})
    title_main = normalize_text(title_main, {"header"}).text
    sent = soup.find("correspAction", attrs={"type": "sent"})
    sent_pers = sent.persName
    sent_pers = normalize_text(sent_pers, {"header"}).text
    recieved = soup.find("correspAction", attrs={"type": "recieved"})
    recieved_pers = recieved.persName
    recieved_pers = normalize_text(recieved_pers, {"header"}).text
    date_of_creation = soup.creation.date
    date_of_creation = normalize_text(date_of_creation, {"header"}).text
    place_of_creation = soup.creation.placeName
    place_of_creation = normalize_text(place_of_creation, {"header"}).text

    # Title including response to, has response
    resp_to = ""
    has_resp = ""
    if soup.find("relatedItem", attrs={"type": "responseTo"}) is not None:
        resp_to = soup.find("relatedItem", attrs={"type": "responseTo"}).bibl.ref.text
    if soup.find("relatedItem", attrs={"type": "hasResponse"}) is not None:
        has_resp = soup.find("relatedItem", attrs={"type": "hasResponse"}).bibl.ref.text

    header_str += r"\section*{\textsubscript{" + resp_to + "}" \
                  + r"\textbf{" + title_num + "}"\
                  + r"\textsubscript{" + has_resp + r"}\\~\vspace{-1em}\\" \
                  + sent_pers + " to " + recieved_pers + \
                  r"\\~\vspace{-1.4em}\\" + place_of_creation + ", " + date_of_creation\
                  + r"}\addcontentsline{toc}{section}{" \
                  + title_num + r".~" + title_main + "}" + "\n"
    header_str += r"\renewcommand{\thefootnoteA}{\arabic{footnoteA}}\setcounter{footnoteA}{0}" + "\n\n"

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
                photo = normalize_text(photo, {"header"}).text
                print(photo)
                header_str += r"\textit{" + photo + "}" + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        if publication.text == "" or publication.text == " ":
            continue
        else:
            publication = normalize_text(publication, {"header"})
            header_str += "\\textit{" + "Published: " + "}" + publication.text + "\n\n"

    # Insert translation
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        if translation.text == "" or translation.text == " ":
            continue
        else:
            for p in translation:
                p = normalize_text(p, {"header"})
                header_str += p.text + "\n"

    # Insert critIntro (Notes:). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Notes:") and p.text != "Notes:":
                p = normalize_text(p, {"header"}).text
                header_str += p + "\n\n"

    header_str += r"\end{center}" + "\n\n"

    header_str = latex_escape(header_str)

    return header_str, title_num
