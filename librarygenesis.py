print("Loading...")

from libgen_api import LibgenSearch, SearchRequest, libgen_search
import os.path
import os
import urllib.request
import ssl
from urllib.parse import unquote
import json
import time
import exceptions
from slugify import slugify
slug = slugify()

class LibgenSearcher(LibgenSearch):
    def search(self, query):
        search_request = SearchRequest(query)
        return search_request.aggregate_request_data()
    def search_filtered(self, query, filters, exact_match=True):
        search_request = SearchRequest(query)
        results = search_request.aggregate_request_data()
        filtered_results = libgen_search.filter_results(
            results=results, filters=filters, exact_match=exact_match
        )
        return filtered_results
    
    
    
s = LibgenSearcher()


class book:
    def __init__(
        self,
        author,
        title,
        publisher,
        year,
        id,
        pages,
        language,
        size,
        extension,
        mirror_1,
        mirror_2,
        mirror_3,
        mirror_4,
        mirror_5,
        edit,
    ):
        self.id = id
        self.author = author
        self.title = title
        self.publisher = publisher
        self.year = year
        self.pages = pages
        self.language = language
        self.size = size
        self.extension = extension
        self.mirror_1 = mirror_1
        self.mirror_2 = mirror_2
        self.mirror_3 = mirror_3
        self.mirror_4 = mirror_4
        self.mirror_5 = mirror_5
        self.edit = edit


def Get_Item(array, key):
    if key in array:
        return array[key]
    else:
        return None


# workflow
# search for book title maybe author and maybe year.
def Search(Title, Author="", Year="", Extension="", readarr=False):
    filters = {}
    if Author != "":
        filters["Author"] = Author
    if Year != "":
        filters["Year"] = Year
    if Extension != "":
        filters["Extension"] = Extension

    if readarr:
        results = s.search_title(Title)
    elif filters == None:
        results = s.search_title(Title)
    else:
        results = s.search_filtered(Title, filters, exact_match=False)

    books = {}
    for result in results:
        b = book(
            Get_Item(result, "Author"),
            Get_Item(result, "Title"),
            Get_Item(result, "Publisher"),
            Get_Item(result, "Year"),
            Get_Item(result, "ID"),
            Get_Item(result, "Pages"),
            Get_Item(result, "Language"),
            Get_Item(result, "Size"),
            Get_Item(result, "Extension"),
            Get_Item(result, "Mirror_1"),
            Get_Item(result, "Mirror_2"),
            Get_Item(result, "Mirror_3"),
            Get_Item(result, "Mirror_4"),
            Get_Item(result, "Mirror_5"),
            Get_Item(result, "Edit"),
        )
        books[b.id] = b
    return books


def __init__():
    print("Searching...")
    while True:
        query = input("Please enter query: ")
        results = Search(query, Extension="pdf")
        # return top result(s) that matches for approval
        for i in enumerate(results):
            print("" + str(i) + " | ", end="")
            print(results[i]["Author"], end=" - ")
            print(results[i]["Title"], end=" (")
            print(results[i]["Year"], end=") ")
            print(results[i]["Extension"].upper())

        # select / approve result
        if len(results) == 0:
            print("No results")
            continue
        result = results[0]
        if len(results) > 1:
            user_selection = input("Enter a number: ")
            if user_selection == "":
                continue
            user_selection = int(user_selection)
            result = results[user_selection]
            break
        elif len(results) == 1:
            user_selection = "y"  # input("Download? [y|N]: ").lower()
            if user_selection != "y":
                continue
            break

class result:
    def __init__(self, item) -> None:
        self.item = item
        Mirror = json.loads('{"Mirror_1": "' + item.URL + '"}')
        print("Getting Download Link...")
        self.download_links = s.resolve_download_links(Mirror)
        if "GET" not in self.download_links:
            print("ERROR: No GET link!")
            return
        self.download_link = self.download_links["GET"]
        self.urifilename = unquote(self.download_link.split("/")[-1])
        self.author = self.urifilename.split("-")[0]
        self.title = self.urifilename.split("-")[1].split(".")[0]
        self.year = ""
        if "(" in Mirror:
            self.year = self.urifilename.split("(")[1]
            self.year = "(" + self.year.split(")")[0] + ")"
        self.extention = self.urifilename.split(".")[-1]

        self.file_name = (
            slug.run(self.author)
            + "-"
            + slug.run(self.title)
            + self.year
            + '.'
            + self.extention
        )
        self.file_name = slug.run(item.NZBName) + '.' + self.extention
        self.file_path = self.item.DestDir + '/' + self.file_name
        self.progress = 0
        

    def download(self):
        print("Downloading....")
        file_path = self.file_path
        DestDir = self.item.DestDir
        FinalDir = self.item.FinalDir
        
        # keep *nix pathing.
        if os.name == 'nt':
            DOWNLOAD_DIR = "P:\\media\\"
            INCOMPLETE_DIR = DOWNLOAD_DIR + "incomplete\\books\\"
            COMPLETED_DIR = DOWNLOAD_DIR + "completed\\books\\"
            file_path = self.file_path.replace("/downloads/incomplete/books/", INCOMPLETE_DIR).replace('/', '\\')
            DestDir = self.item.DestDir.replace("/downloads/incomplete/books/", INCOMPLETE_DIR).replace('/', '\\')
            FinalDir = self.item.FinalDir.replace("/downloads/completed/books/", COMPLETED_DIR).replace('/', '\\')
        
        if os.path.isfile(file_path):
            print("Already downloaded.")
            self.progress = 100
            return
        self.item.ActiveDownloads = 1

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(self.download_link, context=ctx)
        total_size = response.length
        self.item.PausedSizeLo = 500 # this is needed to get progress to work.
        # set total size of download for self.item
        self.item.FileSizeLo = total_size
        if os.path.isdir(DestDir):
            os.remove(DestDir)
        os.makedirs(DestDir)
        try:
            with open(file_path, "wb+") as f:
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break

                    self.progress = abs(
                        int(float(response.length) / float(total_size) * 100) - 100
                    )
                    self.item.SuccessArticles = self.progress * 10
                    self.item.RemainingFileCount = 1000 - self.item.SuccessArticles
                    # set remaining size of download for self.item
                    f.write(chunk)
                    
                    self.item.RemainingSizeLo = total_size - int((self.progress / 100) * total_size)
                    
                f.flush()
        except Exception as e:
            print(f"Failed to save: {e}")
        self.item.SuccessArticles = 1000
        self.item.ActiveDownloads = 0
        print("Done!")
        
